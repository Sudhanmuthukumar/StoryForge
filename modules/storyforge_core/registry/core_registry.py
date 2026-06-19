"""
core_registry.py — Maintains a canonical manifest of StoryForge's architecture.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase

class CoreRegistry:
    """Central registry tracking modules, schemas, databases, and exports."""
    
    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self._initialize_registry()

    def _initialize_registry(self) -> None:
        """Create the default registry if it doesn't exist."""
        registry = self.db.read_db("core_registry.json")
        if not registry:
            registry = {
                "modules": [
                    "dataset_lab", "knowledge_engine", "research_lab", "writer",
                    "game_narrative", "unreal_export", "world_simulation",
                    "dungeon_master", "campaign_director", "narrative_learning",
                    "storyforge_core", "evaluation", "packaging", "training",
                    "creator_suite"
                ],
                "services": [
                    "SimulationEngine", "DungeonMasterService", "CampaignDirectorService",
                    "AdaptiveDirector", "LearningEngine", "EventBus", "TelemetryService",
                    "CoreRegistry", "KnowledgeEngine", "ResearchLabService",
                    "StoryArchitect", "CharacterForge", "LoreBuilder", "QuestGenerator",
                    "NarrativeAnalyzer"
                ],
                "databases": [
                    "npc_memory.json", "world_state.json", "reputation.json",
                    "event_history.json", "campaign_health.json", "campaign_learning.json",
                    "strategy_scores.json", "telemetry.json", "core_registry.json"
                ],
                "exports": [
                    "exports/unreal/alpha_world/npcs",
                    "exports/unreal/alpha_world/quests",
                    "exports/unreal/alpha_world/dialogue",
                    "exports/unreal/alpha_world/lore"
                ]
            }
            self.db.write_db("core_registry.json", registry)

    def get_registry(self) -> Dict[str, Any]:
        """Retrieve the current registry manifest."""
        return self.db.read_db("core_registry.json")
