import unittest
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.story_manager import StoryManager
from services.memory_extractor import MemoryExtractor
from services.relationship_extractor import RelationshipExtractor
from services.character_profiler import CharacterProfiler
from services.story_analyzer import StoryAnalyzer
from services.consistency_engine import ConsistencyEngine
from services.preference_engine import PreferenceEngine

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.sm = StoryManager()
        self.mem = MemoryExtractor()
        self.rel = RelationshipExtractor()
        self.char = CharacterProfiler()
        self.ana = StoryAnalyzer()
        self.con = ConsistencyEngine()
        self.pref = PreferenceEngine()

    def test_full_pipeline_integration(self):
        # Create
        story = self.sm.create_story("Integration Test Story", "Sci-Fi")
        content = "Arjun looked at the stars. He was brave. Arjun loved the stars."
        
        # Memory
        m_dict = self.mem.extract(content)
        self.assertIn("characters", m_dict)
        
        # Relationships
        m_dict["relationships"] = self.rel.extract_relationships(content, m_dict)
        
        # Characters
        self.char.profile_all_characters(content, m_dict)
        
        # Analysis
        a_dict = self.ana.analyze_story(m_dict)
        
        # Consistency
        c_dict = self.con.check_consistency(m_dict, a_dict)
        
        # Preferences
        prof = self.sm.load_user_profile()
        updated_prof = self.pref.learn_from_story(
            prof, {"id": story.id, "genre": "Sci-Fi"}, m_dict, a_dict, c_dict
        )
        
        # Write
        self.sm.update_memory(story.id, m_dict)
        self.sm.update_analysis(story.id, a_dict)
        self.sm.update_consistency(story.id, c_dict)
        self.sm.update_user_profile(updated_prof)
        
        # Verify
        ws = self.sm.load_workspace(story.id)
        self.assertIn("characters", ws.memory)
        self.assertEqual(ws.consistency["consistency_score"], c_dict["consistency_score"])

if __name__ == "__main__":
    unittest.main()
