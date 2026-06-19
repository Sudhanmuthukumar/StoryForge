import json
import re
from pathlib import Path
from datetime import datetime, timezone
import pypdf
import docx

from services.memory_extractor import MemoryExtractor
from services.relationship_extractor import RelationshipExtractor
from services.character_profiler import CharacterProfiler
from services.story_analyzer import StoryAnalyzer
from services.consistency_engine import ConsistencyEngine

CONFIG_PATH = Path("c:/StoryForge AI/config/training_rules.json")

class TrainingEngine:
    def __init__(self):
        self.rules = self._load_rules()
        self.memory_ext = MemoryExtractor()
        self.rel_ext = RelationshipExtractor()
        self.char_prof = CharacterProfiler()
        self.analyzer = StoryAnalyzer()
        self.cons_eng = ConsistencyEngine()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "theme_learning_rate": 1.0,
                "relationship_learning_rate": 1.0,
                "character_learning_rate": 1.0,
                "dialogue_indicators": ["\"", "'", "said", "asked", "replied", "muttered"]
            }

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from supported file types."""
        ext = file_path.suffix.lower()
        if ext == ".txt" or ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".pdf":
            text = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _calculate_style(self, text: str) -> dict:
        """Calculate the style fingerprint."""
        words = text.split()
        word_count = len(words)
        if word_count == 0:
            return {"dialogue_ratio": 0.0, "description_ratio": 0.0, "average_sentence_length": 0.0, "average_paragraph_length": 0.0}

        sentences = re.split(r'(?<=[.!?]) +', text)
        paragraphs = [p for p in text.split('\n') if p.strip()]

        dialogue_inds = self.rules.get("dialogue_indicators", [])
        dialogue_words = sum(1 for w in words if any(ind in w.lower() for ind in dialogue_inds))
        
        dialogue_ratio = dialogue_words / word_count
        description_ratio = 1.0 - dialogue_ratio

        avg_sent_len = word_count / max(1, len(sentences))
        avg_para_len = word_count / max(1, len(paragraphs))

        return {
            "dialogue_ratio": dialogue_ratio,
            "description_ratio": description_ratio,
            "average_sentence_length": avg_sent_len,
            "average_paragraph_length": avg_para_len
        }

    def process_document(self, file_path: Path, training_profile: dict) -> dict:
        """Process a document and update the training profile."""
        try:
            text = self._extract_text(file_path)
        except ValueError:
            return training_profile

        # Pipeline
        memory = self.memory_ext.extract(text)
        memory["relationships"] = self.rel_ext.extract_relationships(text, memory)
        self.char_prof.profile_all_characters(text, memory)
        analysis = self.analyzer.analyze_story(memory)
        consistency = self.cons_eng.check_consistency(memory, analysis)

        # Style Fingerprint
        style = self._calculate_style(text)
        word_count = len(text.split())

        # Update Profile
        training_profile["documents_processed"] = training_profile.get("documents_processed", 0) + 1
        training_profile["total_words"] = training_profile.get("total_words", 0) + word_count

        themes = memory.get("themes", [])
        for theme in themes:
            th_val = theme if isinstance(theme, str) else theme.get("name", "Unknown")
            training_profile["themes"][th_val] = training_profile["themes"].get(th_val, 0) + self.rules.get("theme_learning_rate", 1.0)

        for rel in memory.get("relationships", []):
            rt = rel.get("type")
            if rt:
                training_profile["relationship_patterns"][rt] = training_profile["relationship_patterns"].get(rt, 0) + self.rules.get("relationship_learning_rate", 1.0)

        for char in memory.get("characters", []):
            for trait in char.get("traits", []):
                tv = trait.get("value")
                if tv:
                    training_profile["character_patterns"][tv] = training_profile["character_patterns"].get(tv, 0) + self.rules.get("character_learning_rate", 1.0)

        # Running average for style fingerprint
        old_style = training_profile.get("style_fingerprint", {})
        docs = training_profile["documents_processed"]
        
        for k in ["dialogue_ratio", "description_ratio", "average_sentence_length", "average_paragraph_length"]:
            old_val = old_style.get(k, 0.0)
            new_val = style.get(k, 0.0)
            training_profile["style_fingerprint"][k] = ((old_val * (docs - 1)) + new_val) / docs

        # History
        history = training_profile.get("training_history", [])
        history.append({
            "file_name": file_path.name,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "word_count": word_count,
            "themes_found": [t if isinstance(t, str) else t.get("name", "Unknown") for t in themes],
            "characters_found": len(memory.get("characters", [])),
            "relationships_found": len(memory.get("relationships", []))
        })

        return training_profile
