import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.character_profiler import CharacterProfiler

class TestCharacterProfiler(unittest.TestCase):
    def setUp(self):
        self.profiler = CharacterProfiler()

    def test_case_1_trait(self):
        memory = {"characters": [{"name": "Arjun"}]}
        self.profiler.profile_all_characters("Arjun charged into battle.", memory)
        char = memory["characters"][0]
        self.assertEqual(len(char["traits"]), 1)
        self.assertEqual(char["traits"][0]["value"], "Brave")

    def test_case_2_goal(self):
        memory = {"characters": [{"name": "Arjun"}]}
        self.profiler.profile_all_characters("Arjun wanted to save the kingdom.", memory)
        char = memory["characters"][0]
        self.assertEqual(len(char["goals"]), 1)
        self.assertEqual(char["goals"][0]["value"], "Save Kingdom")

    def test_case_3_fear(self):
        memory = {"characters": [{"name": "Arjun"}]}
        self.profiler.profile_all_characters("Arjun feared the ocean.", memory)
        char = memory["characters"][0]
        self.assertEqual(len(char["fears"]), 1)
        self.assertEqual(char["fears"][0]["value"], "Ocean")

    def test_case_4_relationship(self):
        memory = {
            "characters": [{"name": "Arjun"}, {"name": "Lila"}],
            "relationships": [{"source": "Lila", "target": "Arjun", "type": "Sibling"}]
        }
        self.profiler.profile_all_characters("Lila was Arjun's sister.", memory)
        arjun = memory["characters"][0]
        lila = memory["characters"][1]
        
        self.assertEqual(len(arjun["relationships"]), 1)
        self.assertEqual(arjun["relationships"][0]["target"], "Lila")
        self.assertEqual(arjun["relationships"][0]["type"], "Sibling")
        
        self.assertEqual(len(lila["relationships"]), 1)
        self.assertEqual(lila["relationships"][0]["target"], "Arjun")
        self.assertEqual(lila["relationships"][0]["type"], "Sibling")

    def test_case_5_no_evidence(self):
        memory = {"characters": [{"name": "Varun"}]}
        self.profiler.profile_all_characters("Varun went to sleep.", memory)
        char = memory["characters"][0]
        self.assertEqual(len(char["traits"]), 0)
        self.assertEqual(len(char["goals"]), 0)
        self.assertEqual(len(char["fears"]), 0)

if __name__ == "__main__":
    unittest.main()
