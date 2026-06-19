from typing import Dict, Any
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
import random

class LoreBuilder:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def generate_lore(self, topic: str) -> Dict[str, Any]:
        patterns = self.ke.read_patterns("worldbuilding_patterns")
        
        lore_pattern = random.choice(patterns)["content"] if patterns else "An ancient ruin."
        
        return {
            "topic": topic,
            "description": f"A rich history defining the {topic}.",
            "details": lore_pattern,
            "citations": ["worldbuilding_patterns"]
        }
