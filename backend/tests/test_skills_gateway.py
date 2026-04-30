from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
from datetime import datetime, timedelta

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    print("Health check passed.")

def test_valid_book_appointment():
    # Valid Payload
    payload = {
        "skill_name": "book_appointment",
        "payload": {
            "patient_id": str(uuid4()),
            "appointment_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "reason_code": "CONSULT"
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4())
        }
    }
    
    response = client.post("/skills/execute/book_appointment", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    print("Valid book_appointment payload passed validation.")

def test_invalid_book_appointment():
    # Invalid Payload: missing patient_id and wrong reason_code
    payload = {
        "skill_name": "book_appointment",
        "payload": {
            "appointment_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "reason_code": "WRONG_CODE"
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4())
        }
    }
    
    response = client.post("/skills/execute/book_appointment", json=payload)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    
    error_data = response.json().get("detail", {})
    assert "patient_id" in error_data.get("missing_fields", []), "Should identify missing patient_id"
    
    invalid_fields = [f["field"] for f in error_data.get("invalid_fields", [])]
    assert "reason_code" in invalid_fields, "Should identify invalid reason_code"
    
    print("Invalid book_appointment payload was correctly rejected.")

def test_unrecognized_skill():
    payload = {
        "skill_name": "unknown_skill",
        "payload": {},
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4())
        }
    }
    
    response = client.post("/skills/execute/unknown_skill", json=payload)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("Unrecognized skill was correctly rejected.")

if __name__ == "__main__":
    print("Running Validation Gateway Tests...\n")
    test_health()
    test_valid_book_appointment()
    test_invalid_book_appointment()
    test_unrecognized_skill()
    print("\nAll tests passed successfully!")
