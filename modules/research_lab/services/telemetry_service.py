import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from modules.knowledge_engine.services.knowledge_database import KnowledgeDatabase

class TelemetryService:
    """Manages tracking, logging, and recalculating pattern success metrics for the Research Lab."""
    
    DB_NAMES = [
        "pattern_performance.json",
        "dataset_experiments.json",
        "training_history.json",
        "evaluation_history.json"
    ]
    
    def __init__(self, db_dir: str = "modules/research_lab/databases"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_db = KnowledgeDatabase()
        self._init_dbs()
        
    def _init_dbs(self):
        """Ensure all telemetry files exist."""
        for name in self.DB_NAMES:
            path = self.db_dir / name
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f)
                    
    def read_db(self, db_name: str) -> List[Dict[str, Any]]:
        path = self.db_dir / db_name
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
            
    def write_db(self, db_name: str, data: List[Dict[str, Any]]) -> None:
        path = self.db_dir / db_name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def log_training_run(self, job_id: str, config: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Logs a completed training run."""
        db = self.read_db("training_history.json")
        run_id = str(uuid.uuid4())
        record = {
            "run_id": run_id,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": config,
            "metrics": metrics
        }
        db.append(record)
        self.write_db("training_history.json", db)
        return run_id

    def log_evaluation_run(self, job_id: str, base_score: float, adapter_score: float, improvement_pct: float, patterns_used: List[str]) -> None:
        """Logs an evaluation run and updates all associated patterns."""
        db = self.read_db("evaluation_history.json")
        record = {
            "eval_id": str(uuid.uuid4()),
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_score": base_score,
            "adapter_score": adapter_score,
            "improvement_pct": improvement_pct,
            "patterns_used": patterns_used
        }
        db.append(record)
        self.write_db("evaluation_history.json", db)
        
        # Recalculate pattern performance
        self._update_pattern_performance(patterns_used, improvement_pct)

    def _update_pattern_performance(self, pattern_ids: List[str], eval_delta: float):
        """Updates the internal pattern performance metrics and syncs to KnowledgeEngine."""
        db = self.read_db("pattern_performance.json")
        
        # Convert DB to lookup
        perf_map = {p["pattern_id"]: p for p in db}
        
        for pid in pattern_ids:
            if pid not in perf_map:
                perf_map[pid] = {
                    "pattern_id": pid,
                    "usage_count": 0,
                    "avg_eval_delta": 0.0,
                    "win_rate_contribution": 0.0,
                    "success_score": 5.0
                }
            
            p = perf_map[pid]
            p["usage_count"] += 1
            
            # Exponential moving average for delta
            alpha = 0.3
            p["avg_eval_delta"] = (alpha * eval_delta) + ((1 - alpha) * p["avg_eval_delta"])
            
            # Simple heuristic mapping for success score (1-10)
            # If delta > 0, score goes up. If delta < 0, score goes down.
            delta_modifier = max(min(eval_delta / 5.0, 1.0), -1.0) # clamp between -1 and 1
            new_score = p["success_score"] + delta_modifier
            p["success_score"] = max(1.0, min(10.0, new_score))
            
            # Sync back to knowledge engine
            self.knowledge_db.update_success_score(pid, p["success_score"])
            
        self.write_db("pattern_performance.json", list(perf_map.values()))
