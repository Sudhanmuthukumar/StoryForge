"""
telemetry_service.py — Subscribes to the Event Bus and maintains telemetry metrics.
"""

from typing import Dict, Any, Optional
from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.storyforge_core.events.event_bus import EventBus

class TelemetryService:
    """Centralized metrics collection service."""

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self.bus = EventBus()
        self._initialize_telemetry()
        self._register_listeners()

    def _initialize_telemetry(self) -> None:
        telemetry = self.db.read_db("telemetry.json")
        if not telemetry:
            telemetry = {
                "simulation": {
                    "total_quests_completed": 0,
                    "total_world_events": 0,
                    "reputation_changes": 0
                },
                "health_history": [],
                "learning_updates": 0
            }
            self.db.write_db("telemetry.json", telemetry)

    def _register_listeners(self) -> None:
        self.bus.subscribe("QuestCompleted", self._handle_quest_completed)
        self.bus.subscribe("WorldEventCreated", self._handle_world_event)
        self.bus.subscribe("ReputationChanged", self._handle_reputation_changed)
        self.bus.subscribe("CampaignHealthChanged", self._handle_health_changed)
        self.bus.subscribe("StrategyLearned", self._handle_strategy_learned)

    def _handle_quest_completed(self, event: Dict[str, Any]) -> None:
        t = self.db.read_db("telemetry.json") or {}
        t.setdefault("simulation", {}).setdefault("total_quests_completed", 0)
        t["simulation"]["total_quests_completed"] += 1
        self.db.write_db("telemetry.json", t)

    def _handle_world_event(self, event: Dict[str, Any]) -> None:
        t = self.db.read_db("telemetry.json") or {}
        t.setdefault("simulation", {}).setdefault("total_world_events", 0)
        t["simulation"]["total_world_events"] += 1
        self.db.write_db("telemetry.json", t)

    def _handle_reputation_changed(self, event: Dict[str, Any]) -> None:
        t = self.db.read_db("telemetry.json") or {}
        t.setdefault("simulation", {}).setdefault("reputation_changes", 0)
        t["simulation"]["reputation_changes"] += 1
        self.db.write_db("telemetry.json", t)

    def _handle_health_changed(self, event: Dict[str, Any]) -> None:
        t = self.db.read_db("telemetry.json") or {}
        t.setdefault("health_history", [])
        t["health_history"].append(event["payload"])
        if len(t["health_history"]) > 100:
            t["health_history"] = t["health_history"][-100:]
        self.db.write_db("telemetry.json", t)

    def _handle_strategy_learned(self, event: Dict[str, Any]) -> None:
        t = self.db.read_db("telemetry.json") or {}
        t.setdefault("learning_updates", 0)
        t["learning_updates"] += 1
        self.db.write_db("telemetry.json", t)
