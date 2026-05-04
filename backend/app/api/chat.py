from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..graph.chat_pipeline import create_chat_pipeline
from ..models.chat_state import ChatState
from ..services.pii_scrubber import PIIScrubber
import time

router = APIRouter()

class ChatRequest(BaseModel):
    expert_id: str
    message: str
    session_id: str

@router.post("/chat/message")
async def chat_message(req: ChatRequest):
    scrubber = PIIScrubber()
    pipeline = create_chat_pipeline()
    initial_state = ChatState(
        expert_id=req.expert_id,
        session_id=req.session_id,
        query=scrubber.scrub(req.message)
    )
    
    try:
        # Run LangGraph Pipeline
        # We don't use threadpool here because this is relatively fast and we want to return response.
        # But wait, Prisma async in node might need to be run in a way that doesn't block.
        # LangGraph invoke is synchronous, so we should run it in a threadpool to not block FastAPI
        import asyncio
        start_time = time.time()
        
        result_state_dict = await asyncio.to_thread(
            pipeline.invoke,
            initial_state
        )
        
        # Calculate latency
        latency = int((time.time() - start_time) * 1000)
        
        # Extract from state dict returned by LangGraph
        response_text = scrubber.restore(result_state_dict.get("response", ""))
        confidence = result_state_dict.get("confidence", 0.0)
        persona_mode = result_state_dict.get("persona_mode", "offline")
        rationale = scrubber.restore(result_state_dict.get("rationale", ""))
        sources = [f"Logic Vault ID: {r.get('scenario_id', 'Unknown')}" for r in result_state_dict.get("retrieved_cases", [])]
        
        # NEW SKILL FIELDS
        intent_type = result_state_dict.get("intent_type", "knowledge")
        skill_result = result_state_dict.get("skill_result")
        skill_status = result_state_dict.get("skill_status", "")
        detected_skill = result_state_dict.get("detected_skill", "")
        extracted_params = result_state_dict.get("extracted_params", {})
        
        return {
            "response": response_text,
            "confidence": confidence,
            "persona_mode": persona_mode,
            "sources": sources,
            "rationale": rationale,
            "latency_ms": latency,
            "intent_type": intent_type,
            "skill_result": skill_result,
            "skill_status": skill_status,
            "detected_skill": detected_skill,
            "extracted_params": extracted_params
        }
    except Exception as e:
        print(f"Chat Engine Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
