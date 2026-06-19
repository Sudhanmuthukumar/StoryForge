"""
narrative_health_analyzer.py — Computes quantitative narrative health metrics from simulation databases.

Reads world_state.json, npc_memory.json, reputation.json, and event_history.json
to produce a health snapshot covering:
  - Tension, Conflict, Mystery, Quest Density, Event Frequency, Faction Pressure, World Stability

This is Stage 1 (Observation Mode): purely reads and computes, never modifies state.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase


class NarrativeHealthAnalyzer:
    """Computes narrative health metrics from the current simulation state."""

    # Metric weights for severity scoring
    SEVERITY_WEIGHTS = {
        "Low": 0.2,
        "Medium": 0.5,
        "High": 0.8,
        "Critical": 1.0
    }

    def __init__(self, db: Optional[SimulationDatabase] = None):
        self.db = db or SimulationDatabase()

    def compute_health(self) -> Dict[str, Any]:
        """Compute all narrative health metrics and return a structured snapshot."""
        world_state = self.db.read_db("world_state.json")
        npc_memories = self.db.read_db("npc_memory.json")
        reputation = self.db.read_db("reputation.json")
        event_history = self.db.read_db("event_history.json")

        metrics = {
            "tension": self._compute_tension(world_state, event_history),
            "conflict": self._compute_conflict(reputation),
            "mystery": self._compute_mystery(npc_memories, world_state),
            "quest_density": self._compute_quest_density(world_state),
            "event_frequency": self._compute_event_frequency(event_history),
            "faction_pressure": self._compute_faction_pressure(reputation),
            "world_stability": self._compute_world_stability(world_state),
        }

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": metrics,
        }

    # ══════════════════════════════════════════════════════════════════
    #  METRIC COMPUTATIONS
    # ══════════════════════════════════════════════════════════════════

    def _compute_tension(self, world_state: Dict, event_history: List) -> float:
        """Tension = f(severity of active events, recent skirmishes, stability inverse).
        
        Combines three signals:
        1. Active event severity (weighted)
        2. Recent negative events (skirmishes, rebellions)
        3. Inverse of kingdom stability
        """
        # 1. Active event severity score
        active_events = world_state.get("active_events", [])
        if active_events:
            severity_sum = sum(
                self.SEVERITY_WEIGHTS.get(e.get("severity", "Low"), 0.2)
                for e in active_events
            )
            event_tension = min(1.0, severity_sum / max(len(active_events), 1))
        else:
            event_tension = 0.0

        # 2. Recent skirmish/crisis frequency (last 10 events)
        recent = event_history[-10:] if event_history else []
        crisis_keywords = ["skirmish", "rebellion", "crisis", "conflict", "war", "attack"]
        crisis_count = sum(
            1 for e in recent
            if any(kw in e.get("description", "").lower() for kw in crisis_keywords)
        )
        crisis_tension = min(1.0, crisis_count / 5.0)

        # 3. Stability inverse
        stability = world_state.get("kingdom_status", {}).get("stability", 100)
        stability_tension = 1.0 - (stability / 100.0)

        # Weighted combination
        return round(min(1.0, (event_tension * 0.4 + crisis_tension * 0.3 + stability_tension * 0.3)), 3)

    def _compute_conflict(self, reputation: Dict) -> float:
        """Conflict = measure of negative faction relations.
        
        Scans faction_relations for hostile values (< 0) and computes 
        the proportion of hostile relationships.
        """
        faction_relations = reputation.get("faction_relations", {})
        if not faction_relations:
            return 0.0

        total_pairs = 0
        hostile_sum = 0.0
        seen_pairs = set()

        for fac_a, targets in faction_relations.items():
            for fac_b, value in targets.items():
                pair = tuple(sorted([fac_a, fac_b]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                total_pairs += 1
                if value < 0:
                    hostile_sum += abs(value) / 100.0

        if total_pairs == 0:
            return 0.0

        return round(min(1.0, hostile_sum / total_pairs), 3)

    def _compute_mystery(self, npc_memories: Dict, world_state: Dict) -> float:
        """Mystery = count of unresolved secrets, unexplained events, and active hooks.
        
        Looks for:
        1. NPC memories with high importance and 'mystery' keywords
        2. Unresolved quest hooks in DM state
        3. Active events that are not yet understood
        """
        mystery_keywords = ["secret", "mysterious", "unknown", "hidden", "whisper", "rumor", "ancient", "forbidden"]
        mystery_count = 0

        # Scan NPC memories for mystery-adjacent memories
        for npc_id, mem in npc_memories.items():
            for memory in mem.get("memories", []):
                desc = memory.get("description", "").lower()
                importance = memory.get("importance", 0)
                if importance >= 60 and any(kw in desc for kw in mystery_keywords):
                    mystery_count += 1

        # Count unresolved quest hooks from DM
        dm_data = world_state.get("dungeon_master", {})
        hooks = dm_data.get("narrative_plan", {}).get("quest_hooks", [])
        mystery_count += len(hooks)

        # Tavern rumors add mystery
        rumors = dm_data.get("rumors", {}).get("tavern_rumors", [])
        low_cred = sum(1 for r in rumors if r.get("credibility", "").lower() in ["low", "unverified"])
        mystery_count += low_cred

        # Normalize: 10+ mystery elements = full mystery
        return round(min(1.0, mystery_count / 10.0), 3)

    def _compute_quest_density(self, world_state: Dict) -> float:
        """Quest Density = ratio of active (unresolved) quests to total quests.
        
        Higher density = more things happening, more overwhelmed.
        """
        completed = len(world_state.get("completed_quests", []))
        dm_data = world_state.get("dungeon_master", {})
        active = len(dm_data.get("generated_quests", []))

        total = completed + active
        if total == 0:
            return 0.0

        return round(min(1.0, active / max(total, 1)), 3)

    def _compute_event_frequency(self, event_history: List) -> float:
        """Event Frequency = rate of events over the last 20 ticks.
        
        Higher frequency means more is happening in the world.
        """
        if not event_history:
            return 0.0

        # Count significant events (not just daily ticks)
        significant_types = ["WeeklyTick", "QuestOutcome", "PlayerInteraction", "DungeonMasterTick"]
        recent = event_history[-20:]
        significant = sum(
            1 for e in recent
            if e.get("type", "") in significant_types
        )

        # Normalize: 10+ significant events in last 20 = full frequency
        return round(min(1.0, significant / 10.0), 3)

    def _compute_faction_pressure(self, reputation: Dict) -> float:
        """Faction Pressure = average absolute tension in faction relations.
        
        High absolute values (positive or negative) indicate political pressure.
        """
        faction_relations = reputation.get("faction_relations", {})
        if not faction_relations:
            return 0.0

        values = []
        seen_pairs = set()
        for fac_a, targets in faction_relations.items():
            for fac_b, value in targets.items():
                pair = tuple(sorted([fac_a, fac_b]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                values.append(abs(value))

        if not values:
            return 0.0

        avg_pressure = sum(values) / len(values)
        return round(min(1.0, avg_pressure / 100.0), 3)

    def _compute_world_stability(self, world_state: Dict) -> float:
        """World Stability = normalized kingdom stability index.
        
        Direct read from kingdom_status.stability (0-100 → 0.0-1.0).
        """
        stability = world_state.get("kingdom_status", {}).get("stability", 100)
        return round(stability / 100.0, 3)
