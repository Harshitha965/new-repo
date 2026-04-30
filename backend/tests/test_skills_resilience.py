from fastapi.testclient import TestClient
from app.main import app
from app.skills.database.session import Base, engine, SessionLocal
from app.skills.database.models import SkillDefinition, StateLedger
from uuid import uuid4
from datetime import datetime, timedelta
import time

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def setup_db():
    db = SessionLocal()
    db.query(SkillDefinition).delete()
    db.query(StateLedger).delete()
    db.add(SkillDefinition(skill_name="book_appointment", is_active=True))
    db.add(SkillDefinition(skill_name="send_communication", is_active=True))
    db.commit()
    db.close()

def test_successful_api_call():
    setup_db()
    payload = {
        "skill_name": "book_appointment",
        "payload": {
            "patient_id": str(uuid4()), # Valid patient ID
            "appointment_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "reason_code": "CONSULT"
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4())
        }
    }
    
    start_time = time.time()
    response = client.post("/skills/execute/book_appointment", json=payload)
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert duration < 1.0 # Should execute immediately
    print("test_successful_api_call passed! (No retries needed)")

def test_fatal_api_call_hitl_trigger():
    setup_db()
    workflow_id = str(uuid4())
    payload = {
        "skill_name": "send_communication",
        "payload": {
            "template_id": "test_template",
            "recipient_address": "test@example.com",
            "dynamic_vars": {"trigger_fatal_error": True}
        },
        "metadata": {
            "workflow_id": workflow_id,
            "expert_id": str(uuid4())
        }
    }
    
    response = client.post("/skills/execute/send_communication", json=payload)
    assert response.status_code == 200 # HTTP is OK, but logical status is FAILED
    assert response.json()["status"] == "FAILED"
    assert "Invalid API Key" in response.json()["error_message"]
    
    # Check DB state to ensure HITL was triggered
    db = SessionLocal()
    state = db.query(StateLedger).filter(StateLedger.workflow_id == workflow_id).first()
    assert state.current_state == "WAITING_FOR_HUMAN"
    db.close()
    
    print("test_fatal_api_call_hitl_trigger passed! (Immediate fail, no retry for fatal errors)")

def test_transient_api_failure_max_retries():
    setup_db()
    workflow_id = str(uuid4())
    payload = {
        "skill_name": "book_appointment",
        "payload": {
            # Patient ID starting with 00000000 triggers the TransientNetworkError
            "patient_id": "00000000-" + str(uuid4())[9:],
            "appointment_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "reason_code": "CONSULT"
        },
        "metadata": {
            "workflow_id": workflow_id,
            "expert_id": str(uuid4())
        }
    }
    
    print("Starting transient failure test (this will take ~7 seconds due to retries)...")
    start_time = time.time()
    response = client.post("/skills/execute/book_appointment", json=payload)
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert "RetryError" in response.json()["error_message"] or "Calendar API timed out" in response.json()["error_message"]
    assert duration >= 3.0 # At least 1s + 2s + 4s retries
    
    # Check DB state
    db = SessionLocal()
    state = db.query(StateLedger).filter(StateLedger.workflow_id == workflow_id).first()
    assert state.current_state == "WAITING_FOR_HUMAN"
    db.close()
    
    print(f"test_transient_api_failure_max_retries passed! (Duration: {duration:.2f}s)")

if __name__ == "__main__":
    print("Running Resilience Tests...\n")
    test_successful_api_call()
    test_fatal_api_call_hitl_trigger()
    test_transient_api_failure_max_retries()
    print("\nAll resilience tests passed successfully!")
