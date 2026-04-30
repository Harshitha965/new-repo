from fastapi import HTTPException
from pydantic import ValidationError
from typing import Dict, Any, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.skills.schemas.base import SkillRequest
from app.skills.schemas.contracts import (
    BookAppointmentPayload,
    SendCommunicationPayload,
    ActVisionOcrPayload,
    KnwReportSynthesisPayload,
    ActChecklistVerifyPayload,
    SklPreOpGatekeeperPayload,
    SklExpertSynthesisPayload,
    SklBaselineVigilancePayload
)
from app.skills.database.models import SkillDefinition

# The registry matching a skill_name to its required Pydantic Payload
SKILL_REGISTRY: Dict[str, Type[BaseModel]] = {
    "book_appointment": BookAppointmentPayload,
    "send_communication": SendCommunicationPayload,
    "ACT_VISION_OCR": ActVisionOcrPayload,
    "KNW_REPORT_SYNTHESIS": KnwReportSynthesisPayload,
    "ACT_CHECKLIST_VERIFY": ActChecklistVerifyPayload,
    "SKL_PRE_OP_GATEKEEPER": SklPreOpGatekeeperPayload,
    "SKL_EXPERT_SYNTHESIS": SklExpertSynthesisPayload,
    "SKL_BASELINE_VIGILANCE": SklBaselineVigilancePayload
}

class ValidationGateway:
    @staticmethod
    def authorize_request(db: Session, request: SkillRequest) -> None:
        """
        Checks the database to ensure the skill is active and 
        the expert is authorized to run it (mocked expert logic).
        """
        skill_def = db.query(SkillDefinition).filter(SkillDefinition.skill_name == request.skill_name).first()
        if skill_def and not skill_def.is_active:
            raise HTTPException(
                status_code=403, 
                detail=f"Skill '{request.skill_name}' is currently disabled by the administrator."
            )
        # Note: further expert-specific permission checks could be added here.

    @staticmethod
    def validate_request(request: SkillRequest) -> BaseModel:
        """
        Intercepts the SkillRequest, looks up the corresponding schema,
        and validates the payload.
        """
        skill_name = request.skill_name
        payload_schema = SKILL_REGISTRY.get(skill_name)
        
        if not payload_schema:
            raise HTTPException(
                status_code=400,
                detail=f"Skill '{skill_name}' is not recognized in the registry."
            )
            
        try:
            # Validate the nested payload dictionary against the specific schema
            validated_payload = payload_schema(**request.payload)
            return validated_payload
        except ValidationError as e:
            # Reformat the Pydantic error into a structured response for the LLM
            error_details = e.errors()
            missing_fields = []
            invalid_fields = []
            
            for err in error_details:
                field = err["loc"][0] if err["loc"] else "unknown"
                if err["type"] == "missing":
                    missing_fields.append(field)
                else:
                    invalid_fields.append({"field": field, "error": err["msg"]})
            
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Payload Validation Failed",
                    "missing_fields": missing_fields,
                    "invalid_fields": invalid_fields,
                    "correction_instructions": "Please correct the payload according to the strict schema."
                }
            )
