import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt
from modules.dataset_lab.workers.pattern_worker import PatternWorker

class PatternExtractionView(QWidget):
    """UI View for Phase 2 Pattern Extraction Engine."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self._build_ui()
        self._load_existing_patterns()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- TOP: DASHBOARD ---
        dash_widget = QWidget()
        dash_layout = QVBoxLayout(dash_widget)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        
        # Controls
        ctrl_group = QGroupBox("Pattern Extraction Controls")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        self.btn_start = QPushButton("▶ Start Extraction")
        self.btn_start.clicked.connect(self._start_worker)
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.clicked.connect(self._pause_worker)
        self.btn_pause.setEnabled(False)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.clicked.connect(self._stop_worker)
        self.btn_stop.setEnabled(False)
        self.btn_refresh = QPushButton("🔄 Refresh Explorer")
        self.btn_refresh.clicked.connect(self._load_existing_patterns)
        
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_refresh)
        ctrl_layout.addStretch()
        dash_layout.addWidget(ctrl_group)
        
        # Progress
        prog_group = QGroupBox("Extraction Progress")
        prog_layout = QVBoxLayout(prog_group)
        
        self.lbl_prog = QLabel("Books Processed: 0 | Chapters: 0 | Patterns Found: 0")
        self.bar_prog = QProgressBar()
        self.lbl_task = QLabel("Current Chapter: Idle")
        self.lbl_task.setStyleSheet("color: #6c63ff; font-weight: bold;")
        
        prog_layout.addWidget(self.lbl_prog)
        prog_layout.addWidget(self.bar_prog)
        prog_layout.addWidget(self.lbl_task)
        dash_layout.addWidget(prog_group)
        
        # Logs
        log_group = QGroupBox("Live Analysis Logs")
        log_layout = QVBoxLayout(log_group)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("font-family: monospace; background: #1e1e2e; color: #a6accd;")
        self.txt_logs.setMaximumHeight(150)
        log_layout.addWidget(self.txt_logs)
        dash_layout.addWidget(log_group)
        
        splitter.addWidget(dash_widget)
        
        # --- BOTTOM: EXPLORER ---
        exp_widget = QWidget()
        exp_layout = QHBoxLayout(exp_widget)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree_patterns = QTreeWidget()
        self.tree_patterns.setHeaderLabel("Pattern Database")
        self.tree_patterns.itemClicked.connect(self._on_tree_click)
        
        self.txt_viewer = QTextEdit()
        self.txt_viewer.setReadOnly(True)
        self.txt_viewer.setStyleSheet("background: #15152a; color: #d0d0e8;")
        
        exp_layout.addWidget(self.tree_patterns, 1)
        exp_layout.addWidget(self.txt_viewer, 2)
        
        splitter.addWidget(exp_widget)
        layout.addWidget(splitter)
        
        self.pattern_map = {}
        
    def _log(self, msg: str):
        self.txt_logs.append(msg)
        
    def _start_worker(self):
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused:
                self.worker.resume()
                self._log("Resuming extraction...")
                self.btn_pause.setText("⏸ Pause")
            return
            
        self.worker = PatternWorker()
        self.worker.log_msg.connect(self._log)
        self.worker.current_chapter_updated.connect(self.lbl_task.setText)
        self.worker.progress_updated.connect(self._update_prog)
        self.worker.finished_work.connect(self._on_finished)
        
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setText("⏸ Pause")
        self._log("Starting new pattern extraction job...")
        
        # Count total chapters to set bar maximum
        total_chaps = len(list(Path("dataset_lab/chapters").glob("*.json")))
        self.bar_prog.setMaximum(total_chaps)
        self.bar_prog.setValue(0)
        
        self.worker.start()
        
    def _pause_worker(self):
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused:
                self.worker.resume()
                self._log("Resuming extraction...")
                self.btn_pause.setText("⏸ Pause")
            else:
                self.worker.pause()
                self._log("Pausing extraction (will pause after current chapter finishes)...")
                self.btn_pause.setText("▶ Resume")
                
    def _stop_worker(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log("Cancelling extraction (will stop after current chapter)...")
            self.btn_stop.setEnabled(False)
            
    def _update_prog(self, books, chaps, patterns, categories):
        self.lbl_prog.setText(f"Books Processed: {books} | Chapters: {chaps} | Patterns Found: {patterns}")
        self.bar_prog.setValue(chaps)
        
    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.lbl_task.setText("Current Chapter: Idle")
        self._load_existing_patterns()
        
    def _load_existing_patterns(self):
        self.tree_patterns.clear()
        self.pattern_map.clear()
        
        merged_dir = Path("dataset_lab/patterns/merged")
        if not merged_dir.exists():
            return
            
        categories = {
            "genre_profiles.json": "🎭 Genres",
            "theme_profiles.json": "💡 Themes",
            "character_patterns.json": "👤 Characters",
            "dialogue_patterns.json": "💬 Dialogue",
            "narrative_patterns.json": "📖 Narrative",
            "conflict_patterns.json": "⚔️ Conflict",
            "worldbuilding_patterns.json": "🌍 Worldbuilding",
            "scene_patterns.json": "🎬 Scenes",
            "storytelling_devices.json": "🔧 Devices"
        }
        
        for file_name, cat_label in categories.items():
            path = merged_dir / file_name
            if not path.exists():
                continue
                
            cat_item = QTreeWidgetItem(self.tree_patterns, [cat_label])
            cat_item.setExpanded(False)
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                for entry in data:
                    pat_name = entry.get("pattern", "Unknown")
                    occur = entry.get("occurrences", 0)
                    pat_item = QTreeWidgetItem(cat_item, [f"{pat_name} ({occur})"])
                    self.pattern_map[id(pat_item)] = entry
            except Exception:
                pass
                
    def _on_tree_click(self, item: QTreeWidgetItem, column: int):
        entry = self.pattern_map.get(id(item))
        if entry:
            chaps = ", ".join([str(c) for c in entry.get("chapters", [])])
            text = (
                f"=== PATTERN DETAILS ===\n\n"
                f"Pattern: {entry.get('pattern')}\n"
                f"Occurrences: {entry.get('occurrences')}\n"
                f"Found in Chapter Indexes: [{chaps}]\n"
            )
            self.txt_viewer.setText(text)

    def clear(self):
        """Reset Pattern Extraction UI status and logs."""
        self.bar_prog.setValue(0)
        self.lbl_prog.setText("Books Processed: 0 | Chapters: 0 | Patterns Found: 0")
        self.lbl_task.setText("Current Chapter: Idle")
        self.txt_logs.clear()
        self.txt_viewer.clear()
        self.tree_patterns.clearSelection()
