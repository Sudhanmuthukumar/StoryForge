import json
import hashlib
from pathlib import Path
from typing import Dict, Any

class DatasetFilter:
    """Filters dataset examples based on quality and duplicate reports."""
    
    def __init__(self, pilot_dir: str = "dataset_lab/training/pilot"):
        self.pilot_dir = Path(pilot_dir)
        self.filtered_dir = self.pilot_dir.parent / "filtered"
        self.logs_dir = self.pilot_dir.parent / "logs"
        self.filtered_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_id(self, example: Dict[str, Any]) -> str:
        unique_string = f"{example.get('instruction', '')}_{example.get('input', '')}_{example.get('output', '')}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def run_filter(self) -> Dict[str, int]:
        quality_path = self.logs_dir / "quality_report.json"
        dedup_path = self.logs_dir / "duplicate_report.json"
        
        quality_map = {}
        if quality_path.exists():
            try:
                with open(quality_path, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                    for item in q_data:
                        quality_map[item["example_id"]] = item
            except Exception:
                pass
                
        dedup_map = {}
        if dedup_path.exists():
            try:
                with open(dedup_path, "r", encoding="utf-8") as f:
                    d_data = json.load(f)
                    for item in d_data:
                        dedup_map[item["example_id"]] = item
            except Exception:
                pass
                
        stats = {
            "evaluated": 0,
            "accepted": 0,
            "rejected_quality": 0,
            "rejected_duplicate": 0,
            "rejected_formatting": 0
        }
        
        # Open categorized files for output
        out_files = {}
        
        for file_path in self.pilot_dir.glob("*.jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                        
                    try:
                        ex = json.loads(line)
                        stats["evaluated"] += 1
                    except Exception:
                        stats["rejected_formatting"] += 1
                        continue
                        
                    ex_id = self._generate_id(ex)
                    q_info = quality_map.get(ex_id, {})
                    d_info = dedup_map.get(ex_id, {})
                    
                    # Ensure basic formats
                    out_text = ex.get("output", "")
                    if not out_text or len(out_text.split()) < 20:
                        stats["rejected_formatting"] += 1
                        continue
                        
                    # Check duplicates
                    if d_info.get("status") == "DUPLICATE":
                        stats["rejected_duplicate"] += 1
                        continue
                        
                    # Check quality
                    score = q_info.get("quality_score", ex.get("quality_score", 5))
                    if score < 7.0:
                        stats["rejected_quality"] += 1
                        continue
                        
                    # Accepted
                    cat = ex.get("tags", ["Unknown"])[0].lower().replace(" ", "_")
                    
                    if cat not in out_files:
                        out_path = self.filtered_dir / f"{cat}_filtered.jsonl"
                        out_files[cat] = open(out_path, "w", encoding="utf-8")
                        
                    ex["quality_score"] = score # update with re-evaluated score if exists
                    out_files[cat].write(json.dumps(ex) + "\n")
                    stats["accepted"] += 1
                    
        for f in out_files.values():
            f.close()
            
        return stats
