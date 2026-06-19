"""
story_editor.py — Story editing widget for StoryForge AI.

Provides metadata display (title, genre, story ID, created date)
and a markdown text editor with an explicit Save button.

The welcome/empty state is now managed by Workspace, not this widget.
Emits ``save_requested(story_id, content)`` — never touches the
filesystem itself.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QTextCursor, QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMenu,
)

import difflib

from ui.edit_preview_dialog import EditPreviewDialog


class StoryEditor(QWidget):
    """
    Story tab content: metadata header + markdown editor + Save button.

    Signals
    -------
    save_requested(str, str)
        Emitted as ``(story_id, markdown_content)`` when the user
        clicks the Save button.
    """

    # ── Signals ───────────────────────────────────────────────────────
    save_requested = Signal(str, str)
    # action, selected_text, cursor
    ai_edit_requested = Signal(str, str, QTextCursor)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("editorArea")

        self._current_story_id: str | None = None

        self._build_ui()
        self._connect_signals()

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build the flat editor layout: metadata + editor + save."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(0)

        # ── Metadata header ───────────────────────────────────────────
        # Row 1: Title (left) + Story ID (right)
        meta_row1 = QHBoxLayout()
        meta_row1.setContentsMargins(32, 24, 32, 0)

        self._title_label = QLabel()
        self._title_label.setObjectName("editorTitle")
        self._title_label.setStyleSheet("padding: 0;")

        self._id_label = QLabel()
        self._id_label.setObjectName("metaId")

        meta_row1.addWidget(self._title_label)
        meta_row1.addStretch()
        meta_row1.addWidget(self._id_label)

        # Row 2: Genre (left) + Created date (right)
        meta_row2 = QHBoxLayout()
        meta_row2.setContentsMargins(32, 2, 32, 16)

        self._genre_label = QLabel()
        self._genre_label.setObjectName("editorGenre")
        self._genre_label.setStyleSheet("padding: 0;")

        self._date_label = QLabel()
        self._date_label.setObjectName("metaDate")

        meta_row2.addWidget(self._genre_label)
        meta_row2.addStretch()
        meta_row2.addWidget(self._date_label)

        layout.addLayout(meta_row1)
        layout.addLayout(meta_row2)

        editor_container = QVBoxLayout()
        editor_container.setContentsMargins(24, 0, 24, 0)
        editor_container.setSpacing(8)

        # AI Editing Toolbar
        self._ai_toolbar = QHBoxLayout()
        self._ai_toolbar.setContentsMargins(0, 0, 0, 0)
        
        self._lbl_ai_status = QLabel("")
        self._lbl_ai_status.setStyleSheet("color: #6c63ff; font-weight: bold;")
        self._lbl_ai_status.hide()
        
        actions = [
            ("✨ Continue Writing", "continue_writing"),
            ("✏ Improve Writing", "improve_writing"),
            ("📝 Rewrite", "rewrite"),
            ("🧹 Fix Grammar", "fix_grammar"),
            ("📚 Expand Scene", "expand"),
            ("🎭 Improve Dialogue", "improve_dialogue")
        ]
        
        self._ai_buttons = {}
        for text, action_id in actions:
            btn = QPushButton(text)
            btn.setObjectName("aiEditBtn")
            btn.setStyleSheet("background-color: #1e1e38; color: #d0d0e8; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Use lambda default argument to capture action_id
            btn.clicked.connect(lambda checked=False, a=action_id: self._request_ai_edit(a))
            self._ai_toolbar.addWidget(btn)
            self._ai_buttons[action_id] = btn
            
        self._ai_toolbar.addStretch()
        self._ai_toolbar.addWidget(self._lbl_ai_status)

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("storyTextEdit")
        self._text_edit.setAcceptRichText(False)  # plain-text only
        self._text_edit.setPlaceholderText("Start writing your story…")
        self._text_edit.setTabChangesFocus(False)
        self._text_edit.contextMenuEvent = self._custom_context_menu_event

        editor_container.addLayout(self._ai_toolbar)
        editor_container.addWidget(self._text_edit)
        layout.addLayout(editor_container, stretch=1)

        # ── Save button (right-aligned) ───────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 12, 24, 0)
        btn_row.addStretch()

        self._btn_save = QPushButton("💾  Save")
        self._btn_save.setObjectName("btnSave")
        self._btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save.setToolTip("Save story  (Ctrl+S)")
        self._btn_save.setEnabled(False)
        btn_row.addWidget(self._btn_save)

        layout.addLayout(btn_row)

    # ── Signal wiring ─────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._btn_save.clicked.connect(self._on_save_clicked)
        # Enable the Save button only when text has been modified
        self._text_edit.textChanged.connect(self._on_text_changed)

    def _on_save_clicked(self) -> None:
        """Emit the current story ID and editor content."""
        if self._current_story_id:
            content: str = self._text_edit.toPlainText()
            self.save_requested.emit(self._current_story_id, content)
            # Reset modified flag after saving
            self._text_edit.document().setModified(False)
            self._btn_save.setEnabled(False)

    def _on_text_changed(self) -> None:
        """Enable Save only when the document differs from disk."""
        if self._current_story_id:
            self._btn_save.setEnabled(self._text_edit.document().isModified())

    def _custom_context_menu_event(self, event) -> None:
        menu = self._text_edit.createStandardContextMenu()
        menu.addSeparator()
        
        actions = [
            ("✨ Continue Writing", "continue_writing"),
            ("✏ Improve Writing", "improve_writing"),
            ("📝 Rewrite", "rewrite"),
            ("🧹 Fix Grammar", "fix_grammar"),
            ("📚 Expand Scene", "expand"),
            ("🎭 Improve Dialogue", "improve_dialogue")
        ]
        
        for text, action_id in actions:
            action = QAction(text, self)
            action.triggered.connect(lambda checked=False, a=action_id: self._request_ai_edit(a))
            menu.addAction(action)
            
        menu.exec(event.globalPos())

    def _request_ai_edit(self, action: str) -> None:
        cursor = self._text_edit.textCursor()
        selected_text = cursor.selectedText()
        selected_text = selected_text.replace('\u2029', '\n')
        
        if not cursor.hasSelection():
            if action == "continue_writing":
                # Grab preceding text up to 1500 chars
                pos = cursor.position()
                full_text = self._text_edit.toPlainText()
                start_pos = max(0, pos - 1500)
                selected_text = full_text[start_pos:pos]
            else:
                self._lbl_ai_status.setText("⚠️ Please select text first.")
                self._lbl_ai_status.setStyleSheet("color: #ffaa00; font-weight: bold;")
                self._lbl_ai_status.show()
                QTimer.singleShot(2000, self._lbl_ai_status.hide)
                return
        
        self.set_ai_status("⚒️ Smith is processing...")
        # Emit signal (handled by MainWindow)
        self.ai_edit_requested.emit(action, selected_text, cursor)

    def set_ai_status(self, text: str) -> None:
        if text:
            self._lbl_ai_status.setText(text)
            self._lbl_ai_status.setStyleSheet("color: #6c63ff; font-weight: bold;")
            self._lbl_ai_status.show()
            for btn in self._ai_buttons.values():
                btn.setEnabled(False)
        else:
            self._lbl_ai_status.hide()
            for btn in self._ai_buttons.values():
                btn.setEnabled(True)

    def apply_ai_edit(self, cursor: QTextCursor, original_text: str, new_text: str, is_append: bool = False) -> None:
        self.set_ai_status("")
        # Show preview dialog
        dialog = EditPreviewDialog(original_text, new_text, is_append, self)
        dialog.exec()
        if dialog.action_result == "replace":
            # This triggers a single undo block natively
            if is_append:
                cursor.movePosition(cursor.MoveOperation.EndOfBlock) # Or end of selection
                cursor.insertText("\n\n" + new_text)
            else:
                cursor.insertText(new_text)

    def append_text(self, text_to_add: str) -> None:
        """Insert text at cursor."""
        cursor = self._text_edit.textCursor()
        cursor.insertText(text_to_add + "\n")
        self._text_edit.setTextCursor(cursor)
        self._text_edit.setFocus()

    def find_closest_match(self, search_text: str) -> dict:
        """Find the exact or closest matching block of text in the document."""
        full_text = self._text_edit.toPlainText()
        
        # 1. Exact match (bypassing PySide6's block-boundary issues)
        exact_idx = full_text.find(search_text)
        if exact_idx != -1:
            return {"status": "exact", "start": exact_idx, "end": exact_idx + len(search_text)}
            
        # 2. Fuzzy match
        sm = difflib.SequenceMatcher(None, full_text, search_text)
        blocks = sm.get_matching_blocks()
        
        significant_blocks = [b for b in blocks[:-1] if b.size > 5]
        if not significant_blocks:
            return {"status": "missing"}
            
        start_a = significant_blocks[0].a
        end_a = significant_blocks[-1].a + significant_blocks[-1].size
        
        window_text = full_text[start_a:end_a]
        similarity = difflib.SequenceMatcher(None, window_text, search_text).ratio()
        
        if similarity >= 0.85:
            return {"status": "slightly_modified", "start": start_a, "end": end_a}
        elif similarity >= 0.3:
            return {"status": "heavily_modified", "start": start_a, "end": end_a}
        else:
            return {"status": "missing"}

    def remove_text(self, text_to_remove: str) -> bool:
        """Find the exact match of text_to_remove and delete it. Used only for exact matches."""
        if not text_to_remove:
            return False
            
        match = self.find_closest_match(text_to_remove)
        if match["status"] in ["exact", "slightly_modified"]:
            cursor = self._text_edit.textCursor()
            cursor.setPosition(match["start"])
            cursor.setPosition(match["end"], QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            return True
            
        return False
        
    def locate_and_highlight(self, text_to_find: str) -> None:
        """Find text, scroll to it, and briefly highlight it."""
        if not text_to_find:
            return
            
        match = self.find_closest_match(text_to_find)
        if match["status"] in ["exact", "slightly_modified", "heavily_modified"]:
            # Set cursor and highlight
            cursor = self._text_edit.textCursor()
            cursor.setPosition(match["start"])
            cursor.setPosition(match["end"], QTextCursor.MoveMode.KeepAnchor)
            self._text_edit.setTextCursor(cursor)
            
            selection = QTextEdit.ExtraSelection()
            from PySide6.QtGui import QColor
            selection.format.setBackground(QColor("#6c63ff"))
            selection.format.setForeground(QColor("#ffffff"))
            selection.cursor = cursor
            
            self._text_edit.setExtraSelections([selection])
            QTimer.singleShot(2500, lambda: self._text_edit.setExtraSelections([]))
            self._text_edit.setFocus()
        else:
            QMessageBox.information(self, "Not Found", "This response has not been added to the story.")

    # ── Public API (called by Workspace) ──────────────────────────────

    def load_content(
        self,
        title: str,
        genre: str,
        story_id: str,
        content: str,
        created_at: str = "",
    ) -> None:
        """
        Populate the editor with a story's data.

        Parameters
        ----------
        title : str
            Story title shown in the header.
        genre : str
            Genre tag shown below the title.
        story_id : str
            UUID4 stored internally for the save signal.
        content : str
            Raw markdown loaded from ``story.md``.
        created_at : str, optional
            ISO-8601 timestamp displayed as a readable date.
        """
        self._current_story_id = story_id
        self._title_label.setText(title)
        self._genre_label.setText(genre.upper() if genre else "")
        self._id_label.setText(f"ID: {story_id[:8]}…")
        self._date_label.setText(self._format_date(created_at))

        # Block signals while loading to avoid false "modified" flag
        self._text_edit.blockSignals(True)
        self._text_edit.setPlainText(content)
        self._text_edit.document().setModified(False)
        self._text_edit.blockSignals(False)

        self._btn_save.setEnabled(False)

        # Place cursor at the end for a natural writing start-point
        cursor = self._text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.setFocus()

    def clear(self) -> None:
        """Discard editor state."""
        self._current_story_id = None
        self._text_edit.clear()
        self._title_label.clear()
        self._genre_label.clear()
        self._id_label.clear()
        self._date_label.clear()
        self._btn_save.setEnabled(False)

    @property
    def current_story_id(self) -> str | None:
        """The ID of the story currently loaded in the editor."""
        return self._current_story_id

    @property
    def is_modified(self) -> bool:
        """True when the editor content differs from the last save."""
        return self._text_edit.document().isModified()

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _format_date(iso_string: str) -> str:
        """Convert an ISO-8601 string to a human-readable date, or ''."""
        if not iso_string:
            return ""
        try:
            # Handle both 'Z' and '+00:00' suffixes
            clean = iso_string.replace("Z", "+00:00")
            from datetime import datetime
            dt = datetime.fromisoformat(clean)
            return dt.strftime("Created: %b %d, %Y %H:%M")
        except (ValueError, TypeError):
            return f"Created: {iso_string[:10]}"


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        if data is None: return
        if hasattr(data, 'story') and hasattr(data, 'content'):
            self.load_content(data.story.title, data.story.genre, data.story.id, data.content, data.story.created_at)

