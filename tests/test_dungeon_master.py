import unittest
from unittest.mock import patch
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.dungeon_master.services.event_interpreter import EventInterpreter
from modules.dungeon_master.services.consequence_engine import ConsequenceEngine
from modules.dungeon_master.services.narrative_director import NarrativeDirector
from modules.dungeon_master.services.quest_generator import QuestGenerator
from modules.dungeon_master.services.rumor_generator import RumorGenerator
from modules.dungeon_master.services.dungeon_master_service import DungeonMasterService

class TestDungeonMaster(unittest.TestCase):
    
    def setUp(self):
        # Mock AIService.generate_response to raise an exception, forcing fallback rules
        self.ai_patcher = patch('services.ai_service.AIService.generate_response', side_effect=Exception("Mock LLM offline"))
        self.mock_generate = self.ai_patcher.start()

        # Create a separate temporary folder for test databases
        self.test_db_dir = Path(__file__).parent.parent / "modules" / "world_simulation" / "test_databases_dm"
        if self.test_db_dir.exists():
            shutil.rmtree(self.test_db_dir)
        self.db = SimulationDatabase(db_dir=str(self.test_db_dir))
        
        # Populate databases with minor mock characters so we have test entities
        npc_memory = self.db.read_db("npc_memory.json")
        npc_memory["npc_001"] = {
            "npc_id": "npc_001",
            "name": "Sir Gareth",
            "memories": [],
            "quest_outcomes": {},
            "relationships": {"player": {"trust": 50, "sentiment": "Neutral", "interaction_count": 0}},
            "faction_standing": {"Kingdom of Eldoria": 50},
            "interactions": []
        }
        self.db.write_db("npc_memory.json", npc_memory)
        
    def tearDown(self):
        self.ai_patcher.stop()
        # Clean up temporary test databases folder
        if self.test_db_dir.exists():
            shutil.rmtree(self.test_db_dir)

    def test_schema_files_exist(self):
        schemas_dir = Path(__file__).parent.parent / "modules" / "dungeon_master" / "schemas"
        self.assertTrue((schemas_dir / "event.schema.json").exists())
        self.assertTrue((schemas_dir / "consequence.schema.json").exists())
        self.assertTrue((schemas_dir / "rumor.schema.json").exists())
        self.assertTrue((schemas_dir / "quest_hook.schema.json").exists())

    def test_event_interpreter_fallback(self):
        interpreter = EventInterpreter()
        mock_logs = [
            {
                "tick_index": 1,
                "timestamp": "2026-06-19T12:00:00Z",
                "type": "WeeklyTick",
                "description": "Weekly tick completed. Faction Action: Kingdom of Eldoria signed a trade treaty with The Shadowrunners Guild.",
                "affected_entities": ["Kingdom of Eldoria", "The Shadowrunners Guild"]
            }
        ]
        
        # Run interpreter (falls back deterministically in test environments without Ollama)
        consequences = interpreter.interpret_events(mock_logs)
        self.assertTrue(len(consequences) >= 1)
        
        cons = consequences[0]
        self.assertEqual(cons["type"], "world_event")
        self.assertIn("trade", cons["description"].lower())
        self.assertTrue(interpreter.validate_consequence(cons))

    def test_consequence_engine(self):
        engine = ConsequenceEngine()
        consequences = [
            {
                "consequence_id": "cons_01",
                "type": "world_event",
                "description": "Taxes are raised to fund defenses.",
                "affected_entities": ["npc_001"],
                "severity": "High",
                "mutations": {
                    "stability_delta": -5,
                    "wealth_delta": 200,
                    "defense_delta": 15,
                    "reputation_deltas": {"npc_001": -10}
                }
            }
        ]
        
        new_events = engine.apply_consequences(self.db, consequences)
        
        # Verify mutations applied to world state
        world_state = self.db.read_db("world_state.json")
        self.assertEqual(world_state["kingdom_status"]["stability"], 95)
        self.assertEqual(world_state["kingdom_status"]["wealth"], 1200)
        self.assertEqual(world_state["kingdom_status"]["defense"], 65)
        
        # Verify crisis event was registered in active events due to High severity
        self.assertEqual(len(world_state["active_events"]), 1)
        self.assertEqual(world_state["active_events"][0]["event_id"], "evt_ws_cons_01")
        self.assertEqual(len(new_events), 1)

        # Verify NPC memory update
        npc_memory = self.db.read_db("npc_memory.json")
        self.assertEqual(len(npc_memory["npc_001"]["memories"]), 1)
        self.assertEqual(npc_memory["npc_001"]["relationships"]["player"]["trust"], 40)

    def test_narrative_director(self):
        director = NarrativeDirector()
        
        # Run director on base database
        plan = director.direct_narrative(self.db, [])
        
        self.assertTrue(director.validate_narrative_plan(plan))
        self.assertTrue(len(plan["quest_hooks"]) >= 1)
        self.assertEqual(plan["quest_hooks"][0]["npc_giver"], "Sir Gareth")
        
        # Verify Story Arc Tracker updated campaign progress
        world_state = self.db.read_db("world_state.json")
        self.assertEqual(world_state["campaign_progress"]["active_arc_id"], "act_01") # Still Act I as 0 quests completed

    def test_quest_generator(self):
        generator = QuestGenerator()
        mock_hook = {
            "hook_id": "hook_01",
            "title": "Calm the Crowds",
            "description": "Rioters are gathering in the lower districts.",
            "npc_giver": "Sir Gareth",
            "faction": "Kingdom of Eldoria",
            "related_event_id": "evt_ws_01",
            "objectives": ["Speak to town leaders", "Disperse rioters"],
            "suggested_rewards": [{"reward_type": "Gold", "amount": "150"}]
        }
        
        quest = generator.generate_quest_from_hook(mock_hook)
        self.assertTrue(generator.validate_quest(quest))
        self.assertEqual(quest["quest_id"], "hook_01")
        self.assertEqual(quest["quest_type"], "Faction")
        self.assertEqual(len(quest["objectives"]), 2)

    def test_rumor_generator(self):
        generator = RumorGenerator()
        
        # Run rumor generation
        rumors = generator.generate_rumors(self.db)
        self.assertTrue(generator.validate_rumors(rumors))
        self.assertTrue(len(rumors["tavern_rumors"]) >= 1)
        self.assertTrue(len(rumors["news_bulletins"]) >= 1)
        self.assertTrue(len(rumors["faction_reports"]) >= 1)

    def test_dungeon_master_service_tick(self):
        service = DungeonMasterService(db_dir=str(self.test_db_dir))
        
        # Run tick
        res = service.run_dungeon_master_tick()
        
        # Verify narrative output populated in world state
        world_state = self.db.read_db("world_state.json")
        self.assertIn("dungeon_master", world_state)
        self.assertTrue(len(world_state["dungeon_master"]["generated_quests"]) >= 1)
        self.assertTrue(len(world_state["dungeon_master"]["rumors"]["tavern_rumors"]) >= 1)
        
        # Verify DM tick was logged in history
        history = self.db.read_db("event_history.json")
        self.assertTrue(any(log["type"] == "DungeonMasterTick" for log in history))
