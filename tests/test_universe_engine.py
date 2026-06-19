import unittest
from unittest.mock import patch
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.universe_engine import UniverseEngine
from utils.constants import UNIVERSES_DIR
from core.story_manager import StoryManager

class TestUniverseEngine(unittest.TestCase):
    def setUp(self):
        if UNIVERSES_DIR.exists():
            shutil.rmtree(UNIVERSES_DIR)
        self.engine = UniverseEngine()
        self.sm = StoryManager()

    def tearDown(self):
        if UNIVERSES_DIR.exists():
            shutil.rmtree(UNIVERSES_DIR)

    def test_case_1_create_universe(self):
        u = self.engine.create_universe("Marvel")
        self.assertIn("universe_id", u)
        self.assertEqual(u["name"], "Marvel")
        
        universes = self.engine.list_universes()
        self.assertEqual(len(universes), 1)

    @patch('core.story_manager.StoryManager._find_story_by_id')
    @patch('services.universe_engine.UniverseEngine._read_json')
    def test_case_2_add_story(self, mock_read_json, mock_find_story):
        # We'll just test that the metadata stories list gets updated
        # mock_read_json needs to return appropriate values depending on args
        # Because rebuild_universe is complex, we just want to ensure it adds the story to metadata.
        
        # Real json operations inside create
        # we can unmock during create
        pass

    def test_full_flow(self):
        # Since UniverseEngine uses real files, let's create a real story and real universe
        story1 = self.sm.create_story("Story A", "Fantasy")
        story2 = self.sm.create_story("Story B", "Fantasy")
        
        # Mocking memory for story1
        self.sm.update_memory(story1.id, {
            "characters": [{"name": "Arjun", "traits": [{"value": "Brave"}], "known_facts": ["Alive"]}],
            "events": ["The big battle"]
        })
        
        # Mocking memory for story2
        self.sm.update_memory(story2.id, {
            "characters": [{"name": "Arjun", "traits": [{"value": "Cowardly"}], "known_facts": ["Dead"]}],
            "events": ["The peace treaty"]
        })
        
        # Case 1: Create
        u = self.engine.create_universe("Test Universe")
        uid = u["universe_id"]
        
        # Case 2: Add Story
        self.engine.add_story(uid, story1.id)
        data = self.engine.load_universe(uid)
        self.assertIn(story1.id, data["metadata"]["stories"])
        self.assertEqual(len(data["memory"]["characters"]), 1)
        
        # Case 4 & 5: Shared Character and Conflicting Character Facts
        self.engine.add_story(uid, story2.id)
        data = self.engine.load_universe(uid)
        
        # Shared character -> cross story link
        links = data["relationships"]["cross_story_links"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["entity"], "Arjun")
        self.assertIn("Story A", links[0]["appears_in"])
        self.assertIn("Story B", links[0]["appears_in"])
        
        # Conflict generated
        conflicts = data["relationships"]["universe_conflicts"]
        self.assertTrue(len(conflicts) > 0)
        self.assertTrue(any("traits" in c for c in conflicts))
        self.assertTrue(any("facts" in c for c in conflicts))
        
        # Case 3: Remove Story
        self.engine.remove_story(uid, story1.id)
        data = self.engine.load_universe(uid)
        self.assertNotIn(story1.id, data["metadata"]["stories"])
        self.assertEqual(len(data["memory"]["characters"]), 1) # Only Story B now

if __name__ == "__main__":
    unittest.main()
