import json
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/analysis_rules.json")

class StoryAnalyzer:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"critiques": {}, "risks": {}, "strengths": {}, "weaknesses": {}}

    def analyze_story(self, memory_dict: dict) -> dict:
        """Analyzes structured memory data without scanning raw story text."""
        analysis = {
            "story_health": {"overall": 0, "characters": 0, "relationships": 0, "themes": 0},
            "story_dna": {
                "character_count": 0,
                "relationship_count": 0,
                "goal_count": 0,
                "fear_count": 0,
                "theme_count": 0
            },
            "strengths": [],
            "weaknesses": [],
            "critiques": [],
            "risks": []
        }

        chars = memory_dict.get("characters", [])
        rels = memory_dict.get("relationships", [])
        themes = memory_dict.get("themes", [])

        # --- DNA Extraction ---
        analysis["story_dna"]["character_count"] = len(chars)
        analysis["story_dna"]["relationship_count"] = len(rels)
        analysis["story_dna"]["theme_count"] = len(themes)

        chars_with_goals = 0
        for char in chars:
            goals = char.get("goals", [])
            fears = char.get("fears", [])
            motivations = char.get("motivations", [])
            
            analysis["story_dna"]["goal_count"] += len(goals)
            analysis["story_dna"]["fear_count"] += len(fears)

            name = char.get("name", "Unknown")

            if goals:
                chars_with_goals += 1
                if not motivations:
                    # Risk: Goal without motivation
                    rule = self.rules.get("risks", {}).get("MissingMotivation", {})
                    analysis["risks"].append({
                        "title": rule.get("title", "Missing Motivation"),
                        "reason": f"{name}: {rule.get('reason', 'Goal lacks motivation.')}"
                    })
            else:
                # Critique: Missing Goal
                rule = self.rules.get("critiques", {}).get("MissingGoal", {})
                analysis["critiques"].append({
                    "type": "MissingGoal",
                    "severity": rule.get("severity", "Medium"),
                    "message": f"{name}: {rule.get('message', 'No goals found.')}",
                    "recommendation": rule.get("recommendation", "Add a goal.")
                })

        # --- Strengths & Weaknesses ---
        if len(rels) > 0:
            rule = self.rules.get("strengths", {}).get("ConnectedNetwork", {})
            analysis["strengths"].append({
                "title": rule.get("title", "Connected Network"),
                "description": rule.get("description", "Relationships exist."),
                "evidence": [f"Found {len(rels)} relationship(s)."]
            })
        else:
            rule = self.rules.get("weaknesses", {}).get("IsolatedCharacters", {})
            analysis["weaknesses"].append({
                "title": rule.get("title", "Isolated"),
                "description": rule.get("description", "No relationships exist."),
                "evidence": ["Relationship count is 0."]
            })

        if chars_with_goals > 0:
            rule = self.rules.get("strengths", {}).get("ActiveArcs", {})
            evidence_names = [c.get("name") for c in chars if c.get("goals")]
            analysis["strengths"].append({
                "title": rule.get("title", "Active Arcs"),
                "description": rule.get("description", "Characters have goals."),
                "evidence": [f"Goals found for: {', '.join(evidence_names)}"]
            })

        # --- Health Scoring ---
        # Character Score: Base 50, +10 for each char with goals, -10 for critiques
        char_score = 50 + (chars_with_goals * 10) - (len(analysis["critiques"]) * 10)
        char_score = max(0, min(100, char_score))
        
        # Relationship Score: Base 20, +20 for each relationship
        rel_score = 20 + (len(rels) * 20)
        rel_score = max(0, min(100, rel_score))
        
        # Theme Score: Base 30, +35 for each theme
        theme_score = 30 + (len(themes) * 35)
        theme_score = max(0, min(100, theme_score))

        overall_score = int((char_score + rel_score + theme_score) / 3)
        if len(chars) == 0:
            overall_score = 0  # No story to score

        analysis["story_health"] = {
            "overall": overall_score,
            "characters": char_score,
            "relationships": rel_score,
            "themes": theme_score
        }

        return analysis
