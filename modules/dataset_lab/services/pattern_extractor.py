import json
import re
import ollama
from typing import Dict, Any
from typing import Dict, Any
from services.ai_service import AIService

class PatternExtractor:
    """Extracts storytelling patterns using a 3-pass LLM strategy."""
    
    def __init__(self):
        self.ai = AIService()
        
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Safely parses JSON from an LLM response."""
        try:
            # Find the first { and last } to strip markdown
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                clean = text[start:end+1]
                return json.loads(clean)
        except Exception:
            pass
        return {}
        
    def run_pass_1(self, text: str) -> Dict[str, Any]:
        """Pass 1: Genre, Theme, Narrative Style"""
        prompt = (
            "Analyze the following text and extract storytelling patterns. "
            "Output strictly valid JSON with no conversational filler. Format:\n"
            "{\n"
            "  \"genre_profiles\": [\"list of genres/subgenres\"],\n"
            "  \"theme_profiles\": [\"list of core themes/motifs\"],\n"
            "  \"narrative_patterns\": [\"POV, tense, narrative voice descriptions\"]\n"
            "}\n\n"
            f"TEXT:\n{text[:6000]}"
        )
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            return self._parse_json_response(resp["message"]["content"])
        except Exception:
            return {}
        
    def run_pass_2(self, text: str) -> Dict[str, Any]:
        """Pass 2: Characters, Dialogue, Conflict"""
        prompt = (
            "Analyze the following text and extract storytelling patterns. "
            "Output strictly valid JSON with no conversational filler. Format:\n"
            "{\n"
            "  \"character_patterns\": [\"archetypes, roles, traits\"],\n"
            "  \"dialogue_patterns\": [\"speech styles, subtext, humor\"],\n"
            "  \"conflict_patterns\": [\"internal, external, moral conflicts\"]\n"
            "}\n\n"
            f"TEXT:\n{text[:6000]}"
        )
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            return self._parse_json_response(resp["message"]["content"])
        except Exception:
            return {}
        
    def run_pass_3(self, text: str) -> Dict[str, Any]:
        """Pass 3: Worldbuilding, Scenes, Storytelling Devices"""
        prompt = (
            "Analyze the following text and extract storytelling patterns. "
            "Output strictly valid JSON with no conversational filler. Format:\n"
            "{\n"
            "  \"worldbuilding_patterns\": [\"politics, magic, tech, settings\"],\n"
            "  \"scene_patterns\": [\"pacing, purpose, emotional shifts\"],\n"
            "  \"storytelling_devices\": [\"foreshadowing, mystery, irony\"]\n"
            "}\n\n"
            f"TEXT:\n{text[:6000]}"
        )
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            return self._parse_json_response(resp["message"]["content"])
        except Exception:
            return {}
        
    def extract_all(self, chapter_text: str) -> Dict[str, Any]:
        """Executes all 3 passes and merges the results into a single raw pattern dictionary."""
        p1 = self.run_pass_1(chapter_text)
        p2 = self.run_pass_2(chapter_text)
        p3 = self.run_pass_3(chapter_text)
        
        # Merge dicts
        result = {}
        result.update(p1)
        result.update(p2)
        result.update(p3)
        return result
