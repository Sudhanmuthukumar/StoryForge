"""
graph_view.py

View panel for displaying Graph Engine data textually.
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
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton
)

from services.graph_engine import GraphEngine
from services.universe_engine import UniverseEngine

class GraphView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.graph_engine = GraphEngine()
        self.universe_engine = UniverseEngine()
        self._current_universe_id = None
        self._current_graph = {}
        
        self._count_labels: dict[str, QLabel] = {}
        self._lists: dict[str, QListWidget] = {}
        self._build_ui()
        self.refresh_universe_list()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Header
        ctrl_layout = QHBoxLayout()
        self._combo_universes = QComboBox()
        self._combo_universes.currentIndexChanged.connect(self._on_universe_selected)
        
        ctrl_layout.addWidget(QLabel("Select Universe:"))
        ctrl_layout.addWidget(self._combo_universes, stretch=1)
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
            ("nodes", "🟢", "Total Nodes", 0, 0),
            ("edges", "🔗", "Total Edges", 0, 1),
            ("components", "🧩", "Connected Components", 1, 0),
            ("orphans", "🌀", "Orphan Nodes", 1, 1)
        ]
        
        for key, icon, label, row, col in categories:
            card = self._create_stat_card(key, icon, label)
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid)
        
        # Tools: Search, Neighbors, Component
        tools_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Enter exact Node Name...")
        
        btn_neighbors = QPushButton("Get Neighbors")
        btn_neighbors.clicked.connect(self._on_get_neighbors)
        
        btn_component = QPushButton("Get Connected Component")
        btn_component.clicked.connect(self._on_get_component)
        
        tools_layout.addWidget(self._search_input)
        tools_layout.addWidget(btn_neighbors)
        tools_layout.addWidget(btn_component)
        layout.addLayout(tools_layout)
        
        # Output List
        self._output_list = QListWidget()
        layout.addWidget(QLabel("Explorer Output:"))
        layout.addWidget(self._output_list, stretch=1)
        
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
        univs = self.universe_engine.list_universes()
        if not univs:
            self._combo_universes.addItem("No Universes Found", None)
            self._current_universe_id = None
            self.clear()
        else:
            for u in univs:
                self._combo_universes.addItem(u["name"], u["universe_id"])
            self._combo_universes.setCurrentIndex(0)
            self._current_universe_id = self._combo_universes.currentData()
        self._combo_universes.blockSignals(False)
        self._on_universe_selected()

    def _on_universe_selected(self):
        uid = self._combo_universes.currentData()
        if not uid:
            self.clear()
            return
        self._current_universe_id = uid
        self.load_data(uid)

    def load_data(self, universe_id: str) -> None:
        try:
            self._current_graph = self.graph_engine.load_graph(universe_id)
        except FileNotFoundError:
            self.clear()
            return

        stats = self._current_graph.get("statistics", {})
        self._count_labels["nodes"].setText(str(stats.get("node_count", 0)))
        self._count_labels["edges"].setText(str(stats.get("edge_count", 0)))
        self._count_labels["components"].setText(str(stats.get("connected_components", 0)))
        self._count_labels["orphans"].setText(str(stats.get("orphan_nodes", 0)))
        self._output_list.clear()
        
        # Display all nodes by default
        for n in self._current_graph.get("nodes", []):
            self._output_list.addItem(f"Node: {n['name']} ({n['type']})")
        for e in self._current_graph.get("edges", []):
            if e["relationship"] in ["same_entity", "conflicts_with"]:
                self._output_list.addItem(f"Special Edge: {e['source']} [{e['relationship']}] {e['target']}")

    def _find_node_id(self, name: str) -> str | None:
        for n in self._current_graph.get("nodes", []):
            if n["name"].lower() == name.lower():
                return n["id"]
        return None

    def _on_get_neighbors(self):
        name = self._search_input.text().strip()
        if not name: return
        nid = self._find_node_id(name)
        self._output_list.clear()
        if not nid:
            self._output_list.addItem("Node not found.")
            return
            
        neighbors = self.graph_engine.get_neighbors(self._current_graph, nid)
        self._output_list.addItem(f"Neighbors for '{name}':")
        for n in neighbors:
            self._output_list.addItem(f"  - {n['name']} ({n['type']})")

    def _on_get_component(self):
        name = self._search_input.text().strip()
        if not name: return
        nid = self._find_node_id(name)
        self._output_list.clear()
        if not nid:
            self._output_list.addItem("Node not found.")
            return
            
        comp = self.graph_engine.get_connected_component(self._current_graph, nid)
        self._output_list.addItem(f"Connected Component for '{name}':")
        for n in comp:
            self._output_list.addItem(f"  - {n['name']} ({n['type']})")

    def clear(self) -> None:
        for lbl in self._count_labels.values():
            lbl.setText("0")
        self._output_list.clear()
        self._current_graph = {}
