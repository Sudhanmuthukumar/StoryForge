import sys
import psutil
import shutil
import importlib.util
from typing import Dict, Any

class EnvironmentValidator:
    """Validates hardware and software readiness for LoRA Training."""
    
    def __init__(self):
        self.required_packages = ["torch", "transformers", "peft", "trl", "accelerate"]
        
    def check_environment(self) -> Dict[str, Any]:
        """Returns the full environment evaluation map."""
        
        # Dependency check
        installed_deps = []
        missing_deps = []
        
        for pkg in self.required_packages:
            if importlib.util.find_spec(pkg) is not None:
                installed_deps.append(pkg)
            else:
                missing_deps.append(pkg)
                
        # RAM Check
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        
        # Disk Check (assuming current working directory drive)
        disk_gb = round(shutil.disk_usage(".").free / (1024**3), 2)
        
        # CUDA / VRAM check
        cuda_available = False
        gpu_name = "Unknown or None"
        vram_gb = 0.0
        
        try:
            if "torch" in installed_deps:
                import torch
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    gpu_name = torch.cuda.get_device_name(0)
                    # Convert bytes to GB
                    vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        except Exception:
            pass
            
        training_ready = (len(missing_deps) == 0) and cuda_available and (vram_gb >= 4.0) and (disk_gb >= 10.0)
        
        return {
            "python_version": sys.version.split()[0],
            "gpu": gpu_name,
            "vram_gb": vram_gb,
            "ram_gb": ram_gb,
            "disk_gb": disk_gb,
            "cuda": cuda_available,
            "installed_deps": installed_deps,
            "missing_deps": missing_deps,
            "training_ready": training_ready
        }
