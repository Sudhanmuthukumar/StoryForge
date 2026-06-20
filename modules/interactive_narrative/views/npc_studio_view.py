import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from modules.interactive_narrative.services.interactive_narrative_generator import InteractiveNarrativeGenerator
from modules.export_layer.services.data_exporter import DataExporter

class NPCStudioView(QWidget):
    """UI View for NPC Studio (Priority 4)."""
    
    def __init__(self, generator: InteractiveNarrativeGenerator = None, exporter: DataExporter = None):
        super().__init__()
        self.generator = generator or InteractiveNarrativeGenerator()
        self.exporter = exporter or DataExporter()
        self.current_data = None
        
        self._build_ui()
        self.refresh_patterns()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        title = QLabel("👤 NPC Studio")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Setup Group
        setup_group = QGroupBox("NPC Character Generator")
        setup_layout = QVBoxLayout(setup_group)
        
        h_config = QHBoxLayout()
        h_config.addWidget(QLabel("Character Pattern archetypes (from Knowledge Engine):"))
        self.combo_pattern = QComboBox()
        h_config.addWidget(self.combo_pattern)
        setup_layout.addLayout(h_config)
        
        self.btn_generate = QPushButton("▶ Generate NPC")
        self.btn_generate.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._generate_npc)
        setup_layout.addWidget(self.btn_generate)
        
        layout.addWidget(setup_group)
        
        # Splitter for Details vs JSON
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Character Sheet
        sheet_group = QGroupBox("RPG Character Sheet")
        sheet_layout = QVBoxLayout(sheet_group)
        self.sheet_tree = QTreeWidget()
        self.sheet_tree.setHeaderLabel("Character Attributes")
        self.sheet_tree.setStyleSheet("background: #15152a; color: #d0d0e8;")
        sheet_layout.addWidget(self.sheet_tree)
        splitter.addWidget(sheet_group)
        
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
        self.combo_pattern.addItem("Standard Heroic Archetype", None)
        try:
            patterns = self.generator.db.read_db("character_patterns.json")
            for p in patterns:
                self.combo_pattern.addItem(f"{p.get('name')} (Success: {p.get('success_score', 5.0):.1f})", p.get("id"))
        except Exception:
            pass

    def _generate_npc(self):
        pattern_id = self.combo_pattern.currentData()
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Generating...")
        self.txt_display.setText("Generating character attributes, motivations, secrets, and quest hooks...")
        self.sheet_tree.clear()
        
        try:
            npc_data = self.generator.generate_npc(pattern_id)
            self.current_data = npc_data
            self.txt_display.setText(json.dumps(npc_data, indent=4))
            self._populate_sheet(npc_data)
            self.btn_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate NPC: {str(e)}")
            self.txt_display.clear()
            self.btn_export.setEnabled(False)
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("▶ Generate NPC")

    def _populate_sheet(self, data):
        self.sheet_tree.clear()
        
        # Name & Archetype
        name_item = QTreeWidgetItem()
        name_item.setText(0, f"Name: {data.get('name')}")
        self.sheet_tree.addTopLevelItem(name_item)
        
        arch_item = QTreeWidgetItem()
        arch_item.setText(0, f"Archetype: {data.get('archetype')}")
        self.sheet_tree.addTopLevelItem(arch_item)
        
        faction_item = QTreeWidgetItem()
        faction_item.setText(0, f"Faction: {data.get('faction')}")
        self.sheet_tree.addTopLevelItem(faction_item)
        
        # Motivation & Secret
        mot_item = QTreeWidgetItem()
        mot_item.setText(0, f"Motivation: {data.get('motivation')}")
        self.sheet_tree.addTopLevelItem(mot_item)
        
        sec_item = QTreeWidgetItem()
        sec_item.setText(0, f"Secret: {data.get('secret')}")
        self.sheet_tree.addTopLevelItem(sec_item)
        
        style_item = QTreeWidgetItem()
        style_item.setText(0, f"Dialogue Style: {data.get('dialogue_style')}")
        self.sheet_tree.addTopLevelItem(style_item)
        
        # Relationships
        rels_root = QTreeWidgetItem()
        rels_root.setText(0, "Relationships")
        for rel in data.get("relationships", []):
            item = QTreeWidgetItem(rels_root)
            item.setText(0, f"To: {rel.get('target_npc')} ({rel.get('relation_type')}, Level: {rel.get('level')})")
        self.sheet_tree.addTopLevelItem(rels_root)
        rels_root.setExpanded(True)
        
        # Quest Hooks
        hooks_root = QTreeWidgetItem()
        hooks_root.setText(0, "Quest Hooks")
        for hook in data.get("quest_hooks", []):
            item = QTreeWidgetItem(hooks_root)
            item.setText(0, hook)
        self.sheet_tree.addTopLevelItem(hooks_root)
        hooks_root.setExpanded(True)

    def _export_asset(self):
        if not self.current_data:
            return
            
        fmt = self.combo_format.currentText()
        ext = "csv" if fmt == "CSV" else "json"
        
        default_dir = Path("exports/unreal")
        default_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save NPC Export", 
            str(default_dir / f"npc_{self.current_data.get('name').replace(' ', '_').lower()}.{ext}"), 
            f"Asset (*.{ext})"
        )
        
        if file_path:
            try:
                self.exporter.export_npc(self.current_data, fmt, Path(file_path))
                QMessageBox.information(self, "Success", f"NPC exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export asset: {str(e)}")

    def clear(self):
        if self.combo_pattern.count() > 0:
            self.combo_pattern.setCurrentIndex(0)
        self.txt_display.clear()
        self.sheet_tree.clear()
        self.current_data = None
        self.btn_export.setEnabled(False)
