from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.skills.database.session import get_db
from app.skills.database.models import SkillDefinition, ExecutionLog

router = APIRouter()

@router.get("/skills")
def get_skills(db: Session = Depends(get_db)):
    """Fetch all skill definitions for the Guardrail Editor."""
    skills = db.query(SkillDefinition).all()
    return [
        {
            "id": s.id,
            "skill_name": s.skill_name,
            "is_active": s.is_active,
            "requires_human_approval": s.requires_human_approval
        }
        for s in skills
    ]

@router.post("/skills/{skill_name}/toggle")
def toggle_skill(skill_name: str, db: Session = Depends(get_db)):
    """Toggle the is_active status of a skill."""
    skill = db.query(SkillDefinition).filter(SkillDefinition.skill_name == skill_name).first()
    if not skill:
        # If it doesn't exist, create it (mocking initial discovery)
        skill = SkillDefinition(skill_name=skill_name, is_active=True)
        db.add(skill)
    else:
        skill.is_active = not skill.is_active
    
    db.commit()
    db.refresh(skill)
    return {"skill_name": skill.skill_name, "is_active": skill.is_active}

@router.get("/logs")
def get_logs(db: Session = Depends(get_db), limit: int = 50):
    """Fetch recent execution logs for the Audit View."""
    logs = db.query(ExecutionLog).order_by(ExecutionLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "workflow_id": l.workflow_id,
            "expert_id": l.expert_id,
            "skill_name": l.skill_name,
            "status": l.status,
            "raw_payload": l.raw_payload,
            "error_trace": l.error_trace,
            "created_at": l.created_at.isoformat() + "Z" if l.created_at else None
        }
        for l in logs
    ]
