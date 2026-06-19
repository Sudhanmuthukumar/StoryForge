import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class KnowledgeEngine:
    """Service to interact with the persistent storytelling pattern databases."""

    PATTERN_TYPES = [
        "character_patterns",
        "dialogue_patterns",
        "conflict_patterns",
        "scene_patterns",
        "worldbuilding_patterns",
        "narrative_patterns",
        "pacing_patterns"
    ]

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = Path(db_dir) if db_dir else Path(os.path.dirname(os.path.dirname(__file__))) / "databases"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_databases()

    def _initialize_databases(self):
        for p_type in self.PATTERN_TYPES:
            file_path = self.db_dir / f"{p_type}.json"
            if not file_path.exists():
                file_path.write_text("[]", encoding="utf-8")

    def read_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        if pattern_type not in self.PATTERN_TYPES:
            raise ValueError(f"Invalid pattern type: {pattern_type}")
        file_path = self.db_dir / f"{pattern_type}.json"
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def write_patterns(self, pattern_type: str, patterns: List[Dict[str, Any]]) -> None:
        if pattern_type not in self.PATTERN_TYPES:
            raise ValueError(f"Invalid pattern type: {pattern_type}")
        file_path = self.db_dir / f"{pattern_type}.json"
        file_path.write_text(json.dumps(patterns, indent=4), encoding="utf-8")

    def add_pattern(self, pattern_type: str, content: str, source: str) -> None:
        """Add a pattern or increment its occurrence if it already exists."""
        patterns = self.read_patterns(pattern_type)
        
        # Simple exact match deduplication
        existing = next((p for p in patterns if p.get("content") == content), None)
        if existing:
            existing["occurrence_count"] = existing.get("occurrence_count", 0) + 1
            if source not in existing.setdefault("provenance", []):
                existing["provenance"].append(source)
        else:
            new_id = f"{pattern_type[:4]}_{len(patterns)+1:04d}"
            patterns.append({
                "pattern_id": new_id,
                "pattern_type": pattern_type,
                "content": content,
                "provenance": [source],
                "occurrence_count": 1
            })
            
        self.write_patterns(pattern_type, patterns)
        
    def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        for p_type in self.PATTERN_TYPES:
            patterns = self.read_patterns(p_type)
            stats[p_type] = {
                "count": len(patterns),
                "total_occurrences": sum(p.get("occurrence_count", 1) for p in patterns)
            }
        return stats
