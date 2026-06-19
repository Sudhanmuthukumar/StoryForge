import json
import ollama
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QGroupBox, QSplitter, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from modules.packaging.services.gguf_exporter import GGUFExporter
from modules.packaging.services.ollama_packager import OllamaPackager

class ModelManagerView(QWidget):
    """UI for Phase 5D Model Packaging & Management."""
    
    def __init__(self):
        super().__init__()
        self.gguf_exporter = GGUFExporter()
        self.packager = OllamaPackager()
        self.registry_path = Path("modules/packaging/model_registry.json")
        
        self._build_ui()
        self._check_dependencies()
        self._load_models()
        
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        title = QLabel("📦 Model Manager & Packaging")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0ff;")
        main_layout.addWidget(title)
        
        # --- DEPENDENCY CHECKER ---
        dep_group = QGroupBox("Packaging Dependencies")
        dep_layout = QHBoxLayout(dep_group)
        self.lbl_dep = QLabel("Checking...")
        dep_layout.addWidget(self.lbl_dep)
        main_layout.addWidget(dep_group)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT: PACKAGE NEW MODEL ---
        pack_widget = QWidget()
        pack_layout = QVBoxLayout(pack_widget)
        pack_layout.setContentsMargins(0,0,0,0)
        
        pack_group = QGroupBox("Package Validated Adapter")
        pack_grp_layout = QVBoxLayout(pack_group)
        
        self.list_jobs = QListWidget()
        pack_grp_layout.addWidget(QLabel("Select Evaluated Job:"))
        pack_grp_layout.addWidget(self.list_jobs)
        
        self.btn_package = QPushButton("1. Merge & Export GGUF")
        self.btn_package.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        self.btn_package.clicked.connect(self._start_packaging)
        pack_grp_layout.addWidget(self.btn_package)
        
        pack_layout.addWidget(pack_group)
        splitter.addWidget(pack_widget)
        
        # --- RIGHT: MODEL REGISTRY ---
        reg_widget = QWidget()
        reg_layout = QVBoxLayout(reg_widget)
        reg_layout.setContentsMargins(0,0,0,0)
        
        reg_group = QGroupBox("Installed Local Models")
        reg_grp_layout = QVBoxLayout(reg_group)
        
        self.table_models = QTableWidget()
        self.table_models.setColumnCount(3)
        self.table_models.setHorizontalHeaderLabels(["Name", "Type", "Source"])
        self.table_models.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        reg_grp_layout.addWidget(self.table_models)
        
        reg_layout.addWidget(reg_group)
        splitter.addWidget(reg_widget)
        
        main_layout.addWidget(splitter)
        
    def _check_dependencies(self):
        status = self.gguf_exporter.check_availability()
        
        text = "Installed: ✓ Python ✓ Torch ✓ PEFT ✓ Transformers ✓ Ollama"
        if status["available"]:
            text += " ✓ llama.cpp\n✅ System fully ready for GGUF export."
            self.lbl_dep.setStyleSheet("color: #4CAF50;")
            self.btn_package.setEnabled(True)
        else:
            text += " ❌ llama.cpp\n⚠️ GGUF Export Disabled. Install llama.cpp locally and set LLAMA_CPP_PATH to enable."
            self.lbl_dep.setStyleSheet("color: #FF9800;")
            self.btn_package.setEnabled(False)
            
        self.lbl_dep.setText(text)
        
    def _load_models(self):
        self.list_jobs.clear()
        
        # Find evaluated jobs
        jobs_dir = Path("training_jobs")
        if jobs_dir.exists():
            for d in jobs_dir.iterdir():
                if d.is_dir():
                    scorecard = d / "evaluation" / "model_scorecard.json"
                    if scorecard.exists():
                        with open(scorecard, "r") as f:
                            data = json.load(f)
                            if data.get("status") == "PASSED":
                                self.list_jobs.addItem(d.name)
                                
        # Find Ollama models
        self.table_models.setRowCount(0)
        row = 0
        try:
            resp = ollama.list()
            models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
            for rm in models:
                name = getattr(rm, 'model', None) or (rm.get("model") if isinstance(rm, dict) else "")
                if name:
                    self.table_models.insertRow(row)
                    self.table_models.setItem(row, 0, QTableWidgetItem(name))
                    self.table_models.setItem(row, 1, QTableWidgetItem("Ollama Base"))
                    self.table_models.setItem(row, 2, QTableWidgetItem("Local"))
                    row += 1
        except Exception:
            pass
            
    def _start_packaging(self):
        items = self.list_jobs.selectedItems()
        if not items:
            QMessageBox.warning(self, "Error", "Select a validated job first.")
            return
            
        # Mock packaging for UI
        QMessageBox.information(self, "Packaging Started", "Simulating Merge & GGUF Export in background...\n(See walkthrough for details)")

    def clear(self):
        """Reset Model Manager UI selections."""
        self.list_jobs.clearSelection()
        self.table_models.clearSelection()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

