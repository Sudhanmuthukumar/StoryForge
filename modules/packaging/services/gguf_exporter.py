import os
import subprocess
from pathlib import Path

class GGUFExporter:
    """Manages the conversion of merged safetensors into GGUF using llama.cpp."""
    
    def __init__(self):
        # Allow user to specify a llama.cpp directory via env var, or check local path
        self.llama_cpp_path = os.environ.get("LLAMA_CPP_PATH", "C:\\llama.cpp")
        
    def check_availability(self) -> dict:
        """Verifies if the llama.cpp conversion tools are present."""
        path = Path(self.llama_cpp_path)
        convert_script = path / "convert_hf_to_gguf.py"
        quantize_bin = path / "build" / "bin" / "Release" / "llama-quantize.exe" # Typical windows MSVC build path
        if not quantize_bin.exists():
            quantize_bin = path / "build" / "bin" / "llama-quantize.exe" # Typical MinGW build path
            
        status = {
            "available": False,
            "convert_script": str(convert_script) if convert_script.exists() else None,
            "quantize_bin": str(quantize_bin) if quantize_bin.exists() else None,
            "instructions": "llama.cpp not found. GGUF Export disabled. Please clone llama.cpp and compile it to enable this feature."
        }
        
        if status["convert_script"] and status["quantize_bin"]:
            status["available"] = True
            
        return status
        
    def export_gguf(self, merged_dir: str, output_name: str = "storyforge-q4.gguf") -> str:
        """
        Executes the conversion subprocess.
        Returns the path to the final GGUF.
        """
        status = self.check_availability()
        if not status["available"]:
            raise EnvironmentError(status["instructions"])
            
        output_dir = Path("models/storyforge_gguf")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        out_f16 = output_dir / "temp_f16.gguf"
        final_out = output_dir / output_name
        
        # 1. Convert to F16 GGUF
        subprocess.run(
            ["python", status["convert_script"], merged_dir, "--outfile", str(out_f16), "--outtype", "f16"],
            check=True
        )
        
        # 2. Quantize to Q4_K_M
        subprocess.run(
            [status["quantize_bin"], str(out_f16), str(final_out), "Q4_K_M"],
            check=True
        )
        
        # Cleanup F16
        if out_f16.exists():
            out_f16.unlink()
            
        return str(final_out)
