"""
sidebar.py — Left sidebar widget for StoryForge AI.

Displays the story list and action buttons (Create / Open / Delete).
Emits signals — never performs filesystem operations directly.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.story import Story


class Sidebar(QWidget):
    """
    Left-hand panel showing all available stories and action buttons.

    Signals
    -------
    create_requested()
        Emitted when the user clicks "Create Story".
    open_requested(str)
        Emitted with the story ID when "Open Story" is clicked.
    delete_requested(str)
        Emitted with the story ID when "Delete Story" is clicked.
    story_selection_changed(str)
        Emitted with the story ID whenever the list selection changes.
    """

    create_requested = Signal()
    open_requested = Signal(str)
    delete_requested = Signal(str)
    story_selection_changed = Signal(str)
    import_training_requested = Signal()
    create_universe_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(260)
        self._build_ui()
        self._connect_signals()

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Assemble labels, list widget, and buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)

        # Title
        title = QLabel("StoryForge AI")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Your stories")
        subtitle.setObjectName("sidebarSubtitle")
        layout.addWidget(subtitle)

        # Story list
        self._story_list = QListWidget()
        self._story_list.setObjectName("storyList")
        self._story_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._story_list, stretch=1)

        # ── Action buttons ────────────────────────────────────────────
        self._btn_create = QPushButton("＋  Create Story")
        self._btn_create.setObjectName("btnCreate")
        self._btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_create.setToolTip("Create a new story project")

        self._btn_import_training = QPushButton("📚 Import Training Doc")
        self._btn_import_training.setObjectName("btnImportTraining")
        self._btn_import_training.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self._btn_create)
        layout.addWidget(self._btn_import_training)

    # ── Signal wiring ─────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Wire internal widget signals to public sidebar signals."""
        self._btn_create.clicked.connect(self.create_requested.emit)

        self._story_list.currentItemChanged.connect(self._on_selection_changed)
        # Single-click opens the story
        self._story_list.itemClicked.connect(self._emit_open)
        
        # Context menu
        self._story_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._story_list.customContextMenuRequested.connect(self._show_context_menu)
        
        self._btn_import_training.clicked.connect(self.import_training_requested.emit)

    # ── Slot helpers ──────────────────────────────────────────────────

    def _emit_open(self) -> None:
        """Emit open_requested with the currently selected story ID."""
        story_id = self.selected_story_id()
        if story_id:
            self.open_requested.emit(story_id)

    def _show_context_menu(self, pos) -> None:
        item = self._story_list.itemAt(pos)
        if not item:
            return
            
        story_id = item.data(Qt.ItemDataRole.UserRole)
        
        from PySide6.QtWidgets import QMenu, QMessageBox
        menu = QMenu(self)
        
        action_rename = menu.addAction("Rename Story")
        action_duplicate = menu.addAction("Duplicate Story")
        action_delete = menu.addAction("Delete Story")
        menu.addSeparator()
        action_universe = menu.addAction("Create Universe")
        action_export = menu.addAction("Export Story")
        
        action = menu.exec(self._story_list.mapToGlobal(pos))
        
        if action == action_delete:
            self.delete_requested.emit(story_id)
        elif action == action_universe:
            self.create_universe_requested.emit(story_id)
        elif action in [action_rename, action_duplicate, action_export]:
            QMessageBox.information(self, "Not Implemented", f"'{action.text()}' is a placeholder for future implementation.")

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        """Forward the new selection to listeners."""
        if current is not None:
            story_id = current.data(Qt.ItemDataRole.UserRole)
            if story_id:
                self.story_selection_changed.emit(story_id)

    # ── Public helpers ────────────────────────────────────────────────

    def selected_story_id(self) -> str | None:
        """Return the ID of the currently highlighted story, or ``None``."""
        item = self._story_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def refresh(self, stories: list[Story]) -> None:
        """
        Rebuild the list widget from a fresh list of ``Story`` objects.

        The story ID is stored as ``UserRole`` data on each item so the
        sidebar never needs to know about folder paths.
        """
        self._story_list.clear()
        for story in stories:
            item = QListWidgetItem(story.title)
            item.setData(Qt.ItemDataRole.UserRole, story.id)
            item.setToolTip(f"Genre: {story.genre or '—'}  •  ID: {story.id[:8]}…")
            self._story_list.addItem(item)
