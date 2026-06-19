from typing import Dict, Any

class TrainingEstimator:
    """Heuristic estimator for VRAM, RAM, and Dataset sizes."""
    
    def __init__(self):
        # Rough parameters mapping for approximation
        self.model_sizes = {
            "qwen3:8b": 8.0,
            "qwen2.5:3b": 3.0,
        }
        
    def estimate(self, model_name: str, config: Dict[str, Any], total_examples: int) -> Dict[str, Any]:
        """Calculates rough heuristic estimates for training."""
        
        # Determine base parameter count (fallback to 7B if unknown)
        params_b = 7.0
        for known_model, size in self.model_sizes.items():
            if known_model in model_name:
                params_b = size
                break
                
        rank = config.get("rank", 16)
        batch_size = config.get("batch_size", 2)
        seq_length = config.get("seq_length", 2048)
        
        # VRAM Heuristics (in GB):
        # 1. Base model in 4-bit/8-bit (approx 0.7 GB per 1B parameters)
        base_vram = params_b * 0.7 
        # 2. LoRA weights (approx 0.05 GB per Rank level)
        lora_vram = (rank / 16.0) * 0.5
        # 3. Activations / Batch Size overhead (approx 0.4 GB per batch item per 2048 seq)
        act_vram = batch_size * (seq_length / 2048.0) * 0.4
        
        total_vram_gb = base_vram + lora_vram + act_vram
        
        # RAM Heuristics (Usually needs at least 1.5x model weights to load safely)
        total_ram_gb = params_b * 1.5 + 4.0
        
        # Feasibility check
        feasibility = "FEASIBLE"
        confidence = "HIGH"
        
        if total_vram_gb > 24.0:
            feasibility = "LIKELY OOM (OUT OF MEMORY)"
            confidence = "MEDIUM"
        elif total_vram_gb > 16.0:
            feasibility = "REQUIRES 24GB VRAM"
        elif total_vram_gb > 8.0:
            feasibility = "REQUIRES 12GB+ VRAM"
            
        # Time Estimate (rough heuristic: 1 second per example per epoch for 8B)
        epochs = config.get("epochs", 3)
        time_sec = total_examples * epochs * (params_b / 8.0)
        time_str = f"{time_sec / 3600:.1f} Hours" if time_sec > 3600 else f"{time_sec / 60:.1f} Minutes"
        
        return {
            "vram_gb": round(total_vram_gb, 1),
            "ram_gb": round(total_ram_gb, 1),
            "time_estimate": time_str,
            "feasibility": feasibility,
            "confidence": confidence,
            "total_tokens_est": total_examples * (seq_length * 0.6) # rough guess
        }
