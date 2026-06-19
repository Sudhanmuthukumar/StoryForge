"""
experience_collector.py — Captures pre-intervention states and recommendations.

When the Campaign Director issues a recommendation (or applies a constraint),
the Experience Collector records the current "before" state. This record
stays pending until the observation window passes and the Outcome Analyzer
evaluates it.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase

class ExperienceCollector:
    """Collects state snapshots before and during narrative interventions."""

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()

    def record_intervention(
        self, 
        current_tick: int, 
        health_snapshot: Dict[str, Any], 
        diversity_snapshot: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """Record a new learning event for an issued recommendation.
        
        Args:
            current_tick: The current simulation tick index
            health_snapshot: Current metrics and pacing from Campaign Director
            diversity_snapshot: Current diversity overview from Campaign Director
            recommendation: The specific directive/recommendation issued
            
        Returns:
            The generated learning record ID.
        """
        records = self.db.read_db("campaign_learning.json")
        if not isinstance(records, list):
            records = []

        record_id = f"lr_{uuid.uuid4().hex[:8]}"
        
        # Build the before_state summary
        before_state = {
            "metrics": health_snapshot.get("metrics", {}),
            "pacing_state": health_snapshot.get("pacing_state", "unknown"),
            "overall_diversity": diversity_snapshot.get("overall_diversity", 0.0),
            "main_arc_progress": health_snapshot.get("arc_progress", {}).get("main_campaign", {}).get("progress", 0.0),
            "world_stability": health_snapshot.get("metrics", {}).get("world_stability", 1.0)
        }

        # Build the record
        record = {
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "issued_at_tick": current_tick,
            "recommendation_applied": recommendation,
            "before_state": before_state,
            "after_state": {},
            "outcome_deltas": {},
            "evaluation_status": "pending"
        }

        records.append(record)
        self.db.write_db("campaign_learning.json", records)

        return record_id

    def get_pending_records(self) -> List[Dict[str, Any]]:
        """Retrieve all records that have not yet been evaluated."""
        records = self.db.read_db("campaign_learning.json")
        if not isinstance(records, list):
            return []
        
        return [r for r in records if r.get("evaluation_status") == "pending"]

    def update_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update a learning record with new data (e.g. after_state, deltas)."""
        records = self.db.read_db("campaign_learning.json")
        if not isinstance(records, list):
            return False
            
        for r in records:
            if r.get("record_id") == record_id:
                r.update(updates)
                self.db.write_db("campaign_learning.json", records)
                return True
                
        return False
