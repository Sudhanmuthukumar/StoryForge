import unittest
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.graph_engine import GraphEngine
from services.universe_engine import UniverseEngine
from core.story_manager import StoryManager
from utils.constants import UNIVERSES_DIR

class TestGraphEngine(unittest.TestCase):
    def setUp(self):
        if UNIVERSES_DIR.exists():
            shutil.rmtree(UNIVERSES_DIR)
        self.ue = UniverseEngine()
        self.ge = GraphEngine()
        self.sm = StoryManager()

    def tearDown(self):
        if UNIVERSES_DIR.exists():
            shutil.rmtree(UNIVERSES_DIR)

    def test_full_graph_flow(self):
        story1 = self.sm.create_story("Story A", "Fantasy")
        story2 = self.sm.create_story("Story B", "Fantasy")
        
        self.sm.update_memory(story1.id, {
            "characters": [{"name": "Arjun", "traits": [{"value": "Brave"}], "known_facts": ["Alive"]}],
            "locations": ["Castle"]
        })
        
        self.sm.update_memory(story2.id, {
            "characters": [{"name": "Arjun", "traits": [{"value": "Cowardly"}], "known_facts": ["Dead"]}],
            "locations": ["Cave"]
        })
        
        # This will auto-trigger rebuild -> graph generation
        u = self.ue.create_universe("Graph Universe")
        uid = u["universe_id"]
        
        self.ue.add_story(uid, story1.id)
        self.ue.add_story(uid, story2.id)
        
        graph = self.ge.load_graph(uid)
        
        # Case 1: Build graph -> nodes generated
        self.assertTrue(len(graph["nodes"]) > 0)
        self.assertTrue(len(graph["edges"]) > 0)
        
        # Case 2: Cross-story character -> same_entity edge
        # Case 3: Universe conflict -> conflicts_with edge
        same_ent_edges = [e for e in graph["edges"] if e["relationship"] == "same_entity"]
        conf_edges = [e for e in graph["edges"] if e["relationship"] == "conflicts_with"]
        self.assertTrue(len(same_ent_edges) > 0)
        self.assertTrue(len(conf_edges) > 0)
        
        # Find Arjun node id
        arjun_id = next(n["id"] for n in graph["nodes"] if n["name"] == "Arjun")
        
        # Case 4: Neighbor query
        neighbors = self.ge.get_neighbors(graph, arjun_id)
        self.assertTrue(len(neighbors) > 0)
        # Neighbors should include Story A and Story B
        names = [n["name"] for n in neighbors]
        self.assertIn("Story A", names)
        self.assertIn("Story B", names)
        
        # Case 5: Connected component query
        comp = self.ge.get_connected_component(graph, arjun_id)
        self.assertTrue(len(comp) > len(neighbors)) # Usually component is bigger
        
        # Stats checks
        stats = graph["statistics"]
        self.assertTrue(stats["node_count"] > 0)
        self.assertTrue(stats["edge_count"] > 0)
        self.assertTrue(stats["connected_components"] > 0)

if __name__ == "__main__":
    unittest.main()
