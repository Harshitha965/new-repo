from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.skills.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class SkillDefinition(Base):
    __tablename__ = "skill_definitions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    skill_name = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    requires_human_approval = Column(Boolean, default=False)

class StateLedger(Base):
    __tablename__ = "state_ledger"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, index=True)
    expert_id = Column(String, index=True)
    current_state = Column(String) # e.g., PENDING_EXECUTION, WAITING_FOR_HUMAN
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, index=True)
    expert_id = Column(String, index=True)
    skill_name = Column(String)
    raw_payload = Column(JSON)
    status = Column(String) # PENDING, SUCCESS, FAILED
    error_trace = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
