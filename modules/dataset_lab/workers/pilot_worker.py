import os
import time
import json
import random
import traceback
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from modules.dataset_lab.services.context_generator import ContextGenerator
from modules.dataset_lab.services.dataset_generator import DatasetGenerator

class PilotWorker(QThread):
    """Background worker driving the Phase 3A dataset generation pilot."""
    
    log_msg = Signal(str)
    progress_updated = Signal(int)  # Total generated count
    average_score_updated = Signal(float)
    finished_work = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, target_examples=100, parent=None):
        super().__init__(parent)
        self.context_gen = ContextGenerator()
        self.dataset_gen = DatasetGenerator()
        self.target_examples = target_examples
        self.is_paused = False
        self.is_cancelled = False
        
        self.categories = [
            "Continue Story",
            "Generate Dialogue",
            "Create Character",
            "Create Worldbuilding",
            "Generate Conflict"
        ]
        
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        try:
            merged_dir = Path("dataset_lab/patterns/merged")
            chapters_dir = Path("dataset_lab/chapters")
            
            if not merged_dir.exists() or not chapters_dir.exists():
                self.log_msg.emit("Required directories missing.")
                self.finished_work.emit()
                return
                
            # Load all merged patterns to sample from
            all_patterns = []
            for path in merged_dir.glob("*.json"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_patterns.extend(data)
                except Exception:
                    continue
                    
            if not all_patterns:
                self.log_msg.emit("No patterns found to generate from.")
                self.finished_work.emit()
                return
                
            generated_count = 0
            total_score = 0
            
            self.log_msg.emit(f"Starting Pilot Generation (Target: {self.target_examples} examples)...")
            
            while generated_count < self.target_examples:
                while self.is_paused and not self.is_cancelled:
                    time.sleep(0.5)
                    
                if self.is_cancelled:
                    self.log_msg.emit("Pilot generation cancelled.")
                    break
                    
                # 1. Sample pattern
                pat_data = random.choice(all_patterns)
                pat_name = pat_data.get("pattern", "Unknown")
                chaps = pat_data.get("chapters", [])
                
                if not chaps:
                    continue
                    
                # Select a random chapter index where this pattern was found
                target_chap_idx = random.choice(chaps)
                
                # 2. Find the raw chapter text
                chapter_text = ""
                meta_book = "Unknown"
                meta_chap = "Unknown"
                
                for c_path in chapters_dir.glob("*.json"):
                    try:
                        with open(c_path, "r", encoding="utf-8") as f:
                            c_data = json.load(f)
                            if c_data.get("chapter_index") == target_chap_idx:
                                chapter_text = c_data.get("text", "")
                                meta_book = c_data.get("book", "Unknown")
                                meta_chap = c_data.get("chapter", "Unknown")
                                break
                    except Exception:
                        continue
                        
                if not chapter_text:
                    continue
                    
                self.log_msg.emit(f"Generating Context for '{pat_name}'...")
                
                # 3. Generate Structured Context
                context = self.context_gen.generate_context(pat_name, chapter_text)
                if not context:
                    continue
                    
                # 4. Generate Dataset Example
                target_category = random.choice(self.categories)
                self.log_msg.emit(f"Synthesizing Example ({target_category})...")
                
                meta_dict = {
                    "source_book": meta_book,
                    "source_chapter": meta_chap
                }
                
                example = self.dataset_gen.generate_example(target_category, context, meta_dict)
                if example:
                    self.dataset_gen.save_example(target_category, example)
                    generated_count += 1
                    
                    score = example.get("quality_score", 5)
                    total_score += score
                    avg_score = total_score / generated_count
                    
                    self.progress_updated.emit(generated_count)
                    self.average_score_updated.emit(avg_score)
                    self.log_msg.emit(f"Saved: {target_category} (Score: {score}/10)")
                else:
                    self.log_msg.emit("Synthesis failed. Retrying...")
                    
            self.log_msg.emit("Pilot Generation Finished.")
            self.finished_work.emit()
            
        except Exception as e:
            err = traceback.format_exc()
            self.log_msg.emit(f"CRITICAL ERROR: {err}")
            self.error_occurred.emit(str(e))
