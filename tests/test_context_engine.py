import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.context_builder import ContextBuilder
from services.context_ranker import ContextRanker

class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.builder = ContextBuilder()
        self.ranker = ContextRanker()

    def test_case_1_ranker_relevance(self):
        blocks = [
            {"source_type": "characters", "content": "Arjun is a hero."},
            {"source_type": "themes", "content": "Betrayal is everywhere."}
        ]
        res = self.ranker.rank_and_filter("Tell me about Arjun", blocks)
        self.assertTrue(len(res["selected"]) > 0)
        # First selected should be Arjun
        self.assertIn("Arjun", res["selected"][0]["content"])
        self.assertTrue(res["selected"][0]["relevance"] > res["selected"][1]["relevance"])

    def test_case_2_consistency_warnings(self):
        # Builder logic tested implicitly via mock or by manually constructing blocks
        # Let's test the ranker respects consistency importance (defaults to high)
        blocks = [
            {"source_type": "themes", "content": "Water"},
            {"source_type": "consistency", "content": "Warning: Arjun conflict"}
        ]
        res = self.ranker.rank_and_filter("What conflicts exist?", blocks)
        # Should rank consistency highly due to keyword 'conflicts' + high importance
        self.assertEqual(res["selected"][0]["source_type"], "consistency")

    def test_case_3_unknown_entity(self):
        blocks = [
            {"source_type": "characters", "content": "Arjun is a hero."}
        ]
        res = self.ranker.rank_and_filter("Tell me about Bob", blocks)
        # Baseline relevance is small (0.1) since 'Bob' doesn't match 'Arjun'
        self.assertLess(res["selected"][0]["relevance"], 0.2)

    def test_case_4_context_limit(self):
        self.ranker.max_chars = 100
        blocks = [
            {"source_type": "characters", "content": "X" * 60},
            {"source_type": "characters", "content": "Y" * 60} # Will exceed 100
        ]
        res = self.ranker.rank_and_filter("Tell me", blocks)
        self.assertEqual(len(res["selected"]), 1)
        self.assertEqual(len(res["dropped"]), 1)

if __name__ == "__main__":
    unittest.main()
