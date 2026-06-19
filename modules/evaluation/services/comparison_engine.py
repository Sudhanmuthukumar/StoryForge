import json
import random
from pathlib import Path
from typing import Dict, Any

from modules.evaluation.services.response_grader import ResponseGrader

class ComparisonEngine:
    """Orchestrates grading of responses and computes improvement deltas."""
    
    def __init__(self):
        self.grader = ResponseGrader()
        
    def evaluate_results(self, raw_results_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Takes the raw inference responses, runs them through the blind LLM grader,
        and produces the comparison report.
        """
        raw_path = Path(raw_results_file)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_results = json.load(f)
            
        comparison_report = []
        base_total = 0.0
        adapter_total = 0.0
        wins = 0
        
        for category, data in raw_results.items():
            prompt = data["prompt"]
            base_resp = data["base_response"]
            adapter_resp = data.get("adapter_response", base_resp)
            
            # Randomize A and B for True Blind Mode
            is_base_a = random.choice([True, False])
            
            resp_A = base_resp if is_base_a else adapter_resp
            resp_B = adapter_resp if is_base_a else base_resp
            
            # Grade
            grades = self.grader.grade_blind_responses(prompt, resp_A, resp_B)
            
            base_grade = grades.get("Response A" if is_base_a else "Response B", {})
            adapter_grade = grades.get("Response B" if is_base_a else "Response A", {})
            
            b_score = base_grade.get("overall_score", 0.0)
            a_score = adapter_grade.get("overall_score", 0.0)
            
            base_total += b_score
            adapter_total += a_score
            
            if a_score > b_score:
                wins += 1
                
            report_item = {
                "category": category,
                "base_score": b_score,
                "storyforge_score": a_score,
                "improvement": round(a_score - b_score, 2),
                "base_reasoning": base_grade.get("reasoning", ""),
                "adapter_reasoning": adapter_grade.get("reasoning", "")
            }
            comparison_report.append(report_item)
            
        # Summary
        count = len(raw_results)
        avg_base = base_total / count if count > 0 else 0.0
        avg_adapter = adapter_total / count if count > 0 else 0.0
        win_rate = (wins / count) * 100 if count > 0 else 0.0
        improvement_pct = ((avg_adapter - avg_base) / avg_base * 100) if avg_base > 0 else 0.0
        
        pass_criteria = (improvement_pct > 5.0) and (win_rate >= 50.0)
        
        summary = {
            "avg_base_score": round(avg_base, 2),
            "avg_adapter_score": round(avg_adapter, 2),
            "improvement_pct": round(improvement_pct, 2),
            "win_rate_pct": round(win_rate, 2),
            "passed": pass_criteria
        }
        
        with open(out_dir / "comparison_report.json", "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "details": comparison_report}, f, indent=4)
            
        # Model Scorecard
        scorecard = {
            "model": "StoryForge-LoRA",
            "overall_score": summary["avg_adapter_score"],
            "improvement": summary["improvement_pct"],
            "status": "PASSED" if pass_criteria else "FAILED"
        }
        with open(out_dir / "model_scorecard.json", "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=4)
            
        return summary
