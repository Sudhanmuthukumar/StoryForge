import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QTextEdit, QSplitter, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt
from modules.dataset_lab.workers.pilot_worker import PilotWorker

class DatasetExplorerView(QWidget):
    """UI View for Phase 3A Dataset Pilot."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self._build_ui()
        self._load_datasets()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- TOP: PILOT DASHBOARD ---
        dash_widget = QWidget()
        dash_layout = QVBoxLayout(dash_widget)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        
        ctrl_group = QGroupBox("Pilot Generation Controls")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        self.btn_start = QPushButton("▶ Run Pilot (100 Examples)")
        self.btn_start.clicked.connect(self._start_pilot)
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.clicked.connect(self._pause_pilot)
        self.btn_pause.setEnabled(False)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.clicked.connect(self._stop_pilot)
        self.btn_stop.setEnabled(False)
        self.btn_refresh = QPushButton("🔄 Refresh Explorer")
        self.btn_refresh.clicked.connect(self._load_datasets)
        
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_refresh)
        ctrl_layout.addStretch()
        dash_layout.addWidget(ctrl_group)
        
        prog_group = QGroupBox("Pilot Dashboard")
        prog_layout = QHBoxLayout(prog_group)
        self.lbl_generated = QLabel("Examples Generated: 0")
        self.lbl_score = QLabel("Average Quality Score: 0.0")
        prog_layout.addWidget(self.lbl_generated)
        prog_layout.addWidget(self.lbl_score)
        prog_layout.addStretch()
        dash_layout.addWidget(prog_group)
        
        log_group = QGroupBox("Live Synthesis Logs")
        log_layout = QVBoxLayout(log_group)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("font-family: monospace; background: #1e1e2e; color: #a6accd;")
        self.txt_logs.setMaximumHeight(150)
        log_layout.addWidget(self.txt_logs)
        dash_layout.addWidget(log_group)
        
        splitter.addWidget(dash_widget)
        
        # --- BOTTOM: DATASET EXPLORER ---
        exp_widget = QWidget()
        exp_layout = QHBoxLayout(exp_widget)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table_datasets = QTableWidget()
        self.table_datasets.setColumnCount(4)
        self.table_datasets.setHorizontalHeaderLabels(["Category", "Pattern", "Genre", "Score"])
        self.table_datasets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_datasets.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_datasets.itemSelectionChanged.connect(self._on_table_select)
        
        self.txt_viewer = QTextEdit()
        self.txt_viewer.setReadOnly(True)
        self.txt_viewer.setStyleSheet("background: #15152a; color: #d0d0e8;")
        
        exp_layout.addWidget(self.table_datasets, 1)
        exp_layout.addWidget(self.txt_viewer, 1)
        
        splitter.addWidget(exp_widget)
        layout.addWidget(splitter)
        
        self.dataset_map = {}
        
    def _log(self, msg: str):
        self.txt_logs.append(msg)
        
    def _start_pilot(self):
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused:
                self.worker.resume()
                self._log("Resuming pilot...")
                self.btn_pause.setText("⏸ Pause")
            return
            
        self.worker = PilotWorker(target_examples=100)
        self.worker.log_msg.connect(self._log)
        self.worker.progress_updated.connect(lambda cnt: self.lbl_generated.setText(f"Examples Generated: {cnt}"))
        self.worker.average_score_updated.connect(lambda sc: self.lbl_score.setText(f"Average Quality Score: {sc:.2f}"))
        self.worker.finished_work.connect(self._on_finished)
        
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setText("⏸ Pause")
        self._log("Starting Dataset Pilot Generation...")
        
        self.worker.start()
        
    def _pause_pilot(self):
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused:
                self.worker.resume()
                self._log("Resuming pilot...")
                self.btn_pause.setText("⏸ Pause")
            else:
                self.worker.pause()
                self._log("Pausing pilot...")
                self.btn_pause.setText("▶ Resume")
                
    def _stop_pilot(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log("Cancelling pilot...")
            self.btn_stop.setEnabled(False)
            
    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self._load_datasets()
        
    def _load_datasets(self):
        self.table_datasets.setRowCount(0)
        self.dataset_map.clear()
        
        pilot_dir = Path("dataset_lab/training/pilot")
        if not pilot_dir.exists():
            return
            
        row_idx = 0
        total_score = 0
        
        for path in pilot_dir.glob("*.jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        cat = data.get("tags", ["Unknown"])[0]
                        pat = data.get("source_pattern", "Unknown")
                        gen = data.get("source_genre", "Unknown")
                        score = data.get("quality_score", 0)
                        
                        self.table_datasets.insertRow(row_idx)
                        self.table_datasets.setItem(row_idx, 0, QTableWidgetItem(cat))
                        self.table_datasets.setItem(row_idx, 1, QTableWidgetItem(pat))
                        self.table_datasets.setItem(row_idx, 2, QTableWidgetItem(gen))
                        self.table_datasets.setItem(row_idx, 3, QTableWidgetItem(str(score)))
                        
                        self.dataset_map[row_idx] = data
                        total_score += score
                        row_idx += 1
                    except Exception:
                        continue
                        
        self.lbl_generated.setText(f"Examples Generated: {row_idx}")
        if row_idx > 0:
            self.lbl_score.setText(f"Average Quality Score: {(total_score / row_idx):.2f}")
            
    def _on_table_select(self):
        selected = self.table_datasets.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        data = self.dataset_map.get(row)
        if data:
            text = (
                f"=== DATASET EXAMPLE ===\n\n"
                f"Instruction:\n{data.get('instruction')}\n\n"
                f"Input:\n{data.get('input')}\n\n"
                f"Output:\n{data.get('output')}\n\n"
                f"--- METADATA ---\n"
                f"Quality Score: {data.get('quality_score')}/10\n"
                f"Tags: {data.get('tags')}\n"
                f"Source Pattern: {data.get('source_pattern')}\n"
                f"Source Book: {data.get('source_book')} (Chap {data.get('source_chapter')})\n"
            )
            self.txt_viewer.setText(text)

    def clear(self):
        """Reset dataset pilot view stats and text details."""
        self.lbl_generated.setText("Examples Generated: 0")
        self.lbl_score.setText("Average Quality Score: 0.0")
        self.txt_logs.clear()
        self.table_datasets.clearSelection()
        self.txt_viewer.clear()
