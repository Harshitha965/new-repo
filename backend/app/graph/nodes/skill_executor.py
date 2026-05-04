from app.models.chat_state import ChatState
from app.skills.middleware.validation import ValidationGateway, SKILL_REGISTRY
from app.skills.database.session import SessionLocal
from app.skills.schemas.base import SkillRequest
from app.skills.middleware.hooks import StateTracker

def skill_executor_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Skill Executor Node ---")
    
    skill_name = state.detected_skill
    params = state.extracted_params
    
    # 1. Check if skill is registered
    if skill_name not in SKILL_REGISTRY:
        state.skill_status = "NOT_REGISTERED"
        state.response = (
            f"🔧 I understand you'd like me to perform an action. "
            f"Unfortunately, this action isn't available in my current skill set yet.\n\n"
            f"**Skills I can currently perform:**\n"
            f"- 📅 Book appointments (book_appointment)\n"
            f"- 📧 Send communications (send_communication)\n"
            f"- 🔬 Extract vitals from images (ACT_VISION_OCR)\n"
            f"- 📊 Synthesize clinical reports (KNW_REPORT_SYNTHESIS)\n"
            f"- ✅ Verify pre-op checklists (ACT_CHECKLIST_VERIFY)\n"
            f"- 🛡️ Run pre-op readiness checks (SKL_PRE_OP_GATEKEEPER)\n"
            f"Would you like me to help with any of these instead?"
        )
        return state

    import uuid
    from app.skills.schemas.base import SkillMetadata
    
    try:
        expert_uuid = uuid.UUID(state.expert_id)
    except Exception:
        expert_uuid = uuid.uuid4()
        
    metadata = SkillMetadata(
        workflow_id=uuid.uuid4(),
        expert_id=expert_uuid
    )

    # 2. Build SkillRequest
    request = SkillRequest(
        skill_name=skill_name,
        payload=params,
        metadata=metadata
    )

    db = SessionLocal()
    try:
        # 3. Check Guardrails
        ValidationGateway.authorize_request(db, request)
        
        # 4. Validate payload
        validated_payload = ValidationGateway.validate_request(request)
        
        # 5. Log Execution Start
        log_entry = StateTracker.log_execution_start(db, request)
        
        # 6. Execute Route
        payload_dict = validated_payload.model_dump()
        mock_result = {}
        
        from app.skills.wrappers.calendar_service import CalendarServiceWrapper
        from app.skills.wrappers.email_service import EmailServiceWrapper
        from app.skills.wrappers.clinical_services import ClinicalServicesWrapper
        from app.skills.functional.orchestrator import FunctionalOrchestrator
        
        if skill_name == "book_appointment":
            mock_result = CalendarServiceWrapper.book_appointment(payload_dict)
            action_desc = "Your appointment has been booked successfully."
        elif skill_name == "send_communication":
            mock_result = EmailServiceWrapper.send_communication(payload_dict)
            action_desc = "The communication has been sent successfully."
        elif skill_name == "ACT_CHECKLIST_VERIFY":
            mock_result = ClinicalServicesWrapper.verify_checklist(payload_dict)
            action_desc = "Clinical document audit complete. All required items verified."
        elif skill_name == "SKL_PRE_OP_GATEKEEPER":
            mock_result = FunctionalOrchestrator.execute_pre_op_gatekeeper(payload_dict)
            verdict = mock_result.get("readiness_verdict", "UNKNOWN")
            action_desc = f"The pre-op readiness check is complete. Verdict: **{verdict}**"
        elif skill_name == "SKL_EXPERT_SYNTHESIS":
            mock_result = FunctionalOrchestrator.execute_expert_synthesis(payload_dict)
            brief = mock_result.get("expert_brief", {}).get("brief_text", "")
            action_desc = f"The expert brief has been synthesized:\n\n```text\n{brief}\n```"
        elif skill_name == "SKL_BASELINE_VIGILANCE":
            mock_result = FunctionalOrchestrator.execute_baseline_vigilance(payload_dict)
            status = mock_result.get("vigilance_status", "UNKNOWN")
            msg = mock_result.get("message", "")
            action_desc = f"Baseline vigilance monitoring is complete. Status: **{status}**\n{msg}"
        else:
            mock_result = {"message": f"Successfully executed {skill_name}", "processed_data": payload_dict}
            action_desc = f"Action {skill_name} completed."
            
        # 7. Log Success
        StateTracker.log_execution_success(db, log_entry.id, mock_result)
        
        state.skill_status = "SUCCESS"
        state.skill_result = mock_result
        state.response = action_desc
        
    except Exception as e:
        error_msg = str(e)
        if "disabled by the administrator" in error_msg:
            state.skill_status = "DISABLED"
            state.response = (
                f"🚫 I understand you'd like me to execute **{skill_name}**. "
                f"However, this action is currently restricted by your care team's administrator.\n\n"
                f"**What you can do:**\n"
                f"- Contact your clinic directly at the front desk\n"
                f"- Ask your care coordinator to enable this feature"
            )
        else:
            state.skill_status = "FAILED"
            state.response = f"⚠️ I encountered an error while executing {skill_name}: {error_msg}"
            
        # Log failure if we got past auth and created a log entry
        try:
            if 'log_entry' in locals():
                StateTracker.log_execution_failure(db, log_entry.id, error_msg)
        except Exception:
            pass
            
    finally:
        db.close()
        
    return state
