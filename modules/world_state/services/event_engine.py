import uuid
from typing import Dict, Any
import datetime

class EventEngine:
    def __init__(self):
        pass

    def create_event(self, event_type: str, source_entity: str, target_entity: str, description: str = "") -> Dict[str, Any]:
        """Creates a world-changing event."""
        return {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "source_entity": source_entity,
            "target_entity": target_entity,
            "description": description
        }
