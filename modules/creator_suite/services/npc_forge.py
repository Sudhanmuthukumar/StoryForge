import uuid
from typing import Dict, Any, List, Tuple
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
from modules.creator_suite.services.npc_intelligence.memory_engine import MemoryEngine
from modules.creator_suite.services.npc_intelligence.relationship_engine import RelationshipEngine
from modules.creator_suite.services.npc_intelligence.goal_engine import GoalEngine
from modules.creator_suite.services.npc_intelligence.reaction_engine import ReactionEngine
import random

class NPCForge:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke
        self.memory_engine = MemoryEngine()
        self.relationship_engine = RelationshipEngine()
        self.goal_engine = GoalEngine()
        self.reaction_engine = ReactionEngine()

    def generate_npc(self, role: str, generate_intelligence: bool = False) -> Dict[str, Any]:
        """Generates an NPC. If generate_intelligence is True, returns intelligence profiles in a nested structure."""
        char_patterns = self.ke.read_patterns("character_patterns")
        dialogue_patterns = self.ke.read_patterns("dialogue_patterns")
        
        char_pattern = random.choice(char_patterns)["content"] if char_patterns else "A quiet observer."
        diag_pattern = random.choice(dialogue_patterns)["content"] if dialogue_patterns else "'Greetings, traveler.'"
        
        npc_id = f"npc_{uuid.uuid4().hex[:8]}"
        
        npc_data = {
            "id": npc_id,
            "role": role,
            "name": f"Generated {role.capitalize()}",
            "motivation": char_pattern,
            "secrets": "Hidden lineage.",
            "relationships": "",  # Simple string hook
            "dialogue_hooks": diag_pattern,
            "quest_hooks": "Seeking a lost heirloom.",
            "citations": ["character_patterns", "dialogue_patterns"]
        }
        
        if generate_intelligence:
            # We return a structured wrapper for ease of parsing by the export layer
            # Since the user requested separate files, we wrap them in a dict.
            mem = self.memory_engine.generate_memory(npc_id)
            goal = self.goal_engine.generate_goal(npc_id, npc_data["motivation"])
            reaction = self.reaction_engine.generate_reaction_rules(npc_id)
            
            # Example relationship (to themselves for now, or a generic placeholder)
            rel = self.relationship_engine.generate_relationship(npc_id, "player_01", "NPC_PLAYER")
            
            return {
                "npc": npc_data,
                "npc_memory": mem,
                "npc_relationships": rel,
                "npc_goals": goal,
                "npc_reactions": reaction
            }
        
        return npc_data
