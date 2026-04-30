from app.skills.wrappers.resilience import with_retry, TransientNetworkError
from typing import Dict, Any

class ClinicalServicesWrapper:
    @staticmethod
    @with_retry()
    def verify_checklist(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Base Skill: Audits clinical artifacts for presence."""
        print(f"[Base Skill] Auditing documents for patient {payload.get('patient_id')}...")
        docs = payload.get("required_documents", [])
        
        # Simulated failure for testing the orchestration
        if "fail_audit" in docs:
            print("[Base Skill] Audit Failed! Missing critical document.")
            raise Exception("Audit Failed: Missing 'Surgical Consent Form'.")
            
        return {"status": "passed", "verified_documents": docs}

    @staticmethod
    @with_retry()
    def extract_vitals(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Base Skill: OCR extraction of vitals."""
        print(f"[Base Skill] Extracting vitals via OCR...")
        return {
            "vitals": {"bp": "120/80", "hr": 72},
            "vitals_numeric": {"bp_systolic": 120, "bp_diastolic": 80, "hr": 72},
            "status": "extracted"
        }

    @staticmethod
    def compare_vitals_to_baseline(vitals_numeric: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic threshold comparison engine.
        Compares each extracted numeric vital against the patient's baseline range.
        Returns breach report with severity levels.
        Pure function — no external calls, no LLM reasoning.
        """
        breaches = []
        for vital_name, bounds in thresholds.items():
            if not isinstance(bounds, list) or len(bounds) != 2:
                continue
            low, high = bounds
            current_value = vitals_numeric.get(vital_name)
            if current_value is not None:
                if not (low <= current_value <= high):
                    # CRITICAL if >20% outside range, WARNING otherwise
                    severity = "CRITICAL" if (current_value < low * 0.8 or current_value > high * 1.2) else "WARNING"
                    breaches.append({
                        "vital": vital_name,
                        "current_value": current_value,
                        "safe_range": [low, high],
                        "severity": severity
                    })
        return {"breaches": breaches, "total_checked": len(thresholds)}

    @staticmethod
    @with_retry()
    def synthesize_report(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Base Skill: Deterministic aggregation of clinical data sources."""
        print(f"[Base Skill] Aggregating data sources: {payload.get('data_sources')}")
        # Simulated raw structured data retrieval
        raw_data = {
            "lab_results": "Normal limits",
            "vitals_summary": "Stable",
            "last_visit_notes": "Patient reports minor discomfort."
        }
        return {"raw_data": raw_data, "status": "synthesized"}
