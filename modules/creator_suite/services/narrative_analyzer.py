from typing import Dict, Any
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine

class NarrativeAnalyzer:
    def __init__(self, ke: KnowledgeEngine):
        self.ke = ke

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Heuristic analysis of narrative text."""
        word_count = len(text.split())
        dialogue_count = text.count('"') + text.count("'")  # Rough heuristic
        
        # Pull stats to inform the report
        stats = self.ke.get_statistics()
        
        return {
            "word_count": word_count,
            "pacing_score": "Fast" if word_count < 500 else "Moderate",
            "dialogue_density": round((dialogue_count / max(word_count, 1)) * 100, 2),
            "conflict_density": "High" if "battle" in text.lower() or "fight" in text.lower() else "Low",
            "character_progression": "Static",
            "citations": ["heuristic_analyzer", "knowledge_engine_stats"]
        }
