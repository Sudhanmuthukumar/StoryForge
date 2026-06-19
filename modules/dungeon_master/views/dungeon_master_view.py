import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QGroupBox, QMessageBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QListWidget, QSplitter
)
from PySide6.QtCore import Qt

from modules.dungeon_master.services.dungeon_master_service import DungeonMasterService

class DungeonMasterView(QWidget):
    """UI View for the AI Dungeon Master Layer (Phase 13)."""
    
    def __init__(self):
        super().__init__()
        self.service = DungeonMasterService()
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Title
        title = QLabel("🏰 AI Dungeon Master Control")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #6c63ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Sub Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("dungeonMasterTabs")
        
        # 1. Director & Arcs Tab
        self.director_tab = QWidget()
        self._build_director_tab()
        self.tabs.addTab(self.director_tab, "🏰 Story Director")
        
        # 2. Quests Tab
        self.quests_tab = QWidget()
        self._build_quests_tab()
        self.tabs.addTab(self.quests_tab, "⚔️ Dynamic Quests")
        
        # 3. Rumors Tab
        self.rumors_tab = QWidget()
        self._build_rumors_tab()
        self.tabs.addTab(self.rumors_tab, "🍻 Tavern & News")
        
        layout.addWidget(self.tabs)

    def _build_director_tab(self):
        layout = QHBoxLayout(self.director_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: Controls and Campaign Progress
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        campaign_group = QGroupBox("Campaign Progress Tracker")
        campaign_layout = QVBoxLayout(campaign_group)
        self.lbl_campaign = QLabel("Active Campaign: campaign_01")
        self.lbl_arc = QLabel("Active Arc: act_01 (Arrival)")
        self.lbl_completed = QLabel("Completed Arcs: None")
        self.lbl_regions = QLabel("Active Regions: Shadowfen")
        
        for lbl in [self.lbl_campaign, self.lbl_arc, self.lbl_completed, self.lbl_regions]:
            lbl.setStyleSheet("color: #d0d0e8; font-size: 13px; padding: 2px;")
            campaign_layout.addWidget(lbl)
        left_layout.addWidget(campaign_group)
        
        # Controls
        controls_group = QGroupBox("Dungeon Master Actions")
        controls_layout = QVBoxLayout(controls_group)
        
        self.btn_run_dm = QPushButton("🏰 Trigger Dungeon Master Tick")
        self.btn_run_dm.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 10px; font-size: 13px;")
        self.btn_run_dm.clicked.connect(self._run_dm_tick)
        controls_layout.addWidget(self.btn_run_dm)
        
        left_layout.addWidget(controls_group)
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Right Panel: Narrative Director Output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        event_group = QGroupBox("Next Planned Major Event Beat")
        event_layout = QVBoxLayout(event_group)
        self.txt_next_event = QTextEdit()
        self.txt_next_event.setReadOnly(True)
        self.txt_next_event.setStyleSheet("background: #15152a; color: #e0e0ff; font-size: 13px;")
        event_layout.addWidget(self.txt_next_event)
        right_layout.addWidget(event_group)
        
        conflict_group = QGroupBox("Escalating Conflicts & Character Arcs")
        conflict_layout = QVBoxLayout(conflict_group)
        
        h_split = QSplitter(Qt.Orientation.Vertical)
        
        self.lst_conflicts = QListWidget()
        self.lst_conflicts.setStyleSheet("background: #15152a; color: #d0d0e8;")
        h_split.addWidget(self.lst_conflicts)
        
        self.tree_char_arcs = QTreeWidget()
        self.tree_char_arcs.setHeaderLabels(["Character / Faction", "Arc Development Beat"])
        self.tree_char_arcs.setStyleSheet("background: #15152a; color: #d0d0e8;")
        h_split.addWidget(self.tree_char_arcs)
        
        conflict_layout.addWidget(h_split)
        right_layout.addWidget(conflict_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

    def _build_quests_tab(self):
        layout = QVBoxLayout(self.quests_tab)
        
        h_combo = QHBoxLayout()
        h_combo.addWidget(QLabel("Select Generated Quest:"))
        self.combo_quests = QComboBox()
        self.combo_quests.currentIndexChanged.connect(self._load_quest_details)
        h_combo.addWidget(self.combo_quests)
        h_combo.addStretch()
        layout.addLayout(h_combo)
        
        # Quest details tree
        self.quest_tree = QTreeWidget()
        self.quest_tree.setHeaderLabels(["Quest Element", "Description / Values"])
        self.quest_tree.setStyleSheet("background: #15152a; color: #d0d0e8;")
        layout.addWidget(self.quest_tree)

    def _build_rumors_tab(self):
        layout = QHBoxLayout(self.rumors_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tavern Rumors
        rumor_group = QGroupBox("🍻 Heard in Local Taverns")
        rumor_layout = QVBoxLayout(rumor_group)
        self.tree_rumors = QTreeWidget()
        self.tree_rumors.setHeaderLabels(["Speaker / Location", "Rumor / Credibility"])
        self.tree_rumors.setStyleSheet("background: #15152a; color: #d0d0e8;")
        rumor_layout.addWidget(self.tree_rumors)
        splitter.addWidget(rumor_group)
        
        # Bulletins & Briefings
        bulletin_group = QGroupBox("📜 Proclamations & Faction Reports")
        bulletin_layout = QVBoxLayout(bulletin_group)
        self.tree_bulletins = QTreeWidget()
        self.tree_bulletins.setHeaderLabels(["Issuer / Faction", "News & Confidential Briefs"])
        self.tree_bulletins.setStyleSheet("background: #15152a; color: #d0d0e8;")
        bulletin_layout.addWidget(self.tree_bulletins)
        splitter.addWidget(bulletin_group)
        
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

    # ══════════════════════════════════════════════════════════════════
    #  GUI ACTIONS
    # ══════════════════════════════════════════════════════════════════
    
    def refresh_all(self):
        """Reload databases and update view components."""
        try:
            world_state = self.service.db.read_db("world_state.json")
            dm_data = world_state.get("dungeon_master", {})
            
            # 1. Update Campaign progress labels
            camp = world_state.get("campaign_progress", {})
            self.lbl_campaign.setText(f"Active Campaign: {camp.get('current_campaign_id', 'campaign_01')}")
            self.lbl_arc.setText(f"Active Arc: {camp.get('active_arc_id', 'act_01')}")
            self.lbl_completed.setText(f"Completed Arcs: {', '.join(camp.get('completed_arcs', [])) or 'None'}")
            self.lbl_regions.setText(f"Active Regions: {', '.join(camp.get('active_regions', [])) or 'None'}")
            
            # 2. Update narrative director
            plan = dm_data.get("narrative_plan", {})
            self.txt_next_event.setText(plan.get("next_event_detail", "No events planned yet. Trigger a Dungeon Master tick to begin."))
            
            # Update escalating conflicts
            self.lst_conflicts.clear()
            for conflict in plan.get("escalating_conflicts", []):
                self.lst_conflicts.addItem(conflict)
                
            # Update character arcs tree
            self.tree_char_arcs.clear()
            for char, arc in plan.get("character_arcs", {}).items():
                item = QTreeWidgetItem()
                item.setText(0, char)
                item.setText(1, arc)
                self.tree_char_arcs.addTopLevelItem(item)
                
            # 3. Update dynamic quests list
            self._refresh_quests_combo(dm_data.get("generated_quests", []))
            
            # 4. Update rumors tree
            self._refresh_rumors(dm_data.get("rumors", {}))
            
        except Exception:
            pass

    def _refresh_quests_combo(self, quests: list):
        prev_idx = self.combo_quests.currentIndex()
        prev_id = self.combo_quests.currentData()
        
        self.combo_quests.clear()
        for idx, q in enumerate(quests):
            self.combo_quests.addItem(q.get("title", "Unnamed Quest"), q.get("quest_id"))
            
        if prev_id:
            idx = self.combo_quests.findData(prev_id)
            if idx >= 0:
                self.combo_quests.setCurrentIndex(idx)
        elif self.combo_quests.count() > 0:
            self.combo_quests.setCurrentIndex(0)
        else:
            self.quest_tree.clear()

    def _load_quest_details(self):
        self.quest_tree.clear()
        quest_id = self.combo_quests.currentData()
        if not quest_id:
            return
            
        try:
            world_state = self.service.db.read_db("world_state.json")
            quests = world_state.get("dungeon_master", {}).get("generated_quests", [])
            
            target_q = None
            for q in quests:
                if q.get("quest_id") == quest_id:
                    target_q = q
                    break
                    
            if not target_q:
                return
                
            # Populate quest tree details
            # Metadata
            meta_item = QTreeWidgetItem()
            meta_item.setText(0, "Metadata")
            self.quest_tree.addTopLevelItem(meta_item)
            
            type_item = QTreeWidgetItem(meta_item)
            type_item.setText(0, "Quest Type")
            type_item.setText(1, target_q.get("quest_type", "Faction"))
            
            id_item = QTreeWidgetItem(meta_item)
            id_item.setText(0, "Quest ID")
            id_item.setText(1, target_q.get("quest_id", ""))
            
            desc_item = QTreeWidgetItem(meta_item)
            desc_item.setText(0, "Description")
            desc_item.setText(1, target_q.get("description", ""))
            
            meta_item.setExpanded(True)
            
            # Objectives
            obj_item = QTreeWidgetItem()
            obj_item.setText(0, f"Objectives ({len(target_q.get('objectives', []))})")
            for obj in target_q.get("objectives", []):
                child = QTreeWidgetItem(obj_item)
                child.setText(0, obj.get("objective_id", "obj"))
                child.setText(1, f"{obj.get('description', '')} (Condition: {obj.get('condition', '')})")
            self.quest_tree.addTopLevelItem(obj_item)
            obj_item.setExpanded(True)
            
            # Rewards
            rew_item = QTreeWidgetItem()
            rew_item.setText(0, f"Rewards ({len(target_q.get('rewards', []))})")
            for rew in target_q.get("rewards", []):
                child = QTreeWidgetItem(rew_item)
                child.setText(0, rew.get("reward_type", "Gold"))
                child.setText(1, rew.get("amount", "0"))
            self.quest_tree.addTopLevelItem(rew_item)
            rew_item.setExpanded(True)
            
            # Outcomes
            out_item = QTreeWidgetItem()
            out_item.setText(0, f"Outcomes ({len(target_q.get('outcomes', []))})")
            for out in target_q.get("outcomes", []):
                child = QTreeWidgetItem(out_item)
                child.setText(0, out.get("outcome_id", "outcome"))
                child.setText(1, out.get("description", ""))
            self.quest_tree.addTopLevelItem(out_item)
            out_item.setExpanded(True)
            
        except Exception:
            pass

    def _refresh_rumors(self, rumors: dict):
        self.tree_rumors.clear()
        self.tree_bulletins.clear()
        
        # Tavern Rumors
        for rum in rumors.get("tavern_rumors", []):
            item = QTreeWidgetItem()
            item.setText(0, f"{rum.get('speaker', 'Commoner')} ({rum.get('location', 'Tavern')})")
            item.setText(1, f"\"{rum.get('text', '')}\" [Credibility: {rum.get('credibility', 'Medium')}]")
            self.tree_rumors.addTopLevelItem(item)
            
        # Proclamations and Reports
        for bul in rumors.get("news_bulletins", []):
            item = QTreeWidgetItem()
            item.setText(0, f"📢 Announcement - {bul.get('issuer', 'Crown')}")
            item.setText(1, f"{bul.get('headline')}: {bul.get('body')}")
            self.tree_bulletins.addTopLevelItem(item)
            
        for rep in rumors.get("faction_reports", []):
            item = QTreeWidgetItem()
            item.setText(0, f"🔒 Briefing - {rep.get('faction')} ({rep.get('security_clearance', 'Confidential')})")
            item.setText(1, f"Subject: {rep.get('subject')}\n{rep.get('content')}")
            self.tree_bulletins.addTopLevelItem(item)

    def _run_dm_tick(self):
        try:
            res = self.service.run_dungeon_master_tick()
            QMessageBox.information(
                self, 
                "Dungeon Master Update", 
                f"Narrative campaign successfully updated!\n\n"
                f"- Consequence Engine processed {len(res.get('consequences', []))} consequences.\n"
                f"- Narrative Director planned next steps.\n"
                f"- Dungeon Master generated {len(res.get('generated_quests', []))} dynamic quests."
            )
            self.refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Tick Error", f"Dungeon Master tick failed: {e}")

    def clear(self):
        """Reset view state."""
        self.txt_next_event.clear()
        self.lst_conflicts.clear()
        self.tree_char_arcs.clear()
        self.combo_quests.clear()
        self.quest_tree.clear()
        self.tree_rumors.clear()
        self.tree_bulletins.clear()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

