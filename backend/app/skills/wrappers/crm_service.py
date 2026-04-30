from app.skills.wrappers.resilience import with_retry, TransientNetworkError, ExternalAPIException
from typing import Dict, Any

class CRMServiceWrapper:
    @staticmethod
    @with_retry()
    def write_to_crm(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic wrapper for CRM interactions.
        """
        headers = {"Authorization": "Bearer MOCK_CRM_TOKEN"}
        
        print(f"Calling External CRM API...")
        
        if payload.get("trigger_error"):
            raise TransientNetworkError("CRM Database locked.")
            
        return {"provider_status": "saved", "crm_record_id": "rec_555"}
