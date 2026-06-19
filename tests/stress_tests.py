import unittest
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.story_manager import StoryManager
from services.universe_engine import UniverseEngine
from services.graph_engine import GraphEngine

class TestStress(unittest.TestCase):
    def setUp(self):
        self.sm = StoryManager()
        self.ue = UniverseEngine()
        self.ge = GraphEngine()

    def test_stress_system(self):
        story_ids = []
        # Generate 100 stories
        for i in range(100):
            story = self.sm.create_story(f"Stress Story {i}", "Sci-Fi")
            # Inject dummy memory to force processing loads
            self.sm.update_memory(story.id, {
                "characters": [{"name": f"Char_{i}", "traits": [{"value": "Strong"}]}],
                "events": [f"Event_{i}"]
            })
            story_ids.append(story.id)
            
        universe_ids = []
        # Generate 10 universes
        for i in range(10):
            u = self.ue.create_universe(f"Stress Universe {i}")
            uid = u["universe_id"]
            universe_ids.append(uid)
            # Add 10 stories to each universe
            start_idx = i * 10
            for j in range(10):
                self.ue.add_story(uid, story_ids[start_idx + j])
                
        # Validate large graph
        for uid in universe_ids:
            graph = self.ge.load_graph(uid)
            self.assertIn("nodes", graph)
            self.assertTrue(len(graph["nodes"]) > 0)
            
        # Error Recovery Test: corrupted files
        corrupt_path = self.sm._find_story_by_id(story_ids[0]).memory_path
        with open(corrupt_path, "w") as f:
            f.write("{corrupted_json")
            
        # Attempt load, shouldn't crash
        ws = self.sm.load_workspace(story_ids[0])
        self.assertEqual(ws.memory, {"characters": [], "relationships": [], "events": [], "locations": [], "organizations": [], "artifacts": [], "themes": []}) # Should fall back to default safely
        
        # Cleanup
        for sid in story_ids:
            self.sm.delete_story(sid)
        for uid in universe_ids:
            self.ue.delete_universe(uid)

if __name__ == "__main__":
    unittest.main()
