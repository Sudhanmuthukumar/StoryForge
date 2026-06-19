import os
import time
import json
import traceback
from pathlib import Path
from typing import List
from PySide6.QtCore import QThread, Signal
from modules.dataset_lab.services.pattern_extractor import PatternExtractor
from modules.dataset_lab.services.pattern_merger import PatternMerger

class PatternWorker(QThread):
    """Background worker for iterating over chapters and running LLM pattern extraction."""
    
    # Signals
    log_msg = Signal(str)
    
    # books_processed, chapters_processed, patterns_found, categories_completed
    progress_updated = Signal(int, int, int, int)
    
    # current_chapter text
    current_chapter_updated = Signal(str)
    
    finished_work = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.extractor = PatternExtractor()
        self.merger = PatternMerger()
        
        self.is_paused = False
        self.is_cancelled = False
        self.chapters_dir = Path("dataset_lab/chapters")
        
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        try:
            if not self.chapters_dir.exists():
                self.log_msg.emit("No chapters directory found.")
                self.finished_work.emit()
                return
                
            chapters = list(self.chapters_dir.glob("*.json"))
            if not chapters:
                self.log_msg.emit("No chapters found to process.")
                self.finished_work.emit()
                return
                
            total_chapters = len(chapters)
            books_processed = set()
            chapters_processed = 0
            patterns_found = 0
            
            self.log_msg.emit(f"Starting pattern extraction for {total_chapters} chapters...")
            
            for path in chapters:
                while self.is_paused and not self.is_cancelled:
                    time.sleep(0.5)
                    
                if self.is_cancelled:
                    self.log_msg.emit("Extraction cancelled by user.")
                    break
                    
                # Check if already processed
                raw_filename = f"{path.stem}_patterns.json"
                raw_path = self.merger.raw_dir / raw_filename
                
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        chapter_data = json.load(f)
                except Exception:
                    continue
                    
                book = chapter_data.get("book", "Unknown")
                chap_name = chapter_data.get("chapter", "Unknown")
                chap_idx = chapter_data.get("chapter_index", 0)
                text = chapter_data.get("text", "")
                
                books_processed.add(book)
                self.current_chapter_updated.emit(f"{book} - {chap_name}")
                
                if raw_path.exists():
                    self.log_msg.emit(f"Skipping {path.name} (already processed)")
                    chapters_processed += 1
                    self.progress_updated.emit(len(books_processed), chapters_processed, patterns_found, 9)
                    continue
                
                self.log_msg.emit(f"Analyzing {path.name}...")
                
                # Execute 3-pass LLM calls
                try:
                    patterns = self.extractor.extract_all(text)
                except Exception as e:
                    self.log_msg.emit(f"Error extracting patterns from {path.name}: {e}")
                    continue
                    
                # Save Raw
                self.merger.save_raw(path.name, patterns)
                
                # Merge into unified databases
                self.merger.merge_chapter(chap_idx, patterns)
                
                # Count found
                for cat in self.merger.categories:
                    lst = patterns.get(cat, [])
                    if isinstance(lst, list):
                        patterns_found += len(lst)
                        
                chapters_processed += 1
                self.progress_updated.emit(len(books_processed), chapters_processed, patterns_found, 9)
                self.log_msg.emit(f"Completed {path.name}")
                
            self.log_msg.emit("Pattern extraction phase finished.")
            self.finished_work.emit()
            
        except Exception as e:
            err = traceback.format_exc()
            self.log_msg.emit(f"CRITICAL ERROR: {err}")
            self.error_occurred.emit(str(e))
