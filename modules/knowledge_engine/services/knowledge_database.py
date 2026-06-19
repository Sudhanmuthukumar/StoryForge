import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

class KnowledgeDatabase:
    """Manages CRUD operations for the persistent Storytelling Knowledge Engine databases."""
    
    DB_NAMES = [
        "character_patterns.json",
        "dialogue_patterns.json",
        "conflict_patterns.json",
        "scene_patterns.json",
        "worldbuilding_patterns.json",
        "narrative_patterns.json",
        "pacing_patterns.json"
    ]
    
    def __init__(self, db_dir: str = "modules/knowledge_engine/databases"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._init_dbs()
        
    def _init_dbs(self):
        """Ensure all database files exist with empty lists if missing."""
        for name in self.DB_NAMES:
            path = self.db_dir / name
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f)
                    
    def _get_path(self, db_name: str) -> Path:
        if db_name not in self.DB_NAMES:
            raise ValueError(f"Unknown database: {db_name}")
        return self.db_dir / db_name
        
    def read_db(self, db_name: str) -> List[Dict[str, Any]]:
        path = self._get_path(db_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
            
    def write_db(self, db_name: str, data: List[Dict[str, Any]]) -> None:
        path = self._get_path(db_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    def add_pattern(self, db_name: str, pattern: Dict[str, Any]) -> str:
        """Adds a new pattern or updates occurrence count if it already exists."""
        db = self.read_db(db_name)
        
        # Check for duplicate by name/description fuzzy match
        for existing in db:
            if existing.get("name") == pattern.get("name") and existing.get("category") == pattern.get("category"):
                existing["occurrence_count"] = existing.get("occurrence_count", 0) + 1
                if pattern.get("source_books") and pattern["source_books"][0] not in existing.get("source_books", []):
                    existing["source_books"].append(pattern["source_books"][0])
                if pattern.get("variants") and pattern["variants"][0] not in existing.get("variants", []):
                    existing["variants"].append(pattern["variants"][0])
                self.write_db(db_name, db)
                return existing["id"]
                
        # Create new
        pattern_id = str(uuid.uuid4())
        new_pattern = {
            "id": pattern_id,
            "name": pattern.get("name", "Unknown"),
            "category": pattern.get("category", "General"),
            "description": pattern.get("description", ""),
            "source_books": pattern.get("source_books", []),
            "source_chapters": pattern.get("source_chapters", []),
            "occurrence_count": pattern.get("occurrence_count", 1),
            "variants": pattern.get("variants", []),
            "success_score": pattern.get("success_score", 5.0)  # Default neutral
        }
        db.append(new_pattern)
        self.write_db(db_name, db)
        return pattern_id

    def search_patterns(self, db_name: str, query: str) -> List[Dict[str, Any]]:
        """Basic text search over name and description."""
        db = self.read_db(db_name)
        q = query.lower()
        return [p for p in db if q in p.get("name", "").lower() or q in p.get("description", "").lower()]

    def filter_patterns(self, db_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Filter by attributes like author/book/genre/category."""
        db = self.read_db(db_name)
        result = []
        for p in db:
            match = True
            for k, v in kwargs.items():
                val = p.get(k)
                if isinstance(val, list):
                    if v not in val:
                        match = False
                        break
                elif val != v:
                    match = False
                    break
            if match:
                result.append(p)
        return result
        
    def update_success_score(self, pattern_id: str, new_score: float) -> bool:
        """Globally updates a pattern's success score by iterating all DBs."""
        for db_name in self.DB_NAMES:
            db = self.read_db(db_name)
            for p in db:
                if p.get("id") == pattern_id:
                    p["success_score"] = new_score
                    self.write_db(db_name, db)
                    return True
        return False
