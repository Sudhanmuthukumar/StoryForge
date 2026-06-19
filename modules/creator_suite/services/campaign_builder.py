import uuid
from typing import Dict, Any, List
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
from modules.creator_suite.services.npc_forge import NPCForge
from modules.creator_suite.services.faction_builder import FactionBuilder
from modules.creator_suite.services.quest_chain_builder import QuestChainBuilder

class CampaignBuilder:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke
        self.npc_forge = NPCForge(ke)
        self.faction_builder = FactionBuilder(ke)
        self.quest_builder = QuestChainBuilder(ke)

    def build_campaign(self, title: str) -> Dict[str, Any]:
        campaign_id = f"camp_{uuid.uuid4().hex[:8]}"
        
        factions = [
            self.faction_builder.generate_faction("Imperial"),
            self.faction_builder.generate_faction("Rebel")
        ]
        
        # Link rivalries
        factions[0]["rivalries"] = factions[1]["id"]
        factions[1]["rivalries"] = factions[0]["id"]
        
        npcs = [
            self.npc_forge.generate_npc("General"),
            self.npc_forge.generate_npc("Spy")
        ]
        
        # Associate NPCs with factions (simulated)
        npcs[0]["relationships"] = f"Leader of {factions[0]['id']}"
        npcs[1]["relationships"] = f"Agent for {factions[1]['id']}"
        
        quest_chain = self.quest_builder.generate_chain("The Rebellion")
        
        return {
            "id": campaign_id,
            "title": title,
            "main_arc": "The struggle between the Empire and the Rebellion.",
            "multiple_endings": "1. Empire crushes rebels. 2. Rebels overthrow Empire.",
            "factions": factions,
            "npcs": npcs,
            "quest_chains": [quest_chain],
            "citations": ["campaign_builder"]
        }
