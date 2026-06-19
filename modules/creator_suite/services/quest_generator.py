from typing import Dict, Any
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
import random

class QuestGenerator:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def generate_quest(self, quest_type: str) -> Dict[str, Any]:
        conflicts = self.ke.read_patterns("conflict_patterns")
        scenes = self.ke.read_patterns("scene_patterns")
        
        conflict_pattern = random.choice(conflicts)["content"] if conflicts else "A dispute over resources."
        scene_pattern = random.choice(scenes)["content"] if scenes else "A dense forest."
        
        return {
            "title": f"Generated {quest_type.capitalize()} Quest",
            "type": quest_type,
            "objective": "Resolve the conflict.",
            "conflict": conflict_pattern,
            "location": scene_pattern,
            "citations": ["conflict_patterns", "scene_patterns"]
        }
