"""
memory_extractor.py — Day 5 Memory Extraction Engine
Regex/Frequency-based extractor. 100% offline, zero AI.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/extraction_rules.json")

class MemoryExtractor:
    def __init__(self):
        self.rules = self._load_rules()
        self.version = "1.1.0"

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "character_verbs": ["said", "replied", "walked"],
                "location_prepositions": ["in", "at", "to"],
                "organization_suffixes": ["Guild", "Order"],
                "theme_keywords": {"War": ["war", "battle"]}
            }

    def extract(self, story_text: str, existing_memory: dict = None) -> dict:
        """Extract entities from the story text using heuristics."""
        words = story_text.split()
        story_words = len(words)
        
        # Build new memory structure matching the future-ready schema
        new_memory = {
            "characters": [],
            "relationships": [],
            "events": [],
            "locations": [],
            "organizations": [],
            "artifacts": [],
            "themes": [],
            "quotes": []
        }
        
        if not story_text.strip():
            self._add_metadata(new_memory, story_words)
            return new_memory

        self._extract_characters(story_text, new_memory)
        self._extract_locations(story_text, new_memory)
        self._extract_organizations(story_text, new_memory)
        self._extract_events(story_text, new_memory)
        self._extract_themes(story_text, new_memory, story_words)
        self._extract_quotes(story_text, new_memory)

        self._add_metadata(new_memory, story_words)
        return new_memory

    def _add_metadata(self, memory: dict, word_count: int) -> None:
        memory["extraction_metadata"] = {
            "extractor_version": self.version,
            "last_extraction": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "story_words": word_count,
            "characters_found": len(memory["characters"]),
            "locations_found": len(memory["locations"]),
            "themes_found": len(memory["themes"])
        }

    def _extract_characters(self, text: str, memory: dict) -> None:
        verbs = "|".join(self.rules.get("character_verbs", []))
        # Match capitalized word before a verb
        pattern = re.compile(rf"(?<!The\s)\b([A-Z][a-z]+)\s+(?:{verbs})\b")
        matches = pattern.findall(text)
        
        freq = {}
        for m in matches:
            freq[m] = freq.get(m, 0) + 1
            
        for name, count in freq.items():
            conf = min(0.6 + (count * 0.05), 0.99)
            memory["characters"].append({
                "id": f"char_{uuid.uuid4().hex[:8]}",
                "name": name,
                "aliases": [],
                "mentions": count,
                "confidence": round(conf, 2),
                "attributes": [],
                "relationships": [],
                "first_seen": text.find(name),
                "last_seen": text.rfind(name)
            })

    def _extract_locations(self, text: str, memory: dict) -> None:
        preps = "|".join(self.rules.get("location_prepositions", []))
        pattern = re.compile(rf"\b(?:{preps})\s+(?<!The\s)([A-Z][a-z]+)\b")
        matches = pattern.findall(text)
        
        freq = {}
        for m in matches:
            freq[m] = freq.get(m, 0) + 1
            
        for name, count in freq.items():
            conf = min(0.5 + (count * 0.05), 0.95)
            memory["locations"].append({
                "id": f"loc_{uuid.uuid4().hex[:8]}",
                "name": name,
                "mentions": count,
                "confidence": round(conf, 2),
                "type": "Unknown"
            })

    def _extract_organizations(self, text: str, memory: dict) -> None:
        suffixes = "|".join(self.rules.get("organization_suffixes", []))
        pattern = re.compile(rf"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:{suffixes}))\b")
        matches = pattern.findall(text)
        
        freq = {}
        for m in matches:
            freq[m] = freq.get(m, 0) + 1
            
        for org, count in freq.items():
            memory["organizations"].append({
                "id": f"org_{uuid.uuid4().hex[:8]}",
                "name": org,
                "mentions": count,
                "confidence": 0.90
            })

    def _extract_events(self, text: str, memory: dict) -> None:
        pattern = re.compile(r"\bThe\s+([A-Z][a-z]+\s+(?:War|Festival|Battle|Age|Era))\b")
        matches = pattern.findall(text)
        
        freq = {}
        for m in matches:
            freq[m] = freq.get(m, 0) + 1
            
        for event, count in freq.items():
            memory["events"].append({
                "id": f"evt_{uuid.uuid4().hex[:8]}",
                "name": f"The {event}",
                "mentions": count,
                "confidence": 0.85
            })

    def _extract_themes(self, text: str, memory: dict, total_words: int) -> None:
        text_lower = text.lower()
        for theme_name, keywords in self.rules.get("theme_keywords", {}).items():
            count = sum(text_lower.count(kw) for kw in keywords)
            if count > 0:
                conf = min(0.4 + (count * 0.1), 0.99)
                memory["themes"].append({
                    "id": f"thm_{uuid.uuid4().hex[:8]}",
                    "name": theme_name,
                    "confidence": round(conf, 2)
                })

    def _extract_quotes(self, text: str, memory: dict) -> None:
        # Match "Quote text" followed eventually by "said Name"
        pattern = re.compile(r'"([^"]+)"\s*(?:,|she|he)?\s*(?:said|asked|replied|whispered)\s+([A-Z][a-z]+)')
        matches = pattern.findall(text)
        for quote_text, speaker in matches:
            memory["quotes"].append({
                "id": f"qte_{uuid.uuid4().hex[:8]}",
                "text": f'"{quote_text}"',
                "speaker": speaker,
                "confidence": 0.75
            })
