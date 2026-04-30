from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
import uuid
import hashlib
from ..graph.pipeline import create_pipeline
from ..models.state import GraphState
from ..services.pii_scrubber import PIIScrubber

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory registry of file hashes to detect duplicates across server restarts
# Maps file_hash -> {"document_id": ..., "filename": ...}
_upload_hash_registry: dict[str, dict] = {}

def _compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _rebuild_hash_registry(upload_dir: str):
    """Scan existing uploads to rebuild the hash registry on startup."""
    if _upload_hash_registry:
        return  # Already built
    if not os.path.exists(upload_dir):
        return
    for fname in os.listdir(upload_dir):
        fpath = os.path.join(upload_dir, fname)
        if os.path.isfile(fpath):
            try:
                file_hash = _compute_file_hash(fpath)
                # Extract document_id from filename format: {uuid}_{original_name}
                doc_id = fname.split("_", 1)[0]
                _upload_hash_registry[file_hash] = {
                    "document_id": doc_id,
                    "filename": fname.split("_", 1)[1] if "_" in fname else fname,
                }
            except Exception:
                pass

@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.docx', '.pdf')):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are supported.")
    
    file_id = str(uuid.uuid4())
    # Use absolute path derived from __file__ — never hardcode a drive letter
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "uploads")
    upload_dir = os.path.normpath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # Rebuild hash registry from existing files (runs once)
    _rebuild_hash_registry(upload_dir)

    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Duplicate detection: hash the uploaded file and check if it already exists
    file_hash = _compute_file_hash(file_path)
    if file_hash in _upload_hash_registry:
        existing = _upload_hash_registry[file_hash]
        # Remove the duplicate file we just saved — use the original one
        os.remove(file_path)
        existing_doc_id = existing["document_id"]
        
        # Find the original file on disk to re-run the pipeline (state is in-memory and may be lost on restart)
        original_path = None
        for fname in os.listdir(upload_dir):
            if fname.startswith(existing_doc_id):
                original_path = os.path.join(upload_dir, fname)
                break
        
        if original_path and os.path.exists(original_path):
            # Re-run the pipeline to restore in-memory state (no new chunks created — chunks already exist in Supabase)
            import asyncio
            pipeline = create_pipeline()
            initial_state = GraphState(document_id=existing_doc_id, source_path=original_path)
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(pipeline.invoke, initial_state, {"configurable": {"thread_id": existing_doc_id}}),
                    timeout=300.0
                )
            except Exception:
                pass
            return {
                "message": "Document already exists. Pipeline state restored.",
                "document_id": existing_doc_id,
                "file_path": original_path,
                "pipeline_status": "restored_from_duplicate",
                "is_duplicate": True
            }
        else:
            raise HTTPException(status_code=409, detail="Document was previously uploaded but the file is missing on disk. Please contact support.")
    
    # Register this file hash
    _upload_hash_registry[file_hash] = {"document_id": file_id, "filename": file.filename}

    # Trigger LangGraph Pipeline — pass file_path via state so the ingestion node doesn't hardcode
    import asyncio
    
    pipeline = create_pipeline()
    initial_state = GraphState(document_id=file_id, source_path=file_path)
    
    try:
        # Run synchronous pipeline.invoke in a threadpool so it doesn't block FastAPI
        # Increased timeout to 5 minutes (300 seconds) because heavy OpenAI processing takes time
        result = await asyncio.wait_for(
            asyncio.to_thread(
                pipeline.invoke, 
                initial_state, 
                {"configurable": {"thread_id": file_id}}
            ),
            timeout=300.0
        )
        return {
            "message": "Ingestion started and processed up to HITL breakpoint",
            "document_id": file_id,
            "file_path": file_path,
            "pipeline_status": "paused_at_socratic_node"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context")
async def get_industry_context():
    from ..services.context_manager import ContextManager
    cm = ContextManager()
    return cm.get_context()

@router.get("/state/{document_id}")
async def get_pipeline_state(document_id: str):
    """Fetches the current suspended state of the LangGraph pipeline for a specific document."""
    from ..graph.pipeline import create_pipeline
    pipeline = create_pipeline()
    
    try:
        # Fetch the state using the checkpointer by passing the thread_id
        state = pipeline.get_state({"configurable": {"thread_id": document_id}})
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="State not found for this document.")
            
        return state.values
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resolve")
async def resolve_scenario(document_id: str, scenario_id: str, audio: UploadFile = File(...)):
    # 1. Save audio to a temp file (next to the running script, no hardcoded paths)
    temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"temp_audio_{scenario_id}.wav")
    with open(temp_path, "wb") as f:
        f.write(await audio.read())
        
    # 2. Transcribe locally using Faster-Whisper
    from ..services.stt import STTService
    stt = STTService()
    transcript = stt.transcribe_audio(temp_path)
    scrubber = PIIScrubber()
    transcript = scrubber.scrub(transcript)
    
    # 3. Clean up temp file
    os.remove(temp_path)
    
    # 4. Return transcript to the UI — graph resumption is handled via POST /commit
    return {
        "status": "transcribed",
        "document_id": document_id,
        "scenario_id": scenario_id,
        "transcript": transcript
    }
@router.post("/commit")
async def commit_to_vault(scenario_id: str, expert_decision: str, archetype: str, industry: str = "fertility"):
    """Moves verified logic from the pipeline into the production Logic Vault."""
    from ..services.embeddings import EmbeddingService
    from ..services.supabase_client import SupabaseService
    
    scrubber = PIIScrubber(industry=industry)
    embedder = EmbeddingService()
    db = SupabaseService()
    clean_expert_decision = scrubber.scrub(expert_decision)
    
    # 1. Generate embedding for the verified scenario context
    # This allows the runtime query to match patient questions to this specific expert logic
    vector = embedder.get_embedding(clean_expert_decision)
    
    # 2. Persist to high-purity expert_dna table
    data = {
        "scenario_id": scenario_id,
        "expert_decision": clean_expert_decision,
        "impact_archetype": archetype,
        "industry": industry,
        "embedding": vector
    }
    
    db.insert_expert_dna(data)
    
    return {"status": "committed", "message": "Expert DNA added to production Logic Vault."}

@router.get("/file-info/{document_id}")
async def get_file_info(document_id: str):
    """Returns the filename and URL for an uploaded document so the frontend can embed a viewer."""
    upload_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "uploads"))
    
    if not os.path.exists(upload_dir):
        raise HTTPException(status_code=404, detail="Uploads directory not found.")
    
    # Files are stored as {document_id}_{original_filename}
    for fname in os.listdir(upload_dir):
        if fname.startswith(document_id):
            original_name = fname[len(document_id) + 1:]  # strip uuid_ prefix
            file_ext = os.path.splitext(fname)[1].lower()
            return {
                "filename": original_name,
                "stored_name": fname,
                "file_url": f"http://localhost:8000/uploads/{fname}",
                "file_type": "docx" if file_ext == ".docx" else "pdf" if file_ext == ".pdf" else "unknown"
            }
    
    raise HTTPException(status_code=404, detail="File not found for this document ID.")
