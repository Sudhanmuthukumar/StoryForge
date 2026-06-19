import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QGroupBox, QMessageBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, QSplitter
)
from PySide6.QtCore import Qt

from modules.world_simulation.services.simulation_engine import SimulationEngine

class WorldSimulationView(QWidget):
    """UI View for the World Simulation Engine (Phase 12)."""
    
    def __init__(self):
        super().__init__()
        self.engine = SimulationEngine()
        self._build_ui()
        self.refresh_all()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Title
        title = QLabel("🌍 World Simulation Studio")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Sub Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("simulationTabs")
        
        # 1. Overview Tab
        self.overview_tab = QWidget()
        self._build_overview_tab()
        self.tabs.addTab(self.overview_tab, "🗺️ Overview")
        
        # 2. NPC Memories Tab
        self.memories_tab = QWidget()
        self._build_memories_tab()
        self.tabs.addTab(self.memories_tab, "🧠 NPC Memories")
        
        # 3. Reputation Tab
        self.reputation_tab = QWidget()
        self._build_reputation_tab()
        self.tabs.addTab(self.reputation_tab, "🤝 Factions & Standing")
        
        # 4. Analytics Tab
        self.analytics_tab = QWidget()
        self._build_analytics_tab()
        self.tabs.addTab(self.analytics_tab, "📈 Analytics")
        
        layout.addWidget(self.tabs)
        
    def _build_overview_tab(self):
        layout = QHBoxLayout(self.overview_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: Status and Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Kingdom Status
        status_group = QGroupBox("Kingdom Status")
        status_layout = QVBoxLayout(status_group)
        self.lbl_kingdom = QLabel("Kingdom Name: Eldoria")
        self.lbl_ruler = QLabel("Ruler: King Doran")
        self.lbl_stability = QLabel("Stability: 100/100")
        self.lbl_wealth = QLabel("Treasury: 1000 gold")
        self.lbl_defense = QLabel("Defense: 50/100")
        
        for lbl in [self.lbl_kingdom, self.lbl_ruler, self.lbl_stability, self.lbl_wealth, self.lbl_defense]:
            lbl.setStyleSheet("color: #d0d0e8; font-size: 13px; padding: 2px;")
            status_layout.addWidget(lbl)
        left_layout.addWidget(status_group)
        
        # Simulation Controls
        controls_group = QGroupBox("Simulation Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        self.btn_populate = QPushButton("📥 Import Generated NPCs")
        self.btn_populate.setStyleSheet("background-color: #2a2a4a; color: #e0e0ff; font-weight: bold; padding: 8px;")
        self.btn_populate.clicked.connect(self._populate_npcs)
        controls_layout.addWidget(self.btn_populate)
        
        self.btn_tick_day = QPushButton("☀ Tick Day (Daily Progress)")
        self.btn_tick_day.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_tick_day.clicked.connect(self._tick_day)
        controls_layout.addWidget(self.btn_tick_day)
        
        self.btn_tick_week = QPushButton("📅 Tick Week (Faction Actions)")
        self.btn_tick_week.setStyleSheet("background-color: #b33939; color: white; font-weight: bold; padding: 8px;")
        self.btn_tick_week.clicked.connect(self._tick_week)
        controls_layout.addWidget(self.btn_tick_week)
        
        left_layout.addWidget(controls_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # Right Panel: Event History Logs
        log_group = QGroupBox("Chronological Event History Log")
        log_layout = QVBoxLayout(log_group)
        self.txt_history = QTextEdit()
        self.txt_history.setReadOnly(True)
        self.txt_history.setStyleSheet("background: #15152a; color: #a0a0c0; font-family: monospace;")
        log_layout.addWidget(self.txt_history)
        
        splitter.addWidget(log_group)
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)
        
    def _build_memories_tab(self):
        layout = QVBoxLayout(self.memories_tab)
        
        h_combo = QHBoxLayout()
        h_combo.addWidget(QLabel("Select Character:"))
        self.combo_npcs = QComboBox()
        self.combo_npcs.currentIndexChanged.connect(self._load_npc_memories)
        h_combo.addWidget(self.combo_npcs)
        h_combo.addStretch()
        layout.addLayout(h_combo)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Memory tree list
        tree_group = QGroupBox("NPC Cognitive Memory & Standing")
        tree_layout = QVBoxLayout(tree_group)
        self.mem_tree = QTreeWidget()
        self.mem_tree.setHeaderLabel("Memory Attributes")
        self.mem_tree.setStyleSheet("background: #15152a; color: #d0d0e8;")
        tree_layout.addWidget(self.mem_tree)
        splitter.addWidget(tree_group)
        
        # Interactions log
        inter_group = QGroupBox("Interactions History")
        inter_layout = QVBoxLayout(inter_group)
        self.txt_interactions = QTextEdit()
        self.txt_interactions.setReadOnly(True)
        self.txt_interactions.setStyleSheet("background: #15152a; color: #d0d0e8; font-family: monospace;")
        inter_layout.addWidget(self.txt_interactions)
        splitter.addWidget(inter_group)
        
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)
        
    def _build_reputation_tab(self):
        layout = QHBoxLayout(self.reputation_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Player Rep Table
        player_group = QGroupBox("Player Standing with Factions")
        player_layout = QVBoxLayout(player_group)
        self.table_player_rep = QTableWidget()
        self.table_player_rep.setColumnCount(2)
        self.table_player_rep.setHorizontalHeaderLabels(["Faction", "Reputation Score"])
        self.table_player_rep.horizontalHeader().setStretchLastSection(True)
        self.table_player_rep.setStyleSheet("background: #15152a; color: #d0d0e8;")
        player_layout.addWidget(self.table_player_rep)
        splitter.addWidget(player_group)
        
        # Faction Matrix Table
        matrix_group = QGroupBox("Inter-Faction Alliance Matrix")
        matrix_layout = QVBoxLayout(matrix_group)
        self.table_faction_matrix = QTableWidget()
        self.table_faction_matrix.setColumnCount(3)
        self.table_faction_matrix.setHorizontalHeaderLabels(["Faction A", "Faction B", "Relationship Score"])
        self.table_faction_matrix.horizontalHeader().setStretchLastSection(True)
        self.table_faction_matrix.setStyleSheet("background: #15152a; color: #d0d0e8;")
        matrix_layout.addWidget(self.table_faction_matrix)
        splitter.addWidget(matrix_group)
        
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)
        
    def _build_analytics_tab(self):
        layout = QVBoxLayout(self.analytics_tab)
        
        self.btn_compile = QPushButton("📈 Compile Simulation Report")
        self.btn_compile.setStyleSheet("background-color: #1a9a5a; color: white; font-weight: bold; padding: 10px;")
        self.btn_compile.clicked.connect(self._compile_report)
        layout.addWidget(self.btn_compile)
        
        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setStyleSheet("background: #101020; color: #e0e0ff; font-family: sans-serif; font-size: 12px;")
        layout.addWidget(self.txt_report)
        
    # ══════════════════════════════════════════════════════════════════
    #  GUI ACTIONS
    # ══════════════════════════════════════════════════════════════════
    
    def refresh_all(self):
        """Reload databases and refresh all visual UI controls."""
        self._refresh_kingdom_status()
        self._refresh_history_log()
        self._refresh_npc_combo()
        self._refresh_reputations()
        
    def _refresh_kingdom_status(self):
        try:
            world_state = self.engine.db.read_db("world_state.json")
            ks = world_state.get("kingdom_status", {})
            self.lbl_kingdom.setText(f"Kingdom Name: {ks.get('kingdom_name', 'Eldoria')}")
            self.lbl_ruler.setText(f"Ruler: {ks.get('ruler', 'King Doran')}")
            self.lbl_stability.setText(f"Stability: {ks.get('stability', 100)}/100")
            self.lbl_wealth.setText(f"Treasury: {ks.get('wealth', 1000)} gold")
            self.lbl_defense.setText(f"Defense: {ks.get('defense', 50)}/100")
        except Exception:
            pass
            
    def _refresh_history_log(self):
        try:
            history = self.engine.db.read_db("event_history.json")
            text = ""
            for log in reversed(history):
                text += f"[{log.get('timestamp')[:19]}] TICK {log.get('tick_index')}: {log.get('type')}\n"
                text += f"  {log.get('description')}\n"
                text += f"  Affected: {', '.join(log.get('affected_entities', []))}\n"
                text += "-" * 60 + "\n"
            self.txt_history.setText(text)
        except Exception:
            pass
            
    def _refresh_npc_combo(self):
        prev_idx = self.combo_npcs.currentIndex()
        prev_data = self.combo_npcs.currentData()
        
        self.combo_npcs.clear()
        try:
            npc_memories = self.engine.db.read_db("npc_memory.json")
            for nid, mem in npc_memories.items():
                self.combo_npcs.addItem(mem["name"], nid)
        except Exception:
            pass
            
        # Try to restore index
        if prev_data:
            idx = self.combo_npcs.findData(prev_data)
            if idx >= 0:
                self.combo_npcs.setCurrentIndex(idx)
        elif self.combo_npcs.count() > 0:
            self.combo_npcs.setCurrentIndex(0)
            
    def _load_npc_memories(self):
        nid = self.combo_npcs.currentData()
        self.mem_tree.clear()
        self.txt_interactions.clear()
        if not nid:
            return
            
        try:
            npc_memories = self.engine.db.read_db("npc_memory.json")
            mem = npc_memories.get(nid)
            if not mem:
                return
                
            # Trust & Standing
            p_rel = mem["relationships"].get("player", {})
            trust_item = QTreeWidgetItem()
            trust_item.setText(0, f"Player Trust Level: {p_rel.get('trust', 50)}/100")
            self.mem_tree.addTopLevelItem(trust_item)
            
            sent_item = QTreeWidgetItem()
            sent_item.setText(0, f"Player Sentiment Tier: {p_rel.get('sentiment', 'Neutral')}")
            self.mem_tree.addTopLevelItem(sent_item)
            
            # Faction Standings
            if mem.get("faction_standing"):
                fac_root = QTreeWidgetItem()
                fac_root.setText(0, "Faction Standings")
                for fac, val in mem["faction_standing"].items():
                    item = QTreeWidgetItem(fac_root)
                    item.setText(0, f"{fac}: {val}")
                self.mem_tree.addTopLevelItem(fac_root)
                fac_root.setExpanded(True)
                
            # Memories
            mem_root = QTreeWidgetItem()
            mem_root.setText(0, f"Memory Log ({len(mem.get('memories', []))} events remembered)")
            for m in mem.get("memories", []):
                item = QTreeWidgetItem(mem_root)
                item.setText(0, f"[{m.get('timestamp')[:16]}] {m.get('description')} ({m.get('emotional_impact')})")
            self.mem_tree.addTopLevelItem(mem_root)
            mem_root.setExpanded(True)
            
            # Populate Interactions list
            text = ""
            for idx, inter in enumerate(mem.get("interactions", [])):
                text += f"Interaction #{idx+1} ({inter.get('timestamp')[:19]})\n"
                text += f"  Topic: {inter.get('topic')}\n"
                text += f"  Player Choice: {inter.get('player_choice')}\n"
                text += f"  Outcome: {inter.get('outcome')}\n"
                text += "-" * 50 + "\n"
            if not text:
                text = "No player interactions logged for this character yet."
            self.txt_interactions.setText(text)
            
        except Exception as e:
            self.txt_interactions.setText(f"Error loading NPC data: {e}")
            
    def _refresh_reputations(self):
        try:
            reputation = self.engine.db.read_db("reputation.json")
            
            # 1. Player Table
            player_factions = reputation.get("player", {}).get("factions", {})
            self.table_player_rep.setRowCount(len(player_factions))
            for row, (fac, val) in enumerate(player_factions.items()):
                self.table_player_rep.setItem(row, 0, QTableWidgetItem(fac))
                self.table_player_rep.setItem(row, 1, QTableWidgetItem(f"{val:+}"))
                
            # 2. Factions Relations Matrix
            relations_list = []
            faction_relations = reputation.get("faction_relations", {})
            for facA, targets in faction_relations.items():
                for facB, val in targets.items():
                    # Deduplicate by alphabetical sorting
                    if facA < facB:
                        relations_list.append((facA, facB, val))
                        
            self.table_faction_matrix.setRowCount(len(relations_list))
            for row, (facA, facB, val) in enumerate(relations_list):
                self.table_faction_matrix.setItem(row, 0, QTableWidgetItem(facA))
                self.table_faction_matrix.setItem(row, 1, QTableWidgetItem(facB))
                self.table_faction_matrix.setItem(row, 2, QTableWidgetItem(f"{val:+}"))
                
        except Exception:
            pass
            
    def _populate_npcs(self):
        count = self.engine.populate_npc_memories_from_exports()
        if count > 0:
            QMessageBox.information(self, "Import Success", f"Successfully imported and seeded {count} NPC memory profiles from Phase 11.6 exported assets!")
            self.refresh_all()
        else:
            QMessageBox.warning(self, "No Exports Found", "Could not find any NPC exports inside exports/unreal/alpha_world/npcs/. Make sure the alpha world build is complete.")
            
    def _tick_day(self):
        desc = self.engine.tick_daily()
        QMessageBox.information(self, "Simulation Update", f"Simulation day progressed:\n{desc}")
        self.refresh_all()
        
    def _tick_week(self):
        desc = self.engine.tick_weekly()
        QMessageBox.information(self, "Simulation Update", f"Simulation week progressed!\nFaction Action: {desc}")
        self.refresh_all()
        
    def _compile_report(self):
        try:
            report_md = self.engine.generate_simulation_report()
            self.txt_report.setHtml(f"<pre style='font-family: monospace;'>{report_md}</pre>")
            QMessageBox.information(self, "Report Compiled", "Successfully compiled and saved simulation_report.md in the project root!")
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to compile simulation report: {e}")
            
    def clear(self):
        """Reset view state."""
        self.txt_history.clear()
        self.combo_npcs.clear()
        self.mem_tree.clear()
        self.txt_interactions.clear()
        self.table_player_rep.setRowCount(0)
        self.table_faction_matrix.setRowCount(0)
        self.txt_report.clear()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

