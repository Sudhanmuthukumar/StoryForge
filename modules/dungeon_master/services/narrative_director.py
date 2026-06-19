import json
import uuid
from typing import List, Dict, Any
from services.ai_service import AIService
from modules.world_simulation.services.simulation_database import SimulationDatabase

class NarrativeDirector:
    """Manages the Story Arc Tracker and guides upcoming narrative paths, conflicts, and quest hooks."""
    
    def __init__(self):
        self.ai = AIService()

    def direct_narrative(self, db: SimulationDatabase, recent_consequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tracks story arc progression and plans the next narrative beats based on consequences and state."""
        world_state = db.read_db("world_state.json")
        npc_memory = db.read_db("npc_memory.json")
        reputation = db.read_db("reputation.json")
        
        # 1. Update Story Arc Tracker (progression checks)
        self.update_story_arcs(world_state)
        db.write_db("world_state.json", world_state)
        
        active_events = world_state.get("active_events", [])
        campaign_progress = world_state.get("campaign_progress", {})
        
        # System instructions to output narrative plan
        system_prompt = (
            "You are the Narrative Director for an AI Dungeon Master in a fantasy world.\n"
            "Formulate the next narrative plan based on the world state, active events, and recent consequences.\n"
            "CRITICAL: Do NOT invent completely new world-changing events. All plans and hooks must focus on resolving or escalating the validated active events.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"next_event_detail\": \"string\",\n"
            "  \"quest_hooks\": [\n"
            "    {\n"
            "      \"hook_id\": \"string\",\n"
            "      \"title\": \"string\",\n"
            "      \"description\": \"string\",\n"
            "      \"npc_giver\": \"string\",\n"
            "      \"faction\": \"string\",\n"
            "      \"related_event_id\": \"string\",\n"
            "      \"objectives\": [\"string\"],\n"
            "      \"suggested_rewards\": [\n"
            "        { \"reward_type\": \"string\", \"amount\": \"string\" }\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            "  \"escalating_conflicts\": [\"string\"],\n"
            "  \"character_arcs\": {\n"
            "    \"npc_id_or_name\": \"string\"\n"
            "  }\n"
            "}"
        )

        user_prompt = (
            f"Active Campaign Arc: {campaign_progress.get('active_arc_id', 'act_01')}\n"
            f"Active World Events: {json.dumps(active_events)}\n"
            f"Recent Consequences: {json.dumps(recent_consequences)}\n"
            "Generate the next logical narrative direction, character arcs, and quest hooks."
        )

        plan = {}
        try:
            full_user = user_prompt + "\n\nOutput ONLY a valid JSON object. Do not include markdown formatting."
            response_text = self.ai.generate_response(full_user, [
                {"source_type": "system", "source": "System Instructions", "content": system_prompt}
            ])
            raw = response_text.strip()
            if "```json" in raw:
                raw = raw.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in raw:
                raw = raw.split("```", 1)[1].split("```", 1)[0]
            raw = raw.strip()
            if "</think>" in raw:
                raw = raw.split("</think>", 1)[-1].strip()
                
            parsed = json.loads(raw)
            if self.validate_narrative_plan(parsed):
                plan = self.heal_narrative_plan(parsed, active_events)
        except Exception as e:
            print(f"[NarrativeDirector] LLM planning failed: {e}. Falling back to rule-based director.")
            
        if not plan:
            plan = self.direct_deterministically(world_state, npc_memory, recent_consequences)
            
        return plan

    def update_story_arcs(self, world_state: Dict[str, Any]) -> None:
        """Procedural story arc tracking. Progresses the campaign based on world state metrics."""
        campaign = world_state.setdefault("campaign_progress", {})
        if not campaign.get("current_campaign_id"):
            campaign["current_campaign_id"] = "campaign_01"
        if not campaign.get("active_arc_id"):
            campaign["active_arc_id"] = "act_01"
        if not campaign.get("active_regions"):
            campaign["active_regions"] = ["Shadowfen"]
            
        active_arc = campaign["active_arc_id"]
        stability = world_state.get("kingdom_status", {}).get("stability", 100)
        completed_quests_count = len(world_state.get("completed_quests", []))

        # Progression gates
        if active_arc == "act_01" and completed_quests_count >= 1:
            # Advance to Act II
            campaign["active_arc_id"] = "act_02"
            campaign.setdefault("completed_arcs", []).append("act_01")
            campaign.setdefault("active_regions", []).append("Sundered Grove")
        elif active_arc == "act_02" and completed_quests_count >= 3:
            # Advance to Act III
            campaign["active_arc_id"] = "act_03"
            campaign.setdefault("completed_arcs", []).append("act_02")
            campaign.setdefault("active_regions", []).append("Misty Mountains")

    def validate_narrative_plan(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict): return False
        required = ["next_event_detail", "quest_hooks", "escalating_conflicts", "character_arcs"]
        if not all(r in data for r in required): return False
        if not isinstance(data["quest_hooks"], list): return False
        if not isinstance(data["escalating_conflicts"], list): return False
        if not isinstance(data["character_arcs"], dict): return False
        return True

    def heal_narrative_plan(self, data: Dict[str, Any], active_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        healed_hooks = []
        for hook in data.get("quest_hooks", []):
            if not isinstance(hook, dict): continue
            
            # Ensure related_event_id refers to a valid active event
            rel_evt = hook.get("related_event_id")
            valid_evt_id = "general_quest"
            if active_events:
                valid_ids = [e["event_id"] for e in active_events]
                if rel_evt in valid_ids:
                    valid_evt_id = rel_evt
                else:
                    valid_evt_id = active_events[0]["event_id"]

            healed_hooks.append({
                "hook_id": str(hook.get("hook_id") or f"hook_{uuid.uuid4().hex[:8]}"),
                "title": str(hook.get("title") or "Dynamic Opportunity"),
                "description": str(hook.get("description") or "Details of the quest hook."),
                "npc_giver": str(hook.get("npc_giver") or "npc_001"),
                "faction": str(hook.get("faction") or "Kingdom of Eldoria"),
                "related_event_id": valid_evt_id,
                "objectives": [str(x) for x in hook.get("objectives", [])] or ["Complete objective"],
                "suggested_rewards": [
                    {
                        "reward_type": str(r.get("reward_type") or "Gold"),
                        "amount": str(r.get("amount") or "100")
                    } for r in hook.get("suggested_rewards", [])
                ] or [{"reward_type": "Gold", "amount": "100"}]
            })
            
        return {
            "next_event_detail": str(data.get("next_event_detail") or "The narrative flows naturally."),
            "quest_hooks": healed_hooks,
            "escalating_conflicts": [str(x) for x in data.get("escalating_conflicts", [])],
            "character_arcs": {str(k): str(v) for k, v in data.get("character_arcs", {}).items()}
        }

    def direct_deterministically(self, world_state: Dict[str, Any], npc_memory: Dict[str, Any], recent_consequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback rule-based narrative director matching validated simulation state changes."""
        active_events = world_state.get("active_events", [])
        campaign_progress = world_state.get("campaign_progress", {})
        active_arc = campaign_progress.get("active_arc_id", "act_01")
        
        # Default NPC name
        npc_name = "npc_001"
        for nid, mem in npc_memory.items():
            npc_name = mem.get("name")
            break

        plan = {
            "next_event_detail": "Tensions rise as the consequences of recent events spread to neighboring factions.",
            "quest_hooks": [],
            "escalating_conflicts": ["Factions begin securing border outposts due to regional instability."],
            "character_arcs": {npc_name: f"Reflects on the player's choices in {active_arc}."}
        }

        # If there are active events, link quest hooks directly to them
        if active_events:
            for idx, evt in enumerate(active_events):
                evt_name = evt.get("name", "")
                evt_id = evt.get("event_id", "")
                plan["next_event_detail"] = f"The crisis '{evt_name}' demands urgent resolution."
                
                # Check for crisis type and adapt hook
                if "peasant" in evt_name.lower() or "unrest" in evt_name.lower():
                    title = "Calm the Crowds"
                    desc = f"Unrest rises in the region. Speak to {npc_name} to negotiate or secure the town hall."
                    obj = ["Speak to town leaders", "Disperse rioters"]
                elif "skirmish" in evt_name.lower() or "conflict" in evt_name.lower() or "crisis" in evt_name.lower():
                    title = "Securing the Border"
                    desc = f"Resolve disputes rising from the active conflict event '{evt_name}'."
                    obj = ["Defend the border crossing", "Negotiate truce terms"]
                else:
                    title = "Resolve Local Crisis"
                    desc = f"Fulfill objectives to mitigate the threat of '{evt_name}'."
                    obj = ["Investigate the crisis source", "Report back to outpost"]

                plan["quest_hooks"].append({
                    "hook_id": f"hook_det_{uuid.uuid4().hex[:8]}_{idx}",
                    "title": title,
                    "description": desc,
                    "npc_giver": npc_name,
                    "faction": "Kingdom of Eldoria",
                    "related_event_id": evt_id,
                    "objectives": obj,
                    "suggested_rewards": [{"reward_type": "Gold", "amount": "150"}]
                })
        else:
            # General campaign hook
            active_regions = campaign_progress.get("active_regions") or ["Shadowfen"]
            region_name = active_regions[0] if active_regions else "Shadowfen"
            plan["quest_hooks"].append({
                "hook_id": f"hook_det_gen_{uuid.uuid4().hex[:8]}",
                "title": f"Explore {region_name}",
                "description": "Meet with local contacts to expand faction presence.",
                "npc_giver": npc_name,
                "faction": "Kingdom of Eldoria",
                "related_event_id": "general_quest",
                "objectives": ["Locate contact in tavern", "Perform errand quest"],
                "suggested_rewards": [{"reward_type": "Gold", "amount": "100"}]
            })

        return plan
