import uuid
from typing import Dict, Any

class GoalEngine:
    def generate_goal(self, npc_id: str, motivation: str) -> Dict[str, Any]:
        """Translates NPC Forge motivation into structured goals."""
        return {
            "id": f"goal_{uuid.uuid4().hex[:8]}",
            "npc_id": npc_id,
            "primary_goal": f"Achieve: {motivation}",
            "secondary_goal": "Survive the coming war.",
            "hidden_goal": "Betray the leader if the price is right."
        }
