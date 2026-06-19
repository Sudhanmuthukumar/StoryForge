import json
import ollama
from pathlib import Path
from typing import Dict, Any
from services.ai_service import AIService

class DatasetGenerator:
    """Synthesizes high-quality training datasets from Structured Context abstractions."""
    
    def __init__(self, output_dir: str = "dataset_lab/training/pilot"):
        self.ai = AIService()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return {}

    def generate_example(self, category: str, context: Dict[str, str], metadata: Dict[str, str]) -> Dict[str, Any]:
        """
        Generates an instruction-input-output pairing based strictly on abstract context.
        """
        prompt = (
            f"You are generating a synthetic training dataset for a creative writing AI.\n"
            f"Generate an example for the category: '{category}'.\n"
            f"Use the following abstract structural constraints:\n"
            f"- Pattern: {context.get('source_pattern')}\n"
            f"- Genre: {context.get('genre')}\n"
            f"- Scene Type: {context.get('scene_type')}\n"
            f"- Conflict: {context.get('conflict')}\n"
            f"- Archetype: {context.get('character_archetype')}\n"
            f"- Worldbuilding: {context.get('worldbuilding_type')}\n"
            f"- Summary: {context.get('short_summary')}\n\n"
            "Output strictly valid JSON with no conversational filler in this exact format:\n"
            "{\n"
            "  \"instruction\": \"<What the user would ask, e.g. 'Write a dialogue scene where...'>\",\n"
            "  \"input\": \"<A brief setup or preceding context for the model>\",\n"
            "  \"output\": \"<The generated creative prose (150-300 words) satisfying the instruction>\"\n"
            "}\n"
        )
        
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            gen_data = self._parse_json_response(resp["message"]["content"])
            
            if not gen_data.get("output"):
                return None
                
            # Grade quality
            quality_score = self._score_quality(gen_data["output"], category, context.get("source_pattern"))
            
            return {
                "instruction": gen_data.get("instruction", ""),
                "tags": [category, context.get("genre"), context.get("source_pattern")],
                "quality_score": quality_score,
                "input": gen_data.get("input", ""),
                "output": gen_data.get("output", ""),
                "source_pattern": context.get("source_pattern"),
                "source_scene_type": context.get("scene_type"),
                "source_genre": context.get("genre"),
                "source_book": metadata.get("source_book"),
                "source_chapter": metadata.get("source_chapter")
            }
        except Exception:
            return None

    def _score_quality(self, output_text: str, category: str, pattern: str) -> int:
        """Invokes a quick grading prompt."""
        prompt = (
            f"Rate the following creative text on a scale of 1-10 based on how well it executes "
            f"the storytelling pattern '{pattern}' and the category '{category}'.\n"
            "Output strictly valid JSON: {\"score\": <int>}\n\n"
            f"TEXT:\n{output_text}"
        )
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp["message"]["content"])
            score = data.get("score", 5)
            # Clamping
            return max(1, min(10, int(score)))
        except Exception:
            return 5
            
    def save_example(self, category: str, example: Dict[str, Any]) -> None:
        """Saves as JSONL ensuring bounds (Pilot bounded to a single file)."""
        safe_cat = category.lower().replace(" ", "_")
        file_path = self.output_dir / f"{safe_cat}_001.jsonl"
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(example) + "\n")
