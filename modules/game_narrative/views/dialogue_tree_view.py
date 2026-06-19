import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from modules.game_narrative.services.game_narrative_generator import GameNarrativeGenerator
from modules.unreal_export.services.unreal_exporter import UnrealExporter

class DialogueTreeView(QWidget):
    """UI View for Dialogue Tree Builder (Priority 2)."""
    
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
        title = QLabel("💬 Dialogue Tree Builder")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Setup Group
        setup_group = QGroupBox("Dialogue Tree Parameters")
        setup_layout = QVBoxLayout(setup_group)
        
        h_inputs = QHBoxLayout()
        h_inputs.addWidget(QLabel("NPC Name / Concept:"))
        self.txt_npc = QLineEdit()
        self.txt_npc.setPlaceholderText("e.g. Eldrin, Town Guard, Blacksmith...")
        h_inputs.addWidget(self.txt_npc)
        
        h_inputs.addWidget(QLabel("Conversation Topic:"))
        self.txt_topic = QLineEdit()
        self.txt_topic.setPlaceholderText("e.g. Ask about the stolen relics, trade...")
        h_inputs.addWidget(self.txt_topic)
        setup_layout.addLayout(h_inputs)
        
        h_config = QHBoxLayout()
        h_config.addWidget(QLabel("Dialogue Tone:"))
        self.combo_tone = QComboBox()
        self.combo_tone.addItems(["Neutral", "Friendly", "Hostile", "Sneaky", "Terrified", "Cryptic"])
        h_config.addWidget(self.combo_tone)
        
        h_config.addWidget(QLabel("Dialogue Style Pattern:"))
        self.combo_pattern = QComboBox()
        h_config.addWidget(self.combo_pattern)
        setup_layout.addLayout(h_config)
        
        self.btn_generate = QPushButton("▶ Generate Dialogue Tree")
        self.btn_generate.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._generate_dialogue)
        setup_layout.addWidget(self.btn_generate)
        
        layout.addWidget(setup_group)
        
        # Main Splitter for Visual vs JSON
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Visual Tree Preview
        vis_group = QGroupBox("Branching Visual Tree")
        vis_layout = QVBoxLayout(vis_group)
        self.tree_preview = QTreeWidget()
        self.tree_preview.setHeaderLabel("Dialogue Flow Paths")
        self.tree_preview.setStyleSheet("background: #15152a; color: #d0d0e8;")
        vis_layout.addWidget(self.tree_preview)
        splitter.addWidget(vis_group)
        
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
        self.combo_pattern.addItem("Standard Interactive Dialogue", None)
        try:
            patterns = self.generator.db.read_db("dialogue_patterns.json")
            for p in patterns:
                self.combo_pattern.addItem(f"{p.get('name')} (Success: {p.get('success_score', 5.0):.1f})", p.get("id"))
        except Exception:
            pass

    def _generate_dialogue(self):
        npc = self.txt_npc.text().strip()
        topic = self.txt_topic.text().strip()
        if not npc or not topic:
            QMessageBox.warning(self, "Validation Error", "Please provide NPC Name and Conversation Topic.")
            return
            
        pattern_id = self.combo_pattern.currentData()
        tone = self.combo_tone.currentText()
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Generating...")
        self.txt_display.setText("Generating branching dialogue and choice nodes...")
        self.tree_preview.clear()
        
        try:
            dialogue_data = self.generator.generate_dialogue_tree(npc, topic, tone, pattern_id)
            self.current_data = dialogue_data
            self.txt_display.setText(json.dumps(dialogue_data, indent=4))
            self._populate_tree_preview(dialogue_data)
            self.btn_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate dialogue tree: {str(e)}")
            self.txt_display.clear()
            self.btn_export.setEnabled(False)
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("▶ Generate Dialogue Tree")

    def _populate_tree_preview(self, data):
        self.tree_preview.clear()
        nodes = data.get("nodes", [])
        if not nodes:
            return
            
        # Map node_id -> QTreeWidgetItem
        node_items = {}
        for n in nodes:
            node_id = n.get("node_id")
            speaker = n.get("speaker")
            text = n.get("text")
            
            item = QTreeWidgetItem()
            item.setText(0, f"[{node_id}] {speaker}: \"{text}\"")
            node_items[node_id] = (item, n.get("choices", []))
            self.tree_preview.addTopLevelItem(item)
            
        # Nest choices
        for node_id, (item, choices) in node_items.items():
            for c in choices:
                target = c.get("target_node_id")
                choice_text = c.get("text")
                cond = c.get("condition")
                conseq = c.get("consequence")
                
                info = f"Choice: \"{choice_text}\" -> leads to [{target}]"
                if cond: info += f" (Req: {cond})"
                if conseq: info += f" (Outcome: {conseq})"
                
                choice_item = QTreeWidgetItem(item)
                choice_item.setText(0, info)
                choice_item.setExpanded(True)
                
            item.setExpanded(True)

    def _export_asset(self):
        if not self.current_data:
            return
            
        fmt = self.combo_format.currentText()
        ext = "csv" if fmt == "CSV" else "json"
        
        default_dir = Path("exports/unreal")
        default_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dialogue Export", 
            str(default_dir / f"dialogue_tree.{ext}"), 
            f"Asset (*.{ext})"
        )
        
        if file_path:
            try:
                self.exporter.export_dialogue(self.current_data, fmt, Path(file_path))
                QMessageBox.information(self, "Success", f"Dialogue exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export asset: {str(e)}")

    def clear(self):
        self.txt_npc.clear()
        self.txt_topic.clear()
        self.combo_tone.setCurrentIndex(0)
        if self.combo_pattern.count() > 0:
            self.combo_pattern.setCurrentIndex(0)
        self.txt_display.clear()
        self.tree_preview.clear()
        self.current_data = None
        self.btn_export.setEnabled(False)
