"""
context_inspector.py

View panel for displaying AI Context Engine injection logic.
"""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QFrame,
    QListWidget,
    QTabWidget,
    QHBoxLayout,
    QTextEdit,
    QPushButton
)

class ContextInspector(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contextInspector")
        self._count_labels: dict[str, QLabel] = {}
        self._lists: dict[str, QListWidget] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("Context Inspector")
        lbl.setStyleSheet("font-weight: bold; color: #b0b0c0; font-size: 14px;")
        layout.addWidget(lbl)
        
        # Extended Diagnostic Header
        self._stats_lbl = QLabel("No context loaded.")
        self._stats_lbl.setStyleSheet("color: #8888aa; font-size: 11px;")
        layout.addWidget(self._stats_lbl)

        # Stats Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        grid = QGridLayout()
        grid.setSpacing(16)
        
        categories = [
            ("selected", "✅", "Selected Blocks", 0, 0),
            ("dropped", "❌", "Dropped Blocks", 0, 1),
            ("size", "📏", "Total Chars", 1, 0),
            ("latency", "⏱️", "Latency (ms)", 1, 1)
        ]
        
        for key, icon, label, row, col in categories:
            card = self._create_stat_card(key, icon, label)
            grid.addWidget(card, row, col)
            
        container_layout.addLayout(grid)
        
        # Details view
        self._tabs = QTabWidget()
        
        self._list_selected = QListWidget()
        self._tabs.addTab(self._list_selected, "Selected Context")
        
        self._list_dropped = QListWidget()
        self._tabs.addTab(self._list_dropped, "Dropped Blocks")
        
        container_layout.addWidget(self._tabs, stretch=1)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Prompt Preview Section
        self._prompt_btn = QPushButton("📜 Prompt Preview (Sent to Model) ▼")
        self._prompt_btn.setStyleSheet("text-align: left; font-weight: bold; color: #b0b0c0; font-size: 12px; margin-top: 10px; border: none; background: transparent;")
        self._prompt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prompt_btn.clicked.connect(self._toggle_prompt_preview)
        layout.addWidget(self._prompt_btn)
        
        self._prompt_edit = QTextEdit()
        self._prompt_edit.setReadOnly(True)
        self._prompt_edit.setStyleSheet(
            "background-color: #15152a; color: #e0e0ff; font-family: Consolas, monospace; font-size: 11px; border: 1px solid #2a2a4a;"
        )
        self._prompt_edit.hide() # Collapsed by default
        layout.addWidget(self._prompt_edit)

    def _toggle_prompt_preview(self) -> None:
        is_hidden = self._prompt_edit.isHidden()
        self._prompt_edit.setVisible(is_hidden)
        if is_hidden:
            self._prompt_btn.setText("📜 Prompt Preview (Sent to Model) ▲")
        else:
            self._prompt_btn.setText("📜 Prompt Preview (Sent to Model) ▼")

    def _create_stat_card(self, key: str, icon: str, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        cl = QVBoxLayout(card)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setObjectName("statIcon")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_count = QLabel("0")
        lbl_count.setObjectName("statCount")
        lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_labels[key] = lbl_count
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("statLabel")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        cl.addWidget(lbl_icon)
        cl.addWidget(lbl_count)
        cl.addWidget(lbl_title)
        return card

    def load_data(self, ranked_context: dict, latency_ms: float, final_prompt: str = "") -> None:
        """Display the selected context blocks and update metadata."""
        selected = ranked_context.get("selected", [])
        num_blocks = len(selected)
        
        self._count_labels["selected"].setText(str(num_blocks))
        self._count_labels["dropped"].setText(str(len(ranked_context.get("dropped", []))))
        self._count_labels["size"].setText(str(ranked_context.get("total_chars", 0)))
        self._count_labels["latency"].setText(f"{latency_ms:.1f}")
        
        total_blocks = len(ranked_context.get("all", []))
        
        # Estimated prompt size
        prompt_size = len(final_prompt)
        # Assuming ~4 chars per token, max context usually ~8192 for Ollama 
        est_tokens = prompt_size // 4
        usage_pct = min(100, (est_tokens / 8192) * 100)
        
        from services.ai_service import AIService
        model_name = AIService().model
        
        self._stats_lbl.setText(
            f"Selected Model: {model_name}\n"
            f"Blocks Ranked: {total_blocks} | Blocks Included: {num_blocks}\n"
            f"Prompt Size: {prompt_size} chars (~{est_tokens} tokens)\n"
            f"Estimated Context Usage: {usage_pct:.1f}%\n"
            f"Ranking Latency: {latency_ms:.1f} ms"
        )
        
        self._list_selected.clear()
        out = ""
        for b in selected:
            item = f"[{b['source_type'].upper()}] {b['source']} | Rel: {b['relevance']:.2f} | Imp: {b['importance']:.2f}\n{b['content']}"
            self._list_selected.addItem(item)
            out += item + "\n---\n"
            
        self._list_dropped.clear()
        for b in ranked_context.get("dropped", []):
            item = f"[{b['source_type'].upper()}] {b['source']} | Rel: {b['relevance']:.2f} | Imp: {b['importance']:.2f}\n{b['content']}"
            self._list_dropped.addItem(item)
            
        self._prompt_edit.setPlainText(final_prompt)

    def clear(self) -> None:
        for lbl in self._count_labels.values():
            lbl.setText("0")
        self._stats_lbl.setText("No context loaded.")
        self._list_selected.clear()
        self._list_dropped.clear()
        self._prompt_edit.clear()
