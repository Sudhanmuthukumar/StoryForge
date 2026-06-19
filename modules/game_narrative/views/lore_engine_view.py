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

class LoreEngineView(QWidget):
    """UI View for Lore Engine (Priority 5)."""
    
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
        title = QLabel("🌍 Lore Engine")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Setup Group
        setup_group = QGroupBox("Lore Configurations")
        setup_layout = QVBoxLayout(setup_group)
        
        h_config = QHBoxLayout()
        h_config.addWidget(QLabel("Lore Category:"))
        self.combo_category = QComboBox()
        self.combo_category.addItems(["Kingdom", "Culture", "Religion", "Guild", "Historical Event"])
        h_config.addWidget(self.combo_category)
        
        h_config.addWidget(QLabel("Worldbuilding Pattern:"))
        self.combo_pattern = QComboBox()
        h_config.addWidget(self.combo_pattern)
        setup_layout.addLayout(h_config)
        
        self.btn_generate = QPushButton("▶ Generate Lore")
        self.btn_generate.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._generate_lore)
        setup_layout.addWidget(self.btn_generate)
        
        layout.addWidget(setup_group)
        
        # Splitter for Structure vs JSON
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Structured Lore Preview
        struct_group = QGroupBox("Lore Codex Structure")
        struct_layout = QVBoxLayout(struct_group)
        self.lore_tree = QTreeWidget()
        self.lore_tree.setHeaderLabel("Codex Chapters")
        self.lore_tree.setStyleSheet("background: #15152a; color: #d0d0e8;")
        struct_layout.addWidget(self.lore_tree)
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
        self.combo_pattern.addItem("Standard World History", None)
        try:
            patterns = self.generator.db.read_db("worldbuilding_patterns.json")
            for p in patterns:
                self.combo_pattern.addItem(f"{p.get('name')} (Success: {p.get('success_score', 5.0):.1f})", p.get("id"))
        except Exception:
            pass

    def _generate_lore(self):
        cat = self.combo_category.currentText()
        pattern_id = self.combo_pattern.currentData()
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Generating...")
        self.txt_display.setText("Generating world historical facts, timeline events, core beliefs, and figures...")
        self.lore_tree.clear()
        
        try:
            lore_data = self.generator.generate_lore(cat, pattern_id)
            self.current_data = lore_data
            self.txt_display.setText(json.dumps(lore_data, indent=4))
            self._populate_lore_tree(lore_data)
            self.btn_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate lore: {str(e)}")
            self.txt_display.clear()
            self.btn_export.setEnabled(False)
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("▶ Generate Lore")

    def _populate_lore_tree(self, data):
        self.lore_tree.clear()
        
        # Lore Codex Header
        name_item = QTreeWidgetItem()
        name_item.setText(0, f"Codex: {data.get('name')} ({data.get('category')})")
        self.lore_tree.addTopLevelItem(name_item)
        
        sum_item = QTreeWidgetItem()
        sum_item.setText(0, f"Summary: {data.get('summary')}")
        self.lore_tree.addTopLevelItem(sum_item)
        
        # Historical Events
        hist_root = QTreeWidgetItem()
        hist_root.setText(0, "Historical Timeline")
        for evt in data.get("historical_events", []):
            item = QTreeWidgetItem(hist_root)
            item.setText(0, f"{evt.get('date')}: {evt.get('event_name')} - {evt.get('description')}")
        self.lore_tree.addTopLevelItem(hist_root)
        hist_root.setExpanded(True)
        
        # Core Beliefs
        bel_root = QTreeWidgetItem()
        bel_root.setText(0, "Core Practices / Beliefs")
        for bel in data.get("core_beliefs", []):
            item = QTreeWidgetItem(bel_root)
            item.setText(0, bel)
        self.lore_tree.addTopLevelItem(bel_root)
        bel_root.setExpanded(True)
        
        # Key Figures
        fig_root = QTreeWidgetItem()
        fig_root.setText(0, "Key Figures & Leaders")
        for fig in data.get("key_figures", []):
            item = QTreeWidgetItem(fig_root)
            item.setText(0, f"{fig.get('name')} ({fig.get('role')}): {fig.get('description')}")
        self.lore_tree.addTopLevelItem(fig_root)
        fig_root.setExpanded(True)

    def _export_asset(self):
        if not self.current_data:
            return
            
        fmt = self.combo_format.currentText()
        ext = "csv" if fmt == "CSV" else "json"
        
        default_dir = Path("exports/unreal")
        default_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Lore Export", 
            str(default_dir / f"lore_{self.current_data.get('name').replace(' ', '_').lower()}.{ext}"), 
            f"Asset (*.{ext})"
        )
        
        if file_path:
            try:
                self.exporter.export_lore(self.current_data, fmt, Path(file_path))
                QMessageBox.information(self, "Success", f"Lore exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export asset: {str(e)}")

    def clear(self):
        self.combo_category.setCurrentIndex(0)
        if self.combo_pattern.count() > 0:
            self.combo_pattern.setCurrentIndex(0)
        self.txt_display.clear()
        self.lore_tree.clear()
        self.current_data = None
        self.btn_export.setEnabled(False)
