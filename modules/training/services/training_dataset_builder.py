import json
import time
from pathlib import Path
from typing import List, Dict, Any

class TrainingDatasetBuilder:
    """Compiles filtered datasets into isolated training jobs."""
    
    def __init__(self, filtered_dir: str = "dataset_lab/training/filtered", jobs_dir: str = "training_jobs"):
        self.filtered_dir = Path(filtered_dir)
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_job_id(self) -> str:
        count = len(list(self.jobs_dir.glob("job_*")))
        return f"job_{(count + 1):03d}"
        
    def build_job(self, categories: List[str], config: Dict[str, Any]) -> str:
        """
        Builds the training job folder and merges selected categories.
        Returns the job_id.
        """
        job_id = self._generate_job_id()
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "logs").mkdir(parents=True, exist_ok=True)
        
        train_path = job_dir / "train.jsonl"
        
        example_count = 0
        cats_found = set()
        
        # Merge logic
        if not self.filtered_dir.exists():
            raise FileNotFoundError("Filtered dataset directory does not exist.")
            
        with open(train_path, "w", encoding="utf-8") as f_out:
            for file_path in self.filtered_dir.glob("*.jsonl"):
                # If "All" or category is in filename
                match = False
                if "All Filtered Datasets" in categories:
                    match = True
                else:
                    for cat in categories:
                        safe_cat = cat.lower().replace(" ", "_")
                        if safe_cat in file_path.name:
                            match = True
                            cats_found.add(cat)
                            break
                            
                if match:
                    with open(file_path, "r", encoding="utf-8") as f_in:
                        for line in f_in:
                            if line.strip():
                                f_out.write(line)
                                example_count += 1
                                
        if example_count == 0:
            import shutil
            shutil.rmtree(job_dir)
            raise ValueError("No examples found for selected categories. Job cancelled.")
            
        # Metadata
        metadata = {
            "job_id": job_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataset_count": len(cats_found) if "All Filtered Datasets" not in categories else len(list(self.filtered_dir.glob("*.jsonl"))),
            "example_count": example_count,
            "categories": list(cats_found) if "All Filtered Datasets" not in categories else ["All"]
        }
        
        with open(job_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        # Config
        with open(job_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            
        # Initial Stats (Mocked for now)
        with open(job_dir / "stats.json", "w", encoding="utf-8") as f:
            json.dump({"loss": [], "epoch": 0}, f, indent=4)
            
        return job_id
