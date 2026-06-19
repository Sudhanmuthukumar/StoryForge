import json
from pathlib import Path
from typing import Dict, Any

class CheckpointManager:
    """Manages extraction and processing progress for the Dataset Lab."""
    
    def __init__(self, checkpoints_dir: str = "dataset_lab/checkpoints"):
        self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_checkpoint_path(self, file_name: str) -> Path:
        safe_name = file_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return self.checkpoints_dir / f"{safe_name}.json"
        
    def load_checkpoint(self, file_name: str) -> Dict[str, Any]:
        """Load checkpoint for a given file. Returns default if none exists."""
        path = self._get_checkpoint_path(file_name)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "file": file_name,
            "book": "",
            "chapter": "",
            "progress": 0,
            "chapters_saved": 0
        }
        
    def save_checkpoint(self, file_name: str, data: Dict[str, Any]) -> None:
        """Save progress data to a checkpoint file."""
        path = self._get_checkpoint_path(file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
