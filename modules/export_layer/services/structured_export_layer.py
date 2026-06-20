import json
import csv
import yaml
from pathlib import Path
from typing import Dict, Any, List

class StructuredExportLayer:
    def __init__(self, export_dir: str = "C:/StoryForge AI/exports/unreal/interactive_narrative"):
        self.base_dir = Path(export_dir)
        self.dirs = {
            "npcs": self.base_dir / "npcs",
            "quests": self.base_dir / "quests",
            "factions": self.base_dir / "factions",
            "lore": self.base_dir / "lore",
            "campaigns": self.base_dir / "campaigns",
            "npc_memory": self.base_dir / "npc_memory",
            "npc_relationships": self.base_dir / "npc_relationships",
            "npc_goals": self.base_dir / "npc_goals",
            "npc_reactions": self.base_dir / "npc_reactions",
            "world_state": self.base_dir / "world_state",
            "world_events": self.base_dir / "world_events",
            "world_consequences": self.base_dir / "world_consequences"
        }
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def flatten_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten dictionaries and lists for CSV compatibility."""
        flat = {}
        for k, v in d.items():
            if isinstance(v, list):
                # If list of dicts, it's too complex for single cell, just stringify
                # If list of strings, comma separate
                if v and isinstance(v[0], dict):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = ",".join(str(i) for i in v)
            elif isinstance(v, dict):
                flat[k] = json.dumps(v)
            else:
                flat[k] = v
        return flat

    def _export_json(self, data: List[Dict[str, Any]], filepath: Path):
        filepath.with_suffix(".json").write_text(json.dumps(data, indent=4), encoding="utf-8")

    def _export_csv(self, data: List[Dict[str, Any]], filepath: Path):
        if not data: return
        csv_path = filepath.with_suffix(".csv")
        flattened_data = [self.flatten_dict(item) for item in data]
        keys = flattened_data[0].keys()
        with open(csv_path, 'w', newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flattened_data)

    def _export_yaml(self, data: List[Dict[str, Any]], filepath: Path):
        filepath.with_suffix(".yaml").write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")

    def export_assets(self, category: str, filename: str, data: List[Dict[str, Any]]):
        if category not in self.dirs:
            raise ValueError(f"Invalid category: {category}")
        
        target_dir = self.dirs[category]
        base_path = target_dir / filename
        
        self._export_json(data, base_path)
        self._export_csv(data, base_path)
        self._export_yaml(data, base_path)
        print(f"Exported {category} to {target_dir}")
