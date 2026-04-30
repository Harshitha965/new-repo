from fastapi.testclient import TestClient
from app.main import app
from app.skills.database.session import Base, engine, SessionLocal
from app.skills.database.models import SkillDefinition, ExecutionLog, StateLedger
from uuid import uuid4
from datetime import datetime, timedelta

# Create the tables in the test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def setup_db():
    db = SessionLocal()
    # Clear existing data
    db.query(ExecutionLog).delete()
    db.query(StateLedger).delete()
    db.query(SkillDefinition).delete()
    
    # Add a mock skill definition
    db.add(SkillDefinition(skill_name="book_appointment", is_active=True))
    # Add a disabled skill definition
    db.add(SkillDefinition(skill_name="send_communication", is_active=False))
    db.commit()
    db.close()

def test_successful_execution_log():
    setup_db()
    workflow_id = str(uuid4())
    expert_id = str(uuid4())
    
    payload = {
        "skill_name": "book_appointment",
        "payload": {
            "patient_id": str(uuid4()),
            "appointment_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "reason_code": "CONSULT"
        },
        "metadata": {
            "workflow_id": workflow_id,
            "expert_id": expert_id
        }
    }
    
    response = client.post("/skills/execute/book_appointment", json=payload)
    assert response.status_code == 200, response.text
    
    # Verify Database State
    db = SessionLocal()
    log = db.query(ExecutionLog).filter(ExecutionLog.workflow_id == workflow_id).first()
    assert log is not None
    assert log.status == "SUCCESS"
    
    state = db.query(StateLedger).filter(StateLedger.workflow_id == workflow_id).first()
    assert state is not None
    assert state.current_state == "EXECUTION_COMPLETED"
    db.close()
    print("test_successful_execution_log passed!")

def test_unauthorized_skill():
    setup_db()
    payload = {
        "skill_name": "send_communication",
        "payload": {
            "template_id": "test",
            "recipient_address": "test@test.com",
            "dynamic_vars": {}
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4())
        }
    }
    
    response = client.post("/skills/execute/send_communication", json=payload)
    assert response.status_code == 403
    assert "currently disabled" in response.text
    print("test_unauthorized_skill passed!")

if __name__ == "__main__":
    print("Running State Engine Tests...\n")
    test_successful_execution_log()
    test_unauthorized_skill()
    print("\nAll tests passed successfully!")
