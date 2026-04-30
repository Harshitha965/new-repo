from typing import Dict, Any
from app.skills.wrappers.clinical_services import ClinicalServicesWrapper
from app.skills.wrappers.email_service import EmailServiceWrapper

class FunctionalOrchestrator:
    @staticmethod
    def execute_pre_op_gatekeeper(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates SKL_PRE_OP_GATEKEEPER
        Step 1: Verify checklist
        Step 2: Extract vitals
        Returns Readiness Verdict
        """
        print("\n--- [ORCHESTRATOR] Starting SKL_PRE_OP_GATEKEEPER ---")
        
        # Step 1: Checklist Audit
        try:
            audit_result = ClinicalServicesWrapper.verify_checklist({
                "patient_id": payload["patient_id"],
                "required_documents": payload["required_documents"]
            })
            print("[ORCHESTRATOR] Checklist passed.")
        except Exception as e:
            print(f"[ORCHESTRATOR] Checklist failed: {str(e)}")
            # The saga halts here. We raise to trigger the HITL state
            raise Exception(f"Gatekeeper Halted at Step 1 (Audit): {str(e)}")
            
        # Step 2: Vitals Extraction
        try:
            # We mock the OCR call with an empty image to get the baseline vitals
            vitals_result = ClinicalServicesWrapper.extract_vitals({
                "extraction_type": "VITALS"
            })
            print("[ORCHESTRATOR] Vitals extracted successfully.")
        except Exception as e:
            print(f"[ORCHESTRATOR] Vitals extraction failed: {str(e)}")
            raise Exception(f"Gatekeeper Halted at Step 2 (Vitals OCR): {str(e)}")
            
        # Final Verdict Synthesis
        print("--- [ORCHESTRATOR] Gatekeeper passed successfully! ---\n")
        return {
            "readiness_verdict": "CLEARED_FOR_SURGERY",
            "audit_details": audit_result,
            "vitals_snapshot": vitals_result
        }

    # ------------------------------------------------------------------
    # SKL_EXPERT_SYNTHESIS
    # ------------------------------------------------------------------
    @staticmethod
    def _format_expert_brief(raw_data: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """
        Deterministic Expert Lens Formatter.
        Transforms raw aggregated clinical data into a structured
        clinical brief using the expert's preferred format.
        This is pure formatting — no LLM reasoning involved.
        """
        lab = raw_data.get("lab_results", "N/A")
        vitals = raw_data.get("vitals_summary", "N/A")
        notes = raw_data.get("last_visit_notes", "N/A")

        brief_text = (
            f"=== EXPERT CLINICAL BRIEF ===\n"
            f"Patient ID : {patient_id}\n"
            f"----------------------------\n"
            f"LAB RESULTS  : {lab}\n"
            f"VITALS       : {vitals}\n"
            f"CLINICAL NOTE: {notes}\n"
            f"============================\n"
        )

        return {
            "brief_text": brief_text,
            "sections": {
                "lab_results": lab,
                "vitals_summary": vitals,
                "clinical_notes": notes,
            },
        }

    @staticmethod
    def execute_expert_synthesis(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates SKL_EXPERT_SYNTHESIS
        Step 1: Aggregate clinical data via KNW_REPORT_SYNTHESIS
        Step 2: Format as Expert Clinical Brief (Expert Lens)
        Step 3: Dispatch externally — ONLY if release_approved is True
        """
        print("\n--- [ORCHESTRATOR] Starting SKL_EXPERT_SYNTHESIS ---")

        patient_id = str(payload["patient_id"])
        data_sources = payload["data_sources"]
        release_approved = payload.get("release_approved", False)

        # ── Step 1: Data Aggregation ──────────────────────────────
        try:
            synthesis_result = ClinicalServicesWrapper.synthesize_report({
                "patient_id": patient_id,
                "data_sources": data_sources,
            })
            raw_data = synthesis_result.get("raw_data", {})
            print("[ORCHESTRATOR] Step 1 — Report synthesis complete.")
        except Exception as e:
            print(f"[ORCHESTRATOR] Step 1 FAILED — Report synthesis: {str(e)}")
            raise Exception(
                f"Expert Synthesis Halted at Step 1 (Data Aggregation): {str(e)}"
            )

        # ── Step 2: Expert Lens Formatting ────────────────────────
        try:
            expert_brief = FunctionalOrchestrator._format_expert_brief(
                raw_data, patient_id
            )
            print("[ORCHESTRATOR] Step 2 — Expert brief formatted.")
        except Exception as e:
            print(f"[ORCHESTRATOR] Step 2 FAILED — Brief formatting: {str(e)}")
            raise Exception(
                f"Expert Synthesis Halted at Step 2 (Expert Lens): {str(e)}"
            )

        # ── Step 3: Conditional Dispatch (Safety Gate) ────────────
        if not release_approved:
            print(
                "[ORCHESTRATOR] Release toggle is OFF — brief generated "
                "but NOT dispatched."
            )
            print("--- [ORCHESTRATOR] Expert Synthesis complete (PENDING_RELEASE) ---\n")
            return {
                "dispatch_status": "PENDING_RELEASE",
                "expert_brief": expert_brief,
                "message": "Brief ready for review. Set release_approved=True to dispatch.",
            }

        # Release is approved — send the brief externally
        try:
            dispatch_result = EmailServiceWrapper.send_communication({
                "template_id": "EXPERT_BRIEF_V1",
                "recipient_address": "expert@clinic.local",
                "dynamic_vars": {
                    "patient_id": patient_id,
                    "brief_body": expert_brief["brief_text"],
                },
            })
            print("[ORCHESTRATOR] Step 3 — Brief dispatched externally.")
        except Exception as e:
            print(f"[ORCHESTRATOR] Step 3 FAILED — Dispatch: {str(e)}")
            raise Exception(
                f"Expert Synthesis Halted at Step 3 (Dispatch): {str(e)}"
            )

        print("--- [ORCHESTRATOR] Expert Synthesis complete (DISPATCHED) ---\n")
        return {
            "dispatch_status": "DISPATCHED",
            "expert_brief": expert_brief,
            "dispatch_details": dispatch_result,
        }

    # ------------------------------------------------------------------
    # SKL_BASELINE_VIGILANCE
    # ------------------------------------------------------------------
    @staticmethod
    def execute_baseline_vigilance(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates SKL_BASELINE_VIGILANCE
        Step 1: Extract current vitals via ACT_VISION_OCR
        Step 2: Compare against patient-specific baseline thresholds
        Step 3: Return verdict — ALL_NORMAL or BREACH_DETECTED
        """
        print("\n--- [ORCHESTRATOR] Starting SKL_BASELINE_VIGILANCE ---")

        patient_id = str(payload["patient_id"])
        thresholds = payload["baseline_thresholds"]

        # ── Step 1: Vitals Extraction via OCR ─────────────────────
        try:
            ocr_result = ClinicalServicesWrapper.extract_vitals({
                "extraction_type": "VITALS",
                "image_url": payload.get("image_url"),
            })
            vitals_numeric = ocr_result.get("vitals_numeric", {})
            print(f"[ORCHESTRATOR] Step 1 — Vitals extracted: {vitals_numeric}")
        except Exception as e:
            print(f"[ORCHESTRATOR] Step 1 FAILED — Vitals OCR: {str(e)}")
            raise Exception(
                f"Baseline Vigilance Halted at Step 1 (Vitals OCR): {str(e)}"
            )

        # ── Step 2: Threshold Comparison ──────────────────────────
        try:
            comparison = ClinicalServicesWrapper.compare_vitals_to_baseline(
                vitals_numeric, thresholds
            )
            breaches = comparison.get("breaches", [])
            print(
                f"[ORCHESTRATOR] Step 2 — Comparison complete. "
                f"Checked {comparison['total_checked']} vitals, "
                f"found {len(breaches)} breach(es)."
            )
        except Exception as e:
            print(f"[ORCHESTRATOR] Step 2 FAILED — Threshold comparison: {str(e)}")
            raise Exception(
                f"Baseline Vigilance Halted at Step 2 (Comparison): {str(e)}"
            )

        # ── Step 3: Verdict ───────────────────────────────────────
        if not breaches:
            print("--- [ORCHESTRATOR] Baseline Vigilance complete (ALL_NORMAL) ---\n")
            return {
                "vigilance_status": "ALL_NORMAL",
                "patient_id": patient_id,
                "vitals_snapshot": ocr_result.get("vitals", {}),
                "message": "All vitals within baseline thresholds.",
            }

        print("--- [ORCHESTRATOR] Baseline Vigilance complete (BREACH_DETECTED) ---\n")
        return {
            "vigilance_status": "BREACH_DETECTED",
            "patient_id": patient_id,
            "vitals_snapshot": ocr_result.get("vitals", {}),
            "breaches": breaches,
            "total_checked": comparison["total_checked"],
            "message": f"{len(breaches)} vital(s) outside baseline range.",
        }
