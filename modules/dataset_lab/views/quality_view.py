import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from modules.dataset_lab.services.dataset_filter import DatasetFilter
from modules.dataset_lab.services.benchmark_runner import BenchmarkRunner

class DatasetBenchmarkWorker(QThread):
    progress = Signal(str, int)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.is_running = True
        
    def run(self):
        import subprocess
        import sys
        
        try:
            script = Path("modules/dataset_lab/services/benchmark_runner.py").resolve()
            stats_path = Path("dataset_lab/logs/benchmark_stats.json")
            
            if stats_path.exists():
                stats_path.unlink()
                
            self.progress.emit("Starting Benchmark Pipeline...", 5)
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            
            import time
            while self.is_running:
                ret = proc.poll()
                
                if stats_path.exists():
                    try:
                        with open(stats_path, "r", encoding="utf-8") as f:
                            stats = json.load(f)
                        self.progress.emit(stats.get("stage", "Running..."), stats.get("progress", 50))
                        
                        if stats.get("status") == "COMPLETED":
                            self.finished.emit()
                            return
                    except Exception:
                        pass
                        
                if ret is not None:
                    if ret != 0:
                        self.error.emit(f"Process crashed with exit code {ret}.")
                    else:
                        time.sleep(1)
                        if stats_path.exists():
                            with open(stats_path, "r", encoding="utf-8") as f:
                                stats = json.load(f)
                            if stats.get("status") == "COMPLETED":
                                self.finished.emit()
                                return
                        self.error.emit("Process completed but no stats were found.")
                    return
                    
                time.sleep(1.0)
                
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        self.is_running = False

class QualityView(QWidget):
    """UI View for Phase 4 Dataset Quality Engine & Benchmarking."""
    
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_stats()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- HEALTH SCORE ---
        health_group = QGroupBox("Dataset Health Metrics")
        health_layout = QHBoxLayout(health_group)
        
        self.lbl_health_score = QLabel("Overall Health: --/100")
        self.lbl_health_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        
        self.lbl_metrics = QLabel("Avg Quality: -- | Uniqueness: -- | Category Diversity: -- | Genre Diversity: --")
        
        health_layout.addWidget(self.lbl_health_score)
        health_layout.addSpacing(20)
        health_layout.addWidget(self.lbl_metrics)
        health_layout.addStretch()
        layout.addWidget(health_group)
        
        # --- QUALITY DASHBOARD ---
        dash_group = QGroupBox("Quality & Deduplication Dashboard")
        dash_layout = QVBoxLayout(dash_group)
        
        ctrl_layout = QHBoxLayout()
        self.btn_run_filter = QPushButton("▶ Run Quality Engine & Filter")
        self.btn_run_filter.clicked.connect(self._run_filter)
        
        self.btn_run_bench = QPushButton("▶ Run Model Benchmarks")
        self.btn_run_bench.clicked.connect(self._run_benchmarks)
        
        ctrl_layout.addWidget(self.btn_run_filter)
        ctrl_layout.addWidget(self.btn_run_bench)
        ctrl_layout.addStretch()
        dash_layout.addLayout(ctrl_layout)
        
        self.lbl_stats = QLabel("Evaluated: 0 | Accepted: 0 | Rejected (Quality): 0 | Rejected (Dup): 0")
        dash_layout.addWidget(self.lbl_stats)
        
        layout.addWidget(dash_group)
        layout.addStretch()
        
    def _run_filter(self):
        self.lbl_stats.setText("Running quality engine & filtering... (Check terminal for details)")
        # In a real GUI this would be a QThread like PilotWorker
        # For Phase 4 we just simulate calling the filter.
        filt = DatasetFilter()
        stats = filt.run_filter()
        
        self.lbl_stats.setText(
            f"Evaluated: {stats['evaluated']} | Accepted: {stats['accepted']} | "
            f"Rejected (Quality): {stats['rejected_quality']} | Rejected (Dup): {stats['rejected_duplicate']}"
        )
        self._load_stats()

    def _run_benchmarks(self):
        self.btn_run_bench.setEnabled(False)
        self.lbl_stats.setText("Initializing benchmark models...")
        
        self.bench_worker = DatasetBenchmarkWorker()
        self.bench_worker.progress.connect(self._update_bench_progress)
        self.bench_worker.error.connect(self._handle_bench_error)
        self.bench_worker.finished.connect(self._handle_bench_finished)
        self.bench_worker.start()
        
    def _update_bench_progress(self, msg: str, val: int):
        self.lbl_stats.setText(f"Benchmarking: {msg} ({val}%)")
        
    def _handle_bench_error(self, err: str):
        self.btn_run_bench.setEnabled(True)
        self.lbl_stats.setText(f"Benchmark Error: {err}")
        
    def _handle_bench_finished(self):
        self.btn_run_bench.setEnabled(True)
        self.lbl_stats.setText("Benchmarks completed! Saved to logs/benchmark_results.json")
            
    def _load_stats(self):
        # Calculate health score
        logs_dir = Path("dataset_lab/logs")
        if not logs_dir.exists():
            return
            
        qual_path = logs_dir / "quality_report.json"
        dup_path = logs_dir / "duplicate_report.json"
        
        total_score = 0
        count = 0
        categories = set()
        genres = set()
        
        if qual_path.exists():
            try:
                with open(qual_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        total_score += item.get("quality_score", 5)
                        count += 1
            except Exception:
                pass
                
        avg_q = (total_score / count) if count > 0 else 0
        
        dup_count = 0
        if dup_path.exists():
            try:
                with open(dup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        if item.get("status") == "DUPLICATE":
                            dup_count += 1
            except Exception:
                pass
                
        uniqueness = 100
        if count > 0:
            uniqueness = max(0, 100 - ((dup_count / count) * 100))
            
        health = (avg_q * 10) * 0.6 + uniqueness * 0.4
        
        self.lbl_health_score.setText(f"Overall Health: {health:.1f}/100")
        
        color = "#4CAF50" if health > 75 else "#FFC107" if health > 50 else "#F44336"
        self.lbl_health_score.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        self.lbl_metrics.setText(f"Avg Quality: {avg_q:.2f}/10 | Uniqueness: {uniqueness:.1f}% | Duplicates: {dup_count}")

    def clear(self):
        """Reset the quality view stats labels."""
        self.lbl_health_score.setText("Overall Health: --/100")
        self.lbl_health_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        self.lbl_metrics.setText("Avg Quality: -- | Uniqueness: -- | Category Diversity: -- | Genre Diversity: --")
        self.lbl_stats.setText("Evaluated: 0 | Accepted: 0 | Rejected (Quality): 0 | Rejected (Dup): 0")

    def load_data(self, data=None):
        pass
