import json
import uuid
from typing import Dict, Any
from services.ai_service import AIService

class QuestGenerator:
    """Generates fully realized game Quest assets based on quest hooks and faction conflicts."""
    
    def __init__(self):
        self.ai = AIService()

    def generate_quest_from_hook(self, hook: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a schema-compliant Quest based on a generated quest hook."""
        system_prompt = (
            "You are an expert game quest writer.\n"
            "Build a fully realized, narrative-heavy Quest based on the provided quest hook.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"quest_id\": \"string\",\n"
            "  \"title\": \"string\",\n"
            "  \"description\": \"string\",\n"
            "  \"quest_type\": \"Main\" | \"Side\" | \"Faction\" | \"Companion\" | \"Random Event\",\n"
            "  \"objectives\": [\n"
            "    { \"objective_id\": \"string\", \"description\": \"string\", \"condition\": \"string\" }\n"
            "  ],\n"
            "  \"rewards\": [\n"
            "    { \"reward_type\": \"string\", \"amount\": \"string\" }\n"
            "  ],\n"
            "  \"outcomes\": [\n"
            "    { \"outcome_id\": \"success\" | \"failure\", \"description\": \"string\" }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Generate a Quest from this hook:\n"
            f"Title: {hook.get('title')}\n"
            f"Description: {hook.get('description')}\n"
            f"NPC Giver: {hook.get('npc_giver')}\n"
            f"Faction: {hook.get('faction')}\n"
            f"Objectives: {', '.join(hook.get('objectives', []))}\n"
            f"Suggested Rewards: {json.dumps(hook.get('suggested_rewards', []))}"
        )

        quest = {}
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
            if self.validate_quest(parsed):
                quest = self.heal_quest(parsed, hook)
        except Exception as e:
            print(f"[QuestGenerator] LLM quest generation failed: {e}. Falling back to rule-based quest.")

        if not quest:
            quest = self.generate_deterministically(hook)

        return quest

    def validate_quest(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict): return False
        required = ["quest_id", "title", "description", "quest_type", "objectives", "rewards", "outcomes"]
        if not all(r in data for r in required): return False
        if data["quest_type"] not in ["Main", "Side", "Faction", "Companion", "Random Event"]: return False
        if not isinstance(data["objectives"], list): return False
        if not isinstance(data["rewards"], list): return False
        if not isinstance(data["outcomes"], list): return False
        return True

    def heal_quest(self, data: Dict[str, Any], hook: Dict[str, Any]) -> Dict[str, Any]:
        objectives = []
        for idx, obj in enumerate(data.get("objectives", [])):
            if not isinstance(obj, dict): continue
            objectives.append({
                "objective_id": str(obj.get("objective_id") or f"obj_{idx+1}"),
                "description": str(obj.get("description") or "Complete quest step"),
                "condition": str(obj.get("condition") or "Completed")
            })
        if not objectives:
            objectives = [{"objective_id": "obj_01", "description": "Complete main quest target", "condition": "Objective Completed"}]

        rewards = []
        for r in data.get("rewards", []):
            if not isinstance(r, dict): continue
            rewards.append({
                "reward_type": str(r.get("reward_type") or "Gold"),
                "amount": str(r.get("amount") or "100")
            })
        if not rewards:
            rewards = [{"reward_type": "Gold", "amount": "100"}]

        outcomes = []
        for o in data.get("outcomes", []):
            if not isinstance(o, dict): continue
            outcomes.append({
                "outcome_id": str(o.get("outcome_id") or "outcome_step"),
                "description": str(o.get("description") or "Result of quest outcome")
            })
        if not outcomes:
            outcomes = [
                {"outcome_id": "success", "description": "Successfully completed hook mission."},
                {"outcome_id": "failure", "description": "Failed to complete hook mission."}
            ]

        return {
            "quest_id": str(hook.get("hook_id") or data.get("quest_id") or f"q_{uuid.uuid4().hex[:8]}"),
            "title": str(data.get("title") or hook.get("title") or "Fulfill Contract"),
            "description": str(data.get("description") or hook.get("description") or "No description provided."),
            "quest_type": data["quest_type"],
            "objectives": objectives,
            "rewards": rewards,
            "outcomes": outcomes
        }

    def generate_deterministically(self, hook: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based quest generator matching input hook values."""
        objectives = []
        for idx, obj_desc in enumerate(hook.get("objectives", ["Perform quest objectives"])):
            objectives.append({
                "objective_id": f"obj_det_{idx+1}",
                "description": obj_desc,
                "condition": "Fulfill action target"
            })

        rewards = []
        for r in hook.get("suggested_rewards", [{"reward_type": "Gold", "amount": "150"}]):
            rewards.append({
                "reward_type": r.get("reward_type", "Gold"),
                "amount": r.get("amount", "150")
            })

        return {
            "quest_id": hook.get("hook_id", f"q_{uuid.uuid4().hex[:8]}"),
            "title": hook.get("title", "Dynamic Duty"),
            "description": hook.get("description", "A dynamic contract generated from active events."),
            "quest_type": "Side" if "border" in hook.get("title", "").lower() else "Faction",
            "objectives": objectives,
            "rewards": rewards,
            "outcomes": [
                {"outcome_id": "success", "description": f"The threat of related event {hook.get('related_event_id')} was averted."},
                {"outcome_id": "failure", "description": f"The situation worsened for event {hook.get('related_event_id')}."}
            ]
        }
