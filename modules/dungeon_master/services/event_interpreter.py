import json
import uuid
from typing import List, Dict, Any
from services.ai_service import AIService

class EventInterpreter:
    """Interprets recent simulation event history and player actions into narrative consequences."""
    
    def __init__(self):
        self.ai = AIService()

    def interpret_events(self, recent_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts raw event logs into structured narrative consequences."""
        if not recent_logs:
            return []

        # System Prompt instructing the LLM to analyze and output consequence JSON
        system_prompt = (
            "You are the Event Interpreter for an AI Dungeon Master in a fantasy world.\n"
            "Analyze the provided event logs and generate a JSON list of narrative consequences.\n"
            "Output must adhere strictly to this schema:\n"
            "[\n"
            "  {\n"
            "    \"consequence_id\": \"string\",\n"
            "    \"type\": \"faction_conflict\" | \"world_event\" | \"relationship_change\" | \"campaign_evolution\",\n"
            "    \"description\": \"string\",\n"
            "    \"affected_entities\": [\"string\"],\n"
            "    \"severity\": \"Low\" | \"Medium\" | \"High\" | \"Critical\",\n"
            "    \"mutations\": {\n"
            "      \"stability_delta\": integer,\n"
            "      \"wealth_delta\": integer,\n"
            "      \"defense_delta\": integer,\n"
            "      \"reputation_deltas\": { \"FactionOrNPCName\": integer }\n"
            "    }\n"
            "  }\n"
            "]"
        )

        user_prompt = "Interpret these recent events into narrative consequences:\n\n"
        for log in recent_logs:
            user_prompt += f"- [{log.get('type', 'Unknown')}] (Tick {log.get('tick_index', 0)}): {log.get('description', '')}\n"
            user_prompt += f"  Affected: {', '.join(log.get('affected_entities', []))}\n"

        consequences = []
        try:
            full_user = user_prompt + "\n\nOutput ONLY a valid JSON array. Do not include markdown formatting."
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
            if isinstance(parsed, list):
                for item in parsed:
                    if self.validate_consequence(item):
                        consequences.append(self.heal_consequence(item))
        except Exception as e:
            print(f"[EventInterpreter] LLM interpretation failed: {e}. Falling back to deterministic rules.")

        # Fallback to deterministic consequence generation if LLM fails or yields nothing
        if not consequences:
            consequences = self.interpret_deterministically(recent_logs)

        return consequences

    def validate_consequence(self, item: Dict[str, Any]) -> bool:
        if not isinstance(item, dict): return False
        required = ["consequence_id", "type", "description", "affected_entities", "severity", "mutations"]
        if not all(r in item for r in required): return False
        if item["type"] not in ["faction_conflict", "world_event", "relationship_change", "campaign_evolution"]: return False
        if item["severity"] not in ["Low", "Medium", "High", "Critical"]: return False
        if not isinstance(item["affected_entities"], list): return False
        if not isinstance(item["mutations"], dict): return False
        return True

    def heal_consequence(self, item: Dict[str, Any]) -> Dict[str, Any]:
        mutations = item.get("mutations") or {}
        return {
            "consequence_id": str(item.get("consequence_id") or f"cons_{uuid.uuid4().hex[:8]}"),
            "type": item["type"],
            "description": str(item.get("description") or "A narrative consequence occurs."),
            "affected_entities": [str(x) for x in item.get("affected_entities", [])],
            "severity": item["severity"],
            "mutations": {
                "stability_delta": int(mutations.get("stability_delta", 0)),
                "wealth_delta": int(mutations.get("wealth_delta", 0)),
                "defense_delta": int(mutations.get("defense_delta", 0)),
                "reputation_deltas": {str(k): int(v) for k, v in mutations.get("reputation_deltas", {}).items()}
            }
        }

    def interpret_deterministically(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback rule-based interpreter ensuring deterministic results in offline environments."""
        consequences = []
        for idx, log in enumerate(logs):
            ltype = log.get("type", "")
            desc = log.get("description", "")
            affected = log.get("affected_entities", [])
            cid = f"cons_det_{uuid.uuid4().hex[:8]}_{idx}"

            if "skirmish" in desc.lower() or "skirmish" in ltype.lower():
                consequences.append({
                    "consequence_id": cid,
                    "type": "faction_conflict",
                    "description": f"The armed skirmish leaves local communities in terror. Factions are on high alert.",
                    "affected_entities": affected,
                    "severity": "High",
                    "mutations": {
                        "stability_delta": -10,
                        "wealth_delta": -50,
                        "defense_delta": 5,
                        "reputation_deltas": {affected[0]: -10, affected[1]: -10} if len(affected) >= 2 else {}
                    }
                })
            elif "trade treaty" in desc.lower():
                consequences.append({
                    "consequence_id": cid,
                    "type": "world_event",
                    "description": f"New trade routes open. Regional wealth rises, boosting general commerce.",
                    "affected_entities": affected,
                    "severity": "Low",
                    "mutations": {
                        "stability_delta": 5,
                        "wealth_delta": 100,
                        "defense_delta": 0,
                        "reputation_deltas": {affected[0]: 5, affected[1]: 5} if len(affected) >= 2 else {}
                    }
                })
            elif "border dispute" in desc.lower():
                consequences.append({
                    "consequence_id": cid,
                    "type": "faction_conflict",
                    "description": f"Tension builds along borderlands. Guards double patrols.",
                    "affected_entities": affected,
                    "severity": "Medium",
                    "mutations": {
                        "stability_delta": -5,
                        "wealth_delta": -20,
                        "defense_delta": 10,
                        "reputation_deltas": {}
                    }
                })
            elif "public alliance" in desc.lower():
                consequences.append({
                    "consequence_id": cid,
                    "type": "campaign_evolution",
                    "description": f"The public alliance shifts regional power balances, deterring external threats.",
                    "affected_entities": affected,
                    "severity": "Medium",
                    "mutations": {
                        "stability_delta": 10,
                        "wealth_delta": 20,
                        "defense_delta": 15,
                        "reputation_deltas": {}
                    }
                })
            elif ltype == "QuestOutcome":
                outcome = "success" if "success" in desc.lower() else "failure"
                npc_name = affected[1] if len(affected) >= 2 else "Unknown NPC"
                consequences.append({
                    "consequence_id": cid,
                    "type": "relationship_change",
                    "description": f"Player's quest {outcome} alters how {npc_name} views their reliability.",
                    "affected_entities": affected,
                    "severity": "Low",
                    "mutations": {
                        "stability_delta": 2 if outcome == "success" else -2,
                        "wealth_delta": 50 if outcome == "success" else -10,
                        "defense_delta": 0,
                        "reputation_deltas": {npc_name: 10 if outcome == "success" else -10}
                    }
                })
        
        # Default fallback if nothing else matches
        if not consequences:
            consequences.append({
                "consequence_id": f"cons_det_gen_{uuid.uuid4().hex[:8]}",
                "type": "world_event",
                "description": "General calm settles across the realm, allowing recovery.",
                "affected_entities": ["Eldoria"],
                "severity": "Low",
                "mutations": {
                    "stability_delta": 1,
                    "wealth_delta": 10,
                    "defense_delta": 0,
                    "reputation_deltas": {}
                }
            })
            
        return consequences
