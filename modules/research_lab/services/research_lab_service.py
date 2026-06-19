import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class ResearchLabService:
    """Service to track training runs, evaluations, and pattern metadata."""

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = Path(db_dir) if db_dir else Path(os.path.dirname(os.path.dirname(__file__))) / "databases"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_tracking()

    def _initialize_tracking(self):
        file_path = self.db_dir / "research_tracking.json"
        if not file_path.exists():
            default_data = {
                "training_runs": [],
                "evaluation_runs": [],
                "pattern_usage_metrics": {}
            }
            file_path.write_text(json.dumps(default_data, indent=4), encoding="utf-8")

    def _read_db(self) -> Dict[str, Any]:
        file_path = self.db_dir / "research_tracking.json"
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return {"training_runs": [], "evaluation_runs": [], "pattern_usage_metrics": {}}

    def _write_db(self, data: Dict[str, Any]) -> None:
        file_path = self.db_dir / "research_tracking.json"
        file_path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    def log_training_run(self, run_id: str, dataset_source: str, model_delta: str) -> None:
        data = self._read_db()
        data["training_runs"].append({
            "run_id": run_id,
            "dataset_source": dataset_source,
            "model_delta": model_delta,
            "timestamp": "2026-06-19T00:00:00Z"
        })
        self._write_db(data)

    def log_evaluation_run(self, eval_id: str, target: str, score: float) -> None:
        data = self._read_db()
        data["evaluation_runs"].append({
            "eval_id": eval_id,
            "target": target,
            "score": score,
            "timestamp": "2026-06-19T00:00:00Z"
        })
        self._write_db(data)

    def get_tracking_data(self) -> Dict[str, Any]:
        return self._read_db()
