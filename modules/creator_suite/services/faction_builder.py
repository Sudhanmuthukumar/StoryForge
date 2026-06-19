import uuid
from typing import Dict, Any, List
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
import random

class FactionBuilder:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def generate_faction(self, archetype: str) -> Dict[str, Any]:
        world_patterns = self.ke.read_patterns("worldbuilding_patterns")
        conflict_patterns = self.ke.read_patterns("conflict_patterns")
        
        world = random.choice(world_patterns)["content"] if world_patterns else "An ancient order."
        conflict = random.choice(conflict_patterns)["content"] if conflict_patterns else "A struggle for power."
        
        faction_id = f"fac_{uuid.uuid4().hex[:8]}"
        
        return {
            "id": faction_id,
            "name": f"The {archetype.capitalize()} Faction",
            "goals": world,
            "leadership": "Council of Elders",
            "rivalries": "", # Comma-separated IDs of rival factions
            "resources": "Gold, Iron, Secrets",
            "internal_conflicts": conflict,
            "citations": ["worldbuilding_patterns", "conflict_patterns"]
        }
