import sys
import json
import argparse
from pathlib import Path

# ML Dependencies
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job_dir", required=True, type=str, help="Path to training job with the adapter")
    parser.add_argument("--output_dir", required=True, type=str, help="Path to save merged model")
    args = parser.parse_args()
    
    job_dir = Path(args.job_dir)
    output_dir = Path(args.output_dir)
    adapter_dir = job_dir / "output" / "adapter_model"
    config_file = job_dir / "config.json"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not ML_AVAILABLE:
        print("ML Dependencies missing. Simulating Model Merge...")
        with open(output_dir / "simulated_merge.txt", "w") as f:
            f.write("This is a simulated merged model directory.")
        print(f"Mock Merge Complete. Saved to {output_dir}")
        sys.exit(0)
        
    print("Loading Base Model for Merging...")
    with open(config_file, "r") as f:
        job_cfg = json.load(f)
        
    reg_path = Path("modules/training/model_registry.json")
    hf_repo = job_cfg.get("model", "Qwen/Qwen2.5-3B")
    if reg_path.exists():
        with open(reg_path, "r") as f:
            reg = json.load(f)
            hf_repo = reg.get(hf_repo, {}).get("hf_repo", hf_repo)
            
    tokenizer = AutoTokenizer.from_pretrained(hf_repo, trust_remote_code=True)
    
    # Load base model in FP16 (do not use 8-bit or 4-bit here, we need full precision to merge)
    model = AutoModelForCausalLM.from_pretrained(
        hf_repo, 
        device_map="cpu", # Best to do merging on CPU/RAM to avoid VRAM OOM
        torch_dtype=torch.float16, 
        trust_remote_code=True
    )
    
    print(f"Loading LoRA Adapter from {adapter_dir}...")
    model = PeftModel.from_pretrained(model, str(adapter_dir))
    
    print("Fusing Adapter Weights into Base Model (merge_and_unload)...")
    merged_model = model.merge_and_unload()
    
    print(f"Saving Merged Model to {output_dir}...")
    merged_model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    
    print("Merge Complete.")

if __name__ == "__main__":
    main()
