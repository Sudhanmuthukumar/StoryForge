# ui/chat_message.py
"""Single chat-message bubble widget for the StoryForge AI chat interface."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QToolButton, QMenu
)

class ChatMessage(QFrame):
    _MAX_BUBBLE_WIDTH: int = 500
    
    # action_name, message_id, content
    action_requested = Signal(str, str, str)

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: str,
        message_id: str = None,
        parent_id: str = None,
        story_insertions: list = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.message_id = message_id or ""
        self.parent_id = parent_id or ""
        self.story_insertions = story_insertions or []
        self.raw_content = content
        self.setMaximumWidth(self._MAX_BUBBLE_WIDTH)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(4)
        
        if role == "assistant":
            self._apply_assistant_style(self._layout)
        else:
            self._apply_user_style(self._layout)

        # Add processing/thinking panels (assistant only)
        if role == "assistant":
            self._processing_btn, self._processing_lbl = self._add_collapsible("🧠 StoryForge Processing")
            self._thinking_btn, self._thinking_lbl = self._add_collapsible("📖 Smith is thinking")
            self._diagnostics_btn, self._diagnostics_lbl = self._add_collapsible("📊 Diagnostics")
            
            # Hide them initially until data arrives
            self._processing_btn.hide()
            self._thinking_btn.hide()
            self._diagnostics_btn.hide()
            
            # Generation status
            self._status_layout = QHBoxLayout()
            self._status_layout.setContentsMargins(10, 0, 10, 0)
            self._spinner_lbl = QLabel("")
            self._spinner_lbl.setStyleSheet("color: #6c63ff; font-weight: bold;")
            self._stats_lbl = QLabel("📖 Smith is thinking... | Elapsed: 0.0s | Tokens: 0 | Chars: 0")
            self._stats_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
            self._status_layout.addWidget(self._spinner_lbl)
            self._status_layout.addWidget(self._stats_lbl)
            self._status_layout.addStretch()
            self._layout.addLayout(self._status_layout)
            
            self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            self._spinner_idx = 0
            self._spinner_timer = QTimer(self)
            self._spinner_timer.timeout.connect(self._update_spinner)
            self._spinner_timer.start(100)

        # Response text
        self._content_lbl = QLabel(content)
        self._content_lbl.setObjectName("chatContent")
        self._content_lbl.setWordWrap(True)
        self._content_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._layout.addWidget(self._content_lbl)

        # Bottom Row: Timestamp and Badges
        self._bottom_row = QHBoxLayout()
        self._bottom_row.setContentsMargins(0, 4, 0, 0)
        
        self._badge_lbl = QLabel("📎 Added To Story")
        self._badge_lbl.setStyleSheet("color: #4caf50; font-size: 10px; font-weight: bold;")
        self._badge_lbl.hide()
        if self.story_insertions:
            self._badge_lbl.show()
            
        self._bottom_row.addWidget(self._badge_lbl)
        self._bottom_row.addStretch()

        # Timestamp
        self._ts_label = QLabel(self._format_timestamp(timestamp))
        self._ts_label.setObjectName("chatTimestamp")
        self._ts_label.setStyleSheet("color: #b0b0c0; font-size: 10px;")
        self._ts_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._bottom_row.addWidget(self._ts_label)
        self._layout.addLayout(self._bottom_row)
        
        self.raw_thinking = ""
        self.raw_processing = ""

    def _add_collapsible(self, title: str) -> tuple[QPushButton, QLabel]:
        """Creates a collapsible section and returns the button and the label inside."""
        btn = QPushButton(f"▶ {title}")
        btn.setObjectName("colBtn")
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                background: transparent;
                color: #6c63ff;
                border: none;
                font-weight: bold;
                padding: 2px 0px;
            }
            QPushButton:hover { color: #8c83ff; }
        """)
        
        lbl = QLabel()
        lbl.setObjectName("colLbl")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #a0a0c0; font-family: monospace; font-size: 11px; margin-left: 10px; border-left: 2px solid #3c3c5a; padding-left: 6px;")
        lbl.hide()
        
        # Toggle logic
        def toggle():
            if lbl.isHidden():
                lbl.show()
                btn.setText(f"▼ {title}")
            else:
                lbl.hide()
                btn.setText(f"▶ {title}")
                
        btn.clicked.connect(toggle)
        
        self._layout.addWidget(btn)
        self._layout.addWidget(lbl)
        return btn, lbl

    def _update_spinner(self) -> None:
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self._spinner_lbl.setText(self._spinner_frames[self._spinner_idx])

    def append_processing(self, text: str) -> None:
        self.raw_processing += text + "\n"
        self._processing_lbl.setText(self.raw_processing.strip())
        self._processing_btn.show()

    def update_stats(self, stats: dict) -> None:
        elapsed = stats.get("elapsed", 0)
        tokens = stats.get("tokens", 0)
        chars = stats.get("chars", 0)
        self._stats_lbl.setText(f"⚒️ Smith is forging... | Elapsed: {elapsed:.1f}s | Tokens: {tokens} | Chars: {chars}")

    def finish_generation(self) -> None:
        if hasattr(self, "_spinner_timer"):
            self._spinner_timer.stop()
            self._spinner_lbl.setText("✓")
            self._spinner_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self._stats_lbl.setText("Generation Complete.")

    def append_thinking(self, text: str) -> None:
        self.raw_thinking += text
        self._thinking_lbl.setText(self.raw_thinking.strip())
        self._thinking_btn.show()

    def append_response(self, text: str) -> None:
        self.raw_content += text
        self._content_lbl.setText(self.raw_content.strip())
        
    def set_diagnostics(self, text: str) -> None:
        self._diagnostics_lbl.setText(text)
        self._diagnostics_btn.show()
        
    def show_badge(self) -> None:
        self._badge_lbl.show()

    def _apply_assistant_style(self, layout: QVBoxLayout) -> None:
        self.setObjectName("chatBubbleAssistant")
        self.setStyleSheet("""
            QFrame#chatBubbleAssistant { background-color: #1e1e38; border-radius: 12px; border-top-left-radius: 2px; }
            QFrame#chatBubbleAssistant QLabel { color: #d0d0e8; background: transparent; }
            QFrame#chatBubbleAssistant QLabel#chatSender { color: #8c83ff; font-size: 11px; font-weight: bold; }
        """)
        # Top row: Sender Name + Menu
        top_row = QHBoxLayout()
        sender_label = QLabel("🤖 StoryForge AI")
        sender_label.setObjectName("chatSender")
        top_row.addWidget(sender_label)
        top_row.addStretch()
        
        self._menu_btn = QToolButton()
        self._menu_btn.setText("⋮")
        self._menu_btn.setStyleSheet("QToolButton { background: transparent; border: none; font-size: 16px; font-weight: bold; color: #b0b0c0; } QToolButton::menu-indicator { image: none; }")
        self._menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2a2a4a; color: #d0d0e8; border: 1px solid #3a3a5a; } QMenu::item:selected { background-color: #6c63ff; }")
        
        action_add = menu.addAction("Add To Story")
        action_locate = menu.addAction("Locate In Story")
        action_copy = menu.addAction("Copy")
        action_variations = menu.addAction("Create Variations")
        action_delete = menu.addAction("Delete Message")
        
        action_add.triggered.connect(lambda: self.action_requested.emit("add_to_story", self.message_id, self.raw_content))
        action_locate.triggered.connect(lambda: self.action_requested.emit("locate", self.message_id, self.raw_content))
        action_copy.triggered.connect(lambda: self.action_requested.emit("copy", self.message_id, self.raw_content))
        action_variations.triggered.connect(lambda: self.action_requested.emit("variations", self.message_id, self.raw_content))
        action_delete.triggered.connect(lambda: self.action_requested.emit("delete_message", self.message_id, self.raw_content))
        
        self._menu_btn.setMenu(menu)
        top_row.addWidget(self._menu_btn)
        
        layout.addLayout(top_row)

    def _apply_user_style(self, layout: QVBoxLayout) -> None:
        self.setObjectName("chatBubbleUser")
        self.setStyleSheet("""
            QFrame#chatBubbleUser { background-color: #2a2a4a; border-radius: 12px; border-top-right-radius: 2px; }
            QFrame#chatBubbleUser QLabel { color: #e0e0ff; background: transparent; }
            QFrame#chatBubbleUser QLabel#chatSender { color: #aaaaaa; font-size: 11px; font-weight: bold; }
        """)
        
        # Top row: Menu + Sender Name
        top_row = QHBoxLayout()
        
        self._menu_btn = QToolButton()
        self._menu_btn.setText("⋮")
        self._menu_btn.setStyleSheet("QToolButton { background: transparent; border: none; font-size: 16px; font-weight: bold; color: #b0b0c0; } QToolButton::menu-indicator { image: none; }")
        self._menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1e1e38; color: #d0d0e8; border: 1px solid #3a3a5a; } QMenu::item:selected { background-color: #6c63ff; }")
        
        action_edit = menu.addAction("Edit Prompt")
        action_delete = menu.addAction("Delete Conversation")
        
        action_edit.triggered.connect(lambda: self.action_requested.emit("edit_prompt", self.message_id, self.raw_content))
        action_delete.triggered.connect(lambda: self.action_requested.emit("delete_conversation", self.message_id, self.raw_content))
        
        self._menu_btn.setMenu(menu)
        top_row.addWidget(self._menu_btn)
        top_row.addStretch()
        
        sender_label = QLabel("👤 User")
        sender_label.setObjectName("chatSender")
        top_row.addWidget(sender_label)
        
        layout.addLayout(top_row)

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%d %b %Y • %I:%M %p")
        except (ValueError, TypeError):
            return timestamp
