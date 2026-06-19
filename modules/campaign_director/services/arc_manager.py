"""
arc_manager.py — Tracks and advances hierarchies of story arcs.

Manages four tiers of narrative arcs:
1. Main Campaign: Overall story progression (acts)
2. Regional Arcs: Per-region story developments
3. Faction Arcs: Political/alliance developments
4. Character Arcs: NPC relationship and growth milestones

This module reads world state and computes arc progression without 
modifying the simulation directly.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class ArcManager:
    """Tracks story arc progression across campaigns, regions, factions, and characters."""

    # Default campaign act structure
    DEFAULT_ACTS = [
        {"act_id": "act_01", "name": "The Awakening", "status": "completed", "progress": 1.0, "major_events": []},
        {"act_id": "act_02", "name": "Rising Threats", "status": "active", "progress": 0.0, "major_events": []},
        {"act_id": "act_03", "name": "The Convergence", "status": "pending", "progress": 0.0, "major_events": []},
        {"act_id": "act_04", "name": "The Dark Hour", "status": "pending", "progress": 0.0, "major_events": []},
        {"act_id": "act_05", "name": "Resolution", "status": "pending", "progress": 0.0, "major_events": []},
    ]

    # Thresholds that determine arc phase transitions
    ARC_STATE_THRESHOLDS = {
        "dormant": {"min_events": 0, "max_events": 2},
        "rising": {"min_events": 3, "max_events": 6},
        "peak": {"min_events": 7, "max_events": 10},
        "declining": {"min_events": 11, "max_events": 15},
        "resolved": {"min_events": 16, "max_events": 999},
    }

    CHARACTER_ARC_PHASES = ["introduction", "development", "crisis", "resolution"]

    def __init__(self):
        self.arc_state = {
            "campaign_id": "campaign_01",
            "current_act": "act_02",
            "acts": list(self.DEFAULT_ACTS),
            "faction_arcs": [],
            "character_arcs": [],
        }

    def analyze_arcs(
        self,
        world_state: Dict[str, Any],
        event_history: List[Dict[str, Any]],
        npc_memories: Dict[str, Any],
        reputation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute current arc progression from simulation state.
        
        Returns:
            Full arc state dictionary with main campaign, regional, faction, and character arcs.
        """
        # 1. Update main campaign progression
        self._update_main_campaign(world_state, event_history)

        # 2. Update regional arcs
        regional_arcs = self._compute_regional_arcs(world_state, event_history)

        # 3. Update faction arcs
        self._update_faction_arcs(event_history, reputation)

        # 4. Update character arcs
        self._update_character_arcs(npc_memories)

        return {
            "campaign_id": self.arc_state["campaign_id"],
            "current_act": self.arc_state["current_act"],
            "acts": self.arc_state["acts"],
            "regional_arcs": regional_arcs,
            "faction_arcs": self.arc_state["faction_arcs"],
            "character_arcs": self.arc_state["character_arcs"],
        }

    def _update_main_campaign(self, world_state: Dict, event_history: List) -> None:
        """Update the main campaign act progression based on events and quest completions."""
        campaign_progress = world_state.get("campaign_progress", {})
        active_arc_id = campaign_progress.get("active_arc_id", "act_02")
        completed_arcs = campaign_progress.get("completed_arcs", [])

        self.arc_state["current_act"] = active_arc_id

        # Update act statuses
        for act in self.arc_state["acts"]:
            if act["act_id"] in completed_arcs:
                act["status"] = "completed"
                act["progress"] = 1.0
            elif act["act_id"] == active_arc_id:
                act["status"] = "active"
                # Estimate progress from completed quests and events in this act
                act["progress"] = self._estimate_act_progress(
                    act["act_id"], world_state, event_history
                )
            else:
                if act["status"] != "completed":
                    act["status"] = "pending"
                    act["progress"] = 0.0

    def _estimate_act_progress(self, act_id: str, world_state: Dict, event_history: List) -> float:
        """Estimate progress through an act based on quests completed and major events."""
        completed_quests = len(world_state.get("completed_quests", []))
        dm_ticks = sum(1 for e in event_history if e.get("type") == "DungeonMasterTick")
        weekly_ticks = sum(1 for e in event_history if e.get("type") == "WeeklyTick")

        # Simple heuristic: each completed quest + DM tick + weekly tick adds progress
        total_activity = completed_quests * 0.15 + dm_ticks * 0.1 + weekly_ticks * 0.05
        return round(min(1.0, total_activity), 3)

    def _compute_regional_arcs(self, world_state: Dict, event_history: List) -> List[Dict[str, Any]]:
        """Compute regional arc progression based on active events and regional conditions."""
        active_regions = world_state.get("campaign_progress", {}).get("active_regions", [])

        regional_arcs = []
        for region in active_regions:
            # Count events affecting this region
            region_events = sum(
                1 for e in event_history
                if region.lower() in " ".join(e.get("affected_entities", [])).lower()
                or region.lower() in e.get("description", "").lower()
            )

            # Active events in this region
            active_in_region = sum(
                1 for e in world_state.get("active_events", [])
                if e.get("region", "").lower() == region.lower()
            )

            # Compute progress
            progress = min(1.0, region_events * 0.1 + active_in_region * 0.15)

            # Determine act based on progress
            if progress >= 0.8:
                act = "Climax"
            elif progress >= 0.5:
                act = "Rising Conflict"
            elif progress >= 0.2:
                act = "Exploration"
            else:
                act = "Introduction"

            regional_arcs.append({
                "region": region,
                "act": act,
                "progress": round(progress, 3),
            })

        return regional_arcs

    def _update_faction_arcs(self, event_history: List, reputation: Dict) -> None:
        """Update faction arc states based on event involvement and reputation trends."""
        faction_relations = reputation.get("faction_relations", {})
        all_factions = set(faction_relations.keys())

        faction_arcs = []
        for faction in all_factions:
            # Count events involving this faction
            faction_events = [
                e for e in event_history
                if faction in e.get("affected_entities", [])
                or faction.lower() in e.get("description", "").lower()
            ]

            event_count = len(faction_events)

            # Determine arc state
            if event_count == 0:
                arc_state = "dormant"
            elif event_count <= 3:
                arc_state = "rising"
            elif event_count <= 7:
                arc_state = "peak"
            elif event_count <= 12:
                arc_state = "declining"
            else:
                arc_state = "resolved"

            # Extract key events
            key_events = [
                e.get("description", "")[:80]
                for e in faction_events[-3:]
            ]

            # Compute progress
            progress = min(1.0, event_count / 10.0)

            faction_arcs.append({
                "faction": faction,
                "arc_state": arc_state,
                "key_events": key_events,
                "progress": round(progress, 3),
            })

        self.arc_state["faction_arcs"] = faction_arcs

    def _update_character_arcs(self, npc_memories: Dict) -> None:
        """Update character arc phases based on NPC memory and interaction depth."""
        character_arcs = []

        for npc_id, mem in npc_memories.items():
            memory_count = len(mem.get("memories", []))
            interaction_count = len(mem.get("interactions", []))
            quest_count = len(mem.get("quest_outcomes", {}))
            trust = mem.get("relationships", {}).get("player", {}).get("trust", 50)

            # Total engagement score
            engagement = memory_count + interaction_count * 2 + quest_count * 3

            # Determine arc phase
            if engagement <= 1:
                phase = "introduction"
            elif engagement <= 5:
                phase = "development"
            elif engagement <= 10:
                phase = "crisis"
            else:
                phase = "resolution"

            # Compute progress within phase
            phase_idx = self.CHARACTER_ARC_PHASES.index(phase)
            progress = min(1.0, (phase_idx + min(1.0, engagement / 15.0)) / len(self.CHARACTER_ARC_PHASES))

            # Milestones
            milestones = []
            if quest_count > 0:
                milestones.append(f"Completed {quest_count} quest(s)")
            if interaction_count > 0:
                milestones.append(f"{interaction_count} dialogue interaction(s)")
            if trust >= 70:
                milestones.append("Trusted ally")
            elif trust <= 30:
                milestones.append("Strained relationship")

            character_arcs.append({
                "npc_id": npc_id,
                "name": mem.get("name", "Unknown"),
                "arc_phase": phase,
                "progress": round(progress, 3),
                "milestones": milestones,
            })

        # Sort by progress descending (most developed characters first)
        character_arcs.sort(key=lambda x: x["progress"], reverse=True)
        self.arc_state["character_arcs"] = character_arcs

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load previously saved arc state."""
        if state:
            self.arc_state.update(state)

    def get_arc_summary(self) -> Dict[str, Any]:
        """Get a compact summary of arc progression."""
        active_act = None
        for act in self.arc_state["acts"]:
            if act["status"] == "active":
                active_act = act
                break

        return {
            "campaign_id": self.arc_state["campaign_id"],
            "current_act": self.arc_state["current_act"],
            "active_act_name": active_act["name"] if active_act else "Unknown",
            "active_act_progress": active_act["progress"] if active_act else 0.0,
            "total_acts": len(self.arc_state["acts"]),
            "completed_acts": sum(1 for a in self.arc_state["acts"] if a["status"] == "completed"),
            "total_faction_arcs": len(self.arc_state["faction_arcs"]),
            "total_character_arcs": len(self.arc_state["character_arcs"]),
        }
