from sqlalchemy.orm import Session
from app.skills.database.models import ExecutionLog, StateLedger
from app.skills.schemas.base import SkillRequest
from pydantic import BaseModel

class StateTracker:
    @staticmethod
    def log_execution_start(db: Session, request: SkillRequest) -> ExecutionLog:
        """
        Records the initiation of a skill in the execution_logs.
        Also updates/creates the state_ledger.
        """
        # Create or update State Ledger
        state = db.query(StateLedger).filter(StateLedger.workflow_id == str(request.metadata.workflow_id)).first()
        if not state:
            state = StateLedger(
                workflow_id=str(request.metadata.workflow_id),
                expert_id=str(request.metadata.expert_id),
                current_state="PENDING_EXECUTION"
            )
            db.add(state)
        else:
            state.current_state = "PENDING_EXECUTION"
            
        # Create Execution Log
        log = ExecutionLog(
            workflow_id=str(request.metadata.workflow_id),
            expert_id=str(request.metadata.expert_id),
            skill_name=request.skill_name,
            raw_payload=request.payload,
            status="PENDING"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def log_execution_success(db: Session, log_id: str, result_data: dict) -> None:
        """
        Updates the log to SUCCESS.
        """
        log = db.query(ExecutionLog).filter(ExecutionLog.id == log_id).first()
        if log:
            log.status = "SUCCESS"
            # In a full implementation, you might save the result data somewhere,
            # or update the state_ledger to COMPLETED
            state = db.query(StateLedger).filter(StateLedger.workflow_id == log.workflow_id).first()
            if state:
                state.current_state = "EXECUTION_COMPLETED"
            db.commit()

    @staticmethod
    def log_execution_failure(db: Session, log_id: str, error_msg: str) -> None:
        """
        Updates the log to FAILED and captures the error.
        """
        log = db.query(ExecutionLog).filter(ExecutionLog.id == log_id).first()
        if log:
            log.status = "FAILED"
            log.error_trace = error_msg
            
            # Transition workflow state to allow Human-In-The-Loop
            state = db.query(StateLedger).filter(StateLedger.workflow_id == log.workflow_id).first()
            if state:
                state.current_state = "WAITING_FOR_HUMAN"
            db.commit()
