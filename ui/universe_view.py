"""
universe_view.py

View panel for displaying Multi-Story Universe data.
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
    QPushButton,
    QHBoxLayout,
    QInputDialog,
    QComboBox,
    QMessageBox
)

from services.universe_engine import UniverseEngine
from core.story_manager import StoryManager

class UniverseView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = UniverseEngine()
        self.story_manager = StoryManager()
        self._current_universe_id = None
        
        self._count_labels: dict[str, QLabel] = {}
        self._lists: dict[str, QListWidget] = {}
        self._build_ui()
        self.refresh_universe_list()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Controls Header
        ctrl_layout = QHBoxLayout()
        self._combo_universes = QComboBox()
        self._combo_universes.currentIndexChanged.connect(self._on_universe_selected)
        
        self._btn_create = QPushButton("Create Universe")
        self._btn_create.clicked.connect(self._on_create)
        
        self._btn_delete = QPushButton("Delete Universe")
        self._btn_delete.clicked.connect(self._on_delete)
        
        self._btn_add_story = QPushButton("Add Story")
        self._btn_add_story.clicked.connect(self._on_add_story)
        
        ctrl_layout.addWidget(QLabel("Select Universe:"))
        ctrl_layout.addWidget(self._combo_universes, stretch=1)
        ctrl_layout.addWidget(self._btn_create)
        ctrl_layout.addWidget(self._btn_delete)
        ctrl_layout.addWidget(self._btn_add_story)
        
        main_layout.addLayout(ctrl_layout)

        # Stats Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        grid = QGridLayout()
        grid.setSpacing(16)
        
        categories = [
            ("stories", "📚", "Stories", 0, 0),
            ("characters", "👥", "Shared Characters", 0, 1),
            ("locations", "🗺️", "Shared Locations", 0, 2),
            ("conflicts", "⚠️", "Conflicts", 1, 0),
            ("timeline", "⏱️", "Timeline Events", 1, 1)
        ]
        
        for key, icon, label, row, col in categories:
            card = self._create_stat_card(key, icon, label)
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid)
        
        # Tabs for details
        self._tabs = QTabWidget()
        list_categories = ["Stories", "Shared Characters", "Conflicts", "Timeline"]
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

    def refresh_universe_list(self):
        self._combo_universes.blockSignals(True)
        self._combo_universes.clear()
        univs = self.engine.list_universes()
        if not univs:
            self._combo_universes.addItem("No Universes Found", None)
            self._current_universe_id = None
            self.clear()
        else:
            for u in univs:
                self._combo_universes.addItem(u["name"], u["universe_id"])
            if self._current_universe_id:
                idx = self._combo_universes.findData(self._current_universe_id)
                if idx >= 0:
                    self._combo_universes.setCurrentIndex(idx)
                else:
                    self._combo_universes.setCurrentIndex(0)
            else:
                self._combo_universes.setCurrentIndex(0)
        self._combo_universes.blockSignals(False)
        self._on_universe_selected()

    def _on_universe_selected(self):
        uid = self._combo_universes.currentData()
        if not uid:
            self.clear()
            return
        self._current_universe_id = uid
        self.load_data(uid)

    def _on_create(self):
        name, ok = QInputDialog.getText(self, "Create Universe", "Universe Name:")
        if ok and name.strip():
            u = self.engine.create_universe(name.strip())
            self._current_universe_id = u["universe_id"]
            self.refresh_universe_list()

    def _on_delete(self):
        if not self._current_universe_id: return
        self.engine.delete_universe(self._current_universe_id)
        self._current_universe_id = None
        self.refresh_universe_list()

    def _on_add_story(self):
        if not self._current_universe_id: return
        stories = self.story_manager.list_stories()
        if not stories:
            QMessageBox.warning(self, "No Stories", "No stories available to add.")
            return
            
        items = [s.title for s in stories]
        title, ok = QInputDialog.getItem(self, "Add Story", "Select Story:", items, 0, False)
        if ok and title:
            sid = next(s.id for s in stories if s.title == title)
            self.engine.add_story(self._current_universe_id, sid)
            self.load_data(self._current_universe_id)

    def load_data(self, universe_id: str) -> None:
        try:
            data = self.engine.load_universe(universe_id)
        except FileNotFoundError:
            self.clear()
            return

        meta = data["metadata"]
        mem = data["memory"]
        rels = data["relationships"]
        timeline = data["timeline"]

        self._count_labels["stories"].setText(str(len(meta.get("stories", []))))
        self._count_labels["characters"].setText(str(len(rels.get("cross_story_links", []))))
        
        # approximate shared locations
        locs = mem.get("locations", [])
        shared_locs = len(locs) # Simplification for view
        self._count_labels["locations"].setText(str(shared_locs))
        
        self._count_labels["conflicts"].setText(str(len(rels.get("universe_conflicts", []))))
        self._count_labels["timeline"].setText(str(len(timeline.get("timeline_entries", []))))
            
        self._lists["stories"].clear()
        for sid in meta.get("stories", []):
            try:
                story_obj = self.story_manager._find_story_by_id(sid)
                if story_obj:
                    self._lists["stories"].addItem(story_obj.title)
            except Exception:
                pass
                
        self._lists["shared characters"].clear()
        for c in rels.get("cross_story_links", []):
            self._lists["shared characters"].addItem(f"{c['entity']} ({', '.join(c['appears_in'])})")
            
        self._lists["conflicts"].clear()
        for conf in rels.get("universe_conflicts", []):
            self._lists["conflicts"].addItem(conf)
            
        self._lists["timeline"].clear()
        for ev in timeline.get("timeline_entries", []):
            name = ev.get("name", "Unknown Event")
            src = ev.get("source_story", "Unknown")
            self._lists["timeline"].addItem(f"{name} [{src}]")

    def clear(self) -> None:
        for lbl in self._count_labels.values():
            lbl.setText("0")
        for lw in self._lists.values():
            lw.clear()
