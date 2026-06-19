import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from modules.world_simulation.services.simulation_database import SimulationDatabase
from modules.storyforge_core.events.event_bus import EventBus

class SimulationEngine:
    """Core logic engine for daily/weekly updates, faction actions, and NPC memory updates."""
    
    FACTIONS = [
        "The Order of Sunfire",
        "The Shadowrunners Guild",
        "Elves of the Sundered Grove",
        "Kingdom of Eldoria"
    ]
    
    def __init__(self, db_dir: Optional[str] = None):
        self.db = SimulationDatabase(db_dir=db_dir) if db_dir else SimulationDatabase()
        
    def populate_npc_memories_from_exports(self) -> int:
        """Read generated NPCs from exports/unreal/alpha_world/npcs and populate memory database."""
        npc_dir = Path("exports/unreal/alpha_world/npcs")
        if not npc_dir.exists():
            return 0
            
        npc_memories = self.db.read_db("npc_memory.json")
        reputation = self.db.read_db("reputation.json")
        
        count = 0
        for f in npc_dir.glob("npc_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    npc_data = json.load(file)
                nid = npc_data.get("npc_id")
                name = npc_data.get("name")
                faction = npc_data.get("faction")
                
                if nid and name and nid not in npc_memories:
                    npc_memories[nid] = {
                        "npc_id": nid,
                        "name": name,
                        "memories": [],
                        "quest_outcomes": {},
                        "relationships": {
                            "player": {
                                "trust": 50,
                                "sentiment": "Neutral",
                                "interaction_count": 0
                            }
                        },
                        "faction_standing": {
                            faction: 50
                        } if faction else {},
                        "interactions": []
                    }
                    count += 1
                    
                # Initialize faction in reputation too
                if faction and faction not in reputation["player"]["factions"]:
                    reputation["player"]["factions"][faction] = 0
                    
            except Exception as e:
                print(f"Error loading NPC export {f}: {e}")
                
        if count > 0:
            self.db.write_db("npc_memory.json", npc_memories)
            self.db.write_db("reputation.json", reputation)
            
        return count
        
    def _get_next_tick_index(self, history: List[Dict[str, Any]]) -> int:
        if not history:
            return 1
        return history[-1].get("tick_index", 0) + 1
        
    def _get_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"
        
    # ══════════════════════════════════════════════════════════════════
    #  REPUTATION & MEMORY INTERACTIONS
    # ══════════════════════════════════════════════════════════════════
    
    def record_quest_outcome(self, quest_id: str, title: str, npc_giver_name: str, outcome: str, reputation_change: int) -> None:
        """Record quest outcome in world state, reputation, and NPC memories."""
        npc_memories = self.db.read_db("npc_memory.json")
        world_state = self.db.read_db("world_state.json")
        reputation = self.db.read_db("reputation.json")
        history = self.db.read_db("event_history.json")
        
        # 1. Update World State completed quests
        world_state["completed_quests"].append({
            "quest_id": quest_id,
            "title": title,
            "outcome": outcome,
            "timestamp": self._get_timestamp()
        })
        
        # 2. Find quest giver NPC
        target_nid = None
        target_faction = None
        for nid, mem in npc_memories.items():
            if mem["name"] == npc_giver_name or npc_giver_name in mem["name"]:
                target_nid = nid
                mem["quest_outcomes"][quest_id] = outcome
                
                # Add memory of quest outcome
                mem["memories"].append({
                    "event_id": f"evt_q_{quest_id}",
                    "description": f"Player resolved my quest '{title}' with outcome: {outcome}.",
                    "timestamp": self._get_timestamp(),
                    "emotional_impact": "Gratitude" if outcome == "Success" else "Disappointment",
                    "importance": 70
                })
                
                # Adjust individual trust
                trust = mem["relationships"]["player"]["trust"]
                mem["relationships"]["player"]["trust"] = max(0, min(100, trust + reputation_change))
                mem["relationships"]["player"]["sentiment"] = self._get_sentiment_tier(mem["relationships"]["player"]["trust"])
                
                # Find faction standing
                if mem["faction_standing"]:
                    target_faction = list(mem["faction_standing"].keys())[0]
                break
                
        # 3. Update player reputations
        # NPC specific reputation
        if target_nid:
            current_npc_rep = reputation["player"]["npcs"].get(target_nid, 0)
            reputation["player"]["npcs"][target_nid] = max(-100, min(100, current_npc_rep + reputation_change))
            
        # Faction reputation
        if target_faction:
            current_fac_rep = reputation["player"]["factions"].get(target_faction, 0)
            reputation["player"]["factions"][target_faction] = max(-100, min(100, current_fac_rep + reputation_change))
            
        # 4. Log to event history
        tick = self._get_next_tick_index(history)
        history.append({
            "tick_index": tick,
            "timestamp": self._get_timestamp(),
            "type": "QuestOutcome",
            "description": f"Player completed quest '{title}' ({outcome}). NPC {npc_giver_name} relationship changed by {reputation_change}.",
            "affected_entities": ["player", npc_giver_name] + ([target_faction] if target_faction else [])
        })
        
        # Save databases
        self.db.write_db("world_state.json", world_state)
        self.db.write_db("npc_memory.json", npc_memories)
        self.db.write_db("reputation.json", reputation)
        self.db.write_db("event_history.json", history)
        
    def record_player_interaction(self, npc_name: str, topic: str, player_choice: str, outcome: str, relationship_change: int) -> None:
        """Update relationships and append dialogue interaction log to NPC memory."""
        npc_memories = self.db.read_db("npc_memory.json")
        reputation = self.db.read_db("reputation.json")
        history = self.db.read_db("event_history.json")
        
        target_nid = None
        for nid, mem in npc_memories.items():
            if mem["name"] == npc_name or npc_name in mem["name"]:
                target_nid = nid
                
                # Adjust individual trust
                trust = mem["relationships"]["player"]["trust"]
                mem["relationships"]["player"]["trust"] = max(0, min(100, trust + relationship_change))
                mem["relationships"]["player"]["sentiment"] = self._get_sentiment_tier(mem["relationships"]["player"]["trust"])
                mem["relationships"]["player"]["interaction_count"] += 1
                
                # Add interaction log
                mem["interactions"].append({
                    "timestamp": self._get_timestamp(),
                    "topic": topic,
                    "player_choice": player_choice,
                    "outcome": outcome
                })
                break
                
        if target_nid:
            current_npc_rep = reputation["player"]["npcs"].get(target_nid, 0)
            reputation["player"]["npcs"][target_nid] = max(-100, min(100, current_npc_rep + relationship_change))
            
            # Log to event history
            tick = self._get_next_tick_index(history)
            history.append({
                "tick_index": tick,
                "timestamp": self._get_timestamp(),
                "type": "PlayerInteraction",
                "description": f"Player talked to {npc_name} about '{topic}'. Choice: '{player_choice}'. Outcome: {outcome} ({relationship_change} relationship change).",
                "affected_entities": ["player", npc_name]
            })
            
            self.db.write_db("npc_memory.json", npc_memories)
            self.db.write_db("reputation.json", reputation)
            self.db.write_db("event_history.json", history)
            
    def _get_sentiment_tier(self, trust: int) -> str:
        if trust < 20: return "Hostile"
        if trust < 40: return "Unfriendly"
        if trust < 65: return "Neutral"
        if trust < 85: return "Friendly"
        return "Honored"
        
    # ══════════════════════════════════════════════════════════════════
    #  SIMULATION TICK RUNNER
    # ══════════════════════════════════════════════════════════════════
    
    def tick_daily(self) -> str:
        """Progresses active event durations, updates regional conditions, and relationship stats."""
        world_state = self.db.read_db("world_state.json")
        history = self.db.read_db("event_history.json")
        
        # 1. Update turns remaining for active events
        active_events = []
        expired_events = []
        for e in world_state["active_events"]:
            e["turns_remaining"] -= 1
            if e["turns_remaining"] > 0:
                active_events.append(e)
            else:
                expired_events.append(e["name"])
        world_state["active_events"] = active_events
        
        # 2. Random weather shifts in regional conditions
        weathers = ["Sunny", "Rainy", "Foggy", "Overcast", "Windy", "Stormy"]
        for region, cond in world_state["regional_conditions"].items():
            if random.random() < 0.4: # 40% chance of weather shift
                cond["weather"] = random.choice(weathers)
                
        # 3. Log tick
        tick = self._get_next_tick_index(history)
        event_desc = f"Day {tick} completed."
        if expired_events:
            event_desc += f" Events expired: {', '.join(expired_events)}."
            
        history.append({
            "tick_index": tick,
            "timestamp": self._get_timestamp(),
            "type": "DailyTick",
            "description": event_desc,
            "affected_entities": ["Eldoria"]
        })
        
        self.db.write_db("world_state.json", world_state)
        self.db.write_db("event_history.json", history)
        return event_desc
        
    def tick_weekly(self) -> str:
        """Triggers faction actions, relationship decay, event propagation, and weekly daily tick."""
        # 1. Daily tick processing
        daily_desc = self.tick_daily()
        
        world_state = self.db.read_db("world_state.json")
        reputation = self.db.read_db("reputation.json")
        npc_memories = self.db.read_db("npc_memory.json")
        history = self.db.read_db("event_history.json")
        
        tick = self._get_next_tick_index(history) - 1 # Use current tick index
        
        # 2. Faction Action generation
        faction_action_desc = ""
        factions = list(self.FACTIONS)
        if len(factions) >= 2:
            facA = random.choice(factions)
            factions.remove(facA)
            facB = random.choice(factions)
            
            action_types = ["Trade Treaty", "Border Dispute", "Skirmish", "Public Alliance"]
            act_type = random.choice(action_types)
            
            # Setup reputations defaults
            if facA not in reputation["faction_relations"]:
                reputation["faction_relations"][facA] = {}
            if facB not in reputation["faction_relations"]:
                reputation["faction_relations"][facB] = {}
                
            current_rel = reputation["faction_relations"][facA].get(facB, 0)
            
            if act_type == "Trade Treaty":
                delta = 15
                faction_action_desc = f"{facA} signed a trade treaty with {facB}, improving regional stability."
                world_state["kingdom_status"]["stability"] = min(100, world_state["kingdom_status"]["stability"] + 5)
                world_state["kingdom_status"]["wealth"] += 150
            elif act_type == "Border Dispute":
                delta = -10
                faction_action_desc = f"A minor border dispute occurred between {facA} and {facB}."
            elif act_type == "Skirmish":
                delta = -25
                faction_action_desc = f"A bloody skirmish broke out between {facA} forces and {facB} patrols."
                world_state["kingdom_status"]["stability"] = max(0, world_state["kingdom_status"]["stability"] - 8)
                world_state["kingdom_status"]["wealth"] = max(0, world_state["kingdom_status"]["wealth"] - 100)
            elif act_type == "Public Alliance":
                delta = 20
                faction_action_desc = f"{facA} and {facB} declared a public defensive alliance."
                world_state["kingdom_status"]["stability"] = min(100, world_state["kingdom_status"]["stability"] + 8)
                
            reputation["faction_relations"][facA][facB] = max(-100, min(100, current_rel + delta))
            reputation["faction_relations"][facB][facA] = reputation["faction_relations"][facA][facB]
            
            # Propagate memories of this Faction Action to NPCs in these factions
            for nid, mem in npc_memories.items():
                npc_fac = list(mem["faction_standing"].keys())[0] if mem["faction_standing"] else None
                if npc_fac in [facA, facB]:
                    mem["memories"].append({
                        "event_id": f"evt_fac_{tick}",
                        "description": f"Learned of the event: {faction_action_desc}",
                        "timestamp": self._get_timestamp(),
                        "emotional_impact": "Concerned" if delta < 0 else "Relieved",
                        "importance": 60
                    })
                    
        # 3. Relationship Decay
        # Decays player reputation to 0
        for fac in reputation["player"]["factions"]:
            val = reputation["player"]["factions"][fac]
            if val > 0: reputation["player"]["factions"][fac] -= 1
            elif val < 0: reputation["player"]["factions"][fac] += 1
            
        for nid in reputation["player"]["npcs"]:
            val = reputation["player"]["npcs"][nid]
            if val > 0: reputation["player"]["npcs"][nid] -= 1
            elif val < 0: reputation["player"]["npcs"][nid] += 1
            
        # Decays NPC trust level towards 50
        for nid, mem in npc_memories.items():
            trust = mem["relationships"]["player"]["trust"]
            if trust > 50: mem["relationships"]["player"]["trust"] -= 1
            elif trust < 50: mem["relationships"]["player"]["trust"] += 1
            mem["relationships"]["player"]["sentiment"] = self._get_sentiment_tier(mem["relationships"]["player"]["trust"])
            
        # 4. Event propagation (low stability triggers plague/rebellion)
        stability = world_state["kingdom_status"]["stability"]
        if stability < 40 and random.random() < 0.5:
            # Trigger rebellion
            has_reb = any(e["event_id"] == "evt_rebellion" for e in world_state["active_events"])
            if not has_reb:
                world_state["active_events"].append({
                    "event_id": "evt_rebellion",
                    "name": "Peasant Unrest & Rebellion",
                    "region": "Sundered Grove",
                    "severity": "High",
                    "turns_remaining": 4
                })
                faction_action_desc += " Low stability triggered Peasant Unrest in Sundered Grove."
                
        # 5. Log weekly update
        history.append({
            "tick_index": tick,
            "timestamp": self._get_timestamp(),
            "type": "WeeklyTick",
            "description": f"Weekly tick completed. Faction Action: {faction_action_desc}",
            "affected_entities": [facA, facB] if (facA and facB) else ["Eldoria"]
        })
        
        self.db.write_db("world_state.json", world_state)
        self.db.write_db("reputation.json", reputation)
        self.db.write_db("npc_memory.json", npc_memories)
        self.db.write_db("event_history.json", history)
        
        return faction_action_desc
        
    # ══════════════════════════════════════════════════════════════════
    #  ANALYTICS & REPORT GENERATOR
    # ══════════════════════════════════════════════════════════════════
    
    def generate_simulation_report(self) -> str:
        """Compile logs and state into simulation_report.md."""
        world_state = self.db.read_db("world_state.json")
        reputation = self.db.read_db("reputation.json")
        npc_memories = self.db.read_db("npc_memory.json")
        history = self.db.read_db("event_history.json")
        
        # Sort NPCs by trust
        sorted_npcs = []
        for nid, mem in npc_memories.items():
            sorted_npcs.append((mem["name"], mem["relationships"]["player"]["trust"], mem["relationships"]["player"]["sentiment"]))
        sorted_npcs.sort(key=lambda x: x[1], reverse=True)
        
        # Formulate Markdown Report
        md = "# StoryForge World Simulation Engine - Analytics Report\n\n"
        md += f"**Report Compiled At:** {self._get_timestamp()}\n"
        md += f"**Total Simulation Ticks:** {len(history)} ticks logged.\n\n"
        
        # 1. Kingdom Status
        md += "## 🏛️ Kingdom Status\n"
        ks = world_state["kingdom_status"]
        md += f"*   **Kingdom Name:** {ks['kingdom_name']}\n"
        md += f"*   **Current Ruler:** {ks['ruler']}\n"
        md += f"*   **Stability Index:** {ks['stability']}/100\n"
        md += f"*   **Treasury Wealth:** {ks['wealth']} gold\n"
        md += f"*   **Military Defense:** {ks['defense']}/100\n\n"
        
        # 2. Active Events & Regional Conditions
        md += "## 🌍 Active Events & Conditions\n"
        if world_state["active_events"]:
            md += "| Event | Region | Severity | Days Remaining |\n"
            md += "| :--- | :--- | :---: | :---: |\n"
            for e in world_state["active_events"]:
                md += f"| {e['name']} | {e['region']} | {e['severity']} | {e['turns_remaining']} |\n"
        else:
            md += "*No active global events.*\n"
        md += "\n"
        
        # 3. Player Reputation Standings
        md += "## 🤝 Faction Standing & Reputation\n"
        md += "| Faction | Reputation Score | Standing Tier |\n"
        md += "| :--- | :---: | :--- |\n"
        for fac, val in reputation["player"]["factions"].items():
            tier = "Neutral"
            if val < -50: tier = "Hostile"
            elif val < -10: tier = "Unfriendly"
            elif val > 80: tier = "Honored"
            elif val > 20: tier = "Friendly"
            md += f"| {fac} | {val:+} | {tier} |\n"
        md += "\n"
        
        # 4. NPC Relationship Rankings (Top 5)
        md += "## 👤 NPC Relationship Rankings (Top 5)\n"
        if sorted_npcs:
            md += "| NPC Name | Trust Level | Sentiment |\n"
            md += "| :--- | :---: | :--- |\n"
            for name, trust, sentiment in sorted_npcs[:5]:
                md += f"| {name} | {trust}/100 | {sentiment} |\n"
        else:
            md += "*No NPC relations tracked yet.*\n"
        md += "\n"
        
        # 5. Event History Logs (Last 10 events)
        md += "## 📅 Recent Event Logs (Last 10)\n"
        recent = history[-10:]
        recent.reverse()
        for log in recent:
            md += f"### Tick {log['tick_index']} - {log['type']} ({log['timestamp']})\n"
            md += f"{log['description']}\n"
            md += f"*Affected entities:* {', '.join(log['affected_entities'])}\n\n"
            
        # Write report to disk
        out_path = Path("simulation_report.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
            
        return md
