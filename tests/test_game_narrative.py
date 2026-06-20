import unittest
from unittest.mock import patch, MagicMock
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.interactive_narrative.services.interactive_narrative_generator import InteractiveNarrativeGenerator
from modules.export_layer.services.data_exporter import DataExporter

class TestGameNarrative(unittest.TestCase):
    
    def setUp(self):
        self.generator = InteractiveNarrativeGenerator()
        self.exporter = DataExporter()
        
    def test_schema_files_exist(self):
        schemas_dir = Path(__file__).parent.parent / "modules" / "interactive_narrative" / "schemas"
        self.assertTrue((schemas_dir / "campaign.schema.json").exists())
        self.assertTrue((schemas_dir / "dialogue.schema.json").exists())
        self.assertTrue((schemas_dir / "quest.schema.json").exists())
        self.assertTrue((schemas_dir / "npc.schema.json").exists())
        self.assertTrue((schemas_dir / "lore.schema.json").exists())

    def test_campaign_validation_and_healing(self):
        # Valid data
        valid_campaign = {
            "theme": "Rebellion",
            "story_arcs": [
                {"arc_id": "arc1", "title": "Rise", "description": "Form rebellion", "milestone": "Assemble forces"}
            ],
            "regions": [
                {
                    "region_name": "Forest Outpost",
                    "progression_index": 0,
                    "quest_chains": [
                        {"chain_id": "c1", "title": "Undercover", "quests": ["Talk to spy"], "dependency_chain_id": None}
                    ]
                }
            ]
        }
        self.assertTrue(self.generator.validate_campaign(valid_campaign))
        
        # Invalid data (missing regions)
        invalid_campaign = {
            "theme": "Rebellion",
            "story_arcs": []
        }
        self.assertFalse(self.generator.validate_campaign(invalid_campaign))
        
        # Healing
        healed = self.generator.heal_campaign(invalid_campaign, "Rebellion", 2)
        self.assertTrue(self.generator.validate_campaign(healed))
        self.assertEqual(len(healed["regions"]), 2)

    def test_dialogue_validation_and_healing(self):
        valid_dialogue = {
            "tree_id": "tree_01",
            "npc_name": "Merchant",
            "nodes": [
                {
                    "node_id": "start",
                    "speaker": "Merchant",
                    "text": "Need weapons?",
                    "choices": [
                        {"text": "Show wares", "target_node_id": "shop", "condition": None, "consequence": "OpenShop"}
                    ]
                }
            ]
        }
        self.assertTrue(self.generator.validate_dialogue(valid_dialogue))
        
        invalid_dialogue = {}
        healed = self.generator.heal_dialogue(invalid_dialogue, "Merchant")
        self.assertTrue(self.generator.validate_dialogue(healed))
        self.assertEqual(healed["npc_name"], "Merchant")

    def test_quest_validation_and_healing(self):
        valid_quest = {
            "quest_id": "q1",
            "title": "Clear Den",
            "description": "Clear the goblins.",
            "quest_type": "Side",
            "objectives": [
                {"objective_id": "o1", "description": "Defeat goblin chief", "condition": "ChiefDefeated"}
            ],
            "rewards": [
                {"reward_type": "Gold", "amount": "100"}
            ],
            "outcomes": [
                {"outcome_id": "out1", "description": "The cave is safe."}
            ]
        }
        self.assertTrue(self.generator.validate_quest(valid_quest))
        
        invalid_quest = {"title": "Bad Quest"}
        healed = self.generator.heal_quest(invalid_quest, "Side")
        self.assertTrue(self.generator.validate_quest(healed))

    def test_npc_validation_and_healing(self):
        valid_npc = {
            "npc_id": "npc1",
            "name": "Eldrin",
            "archetype": "Wizard",
            "motivation": "Find book",
            "secret": "None",
            "faction": "Academy",
            "relationships": [
                {"target_npc": "King", "relation_type": "Friend", "level": 50}
            ],
            "dialogue_style": "Poetic",
            "quest_hooks": ["Bring magic scroll"]
        }
        self.assertTrue(self.generator.validate_npc(valid_npc))
        
        invalid_npc = {"name": "Eldrin"}
        healed = self.generator.heal_npc(invalid_npc)
        self.assertTrue(self.generator.validate_npc(healed))

    def test_lore_validation_and_healing(self):
        valid_lore = {
            "lore_id": "lore1",
            "name": "The Great Schism",
            "category": "Historical Event",
            "summary": "The empire divided in two.",
            "historical_events": [
                {"event_name": "Coronation", "date": "100 AE", "description": "King takes crown."}
            ],
            "core_beliefs": ["Unity"],
            "key_figures": [
                {"name": "Alistair", "role": "Emperor", "description": "Divided the realm."}
            ]
        }
        self.assertTrue(self.generator.validate_lore(valid_lore))
        
        invalid_lore = {"category": "Guild"}
        healed = self.generator.heal_lore(invalid_lore, "Guild")
        self.assertTrue(self.generator.validate_lore(healed))

    @patch('services.ai_service.AIService.generate_response')
    def test_llm_generation_campaign(self, mock_generate):
        mock_response = {
            "theme": "Dark Mage Incursion",
            "story_arcs": [
                {"arc_id": "arc1", "title": "The Awakening", "description": "Dark seals break.", "milestone": "Survive the siege."}
            ],
            "regions": [
                {
                    "region_name": "Shadowfen",
                    "progression_index": 0,
                    "quest_chains": [
                        {"chain_id": "c1", "title": "Purify Wards", "quests": ["Talk to priest", "Collect herbs"], "dependency_chain_id": None}
                    ]
                }
            ]
        }
        mock_generate.return_value = json.dumps(mock_response)
        
        res = self.generator.generate_campaign("Dark Mage Incursion", 1)
        self.assertEqual(res["theme"], "Dark Mage Incursion")
        self.assertEqual(len(res["regions"]), 1)
        self.assertEqual(res["regions"][0]["region_name"], "Shadowfen")

    def test_data_exporter_outputs(self):
        # NPC Exporter
        npc = {
            "npc_id": "npc_01",
            "name": "Garrick",
            "archetype": "Fighter",
            "motivation": "Protect town",
            "secret": "Spy",
            "faction": "Guard",
            "relationships": [{"target_npc": "Mayor", "relation_type": "Bodyguard", "level": 90}],
            "dialogue_style": "Gruff",
            "quest_hooks": ["Clear bandits"]
        }
        
        temp_dir = Path("exports/unreal")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = temp_dir / "npc_test.json"
        dt_path = temp_dir / "npc_test_dt.json"
        csv_path = temp_dir / "npc_test.csv"
        
        self.exporter.export_npc(npc, "JSON", json_path)
        self.exporter.export_npc(npc, "UE_DataTable_JSON", dt_path)
        self.exporter.export_npc(npc, "CSV", csv_path)
        
        self.assertTrue(json_path.exists())
        self.assertTrue(dt_path.exists())
        self.assertTrue(csv_path.exists())
        
        # Read files to check structures
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["name"], "Garrick")
            
        with open(dt_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertIn("npc_01", d)
            self.assertEqual(d["npc_01"]["name"], "Garrick")
            
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            self.assertIn("Garrick", lines[1])
            self.assertIn("Mayor:Bodyguard:90", lines[1])
            
        # Clean up temp test files
        json_path.unlink()
        dt_path.unlink()
        csv_path.unlink()

if __name__ == "__main__":
    unittest.main()
