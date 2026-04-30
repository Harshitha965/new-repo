from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.skills.schemas.base import SkillRequest, SkillResponse
from app.skills.middleware.validation import ValidationGateway
from app.skills.middleware.hooks import StateTracker
from app.skills.database.session import get_db

router = APIRouter()

@router.post("/execute/{skill_name}", response_model=SkillResponse)
async def execute_skill(skill_name: str, request: SkillRequest, db: Session = Depends(get_db)):
    """
    Endpoint for the LLM to trigger a skill.
    The request is validated against strict Pydantic schemas and state is logged.
    """
    # 1. Basic sanity check
    if skill_name != request.skill_name:
        raise HTTPException(status_code=400, detail="Path parameter skill_name does not match body skill_name")
    
    # 2. Validation & Authorization Gateway
    ValidationGateway.authorize_request(db, request)
    validated_payload = ValidationGateway.validate_request(request)
    
    # 3. Log Execution Start (State Engine)
    log_entry = StateTracker.log_execution_start(db, request)
    
    # 4. Dynamic Execution Routing
    try:
        payload_dict = validated_payload.model_dump()
        mock_result = {}
        
        from app.skills.wrappers.calendar_service import CalendarServiceWrapper
        from app.skills.wrappers.email_service import EmailServiceWrapper
        from app.skills.functional.orchestrator import FunctionalOrchestrator
        
        if skill_name == "book_appointment":
            mock_result = CalendarServiceWrapper.book_appointment(payload_dict)
        elif skill_name == "send_communication":
            mock_result = EmailServiceWrapper.send_communication(payload_dict)
        elif skill_name == "SKL_PRE_OP_GATEKEEPER":
            mock_result = FunctionalOrchestrator.execute_pre_op_gatekeeper(payload_dict)
        elif skill_name == "SKL_EXPERT_SYNTHESIS":
            mock_result = FunctionalOrchestrator.execute_expert_synthesis(payload_dict)
        elif skill_name == "SKL_BASELINE_VIGILANCE":
            mock_result = FunctionalOrchestrator.execute_baseline_vigilance(payload_dict)
        else:
            # Default generic execution for skills without explicit wrappers yet
            mock_result = {
                "message": f"Successfully executed generic {skill_name}",
                "processed_data": payload_dict
            }
        
        # 5. Log Success
        StateTracker.log_execution_success(db, log_entry.id, mock_result)
        
        return SkillResponse(
            status="SUCCESS",
            data=mock_result,
            error_message=None,
            state_reference=UUID(log_entry.id)
        )
        
    except Exception as e:
        # 5. Log Failure (HITL Trigger)
        StateTracker.log_execution_failure(db, log_entry.id, str(e))
        
        return SkillResponse(
            status="FAILED",
            data=None,
            error_message=str(e),
            state_reference=UUID(log_entry.id)
        )
