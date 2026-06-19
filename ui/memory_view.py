"""
memory_view.py — Read-only display of story memory entities.

Shows statistical counts and lists of extracted entities.
Allows manual extraction refresh via a 'Refresh' button.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class MemoryView(QWidget):
    """
    Shows a summary and list of all extracted memory entities.
    """

    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("memoryArea")
        
        self._count_labels: dict[str, QLabel] = {}
        self._lists: dict[str, QListWidget] = {}
        
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for everything
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header with Title and Refresh button
        header = QHBoxLayout()
        title = QLabel("Memory Overview")
        title.setObjectName("sectionTitle")
        
        self._btn_refresh = QPushButton("🔄 Refresh Memory")
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.clicked.connect(self.refresh_requested.emit)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        # Stat cards grid
        grid = QGridLayout()
        grid.setSpacing(16)
        
        categories = [
            ("characters", "👤", "Characters", 0, 0),
            ("relationships", "🔗", "Relationships", 0, 1),
            ("events", "📅", "Events", 0, 2),
            ("locations", "📍", "Locations", 1, 0),
            ("organizations", "🏛️", "Organizations", 1, 1),
            ("artifacts", "🗡️", "Artifacts", 1, 2),
            ("themes", "💡", "Themes", 2, 0),
            ("quotes", "💬", "Quotes", 2, 1),
        ]
        
        for key, icon, label, row, col in categories:
            card = self._create_stat_card(key, icon, label)
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid)
        
        # Tabs for lists
        self._tabs = QTabWidget()
        self._tabs.setObjectName("memoryTabs")
        
        list_categories = ["Characters", "Relationships", "Locations", "Organizations", "Events", "Themes", "Quotes"]
        for cat in list_categories:
            list_widget = QListWidget()
            self._lists[cat.lower()] = list_widget
            self._tabs.addTab(list_widget, cat)
            
        layout.addWidget(self._tabs, stretch=1)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

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

    def load_data(self, memory: dict) -> None:
        """Populate the UI from the memory dictionary."""
        # Update counts
        for key, lbl in self._count_labels.items():
            val = memory.get(key, [])
            lbl.setText(str(len(val)))
            
        # Update lists
        for cat_key, list_widget in self._lists.items():
            list_widget.clear()
            items = memory.get(cat_key, [])
            for item in items:
                if isinstance(item, dict):
                    # Format standard entities vs quotes
                    if cat_key == "quotes":
                        text = f'{item.get("speaker", "?")}: {item.get("text", "")}'
                    elif cat_key == "relationships":
                        text = f'{item.get("source", "?")} ↔ {item.get("target", "?")} ({item.get("type", "Unknown")})'
                    else:
                        text = item.get("name", "Unknown")
                        if "mentions" in item:
                            text += f' ({item["mentions"]} mentions)'
                            
                        if cat_key == "characters":
                            traits = [t.get("value") for t in item.get("traits", [])]
                            goals = [g.get("value") for g in item.get("goals", [])]
                            fears = [f.get("value") for f in item.get("fears", [])]
                            rels = [f"{r.get('type')}: {r.get('target')}" for r in item.get("relationships", [])]
                            
                            details = []
                            if traits: details.append(f"Traits: {', '.join(traits)}")
                            if goals: details.append(f"Goals: {', '.join(goals)}")
                            if fears: details.append(f"Fears: {', '.join(fears)}")
                            if rels: details.append(f"Rels: {', '.join(rels)}")
                            
                            if details:
                                text += f"\n    -> {' | '.join(details)}"
                    
                    conf = item.get("confidence", 0.0)
                    text += f'  [Conf: {conf}]'
                    
                    if cat_key == "relationships" and "evidence" in item:
                        text += f'  Ev: "{item["evidence"]}"'
                        
                    list_widget.addItem(text)
                else:
                    # Fallback for old string format
                    list_widget.addItem(str(item))

    def clear(self) -> None:
        """Reset the UI."""
        for lbl in self._count_labels.values():
            lbl.setText("0")
        for lw in self._lists.values():
            lw.clear()
