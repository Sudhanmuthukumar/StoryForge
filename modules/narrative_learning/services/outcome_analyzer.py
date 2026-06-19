"""
outcome_analyzer.py — Evaluates the results of past recommendations.

Checks pending learning records. If the observation window (e.g., 3 ticks)
has passed, it compares the current state to the recorded "before" state
and calculates success deltas.
"""

from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.narrative_learning.services.experience_collector import ExperienceCollector

class OutcomeAnalyzer:
    """Analyzes narrative outcomes after an observation window."""

    OBSERVATION_WINDOW_TICKS = 3

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self.collector = ExperienceCollector(db_dir=db_dir)

    def evaluate_pending_records(
        self, 
        current_tick: int, 
        current_health: Dict[str, Any], 
        current_diversity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Evaluate pending learning records that have passed the observation window.
        
        Args:
            current_tick: The current simulation tick index.
            current_health: The latest campaign health snapshot.
            current_diversity: The latest diversity snapshot.
            
        Returns:
            List of evaluated records (with calculated deltas).
        """
        pending = self.collector.get_pending_records()
        evaluated_records = []

        # Build current state summary for comparison
        after_state = {
            "metrics": current_health.get("metrics", {}),
            "pacing_state": current_health.get("pacing_state", "unknown"),
            "overall_diversity": current_diversity.get("overall_diversity", 0.0),
            "main_arc_progress": current_health.get("arc_progress", {}).get("main_campaign", {}).get("progress", 0.0),
            "world_stability": current_health.get("metrics", {}).get("world_stability", 1.0)
        }

        for record in pending:
            issued_tick = record.get("issued_at_tick", 0)
            
            # Check if observation window has elapsed
            if current_tick >= issued_tick + self.OBSERVATION_WINDOW_TICKS:
                before = record.get("before_state", {})
                
                # Calculate deltas
                health_delta = self._calculate_health_delta(before.get("metrics", {}), after_state["metrics"])
                diversity_delta = after_state["overall_diversity"] - before.get("overall_diversity", 0.0)
                arc_delta = after_state["main_arc_progress"] - before.get("main_arc_progress", 0.0)
                stability_delta = after_state["world_stability"] - before.get("world_stability", 1.0)
                
                # Overall outcome score (-1.0 to 1.0)
                # Weights: Health (40%), Diversity (30%), Arc Progress (20%), Stability (10%)
                outcome_score = (
                    (health_delta * 0.4) +
                    (diversity_delta * 0.3) +
                    (arc_delta * 0.2) +
                    (stability_delta * 0.1)
                )

                deltas = {
                    "health_delta": round(health_delta, 4),
                    "diversity_delta": round(diversity_delta, 4),
                    "arc_progress_delta": round(arc_delta, 4),
                    "stability_delta": round(stability_delta, 4),
                    "overall_score": round(outcome_score, 4)
                }

                updates = {
                    "after_state": after_state,
                    "outcome_deltas": deltas,
                    "evaluation_status": "evaluated"
                }

                self.collector.update_record(record["record_id"], updates)
                
                # Create a completed copy to return to the learning engine
                completed_record = dict(record)
                completed_record.update(updates)
                evaluated_records.append(completed_record)

        return evaluated_records

    def _calculate_health_delta(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """Calculate the overall improvement in narrative health metrics.
        
        A simple heuristic: We want tension and mystery to be moderate-to-high, 
        event frequency to be moderate, etc. For simplicity, we'll sum the positive
        improvements.
        """
        if not before or not after:
            return 0.0
            
        score = 0.0
        # Positive metrics (we want these to go up or stay healthy)
        for k in ["quest_density", "mystery"]:
            score += (after.get(k, 0) - before.get(k, 0))
            
        # Balanced metrics (we want these around 0.5 - 0.7, penalize extremes)
        for k in ["tension", "event_frequency"]:
            b_val = before.get(k, 0)
            a_val = after.get(k, 0)
            
            # Distance from ideal (0.6)
            b_dist = abs(b_val - 0.6)
            a_dist = abs(a_val - 0.6)
            
            # Improvement is a reduction in distance
            score += (b_dist - a_dist)
            
        return score / 4.0  # Normalize roughly
