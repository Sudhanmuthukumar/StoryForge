import json
import ollama
from pathlib import Path
from typing import Dict, Any
from services.ai_service import AIService

class ContextGenerator:
    """Generates Structured Context abstractions from raw chapters and patterns to prevent source leakage."""
    
    def __init__(self):
        self.ai = AIService()
        
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return {}

    def generate_context(self, pattern_name: str, chapter_text: str) -> Dict[str, str]:
        """
        Extracts a structural abstraction from the chapter text focusing on the specific pattern.
        This breaks the link to copyrighted prose.
        """
        prompt = (
            f"Analyze the following text specifically looking for the storytelling pattern: '{pattern_name}'.\n"
            "Generate a highly abstract, structural summary of how this pattern is executed in the text. "
            "Do NOT quote the text directly. Do NOT use specific character names or unique proper nouns.\n"
            "Output strictly valid JSON in this format:\n"
            "{\n"
            "  \"source_pattern\": \"<the pattern>\",\n"
            "  \"genre\": \"<inferred genre>\",\n"
            "  \"scene_type\": \"<type of scene>\",\n"
            "  \"conflict\": \"<core conflict type>\",\n"
            "  \"character_archetype\": \"<primary archetype involved>\",\n"
            "  \"worldbuilding_type\": \"<relevant world aspect, or N/A>\",\n"
            "  \"short_summary\": \"<1-2 sentence structural summary>\"\n"
            "}\n\n"
            f"TEXT:\n{chapter_text[:6000]}"
        )
        
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp["message"]["content"])
            
            # Ensure fallbacks
            return {
                "source_pattern": data.get("source_pattern", pattern_name),
                "genre": data.get("genre", "Unknown"),
                "scene_type": data.get("scene_type", "Unknown"),
                "conflict": data.get("conflict", "Unknown"),
                "character_archetype": data.get("character_archetype", "Unknown"),
                "worldbuilding_type": data.get("worldbuilding_type", "Unknown"),
                "short_summary": data.get("short_summary", "A narrative structure.")
            }
        except Exception:
            return None
