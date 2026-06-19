import uuid
from typing import Dict, Any, List
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
import random

class QuestChainBuilder:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def generate_chain(self, theme: str, length: int = 3) -> Dict[str, Any]:
        conflicts = self.ke.read_patterns("conflict_patterns")
        scenes = self.ke.read_patterns("scene_patterns")
        
        chain_id = f"qchain_{uuid.uuid4().hex[:8]}"
        quests = []
        
        for i in range(length):
            conflict = random.choice(conflicts)["content"] if conflicts else "A rising threat."
            scene = random.choice(scenes)["content"] if scenes else "A dark cavern."
            quest_id = f"q_{uuid.uuid4().hex[:8]}"
            quests.append({
                "id": quest_id,
                "chain_id": chain_id,
                "sequence": i + 1,
                "title": f"Part {i+1}: {theme}",
                "objective": conflict,
                "location": scene,
                "branching_outcomes": "Success leads to next quest; Failure leads to alternate path.",
                "consequences": "World state alters."
            })
            
        return {
            "chain_id": chain_id,
            "theme": theme,
            "quests": quests, # List of dicts, must be flattened or handled in CSV export
            "citations": ["conflict_patterns", "scene_patterns"]
        }
