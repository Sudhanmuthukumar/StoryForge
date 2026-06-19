import json
import re
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/character_rules.json")

class CharacterProfiler:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "traits": {},
                "goals": {},
                "motivations": {},
                "fears": {},
                "strengths": {},
                "weaknesses": {}
            }

    def profile_all_characters(self, story_text: str, memory_dict: dict) -> None:
        """Enriches the characters in memory_dict in-place."""
        sentences = re.split(r'(?<=[.!?]) +', story_text)
        
        # Pre-compile regexes
        compiled_rules = {}
        for category, mappings in self.rules.items():
            compiled_rules[category] = []
            for val, patterns in mappings.items():
                for pat in patterns:
                    compiled_rules[category].append((val, re.compile(pat)))

        relationships = memory_dict.get("relationships", [])

        for char in memory_dict.get("characters", []):
            char_name = char.get("name", "")
            
            # Initialize schema fields
            for cat in ["traits", "goals", "motivations", "fears", "strengths", "weaknesses"]:
                if cat not in char:
                    char[cat] = []
            if "known_facts" not in char:
                char["known_facts"] = []
            if "profile_metadata" not in char:
                char["profile_metadata"] = {"confidence": 0.0, "evidence_count": 0}
                
            # Filter relationships
            char_rels = []
            for r in relationships:
                if r.get("source") == char_name:
                    char_rels.append({"target": r.get("target"), "type": r.get("type")})
                elif r.get("target") == char_name:
                    char_rels.append({"target": r.get("source"), "type": r.get("type")})
            char["relationships"] = char_rels

            # Scan sentences for evidence
            evidence_count = 0
            for sentence in sentences:
                if char_name in sentence:
                    # Collect known facts
                    char["known_facts"].append(sentence.strip())
                    
                    # Match configured patterns
                    for category, rules_list in compiled_rules.items():
                        for val, pattern in rules_list:
                            if pattern.search(sentence):
                                char[category].append({
                                    "value": val,
                                    "confidence": 0.90,
                                    "evidence": sentence.strip()
                                })
                                evidence_count += 1
            
            char["profile_metadata"]["evidence_count"] = evidence_count
            if evidence_count > 0:
                char["profile_metadata"]["confidence"] = 0.85
