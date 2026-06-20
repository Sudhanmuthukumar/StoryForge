"""
report_generator.py — Generates the canonical storyforge_evolution_report.md
"""

from typing import Optional
from datetime import datetime
from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.storyforge_core.registry.core_registry import CoreRegistry

class EvolutionReportGenerator:
    """Generates the Phase 15.5 architectural history and telemetry report."""

    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        self.registry = CoreRegistry(db_dir=db_dir)

    def generate_report(self, output_path: str = "storyforge_evolution_report.md") -> str:
        telemetry = self.db.read_db("telemetry.json") or {}
        reg_data = self.registry.get_registry()
        
        md = f"# StoryForge Architecture Evolution Report\n\n"
        md += f"**Generated:** {datetime.utcnow().isoformat()}Z\n"
        md += f"**Phase:** 15.5 - Architecture Consolidation\n\n"
        
        md += "## 1. System Architecture\n\n"
        md += "StoryForge has evolved into a unified, event-driven platform consisting of Generative Modules, Simulation Engines, and a centralized Core.\n\n"
        
        md += "### Core Registry Manifest\n"
        md += f"- **Total Modules:** {len(reg_data.get('modules', []))}\n"
        md += f"- **Core Services:** {len(reg_data.get('services', []))}\n"
        md += f"- **JSON Databases:** {len(reg_data.get('databases', []))}\n"
        md += f"- **Export Layer Paths:** {len(reg_data.get('exports', []))}\n\n"
        
        md += "## 2. Telemetry Statistics\n\n"
        sim_stats = telemetry.get("simulation", {})
        md += f"- **Quests Completed/Generated:** {sim_stats.get('total_quests_completed', 0)}\n"
        md += f"- **World Events Generated:** {sim_stats.get('total_world_events', 0)}\n"
        md += f"- **Reputation Shifts Processed:** {sim_stats.get('reputation_changes', 0)}\n"
        md += f"- **Narrative Strategy Learning Updates:** {telemetry.get('learning_updates', 0)}\n\n"
        
        md += "## 3. Phase Timeline\n\n"
        md += "- **Phase 1-3:** LLaMA Fine-Tuning & Prompt Engineering\n"
        md += "- **Phase 4-5:** Content Generation Pipelines (Quests, Dialogues, NPCs)\n"
        md += "- **Phase 6-8:** Validation & Packaging\n"
        md += "- **Phase 9-11:** Unreal Engine 5 Integration\n"
        md += "- **Phase 12:** World Simulation Engine (Persistent State)\n"
        md += "- **Phase 13:** AI Dungeon Master (Event Consequence Logic)\n"
        md += "- **Phase 14:** Campaign Director (Pacing & Diversity Analysis)\n"
        md += "- **Phase 15:** Narrative Learning Engine (Self-correcting Strategies)\n"
        md += "- **Phase 15.5:** StoryForge Core Consolidation (Event Bus & Registry)\n\n"
        
        md += "## 4. Event Bus Integration\n\n"
        md += "The following events are now actively flowing through the `EventBus` without disrupting the validated direct service integrations:\n"
        md += "- `QuestCompleted` (from DungeonMaster)\n"
        md += "- `WorldEventCreated` (from DungeonMaster)\n"
        md += "- `ReputationChanged` (from SimulationEngine)\n"
        md += "- `CampaignHealthChanged` (from CampaignDirector)\n"
        md += "- `StrategyLearned` (from NarrativeLearningEngine)\n\n"
        
        md += "## 5. Next Steps\n\n"
        md += "StoryForge is now fully consolidated. The platform is ready for expanding into autonomous world creation and dynamic 3D asset generation.\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
            
        return md
