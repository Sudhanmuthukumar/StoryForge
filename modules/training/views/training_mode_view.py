import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QListWidget, QGroupBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from modules.training.services.training_config import TrainingConfig
from modules.training.services.training_estimator import TrainingEstimator
from modules.training.services.training_dataset_builder import TrainingDatasetBuilder
from modules.training.services.training_queue import TrainingQueueManager
from modules.training.services.environment_validator import EnvironmentValidator

class TrainingModeView(QWidget):
    """UI View for Phase 5A Training Mode & LoRA Preparation."""
    
    def __init__(self):
        super().__init__()
        self.config_manager = TrainingConfig()
        self.estimator = TrainingEstimator()
        self.builder = TrainingDatasetBuilder()
        self.validator = EnvironmentValidator()
        self.queue_manager = TrainingQueueManager()
        self.queue_manager.queue_updated.connect(self._refresh_queue_table)
        self.queue_manager.start()
        
        self._build_ui()
        self._load_datasets()
        self._evaluate_readiness()
        self._refresh_queue_table()
        
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("🚀 Training Mode & LoRA Orchestrator")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        main_layout.addWidget(title)
        
        # --- DASHBOARD (READINESS) ---
        dash_group = QGroupBox("Training Readiness")
        dash_layout = QHBoxLayout(dash_group)
        self.lbl_readiness = QLabel("Readiness: CALCULATING...")
        self.lbl_readiness.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.lbl_health_details = QLabel("Examples: 0 | Health Score: 0")
        dash_layout.addWidget(self.lbl_readiness)
        dash_layout.addStretch()
        dash_layout.addWidget(self.lbl_health_details)
        main_layout.addWidget(dash_group)
        
        # --- ENVIRONMENT VALIDATION ---
        env_group = QGroupBox("Environment Validation")
        env_layout = QHBoxLayout(env_group)
        self.lbl_env_status = QLabel("Checking dependencies...")
        self.btn_install_deps = QPushButton("Install Dependencies")
        self.btn_install_deps.setVisible(False)
        self.btn_install_deps.clicked.connect(self._install_dependencies)
        
        env_layout.addWidget(self.lbl_env_status)
        env_layout.addStretch()
        env_layout.addWidget(self.btn_install_deps)
        main_layout.addWidget(env_group)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT: SETUP WIZARD ---
        setup_widget = QWidget()
        setup_layout = QVBoxLayout(setup_widget)
        setup_layout.setContentsMargins(0, 0, 0, 0)
        
        ds_group = QGroupBox("1. Select Dataset")
        ds_layout = QVBoxLayout(ds_group)
        self.list_datasets = QListWidget()
        self.list_datasets.setSelectionMode(QListWidget.MultiSelection)
        ds_layout.addWidget(self.list_datasets)
        setup_layout.addWidget(ds_group)
        
        cfg_group = QGroupBox("2. LoRA Configuration")
        cfg_layout = QVBoxLayout(cfg_group)
        
        # Model Selection
        h_model = QHBoxLayout()
        h_model.addWidget(QLabel("Base Model:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(self.config_manager.get_available_models())
        h_model.addWidget(self.combo_model)
        cfg_layout.addLayout(h_model)
        
        # Hyperparameters
        h_rank = QHBoxLayout()
        h_rank.addWidget(QLabel("Rank (r):"))
        self.spin_rank = QSpinBox()
        self.spin_rank.setRange(4, 256)
        self.spin_rank.setValue(16)
        h_rank.addWidget(self.spin_rank)
        cfg_layout.addLayout(h_rank)
        
        h_epochs = QHBoxLayout()
        h_epochs.addWidget(QLabel("Epochs:"))
        self.spin_epochs = QSpinBox()
        self.spin_epochs.setRange(1, 100)
        self.spin_epochs.setValue(3)
        h_epochs.addWidget(self.spin_epochs)
        cfg_layout.addLayout(h_epochs)
        
        h_batch = QHBoxLayout()
        h_batch.addWidget(QLabel("Batch Size:"))
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 32)
        self.spin_batch.setValue(2)
        h_batch.addWidget(self.spin_batch)
        cfg_layout.addLayout(h_batch)
        
        setup_layout.addWidget(cfg_group)
        
        est_group = QGroupBox("3. Training Estimates")
        est_layout = QVBoxLayout(est_group)
        self.btn_estimate = QPushButton("Calculate Estimates")
        self.btn_estimate.clicked.connect(self._calculate_estimates)
        est_layout.addWidget(self.btn_estimate)
        
        self.lbl_estimates = QLabel("VRAM: -- | RAM: -- | ETA: --\nFeasibility: --")
        est_layout.addWidget(self.lbl_estimates)
        setup_layout.addWidget(est_group)
        
        self.btn_create_job = QPushButton("Create & Queue Job")
        self.btn_create_job.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        self.btn_create_job.clicked.connect(self._create_job)
        setup_layout.addWidget(self.btn_create_job)
        
        splitter.addWidget(setup_widget)
        
        # --- RIGHT: QUEUE MONITOR ---
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        
        mon_group = QGroupBox("Training Queue Monitor")
        mon_grp_layout = QVBoxLayout(mon_group)
        
        self.table_jobs = QTableWidget()
        self.table_jobs.setColumnCount(4)
        self.table_jobs.setHorizontalHeaderLabels(["Job ID", "Status", "Progress", "Stage"])
        self.table_jobs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_jobs.setSelectionBehavior(QTableWidget.SelectRows)
        mon_grp_layout.addWidget(self.table_jobs)
        
        ctrl_h = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start Selected")
        self.btn_start.clicked.connect(self._start_job)
        self.btn_pause = QPushButton("⏸ Pause Selected")
        self.btn_pause.clicked.connect(self._pause_job)
        
        ctrl_h.addWidget(self.btn_start)
        ctrl_h.addWidget(self.btn_pause)
        mon_grp_layout.addLayout(ctrl_h)
        
        monitor_layout.addWidget(mon_group)
        splitter.addWidget(monitor_widget)
        
        main_layout.addWidget(splitter)
        
    def _load_datasets(self):
        self.list_datasets.clear()
        self.list_datasets.addItem("All Filtered Datasets")
        
        filtered_dir = Path("dataset_lab/training/filtered")
        if filtered_dir.exists():
            for f in filtered_dir.glob("*.jsonl"):
                name = f.stem.replace("_filtered", "").replace("_", " ").title()
                self.list_datasets.addItem(name)
                
    def _evaluate_readiness(self):
        # Count examples
        filtered_dir = Path("dataset_lab/training/filtered")
        total_examples = 0
        if filtered_dir.exists():
            for f in filtered_dir.glob("*.jsonl"):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        total_examples += sum(1 for _ in file)
                except Exception:
                    pass
                    
        # Load quality map
        qual_path = Path("dataset_lab/logs/quality_report.json")
        avg_q = 0.0
        if qual_path.exists():
            try:
                with open(qual_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data:
                        avg_q = sum(d.get("quality_score", 0) for d in data) / len(data)
            except Exception:
                pass
                
        self.lbl_health_details.setText(f"Examples: {total_examples} | Avg Quality: {avg_q:.2f}/10")
        
        # Logic
        if total_examples == 0:
            status = "NOT READY"
            color = "#F44336"
        elif total_examples < 50:
            status = "BASIC"
            color = "#FF9800"
        elif total_examples < 500:
            status = "GOOD"
            color = "#FFC107"
        elif total_examples < 2000:
            status = "READY FOR TRAINING"
            color = "#8BC34A"
        else:
            status = "HIGH QUALITY"
            color = "#4CAF50"
            
        self.lbl_readiness.setText(f"Readiness: {status}")
        self.lbl_readiness.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        
        # Validate Environment
        env_status = self.validator.check_environment()
        
        env_text = (
            f"GPU: {env_status['gpu']} | VRAM: {env_status['vram_gb']}GB | "
            f"RAM: {env_status['ram_gb']}GB | Disk: {env_status['disk_gb']}GB\n"
        )
        
        if env_status['training_ready']:
            env_text += "✅ System Ready for LoRA Training"
            self.lbl_env_status.setStyleSheet("color: #4CAF50;")
            self.btn_install_deps.setVisible(False)
        else:
            if env_status['missing_deps']:
                env_text += f"❌ Missing Packages: {', '.join(env_status['missing_deps'])}"
                self.btn_install_deps.setVisible(True)
            elif not env_status['cuda']:
                env_text += "❌ CUDA not available."
            else:
                env_text += "❌ Insufficient VRAM/Disk."
            self.lbl_env_status.setStyleSheet("color: #F44336;")
            
        self.lbl_env_status.setText(env_text)
        
    def _install_dependencies(self):
        # Notify user (in a real app this would pop a terminal window or run a subprocess with progress)
        QMessageBox.information(self, "Action Required", 
            "Please run this in your terminal:\npip install torch transformers peft trl accelerate datasets")
        
    def _calculate_estimates(self):
        items = self.list_datasets.selectedItems()
        if not items:
            self.lbl_estimates.setText("Please select a dataset first.")
            return
            
        # Rough example count mock
        total_ex = 100 * len(items) if "All" not in items[0].text() else 500
        
        config = {
            "rank": self.spin_rank.value(),
            "epochs": self.spin_epochs.value(),
            "batch_size": self.spin_batch.value()
        }
        model = self.combo_model.currentText()
        
        est = self.estimator.estimate(model, config, total_ex)
        text = (
            f"VRAM: {est['vram_gb']} GB | RAM: {est['ram_gb']} GB | ETA: {est['time_estimate']}\n"
            f"Feasibility: {est['feasibility']} (Confidence: {est['confidence']})"
        )
        self.lbl_estimates.setText(text)
        
    def _create_job(self):
        items = self.list_datasets.selectedItems()
        if not items:
            QMessageBox.warning(self, "Error", "No dataset selected.")
            return
            
        cats = [i.text() for i in items]
        config = {
            "model": self.combo_model.currentText(),
            "rank": self.spin_rank.value(),
            "epochs": self.spin_epochs.value(),
            "batch_size": self.spin_batch.value()
        }
        
        try:
            job_id = self.builder.build_job(cats, config)
            self.queue_manager.register_job(job_id)
            QMessageBox.information(self, "Success", f"Job {job_id} queued successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            
    def _refresh_queue_table(self):
        jobs = self.queue_manager.get_all_jobs()
        self.table_jobs.setRowCount(0)
        
        row = 0
        for j_id, state in jobs.items():
            self.table_jobs.insertRow(row)
            self.table_jobs.setItem(row, 0, QTableWidgetItem(j_id))
            self.table_jobs.setItem(row, 1, QTableWidgetItem(state["status"]))
            self.table_jobs.setItem(row, 2, QTableWidgetItem(f"{state['progress']}%"))
            self.table_jobs.setItem(row, 3, QTableWidgetItem(state["stage"]))
            row += 1
            
    def _start_job(self):
        sel = self.table_jobs.selectedItems()
        if not sel:
            return
        job_id = sel[0].text()
        self.queue_manager.update_job_state(job_id, "RUNNING", stage="Starting...")
        
    def _pause_job(self):
        sel = self.table_jobs.selectedItems()
        if not sel:
            return
        job_id = sel[0].text()
        self.queue_manager.update_job_state(job_id, "PAUSED", stage="Paused by User")

    def load_data(self, data=None):
        """Loads training profile or context data."""
        if data is None:
            return
        # Adapts the incoming data into the UI if necessary
        # For now, we simply refresh datasets and queue
        self._load_datasets()
        self._refresh_queue_table()

    def clear(self):
        """Safely reset setup wizard inputs and selections without affecting persisted jobs on disk."""
        self.list_datasets.clearSelection()
        if self.combo_model.count() > 0:
            self.combo_model.setCurrentIndex(0)
        self.spin_rank.setValue(16)
        self.spin_epochs.setValue(3)
        self.spin_batch.setValue(2)
        self.lbl_estimates.setText("VRAM: -- | RAM: -- | ETA: --\nFeasibility: --")
        self.table_jobs.clearSelection()
        self._refresh_queue_table()
