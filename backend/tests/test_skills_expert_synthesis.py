from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4

client = TestClient(app)

PATIENT_ID = str(uuid4())
WORKFLOW_ID = str(uuid4())
EXPERT_ID = str(uuid4())


def _build_payload(release_approved: bool, data_sources=None):
    """Helper to build a valid SKL_EXPERT_SYNTHESIS request body."""
    return {
        "skill_name": "SKL_EXPERT_SYNTHESIS",
        "payload": {
            "patient_id": PATIENT_ID,
            "data_sources": data_sources or ["lab_panel_001", "vitals_snapshot_002"],
            "release_approved": release_approved,
        },
        "metadata": {
            "workflow_id": WORKFLOW_ID,
            "expert_id": EXPERT_ID,
        },
    }


# ─── Test 1: Full happy path (release approved) ──────────────────────
def test_expert_synthesis_with_release():
    payload = _build_payload(release_approved=True)
    response = client.post("/skills/execute/SKL_EXPERT_SYNTHESIS", json=payload)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["dispatch_status"] == "DISPATCHED"
    assert "expert_brief" in body["data"]
    assert "dispatch_details" in body["data"]
    print("[PASS] test_expert_synthesis_with_release")


# ─── Test 2: Safety gate — release NOT approved ──────────────────────
def test_expert_synthesis_without_release():
    payload = _build_payload(release_approved=False)
    response = client.post("/skills/execute/SKL_EXPERT_SYNTHESIS", json=payload)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["dispatch_status"] == "PENDING_RELEASE"
    assert "expert_brief" in body["data"]
    # Dispatch details should NOT be present
    assert "dispatch_details" not in body["data"]
    print("[PASS] test_expert_synthesis_without_release")


# ─── Test 3: Validation rejection — missing required fields ─────────
def test_expert_synthesis_validation_failure():
    payload = {
        "skill_name": "SKL_EXPERT_SYNTHESIS",
        "payload": {
            # Missing patient_id, data_sources, and release_approved
        },
        "metadata": {
            "workflow_id": str(uuid4()),
            "expert_id": str(uuid4()),
        },
    }

    response = client.post("/skills/execute/SKL_EXPERT_SYNTHESIS", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}: {response.text}"
    )

    error_data = response.json().get("detail", {})
    missing = error_data.get("missing_fields", [])

    assert "patient_id" in missing, "Should identify missing patient_id"
    assert "data_sources" in missing, "Should identify missing data_sources"
    assert "release_approved" in missing, "Should identify missing release_approved"
    print("[PASS] test_expert_synthesis_validation_failure")


if __name__ == "__main__":
    print("Running SKL_EXPERT_SYNTHESIS Tests...\n")
    test_expert_synthesis_with_release()
    test_expert_synthesis_without_release()
    test_expert_synthesis_validation_failure()
    print("\nAll SKL_EXPERT_SYNTHESIS tests passed successfully!")
