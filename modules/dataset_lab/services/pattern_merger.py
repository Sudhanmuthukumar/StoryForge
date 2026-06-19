import os
import json
from pathlib import Path
from typing import Dict, Any

class PatternMerger:
    """Merges raw chapter patterns into unified databases without duplicating strings."""
    
    def __init__(self, patterns_dir: str = "dataset_lab/patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.raw_dir = self.patterns_dir / "raw"
        self.merged_dir = self.patterns_dir / "merged"
        
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.merged_dir.mkdir(parents=True, exist_ok=True)
        
        self.categories = [
            "genre_profiles", "theme_profiles", "character_patterns", 
            "dialogue_patterns", "narrative_patterns", "conflict_patterns", 
            "worldbuilding_patterns", "scene_patterns", "storytelling_devices"
        ]
        
    def save_raw(self, chapter_filename: str, patterns: Dict[str, Any]) -> None:
        """Saves the raw JSON output for a specific chapter."""
        out_path = self.raw_dir / f"{chapter_filename.replace('.json', '')}_patterns.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(patterns, f, indent=4)
            
    def merge_chapter(self, chapter_index: int, patterns: Dict[str, Any]) -> None:
        """Merges a chapter's extracted patterns into the unified databases."""
        for cat in self.categories:
            extracted_items = patterns.get(cat, [])
            if not isinstance(extracted_items, list):
                continue
                
            db_path = self.merged_dir / f"{cat}.json"
            db_data = self._load_db(db_path)
            
            for item in extracted_items:
                if not isinstance(item, str) or not item.strip():
                    continue
                    
                item_clean = item.strip()
                # Check for existing
                found = False
                for existing in db_data:
                    # Very simple string matching to prevent exact duplicates
                    if existing["pattern"].lower() == item_clean.lower():
                        if chapter_index not in existing["chapters"]:
                            existing["chapters"].append(chapter_index)
                            existing["occurrences"] = len(existing["chapters"])
                        found = True
                        break
                        
                if not found:
                    db_data.append({
                        "pattern": item_clean,
                        "chapters": [chapter_index],
                        "occurrences": 1
                    })
                    
            self._save_db(db_path, db_data)
            
    def _load_db(self, path: Path) -> list:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
        
    def _save_db(self, path: Path, data: list) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
