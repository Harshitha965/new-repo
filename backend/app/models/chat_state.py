from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatState(BaseModel):
    expert_id: str
    session_id: str
    query: str
    
    # Internal Trajectory
    retrieved_cases: List[dict] = Field(default_factory=list)
    rationale: str = ""
    
    # NEW: Intent Detection
    intent_type: str = "knowledge"  # "knowledge" | "action"
    detected_skill: str = ""        # e.g. "book_appointment"
    extracted_params: Dict[str, Any] = Field(default_factory=dict)
    
    # NEW: Skill Execution Results
    skill_result: Optional[Dict[str, Any]] = None
    skill_status: str = ""          # "SUCCESS" | "FAILED" | "DISABLED"
    
    # Final Output
    response: str = ""
    confidence: float = 0.0
    persona_mode: str = "offline"
