import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.story_analyzer import StoryAnalyzer

class TestStoryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = StoryAnalyzer()

    def test_case_1_character_with_goal(self):
        memory = {
            "characters": [{"name": "Arjun", "goals": [{"value": "Save Kingdom"}], "motivations": [{"value": "Duty"}]}]
        }
        analysis = self.analyzer.analyze_story(memory)
        # Should generate strength 'Active Arcs'
        strengths = [s["title"] for s in analysis["strengths"]]
        self.assertIn("Active Character Arcs", strengths)
        self.assertEqual(len(analysis["critiques"]), 0)

    def test_case_2_character_without_goal(self):
        memory = {
            "characters": [{"name": "Arjun", "goals": []}]
        }
        analysis = self.analyzer.analyze_story(memory)
        # Should generate critique 'Missing Goal'
        critiques = [c["type"] for c in analysis["critiques"]]
        self.assertIn("MissingGoal", critiques)

    def test_case_3_goal_without_motivation(self):
        memory = {
            "characters": [{"name": "Arjun", "goals": [{"value": "Save Kingdom"}], "motivations": []}]
        }
        analysis = self.analyzer.analyze_story(memory)
        # Should generate risk
        risks = [r["title"] for r in analysis["risks"]]
        self.assertIn("Character may feel shallow", risks)

    def test_case_4_relationships_exist(self):
        memory = {
            "relationships": [{"source": "Arjun", "target": "Lila", "type": "Sibling"}]
        }
        analysis = self.analyzer.analyze_story(memory)
        # Should generate strength
        strengths = [s["title"] for s in analysis["strengths"]]
        self.assertIn("Connected Character Network", strengths)

    def test_case_5_no_relationships(self):
        memory = {
            "relationships": []
        }
        analysis = self.analyzer.analyze_story(memory)
        # Should generate weakness
        weaknesses = [w["title"] for w in analysis["weaknesses"]]
        self.assertIn("Characters are isolated", weaknesses)

if __name__ == "__main__":
    unittest.main()
