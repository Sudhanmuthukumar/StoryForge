"""
workspace.py — The main tabbed workspace for StoryForge AI.

Replaces the StoryEditor as the central right-side panel. Contains:
  1. Welcome Screen (when no story is open)
  2. Tabbed Workspace (Story, Memory, Analysis, Chat)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QStackedWidget, QTabWidget, QVBoxLayout, QWidget, QLabel
from PySide6.QtGui import QTextCursor

from models.workspace_data import WorkspaceData
from ui.story_editor import StoryEditor
from ui.memory_view import MemoryView
from ui.analysis_view import AnalysisView
from ui.chat_view import ChatView
from ui.preferences_view import PreferencesView
from modules.training.views.training_mode_view import TrainingModeView
from ui.universe_view import UniverseView
from ui.graph_view import GraphView
from ui.context_inspector import ContextInspector
from modules.dataset_lab.views.dataset_lab_view import DatasetLabView
from modules.evaluation.views.evaluation_view import EvaluationView
from modules.packaging.views.model_manager_view import ModelManagerView
from modules.knowledge_engine.views.knowledge_explorer_view import KnowledgeExplorerView
from modules.research_lab.views.research_dashboard_view import ResearchDashboardView
from modules.writer.views.writer_workspace_view import WriterWorkspaceView
from modules.interactive_narrative.views.interactive_narrative_view import InteractiveNarrativeView
from modules.world_simulation.views.world_simulation_view import WorldSimulationView
from modules.dungeon_master.views.dungeon_master_view import DungeonMasterView
from modules.campaign_director.views.campaign_director_view import CampaignDirectorView


class Workspace(QWidget):
    """
    Main workspace container owning the 4 tabs.
    
    Signals
    -------
    save_requested(str, str)
        Forwarded from StoryEditor.
    chat_message_sent(str, str)
        Forwarded from ChatView.
    """

    save_requested = Signal(str, str)
    chat_message_sent = Signal(str, str)
    ai_edit_requested = Signal(str, str, QTextCursor)
    message_action_requested = Signal(str, str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceArea")
        self._build_ui()
        self._connect_signals()
        
        self.clear_workspace()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # ── Page 0: Welcome ───────────────────────────────────────────
        self._welcome = QWidget()
        self._welcome.setObjectName("editorArea")
        wl = QVBoxLayout(self._welcome)
        wl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📝")
        icon_label.setObjectName("welcomeIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Welcome to StoryForge AI")
        title_label.setObjectName("welcomeTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_label = QLabel("Create or open a story to begin writing")
        sub_label.setObjectName("welcomeSubtitle")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        wl.addWidget(icon_label)
        wl.addSpacing(8)
        wl.addWidget(title_label)
        wl.addSpacing(4)
        wl.addWidget(sub_label)
        
        self._stack.addWidget(self._welcome)

        # ── Page 1: Workspace Tabs ────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("workspaceTabs")
        
        self._story_editor = StoryEditor()
        self._memory_view = MemoryView()
        self._analysis_view = AnalysisView()
        self._chat_view = ChatView()
        self._preferences_view = PreferencesView()
        self._training_view = TrainingModeView()
        self._universe_view = UniverseView()
        self._graph_view = GraphView()
        self._context_inspector = ContextInspector()
        self._dataset_lab_view = DatasetLabView()
        self._evaluation_view = EvaluationView()
        self._model_manager_view = ModelManagerView()
        self._knowledge_engine_view = KnowledgeExplorerView()
        self._research_lab_view = ResearchDashboardView()
        self._writer_workspace_view = WriterWorkspaceView()
        self._interactive_narrative_view = InteractiveNarrativeView()
        self._world_simulation_view = WorldSimulationView()
        self._dungeon_master_view = DungeonMasterView()
        self._campaign_director_view = CampaignDirectorView()

        self._tabs.addTab(self._writer_workspace_view, "✒️ Writer Workspace")
        self._tabs.addTab(self._story_editor, "📝 Story")
        self._tabs.addTab(self._memory_view, "🧠 Memory")
        self._tabs.addTab(self._analysis_view, "📊 Analysis")
        self._tabs.addTab(self._chat_view, "💬 Chat")
        self._tabs.addTab(self._universe_view, "🌌 Universes")
        self._tabs.addTab(self._graph_view, "🕸️ Universe Graph")
        self._tabs.addTab(self._dataset_lab_view, "🔬 Dataset Lab")
        self._tabs.addTab(self._training_view, "📚 Training Mode")
        self._tabs.addTab(self._evaluation_view, "⚖️ Model Evaluation")
        self._tabs.addTab(self._model_manager_view, "📦 Models")
        self._tabs.addTab(self._knowledge_engine_view, "💡 Knowledge Engine")
        self._tabs.addTab(self._research_lab_view, "🔬 Research Lab")
        self._tabs.addTab(self._preferences_view, "👤 Preferences")
        self._tabs.addTab(self._context_inspector, "🔍 Context Inspector")
        self._tabs.addTab(self._interactive_narrative_view, "🎮 Interactive Narrative")
        self._tabs.addTab(self._world_simulation_view, "🌍 World Simulation")
        self._tabs.addTab(self._dungeon_master_view, "🏰 Dungeon Master")
        self._tabs.addTab(self._campaign_director_view, "🎬 Campaign Director")
        
        self._stack.addWidget(self._tabs)

    def _connect_signals(self) -> None:
        self._story_editor.save_requested.connect(self.save_requested.emit)
        self._story_editor.ai_edit_requested.connect(self.ai_edit_requested.emit)
        self._chat_view.message_sent.connect(self.chat_message_sent.emit)
        self._chat_view.message_action_requested.connect(self.message_action_requested.emit)

    def load_workspace(self, data: WorkspaceData) -> None:
        """Populate all tabs with data and switch to the tab view."""
        self._story_editor.load_content(
            title=data.story.title,
            genre=data.story.genre,
            story_id=data.story.id,
            content=data.content,
            created_at=data.story.created_at,
        )
        self._memory_view.load_data(data.memory)
        self._analysis_view.load_data(data.analysis, data.consistency)
        self._chat_view.load_history(data.story.id, data.chat_history)
        self._preferences_view.load_data(data.user_profile)
        self._training_view.load_data(data.training_profile)
        self._interactive_narrative_view.refresh_patterns()
        
        # Make Chat (index 3) the default tab
        self._stack.setCurrentIndex(1)
        self._tabs.setCurrentIndex(3)

    def clear_workspace(self) -> None:
        """Clear all tabs and return to the welcome screen."""
        self._story_editor.clear()
        self._memory_view.clear()
        self._analysis_view.clear()
        self._chat_view.clear()
        self._preferences_view.clear()
        self._training_view.clear()
        self._universe_view.clear()
        self._graph_view.clear()
        self._context_inspector.clear()
        self._dataset_lab_view.clear()
        self._evaluation_view.clear()
        self._model_manager_view.clear()
        self._knowledge_engine_view.clear()
        self._research_lab_view.clear()
        self._writer_workspace_view.clear()
        self._interactive_narrative_view.clear()
        self._world_simulation_view.clear()
        self._dungeon_master_view.clear()
        self._campaign_director_view.clear()
        self._stack.setCurrentIndex(0)
        
    def trigger_save(self) -> None:
        """Simulate a click on the save button (for Ctrl+S shortcut)."""
        self._story_editor._btn_save.click()

    @property
    def current_story_id(self) -> str | None:
        return self._story_editor.current_story_id

    @property
    def is_modified(self) -> bool:
        return self._story_editor.is_modified
