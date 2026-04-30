from app.skills.wrappers.resilience import with_retry, TransientNetworkError, ExternalAPIException
from typing import Dict, Any

class CalendarServiceWrapper:
    @staticmethod
    @with_retry()
    def book_appointment(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper for booking appointments via an external calendar API.
        """
        headers = {"Authorization": "Bearer MOCK_CALENDAR_TOKEN"}
        
        print(f"Calling External Calendar API for patient {payload.get('patient_id')}...")
        
        # Simulated failure for testing the retry mechanism
        # If patient_id starts with '0000', trigger timeout
        if str(payload.get("patient_id")).startswith("00000000"):
            print("Calendar API Timeout!")
            raise TransientNetworkError("Calendar API timed out.")
            
        return {"provider_status": "booked", "calendar_event_id": "evt_12345"}
