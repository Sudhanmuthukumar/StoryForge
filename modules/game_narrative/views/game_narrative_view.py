from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from modules.game_narrative.services.game_narrative_generator import GameNarrativeGenerator
from modules.unreal_export.services.unreal_exporter import UnrealExporter

from modules.game_narrative.views.campaign_planner_view import CampaignPlannerView
from modules.game_narrative.views.dialogue_tree_view import DialogueTreeView
from modules.game_narrative.views.quest_forge_view import QuestForgeView
from modules.game_narrative.views.npc_studio_view import NPCStudioView
from modules.game_narrative.views.lore_engine_view import LoreEngineView

class GameNarrativeView(QWidget):
    """Master View for the Game Narrative Engine (Phase 10 & 11)."""
    
    def __init__(self):
        super().__init__()
        self.generator = GameNarrativeGenerator()
        self.exporter = UnrealExporter()
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Sub Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("gameNarrativeTabs")
        
        self.campaign_planner = CampaignPlannerView(self.generator, self.exporter)
        self.dialogue_tree = DialogueTreeView(self.generator, self.exporter)
        self.quest_forge = QuestForgeView(self.generator, self.exporter)
        self.npc_studio = NPCStudioView(self.generator, self.exporter)
        self.lore_engine = LoreEngineView(self.generator, self.exporter)
        
        self.tabs.addTab(self.campaign_planner, "🗺️ Campaign Planner")
        self.tabs.addTab(self.dialogue_tree, "💬 Dialogue Tree Builder")
        self.tabs.addTab(self.quest_forge, "⚔️ Quest Forge")
        self.tabs.addTab(self.npc_studio, "👤 NPC Studio")
        self.tabs.addTab(self.lore_engine, "🌍 Lore Engine")
        
        layout.addWidget(self.tabs)
        
    def clear(self):
        """Reset all child views cleanly."""
        self.campaign_planner.clear()
        self.dialogue_tree.clear()
        self.quest_forge.clear()
        self.npc_studio.clear()
        self.lore_engine.clear()
        
    def refresh_patterns(self):
        """Reload pacing, dialogue, character, and conflict patterns across all sub-views."""
        self.campaign_planner.refresh_patterns()
        self.dialogue_tree.refresh_patterns()
        self.quest_forge.refresh_patterns()
        self.npc_studio.refresh_patterns()
        self.lore_engine.refresh_patterns()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        self.refresh_patterns()

