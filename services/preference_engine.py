import json
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/preference_rules.json")

class PreferenceEngine:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "confidence_thresholds": {"low": 1, "medium": 5, "high": 10},
                "learning_rates": {"genre": 1.0, "theme": 0.5, "relationship": 0.2, "character_type": 0.2}
            }

    def _calculate_confidence(self, samples: int) -> float:
        """Calculate confidence based on sample size (0.0 to 1.0)."""
        thresholds = self.rules.get("confidence_thresholds", {"low": 1, "medium": 5, "high": 10})
        if samples >= thresholds.get("high", 10):
            return 0.9 + min(0.1, (samples - thresholds.get("high", 10)) * 0.01)
        elif samples >= thresholds.get("medium", 5):
            return 0.6 + ((samples - thresholds.get("medium", 5)) / (thresholds.get("high", 10) - thresholds.get("medium", 5))) * 0.3
        elif samples >= thresholds.get("low", 1):
            return 0.2 + ((samples - thresholds.get("low", 1)) / (thresholds.get("medium", 5) - thresholds.get("low", 1))) * 0.4
        return 0.0

    def _update_preference(self, category_dict: dict, item: str, rate: float):
        """Update a specific preference item in the given category dictionary."""
        if item not in category_dict:
            category_dict[item] = {"score": 0.0, "confidence": 0.0, "samples": 0}
        
        pref = category_dict[item]
        pref["samples"] += 1
        pref["score"] += rate
        pref["confidence"] = self._calculate_confidence(pref["samples"])

    def learn_from_story(self, user_profile: dict, story_metadata: dict, memory_dict: dict, analysis_dict: dict, consistency_dict: dict) -> dict:
        """Updates the user_profile with learnings from the current story."""
        rates = self.rules.get("learning_rates", {})
        
        implicit = user_profile.get("implicit_preferences", {})
        genres = implicit.get("genres", {})
        themes_prefs = implicit.get("themes", {})
        chars_prefs = implicit.get("character_types", {})
        rels_prefs = implicit.get("relationship_types", {})
        
        # Rule 1: Genre
        genre = story_metadata.get("genre")
        if genre:
            self._update_preference(genres, genre, rates.get("genre", 1.0))

        # Rule 2: Themes
        themes = memory_dict.get("themes", [])
        for theme in themes:
            theme_val = theme if isinstance(theme, str) else theme.get("name", "Unknown")
            self._update_preference(themes_prefs, theme_val, rates.get("theme", 0.5))

        # Rule 3: Relationships
        rels = memory_dict.get("relationships", [])
        for rel in rels:
            rel_type = rel.get("type")
            if rel_type:
                self._update_preference(rels_prefs, rel_type, rates.get("relationship", 0.2))

        # Rule 4: Character Types (Traits)
        chars = memory_dict.get("characters", [])
        for char in chars:
            traits = char.get("traits", [])
            for trait in traits:
                trait_val = trait.get("value")
                if trait_val:
                    self._update_preference(chars_prefs, trait_val, rates.get("character_type", 0.2))

        # Rule 5: Consistency issues repeatedly ignored
        # For simplicity, we just log that we encountered unresolved conflicts.
        cons_issues = consistency_dict.get("fact_conflicts", []) + consistency_dict.get("character_conflicts", [])
        if cons_issues:
            history = user_profile.get("preference_history", [])
            history.append({
                "story_id": story_metadata.get("id"),
                "ignored_conflicts": len(cons_issues)
            })

        return user_profile
