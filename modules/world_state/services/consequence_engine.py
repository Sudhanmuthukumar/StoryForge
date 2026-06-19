import uuid
from typing import Dict, Any, List
from modules.world_state.services.world_state_engine import WorldStateEngine

class ConsequenceEngine:
    def __init__(self):
        self.world_engine = WorldStateEngine()

    def process_event(self, event: Dict[str, Any], world_state: Dict[str, Any], npcs: List[Dict[str, Any]], factions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Translates an event into world state updates, NPC memory updates, and Faction strength updates.
        Returns a dictionary containing the delta consequence log.
        """
        consequence_log = {
            "consequence_id": f"conseq_{uuid.uuid4().hex[:8]}",
            "event_id": event["event_id"],
            "world_deltas": {},
            "faction_deltas": {},
            "npc_deltas": {}
        }

        event_type = event["event_type"]

        if event_type == "Quest Completed":
            world_state = self.world_engine.apply_delta(world_state, "security", 15)
            world_state = self.world_engine.apply_delta(world_state, "prosperity", 10)
            consequence_log["world_deltas"] = {"security": "+15", "prosperity": "+10"}
            
            # Example faction logic: if target is a faction, decrease its strength
            for f in factions:
                if f["id"] == event["target_entity"]:
                    # Assume faction has a 'strength' or 'resources' derived string we could alter
                    consequence_log["faction_deltas"][f["id"]] = "Resources Decreased"

        elif event_type == "Quest Failed":
            world_state = self.world_engine.apply_delta(world_state, "crime_level", 20)
            world_state = self.world_engine.apply_delta(world_state, "security", -10)
            consequence_log["world_deltas"] = {"crime_level": "+20", "security": "-10"}

        elif event_type == "NPC Death":
            world_state = self.world_engine.apply_delta(world_state, "stability", -20)
            consequence_log["world_deltas"] = {"stability": "-20"}
            
            # Update NPCs who know this NPC
            for n in npcs:
                if event["target_entity"] in str(n.get("relationships", "")):
                    consequence_log["npc_deltas"][n["id"]] = "Fear +20"

        elif event_type == "Faction Collapse":
            world_state = self.world_engine.apply_delta(world_state, "stability", -40)
            world_state = self.world_engine.apply_delta(world_state, "war_level", -30)
            consequence_log["world_deltas"] = {"stability": "-40", "war_level": "-30"}

        elif event_type == "Faction Alliance":
            world_state = self.world_engine.apply_delta(world_state, "stability", 30)
            world_state = self.world_engine.apply_delta(world_state, "prosperity", 20)
            consequence_log["world_deltas"] = {"stability": "+30", "prosperity": "+20"}

        # Simulate NPC Memory update for all
        for n in npcs:
            if n["id"] == event["source_entity"] or n["id"] == event["target_entity"]:
                 consequence_log["npc_deltas"].setdefault(n["id"], "Remembered Event added")

        return consequence_log
