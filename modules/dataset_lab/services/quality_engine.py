import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import ollama
from services.ai_service import AIService

class QualityEngine:
    """Evaluates the quality of dataset examples across 9 dimensions."""
    
    def __init__(self, input_dir: str = "dataset_lab/training/pilot"):
        self.ai = AIService()
        self.input_dir = Path(input_dir)
        self.report_path = self.input_dir.parent / "logs" / "quality_report.json"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return {}

    def generate_example_id(self, example: Dict[str, Any]) -> str:
        """Generates a stable ID based on instruction and input."""
        unique_string = f"{example.get('instruction', '')}_{example.get('input', '')}_{example.get('output', '')}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def evaluate_all(self, callback=None) -> List[Dict[str, Any]]:
        """Evaluates all .jsonl files in the input directory."""
        if not self.input_dir.exists():
            return []
            
        reports = self._load_existing_report()
        evaluated_ids = {r["example_id"] for r in reports}
        
        for file_path in self.input_dir.glob("*.jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                        
                    try:
                        example = json.loads(line)
                        ex_id = self.generate_example_id(example)
                        
                        if ex_id in evaluated_ids:
                            continue
                            
                        report = self._evaluate_example(ex_id, example)
                        reports.append(report)
                        evaluated_ids.add(ex_id)
                        
                        self._save_report(reports)
                        
                        if callback:
                            callback(report)
                            
                    except Exception:
                        continue
                        
        return reports

    def _evaluate_example(self, ex_id: str, example: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the 9-metric grading prompt."""
        instruction = example.get("instruction", "")
        output_text = example.get("output", "")
        
        prompt = (
            "Evaluate the following synthetic training example for a creative writing AI.\n"
            "Score each of the following categories from 1 to 10:\n"
            "1. coherence, 2. creativity, 3. originality, 4. genre_alignment, 5. character_consistency, "
            "6. dialogue_quality, 7. worldbuilding_quality, 8. instruction_compliance, 9. narrative_quality.\n"
            "Output strictly valid JSON:\n"
            "{\n"
            "  \"coherence\": <int>,\n"
            "  \"creativity\": <int>,\n"
            "  \"originality\": <int>,\n"
            "  \"genre_alignment\": <int>,\n"
            "  \"character_consistency\": <int>,\n"
            "  \"dialogue_quality\": <int>,\n"
            "  \"worldbuilding_quality\": <int>,\n"
            "  \"instruction_compliance\": <int>,\n"
            "  \"narrative_quality\": <int>,\n"
            "  \"notes\": \"<brief reason>\"\n"
            "}\n\n"
            f"INSTRUCTION: {instruction}\n"
            f"OUTPUT: {output_text}"
        )
        
        try:
            resp = ollama.chat(model=self.ai.model, messages=[{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp["message"]["content"])
            
            metrics = ["coherence", "creativity", "originality", "genre_alignment", 
                       "character_consistency", "dialogue_quality", "worldbuilding_quality", 
                       "instruction_compliance", "narrative_quality"]
            
            total_score = 0
            for m in metrics:
                score = max(1, min(10, int(data.get(m, 5))))
                data[m] = score
                total_score += score
                
            avg_score = total_score / len(metrics)
            
            return {
                "example_id": ex_id,
                "quality_score": round(avg_score, 2),
                "coherence": data["coherence"],
                "creativity": data["creativity"],
                "originality": data["originality"],
                "genre_alignment": data["genre_alignment"],
                "character_consistency": data["character_consistency"],
                "dialogue_quality": data["dialogue_quality"],
                "worldbuilding_quality": data["worldbuilding_quality"],
                "instruction_compliance": data["instruction_compliance"],
                "narrative_quality": data["narrative_quality"],
                "notes": data.get("notes", "")
            }
        except Exception:
            return {
                "example_id": ex_id,
                "quality_score": 5.0,
                "coherence": 5, "creativity": 5, "originality": 5, "genre_alignment": 5,
                "character_consistency": 5, "dialogue_quality": 5, "worldbuilding_quality": 5,
                "instruction_compliance": 5, "narrative_quality": 5,
                "notes": "Error evaluating."
            }
            
    def _load_existing_report(self) -> List[Dict[str, Any]]:
        if self.report_path.exists():
            try:
                with open(self.report_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
        
    def _save_report(self, data: List[Dict[str, Any]]) -> None:
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
