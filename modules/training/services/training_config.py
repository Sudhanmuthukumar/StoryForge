import os
import ollama
from typing import Dict, Any, List

class TrainingConfig:
    """Manages LoRA training hyperparameters and dynamically queries available base models."""
    
    def __init__(self):
        self.default_params = {
            "rank": 16,
            "alpha": 32,
            "epochs": 3,
            "learning_rate": 2e-4,
            "batch_size": 2,
            "seq_length": 2048
        }
        
    def get_defaults(self) -> Dict[str, Any]:
        return self.default_params.copy()
        
    def get_available_models(self) -> List[str]:
        """Queries Ollama for locally installed models to act as base models."""
        available = []
        try:
            resp = ollama.list()
            remote_models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
            for rm in remote_models:
                name = getattr(rm, 'model', None) or (rm.get("model") if isinstance(rm, dict) else "")
                if name:
                    available.append(name)
        except Exception:
            pass
            
        if not available:
            # Safe fallbacks if Ollama is unreachable
            available = ["qwen3:8b", "qwen2.5:3b"]
            
        return available
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validates configuration bounds."""
        try:
            if not isinstance(config.get("rank"), int) or config["rank"] < 1:
                return False
            if not isinstance(config.get("alpha"), int) or config["alpha"] < 1:
                return False
            if not isinstance(config.get("epochs"), int) or config["epochs"] < 1:
                return False
            if config.get("batch_size", 0) < 1:
                return False
            return True
        except Exception:
            return False
