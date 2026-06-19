"""
preferences_view.py

View panel for displaying global user preferences learned across stories.
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
    QProgressBar
)

class PreferencesView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._panels: dict[str, QVBoxLayout] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        title = QLabel("Learned User Preferences")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(16)
        
        categories = [
            ("genres", "Favorite Genres", 0, 0),
            ("themes", "Favorite Themes", 0, 1),
            ("character_types", "Character Types", 1, 0),
            ("relationship_types", "Relationship Types", 1, 1),
        ]
        
        for key, label, row, col in categories:
            frame = QFrame()
            frame.setObjectName("statCard")
            fl = QVBoxLayout(frame)
            
            lbl_title = QLabel(label)
            lbl_title.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
            fl.addWidget(lbl_title)
            
            self._panels[key] = fl
            grid.addWidget(frame, row, col)
            
        layout.addLayout(grid)
        layout.addStretch(1)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _add_pref_item(self, layout: QVBoxLayout, name: str, data: dict):
        item_layout = QVBoxLayout()
        item_layout.setSpacing(2)
        
        score = data.get("score", 0.0)
        conf = data.get("confidence", 0.0)
        samples = data.get("samples", 0)
        
        lbl = QLabel(f"{name} (Samples: {samples})")
        
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(conf * 100))
        bar.setFormat(f"Confidence: %p%")
        bar.setFixedHeight(12)
        
        item_layout.addWidget(lbl)
        item_layout.addWidget(bar)
        
        # Wrap in a widget to add to layout
        w = QWidget()
        w.setLayout(item_layout)
        layout.addWidget(w)

    def load_data(self, user_profile: dict) -> None:
        """Populate the UI from the global user_profile dictionary."""
        # Clear existing
        for layout in self._panels.values():
            while layout.count() > 1: # keep title
                item = layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
                    
        implicit = user_profile.get("implicit_preferences", {})
        
        for key, layout in self._panels.items():
            items = implicit.get(key, {})
            # Sort by score descending
            sorted_items = sorted(items.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            for name, data in sorted_items[:5]: # top 5
                self._add_pref_item(layout, name, data)

    def clear(self) -> None:
        self.load_data({})
