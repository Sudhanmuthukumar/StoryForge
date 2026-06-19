"""
learning_engine.py — Updates strategy scores based on evaluated outcomes.

Maintains `strategy_scores.json`. Uses evaluated learning records to adjust
the expected success probability (score) of specific director strategies.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.storyforge_core.events.event_bus import EventBus

class LearningEngine:
    """Updates persistent strategy success scores using RL-like updates."""

    # Default baseline scores for unknown strategies
    DEFAULT_STRATEGY_SCORE = 0.5
    
    # Learning rate (alpha) - how much new outcomes affect the historical score
    LEARNING_RATE = 0.15

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self._initialize_scores()

    def _initialize_scores(self):
        """Ensure strategy_scores.json exists with default structures."""
        scores = self.db.read_db("strategy_scores.json")
        if not scores:
            scores = {
                "strategies": {
                    "pacing_transition": self.DEFAULT_STRATEGY_SCORE,
                    "quest_type_preference": self.DEFAULT_STRATEGY_SCORE,
                    "faction_focus": self.DEFAULT_STRATEGY_SCORE,
                    "event_spawn_block": self.DEFAULT_STRATEGY_SCORE
                },
                "total_evaluations": 0
            }
            self.db.write_db("strategy_scores.json", scores)

    def process_evaluations(self, evaluated_records: List[Dict[str, Any]]) -> None:
        """Update strategy scores based on newly evaluated learning records."""
        if not evaluated_records:
            return

        scores_db = self.db.read_db("strategy_scores.json")
        strategies = scores_db.get("strategies", {})

        for record in evaluated_records:
            rec = record.get("recommendation_applied", {})
            rec_type = rec.get("type", "unknown")
            
            # Get the outcome score (-1.0 to 1.0)
            outcome = record.get("outcome_deltas", {}).get("overall_score", 0.0)
            
            # Map outcome from [-1.0, 1.0] to [0.0, 1.0] for easier score blending
            normalized_outcome = (outcome + 1.0) / 2.0
            # Clamp it just in case
            normalized_outcome = max(0.0, min(1.0, normalized_outcome))
            
            # Get current score
            current_score = strategies.get(rec_type, self.DEFAULT_STRATEGY_SCORE)
            
            # Exponential moving average update
            # New_Score = (1 - alpha) * Current_Score + alpha * New_Outcome
            new_score = ((1.0 - self.LEARNING_RATE) * current_score) + (self.LEARNING_RATE * normalized_outcome)
            
            strategies[rec_type] = round(new_score, 4)
            scores_db["total_evaluations"] = scores_db.get("total_evaluations", 0) + 1

        scores_db["strategies"] = strategies
        self.db.write_db("strategy_scores.json", scores_db)
        EventBus().publish("StrategyLearned", {"strategies_updated": list(strategies.keys())})

    def get_strategy_score(self, strategy_type: str) -> float:
        """Get the current success score for a specific strategy type."""
        scores_db = self.db.read_db("strategy_scores.json")
        strategies = scores_db.get("strategies", {})
        return strategies.get(strategy_type, self.DEFAULT_STRATEGY_SCORE)
