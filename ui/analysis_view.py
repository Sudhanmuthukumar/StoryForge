"""
analysis_view.py

Stat cards panel displaying counts for analysis categories, 
along with detailed lists for Strengths, Weaknesses, Critiques, and Risks.
"""

from __future__ import annotations
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTabWidget,
    QListWidget,
    QPushButton
)

_GRID_COLUMNS = 3

class AnalysisView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._count_labels: dict[str, QLabel] = {}
        self._lists: dict[str, QListWidget] = {}
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

        header = QHBoxLayout()
        title = QLabel("Analysis Overview")
        title.setObjectName("sectionTitle")
        
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Stat cards
        grid = QGridLayout()
        grid.setSpacing(16)
        
        categories = [
            ("health", "❤️", "Health Score", 0, 0),
            ("dna", "🧬", "Story DNA", 0, 1),
            ("consistency", "⚖️", "Consistency", 0, 2),
            ("strengths", "💪", "Strengths", 1, 0),
            ("critiques", "📝", "Critiques", 1, 1),
            ("risks", "🚩", "Risks", 1, 2)
        ]
        
        for key, icon, label, row, col in categories:
            card = self._create_stat_card(key, icon, label)
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid)
        
        # Tabs for details
        self._tabs = QTabWidget()
        self._tabs.setObjectName("analysisTabs")
        
        list_categories = ["DNA", "Strengths", "Weaknesses", "Critiques", "Risks", "Consistency"]
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

    def load_data(self, analysis: dict, consistency: dict = None) -> None:
        """Populate the UI from the analysis and consistency dictionaries."""
        if consistency is None:
            consistency = {}
            
        # Update counts
        health = analysis.get("story_health", {}).get("overall", 0)
        self._count_labels["health"].setText(str(health))
        
        dna_count = len(analysis.get("story_dna", {}).keys())
        self._count_labels["dna"].setText(str(dna_count))
        
        cons_score = consistency.get("consistency_score", 100)
        self._count_labels["consistency"].setText(str(cons_score))
        
        self._count_labels["strengths"].setText(str(len(analysis.get("strengths", []))))
        self._count_labels["critiques"].setText(str(len(analysis.get("critiques", []))))
        self._count_labels["risks"].setText(str(len(analysis.get("risks", []))))
            
        # Update lists
        self._lists["dna"].clear()
        dna = analysis.get("story_dna", {})
        for k, v in dna.items():
            self._lists["dna"].addItem(f"{k.replace('_', ' ').title()}: {v}")
            
        self._lists["strengths"].clear()
        for item in analysis.get("strengths", []):
            self._lists["strengths"].addItem(f"{item.get('title')}\n  {item.get('description')}")
            
        self._lists["weaknesses"].clear()
        for item in analysis.get("weaknesses", []):
            self._lists["weaknesses"].addItem(f"{item.get('title')}\n  {item.get('description')}")
            
        self._lists["critiques"].clear()
        for item in analysis.get("critiques", []):
            self._lists["critiques"].addItem(f"[{item.get('severity')}] {item.get('message')}\n  Recommend: {item.get('recommendation')}")
            
        self._lists["risks"].clear()
        for item in analysis.get("risks", []):
            self._lists["risks"].addItem(f"{item.get('title')}\n  Reason: {item.get('reason')}")

        self._lists["consistency"].clear()
        for k in ["fact_conflicts", "relationship_conflicts", "character_conflicts", "continuity_conflicts"]:
            for item in consistency.get(k, []):
                ev = " | ".join(item.get("evidence", []))
                self._lists["consistency"].addItem(f"[{item.get('severity')}] {item.get('issue')}\n  Evidence: {ev}\n  Recommend: {item.get('recommendation')}")

    def clear(self) -> None:
        for lbl in self._count_labels.values():
            lbl.setText("0")
        for lw in self._lists.values():
            lw.clear()
