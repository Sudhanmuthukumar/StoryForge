"""
pacing_manager.py — Implements dramatic pacing curves for narrative direction.

Manages pacing state transitions following the dramatic arc:
  Rising Action → Climax → Falling Action → Resolution → Cooldown → Rising Action

Based on tension, conflict, and event frequency metrics, determines the 
next target pacing state and formulates directives for the Dungeon Master.
"""

from typing import Dict, List, Any, Optional


class PacingManager:
    """Manages dramatic pacing curves and issues pacing directives."""

    # Pacing state machine: valid transitions
    PACING_TRANSITIONS = {
        "rising_action": ["climax"],
        "climax": ["falling_action"],
        "falling_action": ["resolution"],
        "resolution": ["cooldown"],
        "cooldown": ["rising_action"],
    }

    # Thresholds that trigger state transitions
    TENSION_THRESHOLDS = {
        "rising_action": {"min": 0.3, "max": 0.7},   # Moderate tension, building
        "climax": {"min": 0.7, "max": 1.0},           # High tension peak
        "falling_action": {"min": 0.4, "max": 0.7},   # Tension decreasing
        "resolution": {"min": 0.1, "max": 0.4},       # Low tension, wrapping up
        "cooldown": {"min": 0.0, "max": 0.2},         # Minimal tension, rest
    }

    # Duration ranges for each pacing state (in ticks)
    MIN_TICKS_IN_STATE = {
        "rising_action": 3,
        "climax": 2,
        "falling_action": 2,
        "resolution": 2,
        "cooldown": 3,
    }

    def __init__(self):
        self.current_state = "rising_action"
        self.ticks_in_state = 0

    def analyze_pacing(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze current metrics against pacing targets and produce directives.
        
        Args:
            metrics: Dictionary with tension, conflict, mystery, etc. (0.0-1.0 each)
            
        Returns:
            Dictionary with current state, target state, and directives list.
        """
        tension = metrics.get("tension", 0.0)
        conflict = metrics.get("conflict", 0.0)
        event_freq = metrics.get("event_frequency", 0.0)

        # Combined pacing pressure signal
        pacing_signal = (tension * 0.5 + conflict * 0.3 + event_freq * 0.2)

        self.ticks_in_state += 1

        # Determine if we should transition to the next pacing state
        should_transition = self._should_transition(pacing_signal)
        target_state = self.current_state

        if should_transition:
            possible_next = self.PACING_TRANSITIONS.get(self.current_state, [])
            if possible_next:
                target_state = possible_next[0]

        # Generate directives based on current vs target state
        directives = self._generate_directives(metrics, pacing_signal, target_state)

        result = {
            "current_state": self.current_state,
            "target_state": target_state,
            "ticks_in_state": self.ticks_in_state,
            "pacing_signal": round(pacing_signal, 3),
            "directives": directives,
            "transition_recommended": should_transition,
        }

        # Apply transition if recommended
        if should_transition and target_state != self.current_state:
            self.current_state = target_state
            self.ticks_in_state = 0

        return result

    def _should_transition(self, pacing_signal: float) -> bool:
        """Determine if the current pacing state should transition.
        
        A transition is triggered when:
        1. Minimum duration in current state is met, AND
        2. The pacing signal exceeds or falls below the state's threshold range.
        """
        if self.ticks_in_state < self.MIN_TICKS_IN_STATE.get(self.current_state, 2):
            return False

        thresholds = self.TENSION_THRESHOLDS.get(self.current_state, {"min": 0.0, "max": 1.0})

        if self.current_state == "rising_action":
            # Transition to climax when tension exceeds rising_action max
            return pacing_signal >= thresholds["max"]
        elif self.current_state == "climax":
            # Transition to falling_action after peak duration
            return self.ticks_in_state >= self.MIN_TICKS_IN_STATE["climax"]
        elif self.current_state == "falling_action":
            # Transition to resolution when tension drops below threshold
            return pacing_signal <= thresholds["min"]
        elif self.current_state == "resolution":
            # Transition to cooldown when tension is very low
            return pacing_signal <= 0.15
        elif self.current_state == "cooldown":
            # Transition back to rising_action after rest period
            return self.ticks_in_state >= self.MIN_TICKS_IN_STATE["cooldown"]

        return False

    def _generate_directives(self, metrics: Dict[str, float], pacing_signal: float, target_state: str) -> List[Dict[str, Any]]:
        """Generate pacing directives based on the current narrative state."""
        directives = []
        tension = metrics.get("tension", 0.0)
        stability = metrics.get("world_stability", 1.0)

        if self.current_state == "rising_action":
            if tension < 0.3:
                directives.append({
                    "directive_id": f"pace_rise_{self.ticks_in_state}",
                    "type": "tension_adjustment",
                    "description": f"Tension is low ({tension:.2f}). Increase event spawning and faction conflicts to build rising action.",
                    "priority": "medium",
                    "target_metric": "tension",
                    "current_value": tension,
                    "target_value": 0.5,
                })
            elif tension > 0.6:
                directives.append({
                    "directive_id": f"pace_rise_high_{self.ticks_in_state}",
                    "type": "pacing",
                    "description": f"Tension is building well ({tension:.2f}). Approaching climax threshold. Maintain current event rate.",
                    "priority": "low",
                    "target_metric": "tension",
                    "current_value": tension,
                    "target_value": 0.7,
                })

        elif self.current_state == "climax":
            directives.append({
                "directive_id": f"pace_climax_{self.ticks_in_state}",
                "type": "pacing",
                "description": f"CLIMAX phase active. Tension is {tension:.2f}. Allow major events to resolve. Do not spawn new crises.",
                "priority": "high",
                "target_metric": "tension",
                "current_value": tension,
                "target_value": tension,
            })
            # Block new event spawning during climax resolution
            directives.append({
                "directive_id": f"pace_climax_block_{self.ticks_in_state}",
                "type": "cooldown",
                "description": "Block new crisis events during climax resolution. Let existing events play out.",
                "priority": "high",
                "target_metric": "event_frequency",
                "current_value": metrics.get("event_frequency", 0.0),
                "target_value": 0.3,
            })

        elif self.current_state == "falling_action":
            if tension > 0.5:
                directives.append({
                    "directive_id": f"pace_fall_{self.ticks_in_state}",
                    "type": "tension_adjustment",
                    "description": f"Tension still elevated ({tension:.2f}) during falling action. Reduce event spawn rate. Focus on peaceful resolutions.",
                    "priority": "high",
                    "target_metric": "tension",
                    "current_value": tension,
                    "target_value": 0.3,
                })

        elif self.current_state == "resolution":
            directives.append({
                "directive_id": f"pace_resolve_{self.ticks_in_state}",
                "type": "pacing",
                "description": "Resolution phase. Focus on quest completions, NPC relationship building, and story wrap-up.",
                "priority": "medium",
                "target_metric": "quest_density",
                "current_value": metrics.get("quest_density", 0.0),
                "target_value": 0.2,
            })

        elif self.current_state == "cooldown":
            if tension > 0.2:
                directives.append({
                    "directive_id": f"pace_cool_{self.ticks_in_state}",
                    "type": "cooldown",
                    "description": f"Cooldown active but tension ({tension:.2f}) is above threshold. Block all crisis events. Allow only trade and diplomacy.",
                    "priority": "critical",
                    "target_metric": "tension",
                    "current_value": tension,
                    "target_value": 0.1,
                })
            else:
                directives.append({
                    "directive_id": f"pace_cool_rest_{self.ticks_in_state}",
                    "type": "pacing",
                    "description": "Cooldown proceeding normally. World is at peace. Preparing for next rising action.",
                    "priority": "low",
                    "target_metric": "tension",
                    "current_value": tension,
                    "target_value": 0.0,
                })

        return directives

    def set_state(self, state: str) -> None:
        """Force the pacing manager into a specific state (for loading/restoring)."""
        if state in self.PACING_TRANSITIONS:
            self.current_state = state
            self.ticks_in_state = 0

    def get_state_info(self) -> Dict[str, Any]:
        """Get current pacing state summary."""
        return {
            "current_state": self.current_state,
            "ticks_in_state": self.ticks_in_state,
            "min_ticks_required": self.MIN_TICKS_IN_STATE.get(self.current_state, 2),
            "valid_transitions": self.PACING_TRANSITIONS.get(self.current_state, []),
        }
