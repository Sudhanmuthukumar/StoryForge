import uuid
from typing import Dict, Any

class ReactionEngine:
    def generate_reaction_rules(self, npc_id: str) -> Dict[str, Any]:
        """Generates the reaction ruleset for an NPC."""
        return {
            "id": f"react_{uuid.uuid4().hex[:8]}",
            "npc_id": npc_id,
            "on_attacked": "Reputation -50, Flee",
            "on_bribed": "Trust +20, Reveal Secret",
            "on_quest_complete": "Trust +50, Update Primary Goal"
        }
