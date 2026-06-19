import json
import re
import uuid
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/relationship_rules.json")

class RelationshipExtractor:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def extract_relationships(self, story_text: str, memory_dict: dict) -> list:
        relationships = []
        sentences = re.split(r'(?<=[.!?]) +', story_text)

        # Pre-compile patterns
        compiled_patterns = []
        for category, types in self.rules.items():
            for rel_type, patterns in types.items():
                for pattern in patterns:
                    compiled_patterns.append((rel_type, re.compile(pattern)))

        for i, sentence in enumerate(sentences):
            for rel_type, pattern in compiled_patterns:
                for match in pattern.finditer(sentence):
                    source = match.group("source")
                    target = match.group("target")
                    
                    relationships.append({
                        "relationship_id": f"rel_{uuid.uuid4().hex[:8]}",
                        "source": source,
                        "target": target,
                        "type": rel_type,
                        "confidence": 0.90,
                        "evidence": sentence.strip(),
                        "sentence_index": i,
                        "source_aliases": [],
                        "target_aliases": []
                    })
                    
        return relationships
