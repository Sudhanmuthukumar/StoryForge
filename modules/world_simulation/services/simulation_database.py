import json
from pathlib import Path
from typing import Dict, List, Any, Union

class SimulationDatabase:
    """Manages CRUD operations and schema validations for persistent World Simulation databases."""
    
    DB_NAMES = [
        "npc_memory.json",
        "world_state.json",
        "reputation.json",
        "event_history.json",
        "campaign_health.json",
        "campaign_learning.json",
        "strategy_scores.json",
        "campaign_director_state.json",
        "core_registry.json",
        "telemetry.json"
    ]
    
    def __init__(self, db_dir: str = "modules/world_simulation/databases"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._init_dbs()
        
    def _init_dbs(self) -> None:
        """Create empty default database files if they do not exist."""
        # 1. npc_memory.json
        p_mem = self.db_dir / "npc_memory.json"
        if not p_mem.exists():
            self.write_db("npc_memory.json", {})
            
        # 2. world_state.json
        p_state = self.db_dir / "world_state.json"
        if not p_state.exists():
            default_state = {
                "active_events": [],
                "completed_quests": [],
                "campaign_progress": {
                    "current_campaign_id": None,
                    "active_arc_id": None,
                    "completed_arcs": [],
                    "active_regions": []
                },
                "kingdom_status": {
                    "kingdom_name": "Kingdom of Eldoria",
                    "stability": 100,
                    "wealth": 1000,
                    "defense": 50,
                    "ruler": "King Doran"
                },
                "regional_conditions": {}
            }
            self.write_db("world_state.json", default_state)
            
        # 3. reputation.json
        p_rep = self.db_dir / "reputation.json"
        if not p_rep.exists():
            default_rep = {
                "player": {
                    "factions": {},
                    "npcs": {}
                },
                "faction_relations": {}
            }
            self.write_db("reputation.json", default_rep)
            
        # 4. event_history.json
        p_history = self.db_dir / "event_history.json"
        if not p_history.exists():
            self.write_db("event_history.json", [])
            
    def _get_path(self, db_name: str) -> Path:
        if db_name not in self.DB_NAMES:
            raise ValueError(f"Unknown database: {db_name}")
        return self.db_dir / db_name
        
    def read_db(self, db_name: str) -> Union[Dict[str, Any], List[Any]]:
        path = self._get_path(db_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            if db_name == "event_history.json":
                return []
            return {}
            
    def write_db(self, db_name: str, data: Union[Dict[str, Any], List[Any]]) -> None:
        path = self._get_path(db_name)
        
        is_valid = False
        if db_name == "npc_memory.json":
            is_valid = self.validate_npc_memory(data)
        elif db_name == "world_state.json":
            is_valid = self.validate_world_state(data)
        elif db_name == "reputation.json":
            is_valid = self.validate_reputation(data)
        elif db_name == "event_history.json":
            is_valid = self.validate_event_history(data)
        elif db_name in ["campaign_health.json", "campaign_learning.json", "strategy_scores.json", "campaign_director_state.json", "core_registry.json", "telemetry.json"]:
            is_valid = True
            
        if not is_valid:
            raise ValueError(f"Data failed schema validation check for database: {db_name}")
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    # ══════════════════════════════════════════════════════════════════
    #  SCHEMA VALIDATION
    # ══════════════════════════════════════════════════════════════════
    
    def validate_npc_memory(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        for npc_id, mem in data.items():
            if not isinstance(npc_id, str) or not isinstance(mem, dict):
                return False
            required_fields = ["npc_id", "name", "memories", "quest_outcomes", "relationships", "faction_standing", "interactions"]
            if not all(k in mem for k in required_fields):
                return False
            if not isinstance(mem["npc_id"], str) or not isinstance(mem["name"], str):
                return False
            if not isinstance(mem["memories"], list) or not isinstance(mem["interactions"], list):
                return False
            # Check individual memories
            for m in mem["memories"]:
                if not isinstance(m, dict):
                    return False
                if not all(k in m for k in ["event_id", "description", "timestamp"]):
                    return False
                if not isinstance(m["event_id"], str) or not isinstance(m["description"], str) or not isinstance(m["timestamp"], str):
                    return False
            # Check quest outcomes
            if not isinstance(mem["quest_outcomes"], dict):
                return False
            for qid, outcome in mem["quest_outcomes"].items():
                if not isinstance(qid, str) or not isinstance(outcome, str):
                    return False
            # Check relationships
            if not isinstance(mem["relationships"], dict):
                return False
            for rel_npc, rel_data in mem["relationships"].items():
                if not isinstance(rel_npc, str) or not isinstance(rel_data, dict):
                    return False
                if not all(k in rel_data for k in ["trust", "sentiment"]):
                    return False
                if not isinstance(rel_data["trust"], int) or not isinstance(rel_data["sentiment"], str):
                    return False
            # Check faction standing
            if not isinstance(mem["faction_standing"], dict):
                return False
            for fac, val in mem["faction_standing"].items():
                if not isinstance(fac, str) or not isinstance(val, int):
                    return False
            # Check interactions
            for inter in mem["interactions"]:
                if not isinstance(inter, dict):
                    return False
                if not all(k in inter for k in ["timestamp", "topic", "player_choice", "outcome"]):
                    return False
                if not all(isinstance(inter[k], str) for k in ["timestamp", "topic", "player_choice", "outcome"]):
                    return False
        return True

    def validate_world_state(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        required_fields = ["active_events", "completed_quests", "campaign_progress", "kingdom_status", "regional_conditions"]
        if not all(k in data for k in required_fields):
            return False
            
        # Active Events
        if not isinstance(data["active_events"], list):
            return False
        for e in data["active_events"]:
            if not isinstance(e, dict):
                return False
            if not all(k in e for k in ["event_id", "name", "region", "severity", "turns_remaining"]):
                return False
            if not isinstance(e["turns_remaining"], int):
                return False
            if not all(isinstance(e[k], str) for k in ["event_id", "name", "region", "severity"]):
                return False
                
        # Completed Quests
        if not isinstance(data["completed_quests"], list):
            return False
        for q in data["completed_quests"]:
            if not isinstance(q, dict):
                return False
            if not all(k in q for k in ["quest_id", "title", "outcome", "timestamp"]):
                return False
            if not all(isinstance(q[k], str) for k in ["quest_id", "title", "outcome", "timestamp"]):
                return False
                
        # Campaign Progress
        cp = data["campaign_progress"]
        if not isinstance(cp, dict):
            return False
        if not all(k in cp for k in ["current_campaign_id", "active_arc_id", "completed_arcs", "active_regions"]):
            return False
        if cp["current_campaign_id"] is not None and not isinstance(cp["current_campaign_id"], str):
            return False
        if cp["active_arc_id"] is not None and not isinstance(cp["active_arc_id"], str):
            return False
        if not isinstance(cp["completed_arcs"], list) or not isinstance(cp["active_regions"], list):
            return False
            
        # Kingdom Status
        ks = data["kingdom_status"]
        if not isinstance(ks, dict):
            return False
        if not all(k in ks for k in ["kingdom_name", "stability", "wealth", "defense", "ruler"]):
            return False
        if not isinstance(ks["kingdom_name"], str) or not isinstance(ks["ruler"], str):
            return False
        if not all(isinstance(ks[k], int) for k in ["stability", "wealth", "defense"]):
            return False
            
        # Regional Conditions
        rc = data["regional_conditions"]
        if not isinstance(rc, dict):
            return False
        for region, cond in rc.items():
            if not isinstance(region, str) or not isinstance(cond, dict):
                return False
            if not all(k in cond for k in ["weather", "danger_level", "resources"]):
                return False
            if not all(isinstance(cond[k], str) for k in ["weather", "danger_level", "resources"]):
                return False
        return True

    def validate_reputation(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        if "player" not in data or "faction_relations" not in data:
            return False
            
        # Player Rep
        player = data["player"]
        if not isinstance(player, dict) or "factions" not in player or "npcs" not in player:
            return False
        if not isinstance(player["factions"], dict) or not isinstance(player["npcs"], dict):
            return False
        for f, val in player["factions"].items():
            if not isinstance(f, str) or not isinstance(val, int):
                return False
        for n, val in player["npcs"].items():
            if not isinstance(n, str) or not isinstance(val, int):
                return False
                
        # Faction Relations
        fr = data["faction_relations"]
        if not isinstance(fr, dict):
            return False
        for f1, targets in fr.items():
            if not isinstance(f1, str) or not isinstance(targets, dict):
                return False
            for f2, val in targets.items():
                if not isinstance(f2, str) or not isinstance(val, int):
                    return False
        return True

    def validate_event_history(self, data: Any) -> bool:
        if not isinstance(data, list):
            return False
        for item in data:
            if not isinstance(item, dict):
                return False
            if not all(k in item for k in ["tick_index", "timestamp", "type", "description", "affected_entities"]):
                return False
            if not isinstance(item["tick_index"], int):
                return False
            if not all(isinstance(item[k], str) for k in ["timestamp", "type", "description"]):
                return False
            if not isinstance(item["affected_entities"], list):
                return False
            for entity in item["affected_entities"]:
                if not isinstance(entity, str):
                    return False
        return True
