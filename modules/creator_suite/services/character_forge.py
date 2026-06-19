from typing import Dict, Any
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
import random

class CharacterForge:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def generate_character(self, archetype: str) -> Dict[str, Any]:
        patterns = self.ke.read_patterns("character_patterns")
        
        char_pattern = random.choice(patterns)["content"] if patterns else "A mysterious wanderer."
        
        return {
            "name": f"Generated {archetype}",
            "archetype": archetype,
            "profile": char_pattern,
            "motivation": "To seek the truth.",
            "flaw": "Hubris",
            "growth_arc": "Learns humility",
            "citations": ["character_patterns"]
        }
