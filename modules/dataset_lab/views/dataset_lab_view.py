import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTreeWidget, QTreeWidgetItem, QFileDialog, 
    QTextEdit, QSplitter, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt
from modules.dataset_lab.workers.dataset_worker import DatasetWorker
from modules.dataset_lab.views.pattern_view import PatternExtractionView
from modules.dataset_lab.views.dataset_explorer_view import DatasetExplorerView
from modules.dataset_lab.views.quality_view import QualityView

class DatasetLabView(QWidget):
    """Primary UI View for Dataset Lab MVP."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self._build_ui()
        self._load_existing_chapters()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top Title
        title = QLabel("🔬 Dataset Lab (MVP)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0ff; margin-bottom: 5px;")
        main_layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Import & Extract
        tab_import = QWidget()
        tab_import_layout = QVBoxLayout(tab_import)
        tab_import_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter for Dashboard (Top) and Explorer (Bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- DASHBOARD WIDGET ---
        dashboard_widget = QWidget()
        dash_layout = QVBoxLayout(dashboard_widget)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Controls
        controls_group = QGroupBox("Import & Actions")
        controls_layout = QHBoxLayout(controls_group)
        self.btn_import_files = QPushButton("Import Files (PDF, DOCX, EPUB, TXT)")
        self.btn_import_files.clicked.connect(self._import_files)
        self.btn_import_folder = QPushButton("Import Folder")
        self.btn_import_folder.clicked.connect(self._import_folder)
        self.btn_export = QPushButton("Export Dataset")
        self.btn_export.clicked.connect(self._export_dataset)
        
        controls_layout.addWidget(self.btn_import_files)
        controls_layout.addWidget(self.btn_import_folder)
        controls_layout.addWidget(self.btn_export)
        controls_layout.addStretch()
        dash_layout.addWidget(controls_group)
        
        # 2. Progress Trackers
        prog_group = QGroupBox("Progress Dashboard")
        prog_layout = QVBoxLayout(prog_group)
        
        # File Progress
        self.lbl_file_prog = QLabel("File Progress: 0 Pages | 0 Detected | 0 Saved")
        self.bar_file = QProgressBar()
        prog_layout.addWidget(self.lbl_file_prog)
        prog_layout.addWidget(self.bar_file)
        
        # Library Progress
        self.lbl_lib_prog = QLabel("Library Progress: 0/0 Files | 0 Total Chapters")
        self.bar_lib = QProgressBar()
        prog_layout.addWidget(self.lbl_lib_prog)
        prog_layout.addWidget(self.bar_lib)
        
        # Current Task
        self.lbl_task = QLabel("Current Task: Idle")
        self.lbl_task.setStyleSheet("color: #6c63ff; font-weight: bold;")
        prog_layout.addWidget(self.lbl_task)
        
        dash_layout.addWidget(prog_group)
        
        # 3. Live Logs
        log_group = QGroupBox("Live Logs")
        log_layout = QVBoxLayout(log_group)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("font-family: monospace; background: #1e1e2e; color: #a6accd;")
        self.txt_logs.setMaximumHeight(150)
        log_layout.addWidget(self.txt_logs)
        dash_layout.addWidget(log_group)
        
        splitter.addWidget(dashboard_widget)
        
        # --- EXPLORER WIDGET ---
        explorer_widget = QWidget()
        exp_layout = QHBoxLayout(explorer_widget)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree
        self.tree_books = QTreeWidget()
        self.tree_books.setHeaderLabel("Chapter Explorer")
        self.tree_books.itemClicked.connect(self._on_tree_click)
        
        # Viewer
        self.txt_viewer = QTextEdit()
        self.txt_viewer.setReadOnly(True)
        self.txt_viewer.setStyleSheet("background: #15152a; color: #d0d0e8;")
        
        exp_layout.addWidget(self.tree_books, 1)
        exp_layout.addWidget(self.txt_viewer, 2)
        
        splitter.addWidget(explorer_widget)
        
        tab_import_layout.addWidget(splitter)
        self.tabs.addTab(tab_import, "Import & Extract")
        
        # Tab 2: Pattern Extraction
        self.pattern_view = PatternExtractionView()
        self.tabs.addTab(self.pattern_view, "Pattern Extraction")
        
        # Tab 3: Dataset Pilot
        self.pilot_view = DatasetExplorerView()
        self.tabs.addTab(self.pilot_view, "Dataset Pilot")
        
        # Tab 4: Quality Dashboard
        self.quality_view = QualityView()
        self.tabs.addTab(self.quality_view, "Quality & Benchmarks")
        
        main_layout.addWidget(self.tabs)
        
        # Track loaded chapters internally mapping item to dict
        self.chapter_map = {}
        
    def _log(self, msg: str):
        self.txt_logs.append(msg)
        
    def _import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", "Documents (*.pdf *.docx *.epub *.txt)"
        )
        if files:
            self._start_worker(files)
            
    def _import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            files = []
            for root, _, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(('.pdf', '.docx', '.epub', '.txt')):
                        files.append(os.path.join(root, f))
            if files:
                self._start_worker(files)
            else:
                self._log("No supported files found in folder.")
                
    def _start_worker(self, files: list):
        if self.worker and self.worker.isRunning():
            self._log("A job is already running.")
            return
            
        self.worker = DatasetWorker(files)
        self.worker.log_msg.connect(self._log)
        self.worker.status_updated.connect(self.lbl_task.setText)
        self.worker.file_progress.connect(self._update_file_prog)
        self.worker.library_progress.connect(self._update_lib_prog)
        self.worker.chapter_extracted.connect(self._add_chapter_to_tree)
        self.worker.start()
        
    def _update_file_prog(self, pages, detected, saved):
        self.lbl_file_prog.setText(f"File Progress: ~{pages} Pages | {detected} Detected | {saved} Saved")
        if detected > 0:
            self.bar_file.setMaximum(detected)
            self.bar_file.setValue(saved)
            
    def _update_lib_prog(self, total_files, files_completed, total_chapters):
        self.lbl_lib_prog.setText(f"Library Progress: {files_completed}/{total_files} Files | {total_chapters} Total Chapters")
        self.bar_lib.setMaximum(total_files)
        self.bar_lib.setValue(files_completed)
        
    def _add_chapter_to_tree(self, chapter: dict):
        book_name = chapter.get("book", "Unknown Book")
        chap_name = chapter.get("chapter", "Unknown Chapter")
        
        # Find or create book node
        book_item = None
        for i in range(self.tree_books.topLevelItemCount()):
            item = self.tree_books.topLevelItem(i)
            if item.text(0) == book_name:
                book_item = item
                break
                
        if not book_item:
            book_item = QTreeWidgetItem(self.tree_books, [book_name])
            book_item.setExpanded(True)
            
        chap_item = QTreeWidgetItem(book_item, [chap_name])
        self.chapter_map[id(chap_item)] = chapter
        
    def _on_tree_click(self, item: QTreeWidgetItem, column: int):
        chapter = self.chapter_map.get(id(item))
        if chapter:
            text = chapter.get("text", "")
            meta = (f"Book: {chapter.get('book')}\n"
                    f"Chapter: {chapter.get('chapter')}\n"
                    f"Source: {chapter.get('source_file')}\n"
                    f"Words: {chapter.get('word_count')}\n"
                    "----------------------------------------\n\n")
            self.txt_viewer.setText(meta + text)
            
    def _load_existing_chapters(self):
        chapters_dir = Path("dataset_lab/chapters")
        if not chapters_dir.exists():
            return
            
        for filepath in chapters_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    chapter = json.load(f)
                    self._add_chapter_to_tree(chapter)
            except Exception:
                pass
                
    def _export_dataset(self):
        out_dir = Path("dataset_lab/exports")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Combine all extracted chapters into one big JSONL for export MVP
        out_file = out_dir / "dataset_export.jsonl"
        count = 0
        with open(out_file, "w", encoding="utf-8") as out:
            for chap in self.chapter_map.values():
                out.write(json.dumps(chap) + "\n")
                count += 1
                
        self._log(f"Exported {count} chapters to {out_file}")

    def clear(self):
        """Safely clear/reset temporary states in dataset lab and child views."""
        self.bar_file.setValue(0)
        self.bar_lib.setValue(0)
        self.lbl_file_prog.setText("File Progress: 0 Pages | 0 Detected | 0 Saved")
        self.lbl_lib_prog.setText("Library Progress: 0/0 Files | 0 Total Chapters")
        self.lbl_task.setText("Current Task: Idle")
        self.txt_logs.clear()
        self.txt_viewer.clear()
        self.tree_books.clearSelection()
        if hasattr(self, "pattern_view") and self.pattern_view:
            self.pattern_view.clear()
        if hasattr(self, "pilot_view") and self.pilot_view:
            self.pilot_view.clear()
        if hasattr(self, "quality_view") and self.quality_view:
            self.quality_view.clear()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

