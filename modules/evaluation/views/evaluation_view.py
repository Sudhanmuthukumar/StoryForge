import json
import subprocess
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QGroupBox, QSplitter, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from modules.evaluation.services.comparison_engine import ComparisonEngine

class EvaluationWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, job_dir: str):
        super().__init__()
        self.job_dir = Path(job_dir)
        self.is_running = True
        
    def run(self):
        try:
            self.progress.emit("Starting Inference Pipeline...", 5)
            runner_script = Path("modules/evaluation/services/evaluation_runner.py").resolve()
            output_raw = self.job_dir / "evaluation" / "raw_responses.json"
            stats_path = self.job_dir / "evaluation" / "eval_stats.json"
            
            # Reset stats file if exists
            if stats_path.exists():
                stats_path.unlink()
            
            # Spawn isolated subprocess
            proc = subprocess.Popen(
                [sys.executable, str(runner_script), "--job_dir", str(self.job_dir), "--output_file", str(output_raw)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            
            self.progress.emit("Running Base & Adapter Inference...", 15)
            
            # Polling loop
            while self.is_running:
                ret = proc.poll()
                
                # Check stats file
                if stats_path.exists():
                    try:
                        with open(stats_path, "r", encoding="utf-8") as f:
                            stats = json.load(f)
                            
                        self.progress.emit(stats.get("stage", "Processing..."), stats.get("progress", 50))
                        
                        if stats.get("status") == "COMPLETED":
                            self.finished.emit(stats.get("summary", {}))
                            return
                    except Exception:
                        pass # File might be locked during write
                        
                if ret is not None:
                    # Process died
                    if ret != 0:
                        self.error.emit(f"Evaluation process crashed. Exit code {ret}.")
                    else:
                        # Sometimes writing stats.json is slightly delayed
                        import time
                        time.sleep(1)
                        if stats_path.exists():
                            with open(stats_path, "r", encoding="utf-8") as f:
                                stats = json.load(f)
                            if stats.get("status") == "COMPLETED":
                                self.finished.emit(stats.get("summary", {}))
                                return
                        self.error.emit("Process completed but no final stats were generated.")
                    return
                    
                import time
                time.sleep(1.0)
                
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        self.is_running = False


class EvaluationView(QWidget):
    """UI for Phase 5C Model Evaluation & Benchmarking."""
    
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_completed_jobs()
        
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        title = QLabel("⚖️ Model Evaluation & Benchmarking")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0ff;")
        main_layout.addWidget(title)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL: JOBS ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        
        jobs_group = QGroupBox("Select Trained Adapter")
        jobs_layout = QVBoxLayout(jobs_group)
        self.list_jobs = QListWidget()
        jobs_layout.addWidget(self.list_jobs)
        
        self.btn_run = QPushButton("Run Benchmark Comparison")
        self.btn_run.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self._run_evaluation)
        jobs_layout.addWidget(self.btn_run)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.lbl_status = QLabel("Idle")
        jobs_layout.addWidget(self.progress_bar)
        jobs_layout.addWidget(self.lbl_status)
        
        left_layout.addWidget(jobs_group)
        splitter.addWidget(left_widget)
        
        # --- RIGHT PANEL: DASHBOARD ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        
        dash_group = QGroupBox("Benchmark Results")
        dash_layout = QVBoxLayout(dash_group)
        
        self.lbl_verdict = QLabel("NOT EVALUATED")
        self.lbl_verdict.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px; background-color: #333; text-align: center;")
        self.lbl_verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(self.lbl_verdict)
        
        stats_h = QHBoxLayout()
        
        self.lbl_base_score = QLabel("Base Score:\n--")
        self.lbl_adapter_score = QLabel("Adapter Score:\n--")
        self.lbl_improvement = QLabel("Improvement:\n--")
        self.lbl_win_rate = QLabel("Win Rate:\n--")
        
        for lbl in [self.lbl_base_score, self.lbl_adapter_score, self.lbl_improvement, self.lbl_win_rate]:
            lbl.setStyleSheet("font-size: 16px; border: 1px solid #555; padding: 10px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_h.addWidget(lbl)
            
        dash_layout.addLayout(stats_h)
        
        self.btn_human_review = QPushButton("Open Human Review Mode")
        self.btn_human_review.setEnabled(False)
        dash_layout.addWidget(self.btn_human_review)
        
        right_layout.addWidget(dash_group)
        splitter.addWidget(right_widget)
        
        main_layout.addWidget(splitter)
        
    def _load_completed_jobs(self):
        jobs_dir = Path("training_jobs")
        if not jobs_dir.exists():
            return
            
        self.list_jobs.clear()
        for d in jobs_dir.iterdir():
            if d.is_dir():
                output_dir = d / "output" / "adapter_model"
                if output_dir.exists():
                    self.list_jobs.addItem(d.name)
                    
    def _run_evaluation(self):
        items = self.list_jobs.selectedItems()
        if not items:
            QMessageBox.warning(self, "Error", "Select a job to evaluate.")
            return
            
        job_name = items[0].text()
        job_dir = str(Path("training_jobs") / job_name)
        
        self.btn_run.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Initializing...")
        self.lbl_verdict.setText("EVALUATING...")
        self.lbl_verdict.setStyleSheet("font-size: 24px; font-weight: bold; background-color: #555;")
        
        self.worker = EvaluationWorker(job_dir)
        self.worker.progress.connect(self._update_progress)
        self.worker.error.connect(self._handle_error)
        self.worker.finished.connect(self._handle_finished)
        self.worker.start()
        
    def _update_progress(self, msg: str, val: int):
        self.lbl_status.setText(msg)
        self.progress_bar.setValue(val)
        
    def _handle_error(self, err: str):
        self.btn_run.setEnabled(True)
        self.lbl_status.setText("Error occurred.")
        QMessageBox.critical(self, "Evaluation Error", err)
        
    def _handle_finished(self, summary: dict):
        self.btn_run.setEnabled(True)
        self.lbl_status.setText("Done.")
        self.progress_bar.setValue(100)
        
        self.lbl_base_score.setText(f"Base Score:\n{summary['avg_base_score']}")
        self.lbl_adapter_score.setText(f"Adapter Score:\n{summary['avg_adapter_score']}")
        
        imp = summary['improvement_pct']
        win = summary['win_rate_pct']
        
        self.lbl_improvement.setText(f"Improvement:\n{imp}%")
        self.lbl_win_rate.setText(f"Win Rate:\n{win}%")
        
        if summary['passed']:
            self.lbl_verdict.setText("✅ PASSED: READY FOR PACKAGING")
            self.lbl_verdict.setStyleSheet("font-size: 24px; font-weight: bold; background-color: #4CAF50; color: white;")
        else:
            self.lbl_verdict.setText("❌ FAILED: REQUIRES RETRAINING")
            self.lbl_verdict.setStyleSheet("font-size: 24px; font-weight: bold; background-color: #F44336; color: white;")
            
        self.btn_human_review.setEnabled(True)

    def clear(self):
        """Reset evaluation dashboard metrics and labels."""
        self.lbl_verdict.setText("NOT EVALUATED")
        self.lbl_verdict.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px; background-color: #333; text-align: center;")
        self.lbl_base_score.setText("Base Score:\n--")
        self.lbl_adapter_score.setText("Adapter Score:\n--")
        self.lbl_improvement.setText("Improvement:\n--")
        self.lbl_win_rate.setText("Win Rate:\n--")
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Idle")
        self.btn_human_review.setEnabled(False)
        self.list_jobs.clearSelection()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

