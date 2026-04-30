from ...models.state import GraphState
from ...services.parser import HierarchicalParser
from ...services.embeddings import EmbeddingService
from ...services.pii_scrubber import PIIScrubber
from ...services.supabase_client import SupabaseService
from ...models.schemas import DocumentChunk
import os


def ingestion_node(state: GraphState) -> GraphState:
    print(f"--- INGESTION: Processing Document {state.document_id} ---")

    # Use the file path passed from the ingest API via state — no hardcoded paths
    if not state.source_path or not os.path.exists(state.source_path):
        print(f"[ERROR] source_path missing or file not found: {state.source_path}")
        return state

    parser = HierarchicalParser()
    scrubber = PIIScrubber()
    embedder = EmbeddingService()
    db = SupabaseService()

    # Skip re-ingestion if chunks already exist for this document
    existing_count = 0
    try:
        res = db.client.table("document_chunks").select("id", count="exact").eq("document_id", state.document_id).limit(0).execute()
        existing_count = res.count or 0
    except Exception:
        pass

    file_path = state.source_path

    if existing_count > 0:
        print(f"[SKIP] {existing_count} chunks already exist for document {state.document_id}. Skipping re-ingestion.")
        # Still parse locally to populate state.raw_chunks for downstream nodes
        if file_path.endswith('.docx'):
            chunks = parser.parse_docx(file_path)
        elif file_path.endswith('.pdf'):
            chunks = parser.parse_pdf(file_path)
        else:
            return state
        for chunk in chunks:
            chunk["content"] = scrubber.scrub(chunk["content"])
            chunk["document_id"] = state.document_id
        state.raw_chunks = [DocumentChunk(**c) for c in chunks]
        return state

    all_chunks = []

    # Parse the single uploaded file
    if file_path.endswith('.docx'):
        chunks = parser.parse_docx(file_path)
    elif file_path.endswith('.pdf'):
        chunks = parser.parse_pdf(file_path)
    else:
        print(f"[ERROR] Unsupported file type: {file_path}")
        return state

    for chunk in chunks:
        chunk["content"] = scrubber.scrub(chunk["content"])

    # Filter out empty/whitespace-only chunks
    chunks = [c for c in chunks if c["content"].strip()]

    if not chunks:
        print(f"[ERROR] No text content extracted from {os.path.basename(file_path)}. The document may be scanned/image-only.")
        return state

    # Generate embeddings in batch and save to Supabase
    texts = [c["content"] for c in chunks]
    embeddings = embedder.get_embeddings_batch(texts)

    db_chunks = []
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]
        chunk["document_id"] = state.document_id
        db_chunks.append(chunk)
        all_chunks.append(DocumentChunk(**chunk))

    db.insert_chunks(db_chunks)
    print(f"Ingested {len(chunks)} chunks from {os.path.basename(file_path)}")

    state.raw_chunks = all_chunks
    return state

