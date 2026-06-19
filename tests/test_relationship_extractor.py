import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.relationship_extractor import RelationshipExtractor

class TestRelationshipExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = RelationshipExtractor()

    def test_sibling_relationship(self):
        text = "Arjun's sister Lila arrived."
        rels = self.extractor.extract_relationships(text, {})
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["source"], "Arjun")
        self.assertEqual(rels[0]["target"], "Lila")
        self.assertEqual(rels[0]["type"], "Sibling")

    def test_enemy_relationship(self):
        text = "Arjun hated Varun."
        rels = self.extractor.extract_relationships(text, {})
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["source"], "Arjun")
        self.assertEqual(rels[0]["target"], "Varun")
        self.assertEqual(rels[0]["type"], "Enemy")

    def test_mentor_relationship(self):
        text = "Lila was Arjun's mentor."
        rels = self.extractor.extract_relationships(text, {})
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["source"], "Lila")
        self.assertEqual(rels[0]["target"], "Arjun")
        self.assertEqual(rels[0]["type"], "Mentor")

    def test_no_relationship(self):
        text = "Arjun walked to the store."
        rels = self.extractor.extract_relationships(text, {})
        self.assertEqual(len(rels), 0)

    def test_multiple_relationships(self):
        text = "Arjun's sister Lila arrived. Arjun hated Varun."
        rels = self.extractor.extract_relationships(text, {})
        self.assertEqual(len(rels), 2)
        types = [r["type"] for r in rels]
        self.assertIn("Sibling", types)
        self.assertIn("Enemy", types)

if __name__ == "__main__":
    unittest.main()
