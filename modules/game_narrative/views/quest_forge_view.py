import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from modules.game_narrative.services.game_narrative_generator import GameNarrativeGenerator
from modules.unreal_export.services.unreal_exporter import UnrealExporter

class QuestForgeView(QWidget):
    """UI View for Quest Forge (Priority 3)."""
    
    def __init__(self, generator: GameNarrativeGenerator = None, exporter: UnrealExporter = None):
        super().__init__()
        self.generator = generator or GameNarrativeGenerator()
        self.exporter = exporter or UnrealExporter()
        self.current_data = None
        
        self._build_ui()
        self.refresh_patterns()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        title = QLabel("⚔️ Quest Forge")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Setup Group
        setup_group = QGroupBox("Quest Configuration")
        setup_layout = QVBoxLayout(setup_group)
        
        h_config = QHBoxLayout()
        h_config.addWidget(QLabel("Quest Type:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Main", "Side", "Faction", "Companion", "Random Event"])
        h_config.addWidget(self.combo_type)
        
        h_config.addWidget(QLabel("Conflict / Scene Pattern:"))
        self.combo_pattern = QComboBox()
        h_config.addWidget(self.combo_pattern)
        setup_layout.addLayout(h_config)
        
        self.btn_generate = QPushButton("▶ Forge Quest")
        self.btn_generate.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._generate_quest)
        setup_layout.addWidget(self.btn_generate)
        
        layout.addWidget(setup_group)
        
        # Splitter for Structure vs JSON
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Structured Quest Flow
        struct_group = QGroupBox("Quest Outline")
        struct_layout = QVBoxLayout(struct_group)
        self.quest_tree = QTreeWidget()
        self.quest_tree.setHeaderLabel("Quest Elements")
        self.quest_tree.setStyleSheet("background: #15152a; color: #d0d0e8;")
        struct_layout.addWidget(self.quest_tree)
        splitter.addWidget(struct_group)
        
        # Raw JSON Preview
        json_group = QGroupBox("Raw JSON Asset Preview")
        json_layout = QVBoxLayout(json_group)
        self.txt_display = QTextEdit()
        self.txt_display.setReadOnly(True)
        self.txt_display.setStyleSheet("background: #15152a; color: #d0d0e8; font-family: monospace;")
        json_layout.addWidget(self.txt_display)
        splitter.addWidget(json_group)
        
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)
        
        # Export Group
        export_group = QGroupBox("Unreal Engine Export")
        export_layout = QHBoxLayout(export_group)
        
        export_layout.addWidget(QLabel("Export Format:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["JSON", "UE_DataTable_JSON", "CSV"])
        export_layout.addWidget(self.combo_format)
        
        self.btn_export = QPushButton("📤 Export Asset")
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #1a9a5a; color: white; font-weight: bold; padding: 6px;")
        self.btn_export.clicked.connect(self._export_asset)
        export_layout.addWidget(self.btn_export)
        
        layout.addWidget(export_group)

    def refresh_patterns(self):
        self.combo_pattern.clear()
        self.combo_pattern.addItem("Standard Heroic Conflict", None)
        try:
            # Combine conflict patterns and scene patterns
            db = self.generator.db
            patterns = db.read_db("conflict_patterns.json") + db.read_db("scene_patterns.json")
            for p in patterns:
                cat = p.get("category", "General")
                self.combo_pattern.addItem(f"[{cat}] {p.get('name')} (Success: {p.get('success_score', 5.0):.1f})", p.get("id"))
        except Exception:
            pass

    def _generate_quest(self):
        quest_type = self.combo_type.currentText()
        pattern_id = self.combo_pattern.currentData()
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Forging...")
        self.txt_display.setText("Generating quest details, objectives, rewards, and narrative outcomes...")
        self.quest_tree.clear()
        
        try:
            quest_data = self.generator.generate_quest(quest_type, pattern_id)
            self.current_data = quest_data
            self.txt_display.setText(json.dumps(quest_data, indent=4))
            self._populate_quest_tree(quest_data)
            self.btn_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to forge quest: {str(e)}")
            self.txt_display.clear()
            self.btn_export.setEnabled(False)
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("▶ Forge Quest")

    def _populate_quest_tree(self, data):
        self.quest_tree.clear()
        
        # Quest Header
        title_item = QTreeWidgetItem()
        title_item.setText(0, f"Title: {data.get('title')}")
        self.quest_tree.addTopLevelItem(title_item)
        
        desc_item = QTreeWidgetItem()
        desc_item.setText(0, f"Description: {data.get('description')}")
        self.quest_tree.addTopLevelItem(desc_item)
        
        type_item = QTreeWidgetItem()
        type_item.setText(0, f"Type: {data.get('quest_type')}")
        self.quest_tree.addTopLevelItem(type_item)
        
        # Objectives
        objs_root = QTreeWidgetItem()
        objs_root.setText(0, "Objectives")
        for obj in data.get("objectives", []):
            item = QTreeWidgetItem(objs_root)
            item.setText(0, f"[{obj.get('objective_id')}] {obj.get('description')} (Trigger: {obj.get('condition')})")
        self.quest_tree.addTopLevelItem(objs_root)
        objs_root.setExpanded(True)
        
        # Rewards
        rwds_root = QTreeWidgetItem()
        rwds_root.setText(0, "Rewards")
        for rwd in data.get("rewards", []):
            item = QTreeWidgetItem(rwds_root)
            item.setText(0, f"+{rwd.get('amount')} {rwd.get('reward_type')}")
        self.quest_tree.addTopLevelItem(rwds_root)
        rwds_root.setExpanded(True)
        
        # Outcomes
        otc_root = QTreeWidgetItem()
        otc_root.setText(0, "Narrative Outcomes")
        for otc in data.get("outcomes", []):
            item = QTreeWidgetItem(otc_root)
            item.setText(0, f"[{otc.get('outcome_id')}] {otc.get('description')}")
        self.quest_tree.addTopLevelItem(otc_root)
        otc_root.setExpanded(True)

    def _export_asset(self):
        if not self.current_data:
            return
            
        fmt = self.combo_format.currentText()
        ext = "csv" if fmt == "CSV" else "json"
        
        default_dir = Path("exports/unreal")
        default_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Quest Export", 
            str(default_dir / f"quest.{ext}"), 
            f"Asset (*.{ext})"
        )
        
        if file_path:
            try:
                self.exporter.export_quest(self.current_data, fmt, Path(file_path))
                QMessageBox.information(self, "Success", f"Quest exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export asset: {str(e)}")

    def clear(self):
        self.combo_type.setCurrentIndex(0)
        if self.combo_pattern.count() > 0:
            self.combo_pattern.setCurrentIndex(0)
        self.txt_display.clear()
        self.quest_tree.clear()
        self.current_data = None
        self.btn_export.setEnabled(False)
