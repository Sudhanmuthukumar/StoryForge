import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.consistency_engine import ConsistencyEngine

class TestConsistencyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConsistencyEngine()

    def test_case_1_alive_dead(self):
        memory = {
            "characters": [{"name": "Arjun", "known_facts": ["Arjun is alive.", "Arjun died in battle."]}]
        }
        consistency = self.engine.check_consistency(memory, {})
        self.assertEqual(len(consistency["fact_conflicts"]), 1)
        self.assertEqual(consistency["fact_conflicts"][0]["severity"], "Critical")
        self.assertEqual(consistency["consistency_score"], 75)  # 100 - 25

    def test_case_2_fear_action(self):
        memory = {
            "characters": [{"name": "Arjun", "fears": [{"value": "Ocean"}], "known_facts": ["Arjun loves swimming."]}]
        }
        consistency = self.engine.check_consistency(memory, {})
        self.assertEqual(len(consistency["character_conflicts"]), 1)
        self.assertEqual(consistency["character_conflicts"][0]["severity"], "Medium")
        self.assertEqual(consistency["consistency_score"], 90)  # 100 - 10

    def test_case_3_relationship_conflict(self):
        memory = {
            "relationships": [
                {"source": "Arjun", "target": "Lila", "type": "Sibling"},
                {"source": "Lila", "target": "Arjun", "type": "Spouse"}
            ]
        }
        consistency = self.engine.check_consistency(memory, {})
        self.assertEqual(len(consistency["relationship_conflicts"]), 1)
        self.assertEqual(consistency["relationship_conflicts"][0]["severity"], "Critical")
        self.assertEqual(consistency["consistency_score"], 75)

    def test_case_4_no_conflicts(self):
        memory = {
            "characters": [{"name": "Arjun", "known_facts": ["Arjun is alive."], "fears": []}],
            "relationships": [{"source": "Arjun", "target": "Lila", "type": "Sibling"}]
        }
        consistency = self.engine.check_consistency(memory, {})
        self.assertEqual(len(consistency["fact_conflicts"]), 0)
        self.assertEqual(len(consistency["character_conflicts"]), 0)
        self.assertEqual(len(consistency["relationship_conflicts"]), 0)
        self.assertEqual(consistency["consistency_score"], 100)

    def test_case_5_multiple_conflicts(self):
        memory = {
            "characters": [{"name": "Arjun", "known_facts": ["Arjun is alive.", "Arjun died in battle."]}],
            "relationships": [
                {"source": "Arjun", "target": "Lila", "type": "Sibling"},
                {"source": "Lila", "target": "Arjun", "type": "Spouse"}
            ]
        }
        consistency = self.engine.check_consistency(memory, {})
        self.assertEqual(len(consistency["fact_conflicts"]), 1)
        self.assertEqual(len(consistency["relationship_conflicts"]), 1)
        self.assertEqual(consistency["consistency_score"], 50)  # 100 - 25 - 25

if __name__ == "__main__":
    unittest.main()
