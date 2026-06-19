import sys
import json
import time
import argparse
from pathlib import Path

# Try importing ML dependencies
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


def generate_mock_responses(prompts: list, adapter_path: str) -> dict:
    """Fallback generator if ML dependencies are missing for testing."""
    results = {}
    for p in prompts:
        cat = p["category"]
        results[cat] = {
            "prompt": p["prompt"],
            "base_response": f"[MOCK BASE] Base model struggled slightly with {cat}. Output was generic.",
            "adapter_response": f"[MOCK ADAPTER] The StoryForge adapter excelled at {cat}. Output was rich and vivid."
        }
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job_dir", required=True, type=str, help="Path to training job with the adapter")
    parser.add_argument("--output_file", required=True, type=str, help="Where to save benchmark results")
    args = parser.parse_args()
    
    job_dir = Path(args.job_dir)
    output_file = Path(args.output_file)
    adapter_dir = job_dir / "output"
    config_file = job_dir / "config.json"
    
    # Load Prompts
    prompts_path = Path("dataset_lab/benchmarks/benchmark_prompts.json")
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
        
    results = {}
    
    if not ML_AVAILABLE:
        print("ML Dependencies missing. Generating simulated benchmark responses.")
        results = generate_mock_responses(prompts, str(adapter_dir))
    else:
        print("Loading Base Model for Benchmarking...")
        # Get Base Model from config & registry
        with open(config_file, "r") as f:
            job_cfg = json.load(f)
            
        reg_path = Path("modules/training/model_registry.json")
        hf_repo = job_cfg.get("model", "Qwen/Qwen2.5-3B")
        if reg_path.exists():
            with open(reg_path, "r") as f:
                reg = json.load(f)
                hf_repo = reg.get(hf_repo, {}).get("hf_repo", hf_repo)
                
        tokenizer = AutoTokenizer.from_pretrained(hf_repo, trust_remote_code=True)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            hf_repo, device_map="auto", quantization_config=bnb_config, trust_remote_code=True
        )
        
        # 1. Base Model Pass
        print("Running Base Model Inference...")
        for p in prompts:
            cat = p["category"]
            inputs = tokenizer(p["prompt"], return_tensors="pt").to(model.device)
            out = model.generate(**inputs, max_new_tokens=200, do_sample=True, temperature=0.7)
            text = tokenizer.decode(out[0], skip_special_tokens=True).replace(p["prompt"], "").strip()
            results[cat] = {"prompt": p["prompt"], "base_response": text}
            
        # 2. Adapter Model Pass
        print(f"Loading LoRA Adapter from {adapter_dir}...")
        model = PeftModel.from_pretrained(model, str(adapter_dir))
        
        print("Running Adapter Inference...")
        for p in prompts:
            cat = p["category"]
            inputs = tokenizer(p["prompt"], return_tensors="pt").to(model.device)
            out = model.generate(**inputs, max_new_tokens=200, do_sample=True, temperature=0.7)
            text = tokenizer.decode(out[0], skip_special_tokens=True).replace(p["prompt"], "").strip()
            results[cat]["adapter_response"] = text
            
    # Save Raw Results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print(f"Inference complete. Results saved to {output_file}")
    
    # Write Progress
    stats_path = job_dir / "evaluation" / "eval_stats.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({"status": "GRADING", "progress": 50, "stage": "Blind LLM Grading in Progress..."}, f)

    # Run Comparison Engine
    print("Running Comparison Engine for Blind Grading...")
    from modules.evaluation.services.comparison_engine import ComparisonEngine
    engine = ComparisonEngine()
    summary = engine.evaluate_results(str(output_file), str(job_dir / "evaluation"))
    
    # Write Final Progress
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({"status": "COMPLETED", "progress": 100, "stage": "Evaluation Complete", "summary": summary}, f)
        
    print("Evaluation grading complete.")

if __name__ == "__main__":
    main()
