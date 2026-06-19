import uuid
from typing import Dict, Any, List
import random

class MemoryEngine:
    def generate_memory(self, npc_id: str, known_factions: List[str] = None) -> Dict[str, Any]:
        """Generates the memory profile for an NPC."""
        return {
            "id": f"mem_{uuid.uuid4().hex[:8]}",
            "npc_id": npc_id,
            "known_characters": "",  # Comma separated IDs
            "known_factions": ",".join(known_factions) if known_factions else "",
            "remembered_events": "The Shattering",
            "trust_score": random.randint(10, 90),
            "fear_score": random.randint(10, 90)
        }
