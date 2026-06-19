"""
adaptive_director.py — Refines baseline recommendations using learned strategy scores.

The Adaptive Director sits between the baseline Campaign Director and the Dungeon Master.
It takes the list of deterministic recommendations and uses the Learning Engine's
historical strategy scores to adjust, filter, or re-prioritize them.
"""

from typing import Dict, List, Any, Optional
import random

from modules.narrative_learning.services.learning_engine import LearningEngine

class AdaptiveDirector:
    """Refines rule-based recommendations using historical learning."""

    def __init__(self, db_dir: Optional[str] = None):
        self.learning_engine = LearningEngine(db_dir=db_dir)
        
        # Hyperparameter: how likely we are to explore strategies with low scores
        self.exploration_rate = 0.1

    def refine_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Refine and filter a list of recommendations based on historical success.
        
        Args:
            recommendations: List of raw recommendations from the baseline Director.
            
        Returns:
            Filtered and prioritized list of recommendations.
        """
        if not recommendations:
            return []

        refined = []
        
        for rec in recommendations:
            rec_type = rec.get("type", "unknown")
            score = self.learning_engine.get_strategy_score(rec_type)
            
            # 1. Base Priority Adjustments
            if score > 0.65:
                # Highly successful strategy, boost priority
                rec["priority"] = self._boost_priority(rec.get("priority", "medium"))
            elif score < 0.35:
                # Poorly performing strategy, reduce priority
                rec["priority"] = self._reduce_priority(rec.get("priority", "medium"))
                
            # 2. Filtering mechanism (Thompson sampling / Epsilon-Greedy approach)
            # If the score is very low, we might drop the recommendation entirely
            # unless we roll exploration.
            retention_chance = score + self.exploration_rate
            if random.random() <= retention_chance:
                refined.append(rec)
            else:
                # Suppressed by learning engine
                pass

        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        refined.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 0), reverse=True)

        return refined

    def _boost_priority(self, current_priority: str) -> str:
        if current_priority == "low": return "medium"
        if current_priority == "medium": return "high"
        if current_priority == "high": return "critical"
        return "critical"

    def _reduce_priority(self, current_priority: str) -> str:
        if current_priority == "critical": return "high"
        if current_priority == "high": return "medium"
        if current_priority == "medium": return "low"
        return "low"
