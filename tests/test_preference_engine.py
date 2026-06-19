import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.preference_engine import PreferenceEngine

class TestPreferenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PreferenceEngine()

    def test_case_1_genre(self):
        user_profile = {"implicit_preferences": {"genres": {}}}
        # 3 Fantasy, 1 Sci-Fi
        for _ in range(3):
            self.engine.learn_from_story(user_profile, {"genre": "Fantasy"}, {}, {}, {})
        self.engine.learn_from_story(user_profile, {"genre": "Sci-Fi"}, {}, {}, {})
        
        genres = user_profile["implicit_preferences"]["genres"]
        self.assertIn("Fantasy", genres)
        self.assertIn("Sci-Fi", genres)
        self.assertTrue(genres["Fantasy"]["score"] > genres["Sci-Fi"]["score"])

    def test_case_2_sibling_relationships(self):
        user_profile = {"implicit_preferences": {"relationship_types": {}}}
        # Repeated siblings
        for _ in range(4):
            self.engine.learn_from_story(user_profile, {}, {"relationships": [{"type": "Sibling"}]}, {}, {})
            
        rels = user_profile["implicit_preferences"]["relationship_types"]
        self.assertIn("Sibling", rels)
        self.assertEqual(rels["Sibling"]["samples"], 4)
        self.assertTrue(rels["Sibling"]["score"] > 0)

    def test_case_3_repeated_themes(self):
        user_profile = {"implicit_preferences": {"themes": {}}}
        # Repeated themes
        for _ in range(3):
            self.engine.learn_from_story(user_profile, {}, {"themes": ["Betrayal"]}, {}, {})
            
        themes = user_profile["implicit_preferences"]["themes"]
        self.assertIn("Betrayal", themes)
        self.assertEqual(themes["Betrayal"]["samples"], 3)

    def test_case_4_single_sample_low_confidence(self):
        user_profile = {"implicit_preferences": {"genres": {}}}
        self.engine.learn_from_story(user_profile, {"genre": "Horror"}, {}, {}, {})
        
        horror = user_profile["implicit_preferences"]["genres"]["Horror"]
        self.assertTrue(horror["confidence"] < 0.5)

    def test_case_5_high_confidence(self):
        user_profile = {"implicit_preferences": {"genres": {}}}
        for _ in range(12):
            self.engine.learn_from_story(user_profile, {"genre": "Romance"}, {}, {}, {})
            
        romance = user_profile["implicit_preferences"]["genres"]["Romance"]
        self.assertTrue(romance["confidence"] >= 0.9)

if __name__ == "__main__":
    unittest.main()
