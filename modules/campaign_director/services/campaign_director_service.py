"""
campaign_director_service.py — Orchestrates the Campaign Director tick loop.

The Campaign Director sits ABOVE the Dungeon Master layer and manages:
1. Narrative Health Analysis → Compute metrics
2. Pacing Management → Determine dramatic arc state and issue directives
3. Diversity Management → Check for repetition and suggest focus areas
4. Arc Management → Track story arc progression

Implements three modes:
- Observation: Computes metrics without influencing simulation
- Recommendation: Provides suggestions to the DM
- Control: Actively constrains DM behavior (future)

Current implementation: Observation + Recommendation modes.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.campaign_director.services.narrative_health_analyzer import NarrativeHealthAnalyzer
from modules.campaign_director.services.pacing_manager import PacingManager
from modules.campaign_director.services.diversity_manager import DiversityManager
from modules.campaign_director.services.arc_manager import ArcManager
from modules.narrative_learning.services.outcome_analyzer import OutcomeAnalyzer
from modules.narrative_learning.services.adaptive_director import AdaptiveDirector
from modules.storyforge_core.events.event_bus import EventBus
from modules.narrative_learning.services.experience_collector import ExperienceCollector
from modules.narrative_learning.services.learning_engine import LearningEngine


class CampaignDirectorService:
    """Orchestrates narrative direction: health analysis, pacing, diversity, and arc management."""

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self.health_analyzer = NarrativeHealthAnalyzer(db=self.db)
        self.pacing_manager = PacingManager()
        self.diversity_manager = DiversityManager()
        self.arc_manager = ArcManager()
        
        # Phase 15: Narrative Learning Engine
        self.outcome_analyzer = OutcomeAnalyzer(db_dir=db_dir)
        self.adaptive_director = AdaptiveDirector(db_dir=db_dir)
        self.learning_engine = self.adaptive_director.learning_engine
        self.experience_collector = self.outcome_analyzer.collector
        self.learning_enabled = True
        self.current_tick = 0

        # Director mode: observation | recommendation | control
        self.mode = "observation"

        # History of health snapshots
        self.health_history: List[Dict[str, Any]] = []

        # Active constraints applied to DM
        self.active_constraints: List[Dict[str, Any]] = []

        # Load previous state if exists
        self._load_state()

    def run_director_tick(self) -> Dict[str, Any]:
        """Execute a full Campaign Director tick.

        Order:
        1. Narrative Health Analyzer → Compute metrics
        2. Pacing Manager → Formulate pacing directives
        3. Diversity Manager → Check for narrative stagnation
        4. Arc Manager → Update arc progression
        5. Write health to campaign_health.json
        6. Compile recommendations
        7. (Mode: recommendation) → Apply recommendations as DM constraints

        Returns:
            Dictionary with all director outputs.
        """
        self.current_tick += 1

        # 0. Phase 15: Evaluate pending learning records and update strategy scores
        if self.learning_enabled:
            # We need a quick read of current state to evaluate past recommendations
            current_health = self.health_analyzer.compute_health()
            current_world = self.db.read_db("world_state.json")
            current_hist = self.db.read_db("event_history.json")
            current_mem = self.db.read_db("npc_memory.json")
            current_rep = self.db.read_db("reputation.json")
            current_div = self.diversity_manager.analyze_diversity(current_world, current_hist, current_mem, current_rep)
            
            evaluated = self.outcome_analyzer.evaluate_pending_records(
                self.current_tick, current_health, current_div
            )
            self.learning_engine.process_evaluations(evaluated)

        # 1. Compute narrative health metrics
        health = self.health_analyzer.compute_health()
        metrics = health["metrics"]

        # 2. Pacing Manager analysis
        pacing_result = self.pacing_manager.analyze_pacing(metrics)

        # 3. Diversity Manager analysis
        world_state = self.db.read_db("world_state.json")
        event_history = self.db.read_db("event_history.json")
        npc_memories = self.db.read_db("npc_memory.json")
        reputation = self.db.read_db("reputation.json")

        diversity_result = self.diversity_manager.analyze_diversity(
            world_state, event_history, npc_memories, reputation
        )

        # 4. Arc Manager analysis
        arc_result = self.arc_manager.analyze_arcs(
            world_state, event_history, npc_memories, reputation
        )

        # 5. Compile full health snapshot
        health_snapshot = {
            "timestamp": health["timestamp"],
            "metrics": metrics,
            "pacing_state": pacing_result["current_state"],
            "active_directives": pacing_result["directives"],
            "arc_progress": {
                "main_campaign": {
                    "act": arc_result["current_act"],
                    "progress": self._get_active_act_progress(arc_result),
                },
                "regional_arcs": arc_result.get("regional_arcs", []),
                "faction_arcs": [
                    {
                        "faction": fa["faction"],
                        "state": fa["arc_state"],
                        "progress": fa.get("progress", 0.0),
                    }
                    for fa in arc_result.get("faction_arcs", [])
                ],
                "character_arcs": [
                    {
                        "npc_id": ca["npc_id"],
                        "name": ca["name"],
                        "arc_phase": ca["arc_phase"],
                        "progress": ca["progress"],
                    }
                    for ca in arc_result.get("character_arcs", [])[:10]
                ],
            },
        }

        # Store in history
        self.health_history.append(health_snapshot)
        # Keep last 50 snapshots
        if len(self.health_history) > 50:
            self.health_history = self.health_history[-50:]

        # 6. Write campaign_health.json
        self._save_health(health_snapshot)

        # 7. Compile all recommendations
        raw_recommendations = []
        raw_recommendations.extend(pacing_result["directives"])
        raw_recommendations.extend(diversity_result.get("recommendations", []))
        
        # 8. Phase 15: Apply Learning (Adaptive Director)
        final_recommendations = raw_recommendations
        if self.learning_enabled and self.mode in ["recommendation", "control"]:
            final_recommendations = self.adaptive_director.refine_recommendations(raw_recommendations)
            
            # Record the interventions for future learning
            for rec in final_recommendations:
                self.experience_collector.record_intervention(
                    self.current_tick, health_snapshot, diversity_result, rec
                )

        # 9. Build constraints from recommendations (only in recommendation+ mode)
        constraints = []
        if self.mode in ["recommendation", "control"]:
            # We build constraints based on the *refined* pacing and diversity state
            constraints = self._build_constraints(pacing_result, diversity_result)
            self.active_constraints = constraints

        # 10. Save director state
        self._save_state()

        return {
            "health": health_snapshot,
            "pacing": pacing_result,
            "diversity": diversity_result,
            "arcs": arc_result,
            "raw_recommendations": raw_recommendations,
            "recommendations": final_recommendations,
            "constraints": constraints,
            "mode": self.mode,
        }

    def get_health_history(self) -> List[Dict[str, Any]]:
        """Return the stored health history snapshots."""
        return self.health_history

    def get_active_constraints(self) -> List[Dict[str, Any]]:
        """Return currently active DM constraints."""
        return self.active_constraints

    def set_mode(self, mode: str) -> None:
        """Set the director mode: observation, recommendation, or control."""
        valid_modes = ["observation", "recommendation", "control"]
        if mode in valid_modes:
            self.mode = mode
            self._save_state()

    def generate_report(self) -> str:
        """Generate a comprehensive campaign director report as Markdown."""
        if not self.health_history:
            return "# Campaign Director Report\n\nNo data available. Run a director tick first.\n"

        latest = self.health_history[-1]
        metrics = latest["metrics"]
        pacing_state = latest.get("pacing_state", "unknown")
        arc_progress = latest.get("arc_progress", {})
        directives = latest.get("active_directives", [])

        md = "# 🎬 Campaign Director Report\n\n"
        md += f"**Generated:** {datetime.utcnow().isoformat()}Z\n"
        md += f"**Director Mode:** {self.mode.upper()}\n"
        md += f"**Total Health Snapshots:** {len(self.health_history)}\n\n"

        # Health Metrics
        md += "## 📊 Narrative Health Metrics\n\n"
        md += "| Metric | Value | Status |\n"
        md += "| :--- | :---: | :--- |\n"
        for key, val in metrics.items():
            status = self._metric_status(key, val)
            bar = self._metric_bar(val)
            md += f"| {key.replace('_', ' ').title()} | {bar} {val:.3f} | {status} |\n"
        md += "\n"

        # Pacing
        md += "## 🎭 Pacing State\n\n"
        md += f"**Current Phase:** {pacing_state.replace('_', ' ').title()}\n\n"

        # Directives
        if directives:
            md += "## 📋 Active Directives\n\n"
            for d in directives:
                priority = d.get("priority", "low")
                icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(priority, "⚪")
                md += f"- {icon} **[{priority.upper()}]** {d.get('description', '')}\n"
            md += "\n"

        # Arc Progression
        md += "## 📈 Story Arc Progression\n\n"
        main = arc_progress.get("main_campaign", {})
        md += f"**Main Campaign Act:** {main.get('act', 'Unknown')} (Progress: {main.get('progress', 0):.1%})\n\n"

        # Regional Arcs
        regional = arc_progress.get("regional_arcs", [])
        if regional:
            md += "### Regional Arcs\n"
            md += "| Region | Act | Progress |\n"
            md += "| :--- | :--- | :---: |\n"
            for r in regional:
                md += f"| {r['region']} | {r['act']} | {r['progress']:.1%} |\n"
            md += "\n"

        # Faction Arcs
        faction = arc_progress.get("faction_arcs", [])
        if faction:
            md += "### Faction Arcs\n"
            md += "| Faction | State | Progress |\n"
            md += "| :--- | :--- | :---: |\n"
            for f in faction:
                md += f"| {f['faction']} | {f['state'].title()} | {f.get('progress', 0):.1%} |\n"
            md += "\n"

        # Character Arcs (top 5)
        chars = arc_progress.get("character_arcs", [])
        if chars:
            md += "### Character Arcs (Top 5)\n"
            md += "| NPC | Phase | Progress |\n"
            md += "| :--- | :--- | :---: |\n"
            for c in chars[:5]:
                md += f"| {c['name']} | {c['arc_phase'].title()} | {c['progress']:.1%} |\n"
            md += "\n"

        # Constraints
        if self.active_constraints:
            md += "## 🔒 Active DM Constraints\n\n"
            for c in self.active_constraints:
                md += f"- **{c.get('type', 'unknown')}**: {c.get('description', '')}\n"
            md += "\n"

        # Write to disk
        out_path = Path("campaign_director_report.md")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
        except Exception:
            pass

        return md

    # ══════════════════════════════════════════════════════════════════
    #  PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _get_active_act_progress(self, arc_result: Dict) -> float:
        """Get progress of the currently active act."""
        for act in arc_result.get("acts", []):
            if act.get("status") == "active":
                return act.get("progress", 0.0)
        return 0.0

    def _build_constraints(self, pacing_result: Dict, diversity_result: Dict) -> List[Dict[str, Any]]:
        """Build DM constraints from pacing and diversity analysis."""
        constraints = []

        pacing_state = pacing_result.get("current_state", "rising_action")

        # Pacing constraints
        if pacing_state == "cooldown":
            constraints.append({
                "constraint_id": "cooldown_block",
                "type": "event_spawn_block",
                "description": "Cooldown active: block all crisis event spawns. Allow only peaceful events.",
                "duration_ticks": self.pacing_manager.MIN_TICKS_IN_STATE.get("cooldown", 3),
            })

        elif pacing_state == "climax":
            constraints.append({
                "constraint_id": "climax_focus",
                "type": "event_spawn_block",
                "description": "Climax active: block new event spawns. Let existing events resolve.",
                "duration_ticks": self.pacing_manager.MIN_TICKS_IN_STATE.get("climax", 2),
            })

        # Diversity constraints
        for rec in diversity_result.get("recommendations", []):
            if rec.get("priority") in ["high", "critical"]:
                if "neglected" in rec.get("description", "").lower() or "faction" in rec.get("type", "").lower():
                    constraints.append({
                        "constraint_id": f"div_{rec.get('type', 'focus')}",
                        "type": "faction_focus",
                        "description": rec["description"],
                        "duration_ticks": 3,
                    })
                elif "quest" in rec.get("description", "").lower():
                    constraints.append({
                        "constraint_id": f"div_quest_{rec.get('type', 'pref')}",
                        "type": "quest_type_preference",
                        "description": rec["description"],
                        "duration_ticks": 3,
                    })

        return constraints

    def _metric_status(self, key: str, value: float) -> str:
        """Return a human-readable status for a metric value."""
        if key == "world_stability":
            if value >= 0.7:
                return "✅ Stable"
            elif value >= 0.4:
                return "⚠️ Unstable"
            else:
                return "🔴 Critical"
        elif key in ["tension", "conflict", "faction_pressure"]:
            if value >= 0.7:
                return "🔴 High"
            elif value >= 0.4:
                return "⚠️ Moderate"
            else:
                return "✅ Low"
        elif key in ["mystery", "quest_density", "event_frequency"]:
            if value >= 0.7:
                return "📈 High"
            elif value >= 0.3:
                return "📊 Moderate"
            else:
                return "📉 Low"
        return "—"

    def _metric_bar(self, value: float) -> str:
        """Create a text-based progress bar for a metric."""
        filled = int(value * 10)
        return "█" * filled + "░" * (10 - filled)

    def _save_health(self, snapshot: Dict[str, Any]) -> None:
        """Write the health snapshot to campaign_health.json."""
        self.db.write_db("campaign_health.json", self.health_history)
        EventBus().publish("CampaignHealthChanged", snapshot)
        health_path = self.db.db_dir / "campaign_health.json"
        try:
            with open(health_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=4)
        except Exception as e:
            print(f"Error saving campaign health: {e}")

    def _save_state(self) -> None:
        """Persist director state to disk."""
        state_path = self.db.db_dir / "campaign_director_state.json"
        state = {
            "mode": self.mode,
            "pacing_state": self.pacing_manager.current_state,
            "pacing_ticks": self.pacing_manager.ticks_in_state,
            "health_history_count": len(self.health_history),
            "active_constraints": self.active_constraints,
        }
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except Exception:
            pass

    def _load_state(self) -> None:
        """Load persisted director state from disk."""
        state_path = self.db.db_dir / "campaign_director_state.json"
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.mode = state.get("mode", "observation")
                pacing = state.get("pacing_state", "rising_action")
                if pacing in self.pacing_manager.PACING_TRANSITIONS:
                    self.pacing_manager.current_state = pacing
                    self.pacing_manager.ticks_in_state = state.get("pacing_ticks", 0)
                self.active_constraints = state.get("active_constraints", [])
            except Exception:
                pass
