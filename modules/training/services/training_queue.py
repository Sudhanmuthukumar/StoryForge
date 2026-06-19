import json
import time
import subprocess
import os
import sys
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from typing import Dict, Any, List

class TrainingQueueManager(QThread):
    """
    Persistent job orchestrator for LoRA Training.
    Spawns lora_trainer.py as a subprocess and monitors its stats.
    """
    
    queue_updated = Signal()
    job_progress_updated = Signal(str, int, str) # job_id, progress_percent, current_stage
    job_log_updated = Signal(str, str) # job_id, log_line
    
    def __init__(self, jobs_dir: str = "training_jobs"):
        super().__init__()
        self.jobs_dir = Path(jobs_dir)
        self.queue_file = self.jobs_dir / "queue.json"
        
        # In-memory queue: job_id -> state dict
        self.queue_data = {}
        self._load_queue()
        
        self.is_running = True
        self.active_processes = {} # job_id -> subprocess.Popen
        
    def _load_queue(self):
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    self.queue_data = json.load(f)
            except Exception:
                self.queue_data = {}
                
        # Recover interrupted states
        for job_id, state in self.queue_data.items():
            if state["status"] in ["PREPARING", "RUNNING"]:
                state["status"] = "PAUSED"
                state["stage"] = "Interrupted by system shutdown"
        self._save_queue()
                
    def _save_queue(self):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(self.queue_data, f, indent=4)
        self.queue_updated.emit()
            
    def register_job(self, job_id: str):
        self.queue_data[job_id] = {
            "status": "PENDING",
            "progress": 0,
            "stage": "Waiting to start..."
        }
        self._save_queue()
        
    def update_job_state(self, job_id: str, status: str, progress: int = None, stage: str = None):
        if job_id in self.queue_data:
            self.queue_data[job_id]["status"] = status
            if progress is not None:
                self.queue_data[job_id]["progress"] = progress
            if stage is not None:
                self.queue_data[job_id]["stage"] = stage
            self._save_queue()
            
            prog = self.queue_data[job_id]["progress"]
            stg = self.queue_data[job_id]["stage"]
            self.job_progress_updated.emit(job_id, prog, stg)
            
    def get_all_jobs(self) -> Dict[str, Any]:
        return self.queue_data
        
    def start_job(self, job_id: str):
        """Spawns the lora_trainer.py subprocess."""
        if job_id not in self.queue_data or job_id in self.active_processes:
            return
            
        self.update_job_state(job_id, "PREPARING", 0, "Initializing Subprocess...")
        
        job_dir = self.jobs_dir / job_id
        log_file = job_dir / "training_log.txt"
        
        script_path = Path("modules/training/services/lora_trainer.py").resolve()
        
        f_log = open(log_file, "a", encoding="utf-8")
        
        try:
            # Spawn isolated subprocess
            proc = subprocess.Popen(
                [sys.executable, str(script_path), "--job_dir", str(job_dir)],
                stdout=f_log,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            self.active_processes[job_id] = (proc, f_log)
            self.update_job_state(job_id, "RUNNING", 1, "Loading Model...")
        except Exception as e:
            self.update_job_state(job_id, "FAILED", 0, f"Error: {str(e)}")
            f_log.close()
            
    def pause_job(self, job_id: str):
        """Gracefully kills the subprocess, allowing checkpoints to remain."""
        if job_id in self.active_processes:
            proc, f_log = self.active_processes[job_id]
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            finally:
                f_log.close()
                del self.active_processes[job_id]
                
        self.update_job_state(job_id, "PAUSED", stage="Paused by User. Checkpoints saved.")
        
    def stop_manager(self):
        self.is_running = False
        for j_id in list(self.active_processes.keys()):
            self.pause_job(j_id)
            
    def run(self):
        """Polling loop to read stats.json from active subprocesses."""
        while self.is_running:
            time.sleep(2.0)
            
            for job_id, (proc, f_log) in list(self.active_processes.items()):
                # Check if process died
                ret = proc.poll()
                
                # Read stats
                job_dir = self.jobs_dir / job_id
                stats_path = job_dir / "stats.json"
                
                if stats_path.exists():
                    try:
                        with open(stats_path, "r", encoding="utf-8") as f:
                            stats = json.load(f)
                            
                        if stats.get("status") == "COMPLETED":
                            self.update_job_state(job_id, "COMPLETED", 100, "Adapter Saved.")
                            f_log.close()
                            del self.active_processes[job_id]
                            continue
                            
                        # Update progress
                        step = stats.get("step", 0)
                        max_s = stats.get("max_steps", 1)
                        if max_s == 0: max_s = 1
                        prog = int((step / max_s) * 100)
                        
                        loss = stats.get("loss", 0.0)
                        eta = stats.get("eta_sec", 0.0)
                        
                        stg = f"Step: {step}/{max_s} | Loss: {loss:.4f} | ETA: {eta:.0f}s"
                        self.update_job_state(job_id, "RUNNING", prog, stg)
                    except Exception:
                        pass
                        
                if ret is not None and job_id in self.active_processes:
                    # Process exited but didn't mark COMPLETED in stats
                    if ret == 0:
                        self.update_job_state(job_id, "COMPLETED", 100, "Adapter Saved.")
                    else:
                        self.update_job_state(job_id, "FAILED", stage=f"Subprocess crashed (Exit {ret}). Check logs.")
                    f_log.close()
                    del self.active_processes[job_id]
