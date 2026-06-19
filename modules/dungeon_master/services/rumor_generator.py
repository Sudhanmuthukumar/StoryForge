import json
import uuid
from typing import Dict, Any, List
from services.ai_service import AIService
from modules.world_simulation.services.simulation_database import SimulationDatabase

class RumorGenerator:
    """Generates reactive rumors, public bulletins, and confidential reports based on world events."""
    
    def __init__(self):
        self.ai = AIService()

    def generate_rumors(self, db: SimulationDatabase) -> Dict[str, Any]:
        """Creates schema-compliant rumors and news reports based on the latest world state."""
        world_state = db.read_db("world_state.json")
        reputation = db.read_db("reputation.json")
        
        active_events = world_state.get("active_events", [])
        kingdom_status = world_state.get("kingdom_status", {})
        
        system_prompt = (
            "You are a gossip master and news herald in a fantasy world.\n"
            "Given the current world state, generate a JSON object containing rumors, bulletins, and briefings.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"tavern_rumors\": [\n"
            "    { \"rumor_id\": \"string\", \"speaker\": \"string\", \"text\": \"string\", \"location\": \"string\", \"credibility\": \"Low\" | \"Medium\" | \"High\" }\n"
            "  ],\n"
            "  \"news_bulletins\": [\n"
            "    { \"bulletin_id\": \"string\", \"headline\": \"string\", \"body\": \"string\", \"issuer\": \"string\" }\n"
            "  ],\n"
            "  \"faction_reports\": [\n"
            "    { \"report_id\": \"string\", \"faction\": \"string\", \"subject\": \"string\", \"content\": \"string\", \"security_clearance\": \"Public\" | \"Confidential\" | \"Top Secret\" }\n"
            "  ],\n"
            "  \"regional_updates\": [\n"
            "    { \"update_id\": \"string\", \"region\": \"string\", \"status\": \"string\", \"danger_level\": \"Low\" | \"Medium\" | \"High\" | \"Critical\", \"weather\": \"string\" }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Kingdom Status: {json.dumps(kingdom_status)}\n"
            f"Active World Events: {json.dumps(active_events)}\n"
            "Generate tavern rumors, news bulletins, faction reports, and regional updates based on these conditions."
        )

        rumors = {}
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
            if self.validate_rumors(parsed):
                rumors = self.heal_rumors(parsed)
        except Exception as e:
            print(f"[RumorGenerator] LLM rumors generation failed: {e}. Falling back to rule-based rumors.")

        if not rumors:
            rumors = self.generate_deterministically(world_state)

        return rumors

    def validate_rumors(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict): return False
        required = ["tavern_rumors", "news_bulletins", "faction_reports", "regional_updates"]
        if not all(r in data for r in required): return False
        if not isinstance(data["tavern_rumors"], list): return False
        if not isinstance(data["news_bulletins"], list): return False
        if not isinstance(data["faction_reports"], list): return False
        if not isinstance(data["regional_updates"], list): return False
        return True

    def heal_rumors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        healed = {
            "tavern_rumors": [],
            "news_bulletins": [],
            "faction_reports": [],
            "regional_updates": []
        }

        for r in data.get("tavern_rumors", []):
            if not isinstance(r, dict): continue
            healed["tavern_rumors"].append({
                "rumor_id": str(r.get("rumor_id") or f"rum_{uuid.uuid4().hex[:8]}"),
                "speaker": str(r.get("speaker") or "Commoner"),
                "text": str(r.get("text") or "Strange things are happening..."),
                "location": str(r.get("location") or "The Golden Flask Tavern"),
                "credibility": r.get("credibility") if r.get("credibility") in ["Low", "Medium", "High"] else "Medium"
            })

        for b in data.get("news_bulletins", []):
            if not isinstance(b, dict): continue
            healed["news_bulletins"].append({
                "bulletin_id": str(b.get("bulletin_id") or f"bul_{uuid.uuid4().hex[:8]}"),
                "headline": str(b.get("headline") or "Kingdom Proclamation"),
                "body": str(b.get("body") or "Hear ye, hear ye!"),
                "issuer": str(b.get("issuer") or "Town Crier")
            })

        for f in data.get("faction_reports", []):
            if not isinstance(f, dict): continue
            healed["faction_reports"].append({
                "report_id": str(f.get("report_id") or f"rep_{uuid.uuid4().hex[:8]}"),
                "faction": str(f.get("faction") or "Kingdom of Eldoria"),
                "subject": str(f.get("subject") or "Security Alert"),
                "content": str(f.get("content") or "Maintain defensive postures."),
                "security_clearance": f.get("security_clearance") if f.get("security_clearance") in ["Public", "Confidential", "Top Secret"] else "Confidential"
            })

        for u in data.get("regional_updates", []):
            if not isinstance(u, dict): continue
            healed["regional_updates"].append({
                "update_id": str(u.get("update_id") or f"upd_{uuid.uuid4().hex[:8]}"),
                "region": str(u.get("region") or "Shadowfen"),
                "status": str(u.get("status") or "Stable"),
                "danger_level": u.get("danger_level") if u.get("danger_level") in ["Low", "Medium", "High", "Critical"] else "Low",
                "weather": str(u.get("weather") or "Sunny")
            })

        return healed

    def generate_deterministically(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based rumors generator matching validated simulation state changes."""
        active_events = world_state.get("active_events", [])
        stability = world_state.get("kingdom_status", {}).get("stability", 100)

        healed = {
            "tavern_rumors": [],
            "news_bulletins": [],
            "faction_reports": [],
            "regional_updates": []
        }

        # 1. Tavern Rumors
        if active_events:
            evt_name = active_events[0].get("name", "the crisis")
            healed["tavern_rumors"].append({
                "rumor_id": "rum_det_01",
                "speaker": "Barnaby, tavern patron",
                "text": f"They say the guards are terrified of {evt_name}! Nobody wants to walk the roads after dark.",
                "location": "The Golden Flask Tavern",
                "credibility": "Medium"
            })
        else:
            healed["tavern_rumors"].append({
                "rumor_id": "rum_det_01",
                "speaker": "Elara, traveling merchant",
                "text": "The roads are quiet today. Almost too quiet. Let's hope the bandits stay in their caves.",
                "location": "The Golden Flask Tavern",
                "credibility": "Low"
            })

        # 2. News Bulletins
        healed["news_bulletins"].append({
            "bulletin_id": "bul_det_01",
            "headline": f"By Royal Decree: Stability stands at {stability}%",
            "body": "The Crown commands all citizens to report any suspicious activities or faction recruitments to local guards.",
            "issuer": "Lord Commander Vance"
        })

        # 3. Faction Reports
        healed["faction_reports"].append({
            "report_id": "rep_det_01",
            "faction": "The Order of Sunfire",
            "subject": "Weekly Threat Assessment",
            "content": f"Active security threats in area: {len(active_events)} active crises detected. Bolster gate defense.",
            "security_clearance": "Confidential"
        })

        # 4. Regional Updates
        regions = world_state.get("campaign_progress", {}).get("active_regions", ["Shadowfen"])
        for idx, r in enumerate(regions):
            cond = world_state.get("regional_conditions", {}).get(r, {})
            healed["regional_updates"].append({
                "update_id": f"upd_det_{idx+1}",
                "region": r,
                "status": "Alert" if active_events else "Calm",
                "danger_level": "High" if active_events else "Low",
                "weather": cond.get("weather", "Sunny")
            })

        return healed
