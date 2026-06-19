import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.dungeon_master.services.event_interpreter import EventInterpreter
from modules.dungeon_master.services.consequence_engine import ConsequenceEngine
from modules.dungeon_master.services.narrative_director import NarrativeDirector
from modules.dungeon_master.services.quest_generator import QuestGenerator
from modules.dungeon_master.services.rumor_generator import RumorGenerator
from modules.storyforge_core.events.event_bus import EventBus

class DungeonMasterService:
    """Orchestrates the AI Dungeon Master layer: interprets events, determines plans, and generates quests/rumors."""
    
    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self.interpreter = EventInterpreter()
        self.consequence_engine = ConsequenceEngine()
        self.director = NarrativeDirector()
        self.quest_generator = QuestGenerator()
        self.rumor_generator = RumorGenerator()

    def run_dungeon_master_tick(self) -> Dict[str, Any]:
        """Executes a full Dungeon Master orchestration loop in the exact structural order:
        World State -> Consequence Engine -> Narrative Director -> Dungeon Master -> Narrative Output.
        """
        # 1. Load latest simulation logs
        history = self.db.read_db("event_history.json")
        
        # Take the last 3 events to interpret (focus on latest developments)
        recent_logs = history[-3:] if history else []
        
        # 2. Event Interpreter (Interpret history -> consequences)
        consequences = self.interpreter.interpret_events(recent_logs)
        
        # 3. Consequence Engine (Apply consequences to update World State, NPC memories, reputations)
        new_events = self.consequence_engine.apply_consequences(self.db, consequences)
        
        # 4. Narrative Director (Direct story arcs, generate narrative plan & quest hooks)
        narrative_plan = self.director.direct_narrative(self.db, consequences)
        
        # 5. Dungeon Master (Quest generation from hooks)
        generated_quests = []
        for hook in narrative_plan.get("quest_hooks", []):
            quest = self.quest_generator.generate_quest_from_hook(hook)
            generated_quests.append(quest)
            
            # Export generated quest to Unreal export folder
            self._export_quest_to_unreal(quest)
            EventBus().publish("QuestCompleted", {"quest_id": quest.get('id', hook.get('id', 'new')), "title": quest.get('title')})

        # 6. Rumor Generator (Generate rumors & safety bulletins)
        rumors = self.rumor_generator.generate_rumors(self.db)
        
        # 7. Narrative Output compilation (Write plan, quests, and rumors into World State)
        world_state = self.db.read_db("world_state.json")
        world_state["dungeon_master"] = {
            "narrative_plan": narrative_plan,
            "generated_quests": generated_quests,
            "rumors": rumors,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        self.db.write_db("world_state.json", world_state)
        
        # 8. Log Dungeon Master tick to Event History
        timestamp = datetime.utcnow().isoformat() + "Z"
        next_tick = self._get_next_tick_index(history)
        
        history.append({
            "tick_index": next_tick,
            "timestamp": timestamp,
            "type": "DungeonMasterTick",
            "description": (
                f"Dungeon Master completed narrative beat. "
                f"Resolved {len(consequences)} consequences, "
                f"spawned {len(new_events)} crises, "
                f"tracked Story Arc progression, "
                f"and populated {len(generated_quests)} new quests & rumors."
            ),
            "affected_entities": ["Dungeon Master"]
        })

        for event in new_events:
            self.db.write_db("event_history.json", event)
            EventBus().publish("WorldEventCreated", {"event_id": event.get("id"), "type": event.get("type")})

        self.db.write_db("event_history.json", history)
        
        return {
            "consequences": consequences,
            "narrative_plan": narrative_plan,
            "generated_quests": generated_quests,
            "rumors": rumors
        }

    def _get_next_tick_index(self, history: List[Dict[str, Any]]) -> int:
        if not history:
            return 1
        return history[-1].get("tick_index", 0) + 1

    def _export_quest_to_unreal(self, quest: Dict[str, Any]) -> None:
        """Saves generated quests into exports/unreal/alpha_world/quests/ for engine import."""
        export_dir = Path("exports/unreal/alpha_world/quests")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        quest_id = quest.get("quest_id", f"quest_{uuid.uuid4().hex[:8]}")
        out_file = export_dir / f"{quest_id}.json"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(quest, f, indent=4)
        except Exception as e:
            print(f"Error exporting DM quest {quest_id}: {e}")
