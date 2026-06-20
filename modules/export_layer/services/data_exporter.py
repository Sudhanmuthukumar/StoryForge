import json
import csv
from pathlib import Path

class DataExporter:
    """Service to export StoryForge narrative assets into Unreal Engine DataTable JSON and CSV formats."""

    def __init__(self):
        pass

    def _flatten_relationships(self, rels: list) -> str:
        items = []
        for r in rels:
            items.append(f"{r.get('target_npc')}:{r.get('relation_type')}:{r.get('level', 0)}")
        return ";".join(items)

    def _flatten_quest_hooks(self, hooks: list) -> str:
        return ";".join(hooks)

    def _flatten_choices(self, choices: list) -> str:
        items = []
        for c in choices:
            cond = c.get('condition') or "None"
            conseq = c.get('consequence') or "None"
            items.append(f"{c.get('text')}|{c.get('target_node_id')}|{cond}|{conseq}")
        return ";".join(items)

    def _flatten_objectives(self, objectives: list) -> str:
        items = []
        for o in objectives:
            items.append(f"{o.get('objective_id')}:{o.get('description')}:{o.get('condition')}")
        return ";".join(items)

    def _flatten_rewards(self, rewards: list) -> str:
        items = []
        for r in rewards:
            items.append(f"{r.get('reward_type')}:{r.get('amount')}")
        return ";".join(items)

    def _flatten_outcomes(self, outcomes: list) -> str:
        items = []
        for o in outcomes:
            items.append(f"{o.get('outcome_id')}:{o.get('description')}")
        return ";".join(items)

    def _flatten_events(self, events: list) -> str:
        items = []
        for e in events:
            items.append(f"{e.get('event_name')}:{e.get('date')}:{e.get('description')}")
        return ";".join(items)

    def _flatten_figures(self, figures: list) -> str:
        items = []
        for f in figures:
            items.append(f"{f.get('name')}:{f.get('role')}:{f.get('description')}")
        return ";".join(items)

    def _flatten_quest_chains(self, chains: list) -> str:
        items = []
        for c in chains:
            quests_str = ",".join(c.get('quests', []))
            dep = c.get('dependency_chain_id') or "None"
            items.append(f"{c.get('chain_id')}|{c.get('title')}|[{quests_str}]|{dep}")
        return ";".join(items)

    # ══════════════════════════════════════════════════════════════════
    #  EXPORT METHODS
    # ══════════════════════════════════════════════════════════════════

    def export_npc(self, npc: dict, format_type: str, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "JSON":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(npc, f, indent=4)
                
        elif format_type == "UE_DataTable_JSON":
            # Map of RowName -> RowData
            dt = {
                npc["npc_id"]: {
                    "name": npc["name"],
                    "archetype": npc["archetype"],
                    "motivation": npc["motivation"],
                    "secret": npc["secret"],
                    "faction": npc["faction"],
                    "relationships": npc["relationships"],
                    "dialogue_style": npc["dialogue_style"],
                    "quest_hooks": npc["quest_hooks"]
                }
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dt, f, indent=4)
                
        elif format_type == "CSV":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "npc_id", "npc_name", "archetype", "motivation", "secret", "faction", "dialogue_style", "relationships", "quest_hooks"])
                writer.writerow([
                    npc["npc_id"],
                    npc["npc_id"],
                    npc["name"],
                    npc["archetype"],
                    npc["motivation"],
                    npc["secret"],
                    npc["faction"],
                    npc["dialogue_style"],
                    self._flatten_relationships(npc["relationships"]),
                    self._flatten_quest_hooks(npc["quest_hooks"])
                ])

    def export_quest(self, quest: dict, format_type: str, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "JSON":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(quest, f, indent=4)
                
        elif format_type == "UE_DataTable_JSON":
            dt = {
                quest["quest_id"]: {
                    "title": quest["title"],
                    "description": quest["description"],
                    "quest_type": quest["quest_type"],
                    "objectives": quest["objectives"],
                    "rewards": quest["rewards"],
                    "outcomes": quest["outcomes"]
                }
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dt, f, indent=4)
                
        elif format_type == "CSV":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "quest_id", "title", "description", "quest_type", "objectives", "rewards", "outcomes"])
                writer.writerow([
                    quest["quest_id"],
                    quest["quest_id"],
                    quest["title"],
                    quest["description"],
                    quest["quest_type"],
                    self._flatten_objectives(quest["objectives"]),
                    self._flatten_rewards(quest["rewards"]),
                    self._flatten_outcomes(quest["outcomes"])
                ])

    def export_dialogue(self, dialogue: dict, format_type: str, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "JSON":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dialogue, f, indent=4)
                
        elif format_type == "UE_DataTable_JSON":
            # In Unreal, a Dialogue Tree DataTable represents flat nodes
            dt = {}
            for node in dialogue.get("nodes", []):
                dt[node["node_id"]] = {
                    "speaker": node["speaker"],
                    "text": node["text"],
                    "choices": node["choices"],
                    "tree_id": dialogue["tree_id"],
                    "npc_name": dialogue["npc_name"]
                }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dt, f, indent=4)
                
        elif format_type == "CSV":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "node_id", "speaker", "text", "choices", "tree_id"])
                for node in dialogue.get("nodes", []):
                    writer.writerow([
                        node["node_id"],
                        node["node_id"],
                        node["speaker"],
                        node["text"],
                        self._flatten_choices(node["choices"]),
                        dialogue["tree_id"]
                    ])

    def export_campaign(self, campaign: dict, format_type: str, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "JSON":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=4)
                
        elif format_type == "UE_DataTable_JSON":
            # Map region progression index and story arcs
            dt = {}
            # Arcs
            for arc in campaign.get("story_arcs", []):
                dt[arc["arc_id"]] = {
                    "type": "StoryArc",
                    "title": arc["title"],
                    "description": arc["description"],
                    "milestone_or_progression": arc["milestone"]
                }
            # Regions
            for reg in campaign.get("regions", []):
                dt[reg["region_name"]] = {
                    "type": "Region",
                    "title": reg["region_name"],
                    "description": f"Progression index: {reg['progression_index']}",
                    "milestone_or_progression": str(reg["progression_index"]),
                    "quest_chains": reg["quest_chains"]
                }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dt, f, indent=4)
                
        elif format_type == "CSV":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "type", "title", "description", "milestone_or_progression", "quest_chains"])
                for arc in campaign.get("story_arcs", []):
                    writer.writerow([
                        arc["arc_id"],
                        "StoryArc",
                        arc["title"],
                        arc["description"],
                        arc["milestone"],
                        ""
                    ])
                for reg in campaign.get("regions", []):
                    writer.writerow([
                        reg["region_name"],
                        "Region",
                        reg["region_name"],
                        f"Region index: {reg['progression_index']}",
                        str(reg["progression_index"]),
                        self._flatten_quest_chains(reg["quest_chains"])
                    ])

    def export_lore(self, lore: dict, format_type: str, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "JSON":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(lore, f, indent=4)
                
        elif format_type == "UE_DataTable_JSON":
            dt = {
                lore["lore_id"]: {
                    "name": lore["name"],
                    "category": lore["category"],
                    "summary": lore["summary"],
                    "historical_events": lore["historical_events"],
                    "core_beliefs": lore["core_beliefs"],
                    "key_figures": lore["key_figures"]
                }
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dt, f, indent=4)
                
        elif format_type == "CSV":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "lore_id", "lore_name", "category", "summary", "historical_events", "core_beliefs", "key_figures"])
                writer.writerow([
                    lore["lore_id"],
                    lore["lore_id"],
                    lore["name"],
                    lore["category"],
                    lore["summary"],
                    self._flatten_events(lore["historical_events"]),
                    ";".join(lore["core_beliefs"]),
                    self._flatten_figures(lore["key_figures"])
                ])
