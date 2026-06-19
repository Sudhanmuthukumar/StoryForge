import uuid
from typing import Dict, Any

class WorldStateEngine:
    def __init__(self):
        pass

    def create_world(self, name: str = "Base World") -> Dict[str, Any]:
        """Initializes a new world state."""
        return {
            "world_id": f"world_{uuid.uuid4().hex[:8]}",
            "name": name,
            "security": 50,
            "prosperity": 50,
            "stability": 50,
            "war_level": 0,
            "crime_level": 20,
            "magic_level": 50,
            "trade_level": 50
        }

    def apply_delta(self, state: Dict[str, Any], metric: str, amount: int) -> Dict[str, Any]:
        """Applies a delta to a world state metric, bounding it between 0 and 100."""
        if metric in state:
            state[metric] = max(0, min(100, state[metric] + amount))
        return state
