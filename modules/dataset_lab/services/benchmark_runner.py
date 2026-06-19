import json
import time
from pathlib import Path
from typing import Dict, Any, List
import ollama

class BenchmarkRunner:
    """Evaluates model performance against a curated StoryForge prompt suite."""
    
    def __init__(self, benchmarks_dir: str = "dataset_lab/benchmarks"):
        self.benchmarks_dir = Path(benchmarks_dir)
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = self.benchmarks_dir.parent / "logs" / "benchmark_results.json"
        
        # Ensure we have at least one test case
        self._seed_benchmarks()
        
    def _seed_benchmarks(self):
        sample_path = self.benchmarks_dir / "core_prompts.json"
        if not sample_path.exists():
            sample_data = [
                {"category": "Fantasy", "prompt": "A young scout discovers strange footprints beyond the village border."},
                {"category": "Sci-Fi", "prompt": "The ship's AI calmly explains why the airlock must remain sealed."},
                {"category": "Horror", "prompt": "You wake up and the mirror in your room is facing the wall."},
                {"category": "Dialogue", "prompt": "Two rival assassins are forced to share a cab ride in the rain."}
            ]
            with open(sample_path, "w", encoding="utf-8") as f:
                json.dump(sample_data, f, indent=4)
                
    def run_benchmarks(self, models: List[str] = ["qwen3:8b", "qwen2.5:3b"]) -> Dict[str, Any]:
        prompts = []
        for path in self.benchmarks_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        prompts.extend(data)
            except Exception:
                continue
                
        if not prompts:
            return {}
            
        results = {"timestamp": time.time(), "models": {}, "comparisons": []}
        
        # Test models available
        available = []
        try:
            resp = ollama.list()
            remote_models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
            for rm in remote_models:
                name = getattr(rm, 'model', None) or (rm.get("model") if isinstance(rm, dict) else "")
                available.append(name)
        except Exception:
            pass
            
        active_models = [m for m in models if any(m in a for a in available)]
        if not active_models:
            # Fallback to whatever is active
            active_models = ["qwen3:8b"]
            
        for model in active_models:
            results["models"][model] = {"total_score": 0, "evaluations": []}
            
            for idx, p in enumerate(prompts):
                cat = p.get("category", "General")
                prompt_text = p.get("prompt", "")
                
                # Write intermediate progress
                progress_pct = int(((active_models.index(model) * len(prompts) + idx) / (len(active_models) * len(prompts))) * 100)
                stats_path = self.benchmarks_dir.parent / "logs" / "benchmark_stats.json"
                try:
                    with open(stats_path, "w", encoding="utf-8") as f:
                        json.dump({"status": "RUNNING", "progress": progress_pct, "stage": f"Evaluating {model} - {cat}"}, f)
                except Exception:
                    pass
                
                try:
                    start_t = time.time()
                    resp = ollama.chat(model=model, messages=[
                        {"role": "system", "content": "Write a 150 word creative response to the prompt."},
                        {"role": "user", "content": prompt_text}
                    ])
                    output = resp["message"]["content"]
                    dur = time.time() - start_t
                    
                    # Auto-Grade
                    score = self._grade_output(model, output, cat)
                    
                    results["models"][model]["evaluations"].append({
                        "category": cat,
                        "prompt": prompt_text,
                        "output": output,
                        "score": score,
                        "time_sec": round(dur, 2)
                    })
                    results["models"][model]["total_score"] += score
                except Exception as e:
                    continue
                    
            evals = len(results["models"][model]["evaluations"])
            if evals > 0:
                results["models"][model]["avg_score"] = results["models"][model]["total_score"] / evals
                
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
            
        # Write final progress
        try:
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump({"status": "COMPLETED", "progress": 100, "stage": "Benchmarks complete", "results": results}, f)
        except Exception:
            pass
            
        return results
        
    def _grade_output(self, grading_model: str, text: str, category: str) -> int:
        prompt = (
            f"Rate the following creative text on a scale of 1-100 based on Creativity, Coherence, "
            f"Detail, Consistency, and {category} Genre Alignment.\n"
            "Output strictly valid JSON: {\"score\": <int>}\n\n"
            f"TEXT:\n{text}"
        )
        try:
            resp = ollama.chat(model=grading_model, messages=[{"role": "user", "content": prompt}])
            out = resp["message"]["content"]
            start = out.find('{')
            end = out.rfind('}')
            data = json.loads(out[start:end+1])
            return max(1, min(100, int(data.get("score", 50))))
        except Exception:
            return 50

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks_dir", type=str, default="dataset_lab/benchmarks")
    args = parser.parse_args()
    
    runner = BenchmarkRunner(benchmarks_dir=args.benchmarks_dir)
    runner.run_benchmarks()
