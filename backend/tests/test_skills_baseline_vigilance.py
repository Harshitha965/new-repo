from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4

client = TestClient(app)

PATIENT_ID = str(uuid4())
WORKFLOW_ID = str(uuid4())
EXPERT_ID = str(uuid4())


def _build_payload(thresholds, image_url=None):
    """Helper to build a valid SKL_BASELINE_VIGILANCE request body."""
    payload = {
        "patient_id": PATIENT_ID,
        "baseline_thresholds": thresholds,
    }
    if image_url:
        payload["image_url"] = image_url

    return {
        "skill_name": "SKL_BASELINE_VIGILANCE",
        "payload": payload,
        "metadata": {
            "workflow_id": WORKFLOW_ID,
            "expert_id": EXPERT_ID,
        },
    }


# ─── Test 1: All vitals within baseline → ALL_NORMAL ─────────────────
def test_vigilance_all_normal():
    # Mock vitals return bp_systolic=120, bp_diastolic=80, hr=72
    # These thresholds are wide enough that everything is in range
    thresholds = {
        "bp_systolic": [100, 140],
        "bp_diastolic": [60, 90],
        "hr": [60, 100],
    }
    payload = _build_payload(thresholds)
    response = client.post("/skills/execute/SKL_BASELINE_VIGILANCE", json=payload)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["vigilance_status"] == "ALL_NORMAL"
    assert "breaches" not in body["data"]
    print("[PASS] test_vigilance_all_normal")


# ─── Test 2: Vitals outside baseline → BREACH_DETECTED ───────────────
def test_vigilance_breach_detected():
    # Mock vitals: bp_systolic=120, hr=72
    # Set thresholds so that hr=72 is OUT OF RANGE (expecting 200-300)
    thresholds = {
        "bp_systolic": [100, 140],   # 120 is in range → no breach
        "hr": [200, 300],            # 72 is way out → CRITICAL breach
    }
    payload = _build_payload(thresholds)
    response = client.post("/skills/execute/SKL_BASELINE_VIGILANCE", json=payload)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["vigilance_status"] == "BREACH_DETECTED"
    assert len(body["data"]["breaches"]) >= 1

    hr_breach = next(b for b in body["data"]["breaches"] if b["vital"] == "hr")
    assert hr_breach["current_value"] == 72
    assert hr_breach["severity"] == "CRITICAL"
    print("[PASS] test_vigilance_breach_detected")


# ─── Test 3: Validation failure — missing required fields ────────────
def test_vigilance_validation_failure():
    payload = {
        "skill_name": "SKL_BASELINE_VIGILANCE",
        "payload": {
            # Missing patient_id and baseline_thresholds
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4()),
        },
    }

    response = client.post("/skills/execute/SKL_BASELINE_VIGILANCE", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}: {response.text}"
    )

    error_data = response.json().get("detail", {})
    missing = error_data.get("missing_fields", [])

    assert "patient_id" in missing, "Should identify missing patient_id"
    assert "baseline_thresholds" in missing, "Should identify missing baseline_thresholds"
    print("[PASS] test_vigilance_validation_failure")


if __name__ == "__main__":
    print("Running SKL_BASELINE_VIGILANCE Tests...\n")
    test_vigilance_all_normal()
    test_vigilance_breach_detected()
    test_vigilance_validation_failure()
    print("\nAll SKL_BASELINE_VIGILANCE tests passed successfully!")
