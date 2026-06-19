import json
from datetime import datetime
from typing import List, Dict, Any
from modules.world_simulation.services.simulation_database import SimulationDatabase

class ConsequenceEngine:
    """Applies validated narrative consequences to modify World State, NPC Memory, and Reputation."""
    
    def __init__(self):
        pass

    def apply_consequences(self, db: SimulationDatabase, consequences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mutates simulation databases based on a list of validated consequences."""
        if not consequences:
            return []

        world_state = db.read_db("world_state.json")
        npc_memory = db.read_db("npc_memory.json")
        reputation = db.read_db("reputation.json")
        
        new_events = []
        timestamp = datetime.utcnow().isoformat() + "Z"

        for cons in consequences:
            mutations = cons.get("mutations", {})
            
            # 1. Update Kingdom Status
            ks = world_state.setdefault("kingdom_status", {
                "kingdom_name": "Kingdom of Eldoria",
                "stability": 100,
                "wealth": 1000,
                "defense": 50,
                "ruler": "King Doran"
            })
            
            stability_delta = mutations.get("stability_delta", 0)
            wealth_delta = mutations.get("wealth_delta", 0)
            defense_delta = mutations.get("defense_delta", 0)
            
            ks["stability"] = max(0, min(100, ks.get("stability", 100) + stability_delta))
            ks["wealth"] = max(0, ks.get("wealth", 1000) + wealth_delta)
            ks["defense"] = max(0, min(100, ks.get("defense", 50) + defense_delta))
            
            # 2. Update player reputation with factions/NPCs
            rep_deltas = mutations.get("reputation_deltas", {})
            for entity, delta in rep_deltas.items():
                # Check if it's a faction
                if entity in reputation.get("player", {}).get("factions", {}):
                    reputation["player"]["factions"][entity] = max(-100, min(100, reputation["player"]["factions"][entity] + delta))
                # Check if it's an NPC ID
                elif entity in npc_memory:
                    reputation["player"]["npcs"][entity] = max(-100, min(100, reputation["player"]["npcs"].get(entity, 0) + delta))
                    # Also update specific NPC relationship trust
                    npc = npc_memory[entity]
                    trust = npc.get("relationships", {}).get("player", {}).get("trust", 50)
                    npc["relationships"]["player"]["trust"] = max(0, min(100, trust + delta))
                    npc["relationships"]["player"]["sentiment"] = self._get_sentiment_tier(npc["relationships"]["player"]["trust"])
                else:
                    # Default: treat as new faction name
                    reputation.setdefault("player", {}).setdefault("factions", {})[entity] = max(-100, min(100, delta))

            # 3. Propagate consequence memory to affected NPCs
            affected = cons.get("affected_entities", [])
            for entity in affected:
                # Find NPC in memory by name or ID
                target_nid = None
                if entity in npc_memory:
                    target_nid = entity
                else:
                    for nid, npc in npc_memory.items():
                        if npc.get("name") == entity or entity in npc.get("name"):
                            target_nid = nid
                            break
                            
                if target_nid:
                    npc = npc_memory[target_nid]
                    npc.setdefault("memories", []).append({
                        "event_id": f"evt_c_{cons['consequence_id']}",
                        "description": cons["description"],
                        "timestamp": timestamp,
                        "emotional_impact": "Fear" if cons["severity"] in ["High", "Critical"] else "Observation",
                        "importance": 50 if cons["severity"] == "Low" else (70 if cons["severity"] == "Medium" else 90)
                    })

            # 4. Generate world event if severity is High or Critical
            if cons["severity"] in ["High", "Critical"]:
                # Construct name and default region
                event_name = f"Crisis: {cons['type'].replace('_', ' ').title()}"
                region = "Shadowfen" # Default region
                
                # Check if there is already an event with this ID to prevent duplicates
                evt_id = f"evt_ws_{cons['consequence_id']}"
                has_event = any(e.get("event_id") == evt_id for e in world_state.setdefault("active_events", []))
                
                if not has_event:
                    new_evt = {
                        "event_id": evt_id,
                        "name": event_name,
                        "region": region,
                        "severity": cons["severity"],
                        "turns_remaining": 3 if cons["severity"] == "High" else 5
                    }
                    world_state["active_events"].append(new_evt)
                    new_events.append(new_evt)

        # Save mutated databases back
        db.write_db("world_state.json", world_state)
        db.write_db("npc_memory.json", npc_memory)
        db.write_db("reputation.json", reputation)
        
        return new_events

    def _get_sentiment_tier(self, trust: int) -> str:
        if trust < 20: return "Hostile"
        if trust < 40: return "Unfriendly"
        if trust < 65: return "Neutral"
        if trust < 85: return "Friendly"
        return "Honored"
