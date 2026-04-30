from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal, Union
from datetime import datetime
from uuid import UUID

# 1. Book Appointment
class BookAppointmentPayload(BaseModel):
    patient_id: UUID
    appointment_time: datetime = Field(description="ISO-8601 string, must be in the future")
    reason_code: Literal["CONSULT", "FOLLOW_UP", "URGENT"]

# 2. Send Communication
class SendCommunicationPayload(BaseModel):
    template_id: str
    recipient_address: str = Field(description="Email or WhatsApp number")
    dynamic_vars: dict = Field(default_factory=dict, description="Variables for the template")

# 3. Vision OCR
class ActVisionOcrPayload(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    extraction_type: Literal["VITALS", "LAB_RESULTS", "GENERAL_TEXT"]

# 4. Report Synthesis
class KnwReportSynthesisPayload(BaseModel):
    patient_id: UUID
    data_sources: List[str] = Field(description="List of IDs or references to the data sources")

# 5. Checklist Verify
class ActChecklistVerifyPayload(BaseModel):
    patient_id: UUID
    required_documents: List[str] = Field(description="List of document types that must be present")

# 6. Pre-Op Gatekeeper (Functional Skill)
class SklPreOpGatekeeperPayload(BaseModel):
    patient_id: UUID
    surgery_date: datetime = Field(description="ISO-8601 string, date of scheduled surgery")
    required_documents: List[str] = Field(description="Checklist of required pre-op documents")

# 7. Expert Synthesis (Functional Skill)
class SklExpertSynthesisPayload(BaseModel):
    patient_id: UUID
    data_sources: List[str] = Field(description="List of IDs or references to the data sources")
    release_approved: bool = Field(description="Safety toggle. Must be True to dispatch externally.")

# 8. Baseline Vigilance (Functional Skill)
class SklBaselineVigilancePayload(BaseModel):
    patient_id: UUID
    baseline_thresholds: dict = Field(
        description="Patient-specific baseline ranges, e.g. {'bp_systolic': [100, 140], 'hr': [60, 100]}"
    )
    image_url: Optional[str] = Field(default=None, description="URL of bedside monitor image for OCR")
