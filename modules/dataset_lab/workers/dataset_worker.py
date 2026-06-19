import os
import time
import traceback
from typing import List
from PySide6.QtCore import QThread, Signal
from modules.dataset_lab.services.document_extractor import DocumentExtractor
from modules.dataset_lab.services.chapter_splitter import ChapterSplitter
from modules.dataset_lab.services.checkpoint_manager import CheckpointManager

class DatasetWorker(QThread):
    """Background worker for extracting text and splitting chapters."""
    
    # Signals
    log_msg = Signal(str)
    
    # Progress: pages_processed, chapters_detected, chapters_saved
    file_progress = Signal(int, int, int)
    
    # Library progress: files_imported, files_completed, total_chapters
    library_progress = Signal(int, int, int)
    
    # Status text (e.g. "Extracting...", "Splitting...")
    status_updated = Signal(str)
    
    # When a chapter is saved, emit its data to update the UI
    chapter_extracted = Signal(dict)
    
    # When all work completes
    finished_work = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, file_paths: List[str], parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.extractor = DocumentExtractor()
        self.splitter = ChapterSplitter()
        self.checkpoint = CheckpointManager()
        
        self.total_chapters_overall = 0
        self.is_cancelled = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        total_files = len(self.file_paths)
        files_completed = 0
        
        try:
            for idx, file_path in enumerate(self.file_paths):
                if self.is_cancelled:
                    self.log_msg.emit("Job cancelled by user.")
                    break
                    
                filename = os.path.basename(file_path)
                self.log_msg.emit(f"Starting {filename}...")
                
                # Check checkpoint
                ckpt = self.checkpoint.load_checkpoint(filename)
                # For this MVP, if it failed mid-file we'll restart the file.
                # If you want true mid-file resuming, it requires byte-range tracking.
                if ckpt.get("progress") == 100:
                    self.log_msg.emit(f"Skipping {filename} (already 100% processed).")
                    files_completed += 1
                    self.library_progress.emit(total_files, files_completed, self.total_chapters_overall)
                    continue
                
                # 1. Extraction
                self.status_updated.emit("Extracting...")
                self.log_msg.emit("Running document extractor...")
                
                try:
                    doc_data = self.extractor.extract(file_path)
                except Exception as e:
                    self.log_msg.emit(f"Error extracting {filename}: {str(e)}")
                    continue
                    
                title = doc_data.get("title", "Unknown")
                raw_text = doc_data.get("raw_text", "")
                
                # We do not have literal pages mapped in basic text merge, so approximate
                pages_approx = len(raw_text) // 2000
                self.file_progress.emit(pages_approx, 0, 0)
                
                # Save raw text
                raw_path = os.path.join("dataset_lab", "raw", f"{title.replace(' ', '_')}.txt")
                os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                with open(raw_path, "w", encoding="utf-8") as f:
                    f.write(raw_text)
                    
                # 2. Splitting
                self.status_updated.emit("Splitting...")
                self.log_msg.emit(f"Extracted {len(raw_text)} chars. Detecting chapters...")
                
                chapters = self.splitter.split(file_path, title, raw_text)
                total_chap = len(chapters)
                self.log_msg.emit(f"Detected {total_chap} chapters.")
                self.file_progress.emit(pages_approx, total_chap, 0)
                
                # 3. Saving
                self.status_updated.emit("Saving...")
                chapters_saved = 0
                for chapter in chapters:
                    if self.is_cancelled:
                        break
                    
                    saved_path = self.splitter.save_chapter(chapter)
                    self.log_msg.emit(f"Saved: {os.path.basename(saved_path)}")
                    chapters_saved += 1
                    self.total_chapters_overall += 1
                    
                    self.file_progress.emit(pages_approx, total_chap, chapters_saved)
                    self.library_progress.emit(total_files, files_completed, self.total_chapters_overall)
                    self.chapter_extracted.emit(chapter)
                    time.sleep(0.01) # UI breath
                
                # Update Checkpoint
                self.checkpoint.save_checkpoint(filename, {
                    "file": filename,
                    "book": title,
                    "chapter": "Complete",
                    "progress": 100,
                    "chapters_saved": chapters_saved
                })
                
                files_completed += 1
                self.library_progress.emit(total_files, files_completed, self.total_chapters_overall)
                
            self.status_updated.emit("Idle")
            self.log_msg.emit("All extraction jobs completed.")
            self.finished_work.emit()
            
        except Exception as e:
            err = traceback.format_exc()
            self.log_msg.emit(f"CRITICAL ERROR: {err}")
            self.error_occurred.emit(str(e))
            self.status_updated.emit("Error")
