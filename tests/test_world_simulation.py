import unittest
import unittest.mock
from unittest.mock import patch, MagicMock
import sys
import json
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.world_simulation.services.simulation_database import SimulationDatabase

class TestWorldSimulation(unittest.TestCase):
    
    def setUp(self):
        # Create a separate temporary folder for test databases
        self.test_db_dir = Path(__file__).parent.parent / "modules" / "world_simulation" / "test_databases"
        if self.test_db_dir.exists():
            shutil.rmtree(self.test_db_dir)
        self.db = SimulationDatabase(db_dir=str(self.test_db_dir))
        
    def tearDown(self):
        # Clean up temporary test databases folder
        if self.test_db_dir.exists():
            shutil.rmtree(self.test_db_dir)

    def test_schema_files_exist(self):
        schemas_dir = Path(__file__).parent.parent / "modules" / "world_simulation" / "schemas"
        self.assertTrue((schemas_dir / "npc_memory.schema.json").exists())
        self.assertTrue((schemas_dir / "world_state.schema.json").exists())
        self.assertTrue((schemas_dir / "reputation.schema.json").exists())
        self.assertTrue((schemas_dir / "event_history.schema.json").exists())

    def test_database_initialization(self):
        # Check that initialization creates the default files
        self.assertTrue((self.test_db_dir / "npc_memory.json").exists())
        self.assertTrue((self.test_db_dir / "world_state.json").exists())
        self.assertTrue((self.test_db_dir / "reputation.json").exists())
        self.assertTrue((self.test_db_dir / "event_history.json").exists())

        # Check default content
        state = self.db.read_db("world_state.json")
        self.assertEqual(state["kingdom_status"]["kingdom_name"], "Kingdom of Eldoria")
        
        rep = self.db.read_db("reputation.json")
        self.assertIn("player", rep)
        self.assertEqual(rep["player"]["factions"], {})
        
        history = self.db.read_db("event_history.json")
        self.assertEqual(history, [])

    def test_npc_memory_validation(self):
        # Valid NPC memory dictionary
        valid_mem = {
            "npc_001": {
                "npc_id": "npc_001",
                "name": "Alistair the Paladin (1)",
                "memories": [
                    {
                        "event_id": "evt_01",
                        "description": "Met the player.",
                        "timestamp": "2026-06-19T12:00:00Z",
                        "emotional_impact": "Surprised",
                        "importance": 50
                    }
                ],
                "quest_outcomes": {
                    "quest_01": "Success"
                },
                "relationships": {
                    "player": {
                        "trust": 60,
                        "sentiment": "Neutral",
                        "interaction_count": 1
                    }
                },
                "faction_standing": {
                    "The Order of Sunfire": 75
                },
                "interactions": [
                    {
                        "timestamp": "2026-06-19T12:00:00Z",
                        "topic": "The Order of Sunfire",
                        "player_choice": "Asked about order history",
                        "outcome": "Informative talk"
                    }
                ]
            }
        }
        self.assertTrue(self.db.validate_npc_memory(valid_mem))
        
        # Invalid memory (missing name)
        invalid_mem = {
            "npc_001": {
                "npc_id": "npc_001",
                "memories": []
            }
        }
        self.assertFalse(self.db.validate_npc_memory(invalid_mem))
        
        # Test write and read operations
        self.db.write_db("npc_memory.json", valid_mem)
        read_data = self.db.read_db("npc_memory.json")
        self.assertEqual(read_data["npc_001"]["name"], "Alistair the Paladin (1)")

    def test_world_state_validation(self):
        # Valid state
        valid_state = {
            "active_events": [
                {
                    "event_id": "e1",
                    "name": "Storm",
                    "region": "Shadowfen",
                    "severity": "Low",
                    "turns_remaining": 3
                }
            ],
            "completed_quests": [
                {
                    "quest_id": "q1",
                    "title": "Clear Cave",
                    "outcome": "Success",
                    "timestamp": "2026-06-19T12:00:00Z"
                }
            ],
            "campaign_progress": {
                "current_campaign_id": "campaign_1",
                "active_arc_id": "act_01",
                "completed_arcs": [],
                "active_regions": ["Shadowfen"]
            },
            "kingdom_status": {
                "kingdom_name": "Eldoria",
                "stability": 90,
                "wealth": 2000,
                "defense": 45,
                "ruler": "King Doran"
            },
            "regional_conditions": {
                "Shadowfen": {
                    "weather": "Rainy",
                    "danger_level": "High",
                    "resources": "Iron, Herbs"
                }
            }
        }
        self.assertTrue(self.db.validate_world_state(valid_state))

        # Invalid state (stability as string instead of int)
        invalid_state = valid_state.copy()
        invalid_state["kingdom_status"] = {
            "kingdom_name": "Eldoria",
            "stability": "high",
            "wealth": 2000,
            "defense": 45,
            "ruler": "King Doran"
        }
        self.assertFalse(self.db.validate_world_state(invalid_state))

    def test_reputation_validation(self):
        valid_rep = {
            "player": {
                "factions": {
                    "Mages Guild": 40
                },
                "npcs": {
                    "npc_001": 20
                }
            },
            "faction_relations": {
                "Mages Guild": {
                    "Templars": -50
                }
            }
        }
        self.assertTrue(self.db.validate_reputation(valid_rep))

        # Invalid reputation (missing faction_relations)
        invalid_rep = {
            "player": {
                "factions": {},
                "npcs": {}
            }
        }
        self.assertFalse(self.db.validate_reputation(invalid_rep))

    def test_event_history_validation(self):
        valid_history = [
            {
                "tick_index": 1,
                "timestamp": "2026-06-19T12:00:00Z",
                "type": "General",
                "description": "A new day began in Eldoria.",
                "affected_entities": ["Eldoria"]
            }
        ]
        self.assertTrue(self.db.validate_event_history(valid_history))

        # Invalid history (missing affected_entities)
        invalid_history = [
            {
                "tick_index": 1,
                "timestamp": "2026-06-19T12:00:00Z",
                "type": "General",
                "description": "A new day began in Eldoria."
            }
        ]
        self.assertFalse(self.db.validate_event_history(invalid_history))

    @unittest.mock.patch('modules.interactive_narrative.services.interactive_narrative_generator.InteractiveNarrativeGenerator._call_llm_json')
    def test_dialogue_prompt_context_injection(self, mock_call_llm):
        mock_call_llm.return_value = {
            "tree_id": "test_tree",
            "npc_name": "Alistair the Paladin (1)",
            "nodes": []
        }
        
        valid_mem = {
            "npc_001": {
                "npc_id": "npc_001",
                "name": "Alistair the Paladin (1)",
                "memories": [
                    {"event_id": "e_01", "description": "Witnessed heroic act.", "timestamp": "2026-06-19"}
                ],
                "quest_outcomes": {},
                "relationships": {
                    "player": {"trust": 95, "sentiment": "Friendly", "interaction_count": 0}
                },
                "faction_standing": {},
                "interactions": []
            }
        }
        self.db.write_db("npc_memory.json", valid_mem)
        
        from modules.interactive_narrative.services.interactive_narrative_generator import InteractiveNarrativeGenerator
        
        # Patch the default db_dir in __init__ of SimulationDatabase
        from modules.world_simulation.services.simulation_database import SimulationDatabase
        orig_defaults = SimulationDatabase.__init__.__defaults__
        SimulationDatabase.__init__.__defaults__ = (str(self.test_db_dir),)
        
        try:
            generator = InteractiveNarrativeGenerator()
            generator.generate_dialogue_tree("Alistair the Paladin (1)", "Quest Inquiry", "Friendly")
            
            self.assertTrue(mock_call_llm.called)
            user_prompt = mock_call_llm.call_args[0][1]
            self.assertIn("PERSISTENT WORLD SIMULATION CONTEXT", user_prompt)
            self.assertIn("Witnessed heroic act.", user_prompt)
            self.assertIn("Friendly", user_prompt)
        finally:
            # Restore original default values
            SimulationDatabase.__init__.__defaults__ = orig_defaults

    def test_quest_outcome_recording(self):
        from modules.world_simulation.services.simulation_engine import SimulationEngine
        engine = SimulationEngine(db_dir=str(self.test_db_dir))
        
        # Seed memories and faction standings
        valid_mem = {
            "npc_001": {
                "npc_id": "npc_001",
                "name": "Alistair the Paladin (1)",
                "memories": [],
                "quest_outcomes": {},
                "relationships": {
                    "player": {"trust": 50, "sentiment": "Neutral", "interaction_count": 0}
                },
                "faction_standing": {
                    "The Order of Sunfire": 50
                },
                "interactions": []
            }
        }
        self.db.write_db("npc_memory.json", valid_mem)
        
        engine.record_quest_outcome("q1", "Retrieve Crown", "Alistair the Paladin (1)", "Success", 15)
        
        # Read back database state
        mem = self.db.read_db("npc_memory.json")
        self.assertIn("q1", mem["npc_001"]["quest_outcomes"])
        self.assertEqual(mem["npc_001"]["relationships"]["player"]["trust"], 65)
        self.assertEqual(len(mem["npc_001"]["memories"]), 1)
        
        rep = self.db.read_db("reputation.json")
        self.assertEqual(rep["player"]["npcs"]["npc_001"], 15)
        self.assertEqual(rep["player"]["factions"]["The Order of Sunfire"], 15)
        
        history = self.db.read_db("event_history.json")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["type"], "QuestOutcome")

    def test_player_interaction_recording(self):
        from modules.world_simulation.services.simulation_engine import SimulationEngine
        engine = SimulationEngine(db_dir=str(self.test_db_dir))
        
        valid_mem = {
            "npc_001": {
                "npc_id": "npc_001",
                "name": "Alistair the Paladin (1)",
                "memories": [],
                "quest_outcomes": {},
                "relationships": {
                    "player": {"trust": 50, "sentiment": "Neutral", "interaction_count": 0}
                },
                "faction_standing": {},
                "interactions": []
            }
        }
        self.db.write_db("npc_memory.json", valid_mem)
        
        engine.record_player_interaction("Alistair the Paladin (1)", "The Sundered Grove", "Offer resources", "Trust Gained", 10)
        
        mem = self.db.read_db("npc_memory.json")
        self.assertEqual(mem["npc_001"]["relationships"]["player"]["trust"], 60)
        self.assertEqual(mem["npc_001"]["relationships"]["player"]["interaction_count"], 1)
        self.assertEqual(len(mem["npc_001"]["interactions"]), 1)

    def test_daily_weekly_ticking(self):
        from modules.world_simulation.services.simulation_engine import SimulationEngine
        engine = SimulationEngine(db_dir=str(self.test_db_dir))
        
        # Set up active event with turns remaining
        state = self.db.read_db("world_state.json")
        state["active_events"].append({
            "event_id": "evt_test",
            "name": "Test Event",
            "region": "Sundered Grove",
            "severity": "Medium",
            "turns_remaining": 2
        })
        state["regional_conditions"]["Sundered Grove"] = {
            "weather": "Sunny",
            "danger_level": "Medium",
            "resources": "Wood"
        }
        self.db.write_db("world_state.json", state)
        
        # Test daily tick
        engine.tick_daily()
        state = self.db.read_db("world_state.json")
        self.assertEqual(state["active_events"][0]["turns_remaining"], 1)
        
        # Test weekly tick
        engine.tick_weekly()
        state = self.db.read_db("world_state.json")
        # Event should now be expired and removed
        self.assertEqual(len(state["active_events"]), 0)

    def test_generate_simulation_report(self):
        from modules.world_simulation.services.simulation_engine import SimulationEngine
        engine = SimulationEngine(db_dir=str(self.test_db_dir))
        
        report_md = engine.generate_simulation_report()
        self.assertIn("StoryForge World Simulation Engine", report_md)
        self.assertIn("Kingdom Status", report_md)
        
        # Verify it writes simulation_report.md
        report_path = Path("simulation_report.md")
        self.assertTrue(report_path.exists())
        report_path.unlink() # clean up

if __name__ == "__main__":
    unittest.main()
