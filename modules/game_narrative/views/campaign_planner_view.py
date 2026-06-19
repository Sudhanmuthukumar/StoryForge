import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QSpinBox, QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from modules.game_narrative.services.game_narrative_generator import GameNarrativeGenerator
from modules.unreal_export.services.unreal_exporter import UnrealExporter

class CampaignPlannerView(QWidget):
    """UI View for Game Campaign Planner (Priority 1)."""
    
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
        title = QLabel("🗺️ Campaign Planner")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Setup Group
        setup_group = QGroupBox("Campaign Configuration")
        setup_layout = QVBoxLayout(setup_group)
        
        h_theme = QHBoxLayout()
        h_theme.addWidget(QLabel("Campaign Theme / Concept:"))
        self.txt_theme = QTextEdit()
        self.txt_theme.setPlaceholderText("e.g. Return of the ancient dragon, rebellion against the empire...")
        self.txt_theme.setMaximumHeight(60)
        h_theme.addWidget(self.txt_theme)
        setup_layout.addLayout(h_theme)
        
        h_config = QHBoxLayout()
        h_config.addWidget(QLabel("Number of Regions:"))
        self.spin_regions = QSpinBox()
        self.spin_regions.setRange(1, 10)
        self.spin_regions.setValue(3)
        h_config.addWidget(self.spin_regions)
        
        h_config.addWidget(QLabel("Pacing Pattern:"))
        self.combo_pattern = QComboBox()
        h_config.addWidget(self.combo_pattern)
        setup_layout.addLayout(h_config)
        
        self.btn_generate = QPushButton("▶ Generate Campaign Plan")
        self.btn_generate.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._generate_plan)
        setup_layout.addWidget(self.btn_generate)
        
        layout.addWidget(setup_group)
        
        # Display Group
        display_group = QGroupBox("Generated Campaign Plan")
        display_layout = QVBoxLayout(display_group)
        
        self.txt_display = QTextEdit()
        self.txt_display.setReadOnly(True)
        self.txt_display.setStyleSheet("background: #15152a; color: #d0d0e8; font-family: monospace;")
        display_layout.addWidget(self.txt_display)
        
        layout.addWidget(display_group)
        
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
        self.combo_pattern.addItem("Standard Pacing Structure", None)
        try:
            patterns = self.generator.db.read_db("pacing_patterns.json")
            for p in patterns:
                self.combo_pattern.addItem(f"{p.get('name')} (Success: {p.get('success_score', 5.0):.1f})", p.get("id"))
        except Exception:
            pass

    def _generate_plan(self):
        theme = self.txt_theme.toPlainText().strip()
        if not theme:
            QMessageBox.warning(self, "Validation Error", "Please provide a campaign theme.")
            return
            
        pattern_id = self.combo_pattern.currentData()
        region_count = self.spin_regions.value()
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Generating...")
        self.txt_display.setText("Synthesizing campaign plan using pacing patterns and Ollama...")
        
        try:
            campaign_data = self.generator.generate_campaign(theme, region_count, pattern_id)
            self.current_data = campaign_data
            self.txt_display.setText(json.dumps(campaign_data, indent=4))
            self.btn_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate campaign: {str(e)}")
            self.txt_display.clear()
            self.btn_export.setEnabled(False)
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("▶ Generate Campaign Plan")

    def _export_asset(self):
        if not self.current_data:
            return
            
        fmt = self.combo_format.currentText()
        ext = "csv" if fmt == "CSV" else "json"
        
        # Ensure default export dir exists
        default_dir = Path("exports/unreal")
        default_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Campaign Export", 
            str(default_dir / f"campaign_plan.{ext}"), 
            f"Asset (*.{ext})"
        )
        
        if file_path:
            try:
                self.exporter.export_campaign(self.current_data, fmt, Path(file_path))
                QMessageBox.information(self, "Success", f"Campaign exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export asset: {str(e)}")

    def clear(self):
        self.txt_theme.clear()
        self.spin_regions.setValue(3)
        if self.combo_pattern.count() > 0:
            self.combo_pattern.setCurrentIndex(0)
        self.txt_display.clear()
        self.current_data = None
        self.btn_export.setEnabled(False)
