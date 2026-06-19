import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy

from utils.constants import (
    UNIVERSES_DIR,
    DEFAULT_UNIVERSE_METADATA,
    DEFAULT_UNIVERSE_MEMORY,
    DEFAULT_UNIVERSE_RELATIONSHIPS,
    DEFAULT_UNIVERSE_TIMELINE,
)
from core.story_manager import StoryManager
from services.graph_engine import GraphEngine

CONFIG_PATH = Path("c:/StoryForge AI/config/universe_rules.json")

class UniverseEngine:
    def __init__(self):
        self.rules = self._load_rules()
        self.story_manager = StoryManager()
        self.graph_engine = GraphEngine()
        UNIVERSES_DIR.mkdir(parents=True, exist_ok=True)

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "conflict_detection": {
                    "same_name": True,
                    "different_traits": True,
                    "different_goals": True,
                    "different_facts": True
                }
            }

    def _read_json(self, path: Path, default: dict) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return deepcopy(default)

    def _write_json(self, path: Path, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def list_universes(self) -> list:
        universes = []
        if not UNIVERSES_DIR.exists():
            return universes
        for udir in UNIVERSES_DIR.iterdir():
            if udir.is_dir():
                meta_path = udir / "metadata.json"
                if meta_path.exists():
                    universes.append(self._read_json(meta_path, {}))
        return universes

    def create_universe(self, name: str) -> dict:
        uid = str(uuid.uuid4())
        udir = UNIVERSES_DIR / uid
        udir.mkdir(parents=True, exist_ok=True)
        
        meta = deepcopy(DEFAULT_UNIVERSE_METADATA)
        meta["universe_id"] = uid
        meta["name"] = name
        meta["created_at"] = datetime.now(timezone.utc).isoformat()
        meta["updated_at"] = meta["created_at"]
        
        self._write_json(udir / "metadata.json", meta)
        self._write_json(udir / "universe_memory.json", deepcopy(DEFAULT_UNIVERSE_MEMORY))
        self._write_json(udir / "universe_relationships.json", deepcopy(DEFAULT_UNIVERSE_RELATIONSHIPS))
        self._write_json(udir / "universe_timeline.json", deepcopy(DEFAULT_UNIVERSE_TIMELINE))
        
        return meta

    def delete_universe(self, universe_id: str) -> None:
        udir = UNIVERSES_DIR / universe_id
        if udir.exists() and udir.is_dir():
            shutil.rmtree(udir)

    def add_story(self, universe_id: str, story_id: str) -> None:
        udir = UNIVERSES_DIR / universe_id
        if not udir.exists():
            raise FileNotFoundError("Universe not found")
            
        meta = self._read_json(udir / "metadata.json", DEFAULT_UNIVERSE_METADATA)
        if story_id not in meta["stories"]:
            meta["stories"].append(story_id)
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_json(udir / "metadata.json", meta)
            self.rebuild_universe(universe_id)

    def remove_story(self, universe_id: str, story_id: str) -> None:
        udir = UNIVERSES_DIR / universe_id
        if not udir.exists():
            raise FileNotFoundError("Universe not found")
            
        meta = self._read_json(udir / "metadata.json", DEFAULT_UNIVERSE_METADATA)
        if story_id in meta["stories"]:
            meta["stories"].remove(story_id)
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_json(udir / "metadata.json", meta)
            self.rebuild_universe(universe_id)

    def rebuild_universe(self, universe_id: str) -> None:
        udir = UNIVERSES_DIR / universe_id
        meta = self._read_json(udir / "metadata.json", DEFAULT_UNIVERSE_METADATA)
        
        mem = deepcopy(DEFAULT_UNIVERSE_MEMORY)
        rels = deepcopy(DEFAULT_UNIVERSE_RELATIONSHIPS)
        timeline = deepcopy(DEFAULT_UNIVERSE_TIMELINE)
        
        cross_links = {}
        conflicts = []
        char_registry = {}
        
        # Load all stories
        for sid in meta["stories"]:
            try:
                story_obj = self.story_manager._find_story_by_id(sid)
                if not story_obj: continue
                smem = self._read_json(story_obj.memory_path, {})
                s_title = story_obj.title
            except Exception:
                continue
                
            # Aggregate Memory & Detect Conflicts
            for cat in ["characters", "locations", "themes", "events", "organizations", "artifacts"]:
                for item in smem.get(cat, []):
                    name = item if isinstance(item, str) else item.get("name", "Unknown")
                    if isinstance(item, str):
                        item = {"name": item}
                    item["source_story"] = s_title
                    mem[cat].append(item)
                    
                    if cat == "characters":
                        if name not in cross_links:
                            cross_links[name] = {"entity": name, "appears_in": []}
                        if s_title not in cross_links[name]["appears_in"]:
                            cross_links[name]["appears_in"].append(s_title)
                            
                        # Detect conflicts
                        if name in char_registry:
                            reg = char_registry[name]
                            if self.rules.get("conflict_detection", {}).get("different_traits", True):
                                rt = sorted([t.get("value") for t in reg.get("traits", [])])
                                it = sorted([t.get("value") for t in item.get("traits", [])])
                                if rt != it and it:
                                    conflicts.append(f"Character '{name}' has conflicting traits in {reg['source_story']} vs {s_title}")
                            
                            if self.rules.get("conflict_detection", {}).get("different_facts", True):
                                rf = sorted(reg.get("known_facts", []))
                                iff = sorted(item.get("known_facts", []))
                                if rf != iff and iff:
                                    conflicts.append(f"Character '{name}' has conflicting facts in {reg['source_story']} vs {s_title}")
                        else:
                            char_registry[name] = item

            # Aggregate Timeline (Events)
            for event in smem.get("events", []):
                ev = event if isinstance(event, dict) else {"name": event}
                ev["source_story"] = s_title
                timeline["timeline_entries"].append(ev)

        # Build cross-story links structure
        for link in cross_links.values():
            if len(link["appears_in"]) > 1:
                rels["cross_story_links"].append(link)
                
        rels["universe_conflicts"] = conflicts
        
        self._write_json(udir / "universe_memory.json", mem)
        self._write_json(udir / "universe_relationships.json", rels)
        self._write_json(udir / "universe_timeline.json", timeline)
        
        self.graph_engine.build_graph(universe_id)

    def load_universe(self, universe_id: str) -> dict:
        udir = UNIVERSES_DIR / universe_id
        if not udir.exists():
            raise FileNotFoundError("Universe not found")
        return {
            "metadata": self._read_json(udir / "metadata.json", DEFAULT_UNIVERSE_METADATA),
            "memory": self._read_json(udir / "universe_memory.json", DEFAULT_UNIVERSE_MEMORY),
            "relationships": self._read_json(udir / "universe_relationships.json", DEFAULT_UNIVERSE_RELATIONSHIPS),
            "timeline": self._read_json(udir / "universe_timeline.json", DEFAULT_UNIVERSE_TIMELINE)
        }
