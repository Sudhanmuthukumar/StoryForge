# ui/chat_view.py
"""Full chat interface widget for the StoryForge AI application."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
    QScrollArea
)

from ui.chat_message import ChatMessage
from services.ai_service import AIService


class ChatView(QWidget):
    """A complete chat panel containing a scrollable message area and an input row.

    Signals
    -------
    message_sent(str, str)
        Emitted as ``(story_id, text)`` when the user sends a new message.
    message_action_requested(str, str, str)
        Emitted as ``(action_name, message_id, content)`` for menu actions.

    Public API
    ----------
    load_history(story_id, messages)
        Replace the current view with an existing conversation.
    add_message(role, content, timestamp)
        Append a single bubble and auto-scroll.
    clear()
        Remove every message and reset the story id.
    set_input_enabled(enabled)
        Toggle the input field and send button.
    """

    message_sent: Signal = Signal(str, str)
    message_action_requested = Signal(str, str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_story_id: str | None = None

        # ── main vertical layout ──────────────────────────────────────
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── scrollable message area ───────────────────────────────────
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self._message_container = QWidget()
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(8, 8, 8, 8)
        self._message_layout.setSpacing(8)
        self._message_layout.addStretch()  # keeps bubbles stacked from top

        self._scroll_area.setWidget(self._message_container)
        main_layout.addWidget(self._scroll_area, stretch=1)
        
        # ── settings row ──────────────────────────────────────────────
        self._ai_service = AIService()
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(12, 4, 12, 0)
        
        lbl_model = QLabel("Model:")
        lbl_model.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        
        self._model_combo = QComboBox()
        self._model_combo.setStyleSheet("background-color: #1e1e38; color: #d0d0e8; border-radius: 4px; padding: 2px 8px;")
        
        # Load available models
        models = self._ai_service.get_available_models()
        if not models:
            self._model_combo.addItem("No Ollama Models Found")
            self._model_combo.setEnabled(False)
        else:
            for m in models:
                if not m:
                    continue
                display_text = m
                if "qwen3:8b" in m:
                    display_text += " (Best Quality)"
                elif "qwen2.5:3b" in m:
                    display_text += " (Fast)"
                self._model_combo.addItem(display_text, userData=m)
                
            # Set to saved model
            saved_model = self._ai_service.model
            idx = self._model_combo.findData(saved_model)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
            
            self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        
        settings_row.addWidget(lbl_model)
        settings_row.addWidget(self._model_combo)
        settings_row.addStretch()
        main_layout.addLayout(settings_row)

        # ── input row ─────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setContentsMargins(8, 4, 8, 8)
        input_row.setSpacing(6)

        self._input_field = QLineEdit()
        self._input_field.setObjectName("chatInput")
        self._input_field.setPlaceholderText("Type a message...")
        self._input_field.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self._send_button = QPushButton("Send")
        self._send_button.setObjectName("btnSend")
        self._send_button.setEnabled(False)

        input_row.addWidget(self._input_field)
        input_row.addWidget(self._send_button)
        main_layout.addLayout(input_row)

        # ── connections ───────────────────────────────────────────────
        self._send_button.clicked.connect(self._on_send)
        self._input_field.returnPressed.connect(self._on_send)
        self._input_field.textChanged.connect(self._on_text_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_history(
        self, story_id: str, messages: list[dict[str, str]]
    ) -> None:
        """Clear the view, set the active story, and render *messages*.

        Parameters
        ----------
        story_id : str
            The identifier of the story whose chat is being loaded.
        messages : list[dict]
            Each dict must contain ``"role"``, ``"content"``, and
            ``"timestamp"`` keys.
        """
        self.clear()
        self._current_story_id = story_id
        for msg in messages:
            self.add_message(
                role=msg.get("role", "assistant"),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp", ""),
                message_id=msg.get("id"),
                parent_id=msg.get("parent_id"),
                story_insertions=msg.get("story_insertions", [])
            )

    def add_message(
        self, role: str, content: str, timestamp: str,
        message_id: str = None, parent_id: str = None, story_insertions: list = None
    ) -> ChatMessage:
        """Append a single chat bubble and auto-scroll to the bottom.

        Parameters
        ----------
        role : str
            ``"user"`` or ``"assistant"``.
        content : str
            The message body.
        timestamp : str
            A timestamp string forwarded to :class:`ChatMessage`.
        """
        bubble = ChatMessage(
            role=role, content=content, timestamp=timestamp,
            message_id=message_id, parent_id=parent_id, story_insertions=story_insertions
        )
        bubble.action_requested.connect(self.message_action_requested.emit)

        # Wrap the bubble in an alignment row so user messages sit on the
        # right and assistant messages sit on the left.
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        if role == "user":
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch()

        # Insert *before* the trailing stretch so bubbles stay stacked
        # from the top.
        insert_index = self._message_layout.count() - 1
        self._message_layout.insertLayout(insert_index, row_layout)

        # Auto-scroll to bottom after the layout pass.
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._scroll_to_bottom)
        return bubble

    def clear(self) -> None:
        """Remove all message bubbles and reset the story id."""
        self._current_story_id = None

        # Remove every item except the trailing stretch.
        while self._message_layout.count() > 1:
            item = self._message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable the input field and send button."""
        self._input_field.setEnabled(enabled)
        self._send_button.setEnabled(
            enabled and bool(self._input_field.text().strip())
        )

    def set_thinking_state(self, is_thinking: bool) -> None:
        """Toggle UI controls and button text during AI generation."""
        if is_thinking:
            self._input_field.setEnabled(False)
            self._send_button.setEnabled(False)
            self._send_button.setText("Thinking...")
        else:
            self._input_field.setEnabled(True)
            self._send_button.setText("Send")
            self._send_button.setEnabled(bool(self._input_field.text().strip()))

    # ------------------------------------------------------------------
    # Private slots / helpers
    # ------------------------------------------------------------------

    def _on_send(self) -> None:
        """Handle send-button clicks and Enter key presses."""
        text = self._input_field.text().strip()
        if not text:
            return
        if self._current_story_id is None:
            return

        self._input_field.clear()
        self.message_sent.emit(self._current_story_id, text)

    def _on_text_changed(self, text: str) -> None:
        """Enable the send button only when there is non-whitespace input."""
        self._send_button.setEnabled(
            bool(text.strip()) and self._input_field.isEnabled()
        )

    def _scroll_to_bottom(self) -> None:
        """Scroll the message area to the very bottom."""
        v_bar = self._scroll_area.verticalScrollBar()
        v_bar.setValue(v_bar.maximum())

    @staticmethod
    def _clear_layout(layout: QVBoxLayout | QHBoxLayout) -> None:
        """Recursively delete all items from *layout*."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                ChatView._clear_layout(item.layout())

    def _on_model_changed(self, index: int) -> None:
        """Save the selected model to config."""
        model_name = self._model_combo.itemData(index)
        if model_name:
            self._ai_service.save_model(model_name)


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        if data is None: return
        if hasattr(data, 'story') and hasattr(data, 'chat_history'):
            self.load_history(data.story.id, data.chat_history)

