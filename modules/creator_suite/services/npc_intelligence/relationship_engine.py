import uuid
from typing import Dict, Any

class RelationshipEngine:
    def generate_relationship(self, source_id: str, target_id: str, rel_type: str = "NPC_NPC") -> Dict[str, Any]:
        """Generates a bidirectional or directional relationship node."""
        return {
            "id": f"rel_{uuid.uuid4().hex[:8]}",
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": rel_type,
            "affinity": 50,  # 0 to 100
            "status": "Neutral"
        }
