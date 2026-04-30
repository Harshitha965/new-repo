from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime

class SkillMetadata(BaseModel):
    workflow_id: UUID
    expert_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SkillRequest(BaseModel):
    skill_name: str = Field(description="The exact name of the skill to execute")
    payload: Dict[str, Any] = Field(description="The arguments required by the skill")
    metadata: SkillMetadata

class SkillResponse(BaseModel):
    status: str = Field(description="SUCCESS | FAILED | PENDING_HUMAN")
    data: Optional[Dict[str, Any]] = Field(default=None, description="The result of the skill execution")
    error_message: Optional[str] = Field(default=None, description="Error details if the skill failed")
    state_reference: Optional[UUID] = Field(default=None, description="UUID of the log entry in the state ledger")
