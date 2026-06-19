import subprocess
from pathlib import Path
from typing import Dict, Any

class OllamaPackager:
    """Manages the creation of Modelfiles and registering models with Ollama."""
    
    def __init__(self):
        self.system_prompt = """You are StoryForge Writer, a specialized AI assistant.
You excel at crafting intricate fantasy narratives, engaging dialogue, and vivid worldbuilding.
Always respond in a creative, narrative tone when asked to tell a story."""
        
    def create_modelfile(self, model_name: str, gguf_path: str, params: Dict[str, Any] = None) -> str:
        """Writes a Modelfile pointing to the GGUF."""
        output_dir = Path("models/modelfiles")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        modelfile_path = output_dir / f"Modelfile_{model_name}"
        gguf_abs = Path(gguf_path).resolve()
        
        lines = [
            f"FROM {gguf_abs}",
            ""
        ]
        
        if params:
            for k, v in params.items():
                lines.append(f"PARAMETER {k} {v}")
                
        lines.append("")
        lines.append(f'SYSTEM """{self.system_prompt}"""')
        
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        return str(modelfile_path)
        
    def register_model(self, model_name: str, modelfile_path: str) -> bool:
        """Executes 'ollama create' to register the model."""
        try:
            subprocess.run(
                ["ollama", "create", model_name, "-f", modelfile_path],
                check=True
            )
            return True
        except Exception as e:
            print(f"Failed to register model {model_name} with Ollama: {e}")
            return False
