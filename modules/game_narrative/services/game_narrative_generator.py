import json
import uuid
from pathlib import Path
from services.ai_service import AIService
from modules.knowledge_engine.services.knowledge_database import KnowledgeDatabase

class GameNarrativeGenerator:
    """Core generator service for Phase 10 & 11 narrative game assets, verifying JSON schemas."""
    
    def __init__(self):
        self.ai = AIService()
        self.db = KnowledgeDatabase()
        
    def _call_llm_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Helper to invoke Ollama and parse structured JSON responses."""
        full_user = user_prompt + "\n\nOutput ONLY a valid JSON object matching the requested schema. Do not include markdown formatting like ```json or thinking tags."
        try:
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
                
            return json.loads(raw)
        except Exception as e:
            # Fallback mock schema compliant dictionary on failure
            print(f"[GameNarrativeGenerator] JSON Parse Error: {e}. Raw response: {response_text}")
            raise ValueError(f"LLM failed to output parseable JSON: {str(e)}")

    # ══════════════════════════════════════════════════════════════════
    #  CAMPAIGN PLANNER (Priority 1)
    # ══════════════════════════════════════════════════════════════════

    def generate_campaign(self, theme: str, region_count: int, pattern_id: str = None) -> dict:
        pattern_desc = "Standard pacing structure with rising actions and climaxes."
        pattern_name = "Epic Narrative Pacing"
        
        if pattern_id:
            for p in self.db.read_db("pacing_patterns.json"):
                if p.get("id") == pattern_id:
                    pattern_name = p.get("name")
                    pattern_desc = p.get("description")
                    break
                    
        system_prompt = (
            "You are an expert game narrative director. Generate a game campaign planner.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"theme\": \"string\",\n"
            "  \"story_arcs\": [\n"
            "    { \"arc_id\": \"string\", \"title\": \"string\", \"description\": \"string\", \"milestone\": \"string\" }\n"
            "  ],\n"
            "  \"regions\": [\n"
            "    {\n"
            "      \"region_name\": \"string\",\n"
            "      \"progression_index\": integer,\n"
            "      \"quest_chains\": [\n"
            "        { \"chain_id\": \"string\", \"title\": \"string\", \"quests\": [\"string\"], \"dependency_chain_id\": \"string\" or null }\n"
            "        ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate a campaign themed around '{theme}' across {region_count} regions.\n"
            f"Ground this design in the storytelling pacing pattern: '{pattern_name}' - {pattern_desc}."
        )
        
        try:
            raw_data = self._call_llm_json(system_prompt, user_prompt)
        except Exception:
            raw_data = {}
            
        return self.heal_campaign(raw_data, theme, region_count)

    def validate_campaign(self, data: dict) -> bool:
        if not isinstance(data, dict): return False
        if "theme" not in data or not isinstance(data["theme"], str): return False
        if "story_arcs" not in data or not isinstance(data["story_arcs"], list): return False
        for arc in data["story_arcs"]:
            if not isinstance(arc, dict): return False
            for f in ["arc_id", "title", "description", "milestone"]:
                if f not in arc or not isinstance(arc[f], str): return False
        if "regions" not in data or not isinstance(data["regions"], list): return False
        for reg in data["regions"]:
            if not isinstance(reg, dict): return False
            if "region_name" not in reg or not isinstance(reg["region_name"], str): return False
            if "progression_index" not in reg or not isinstance(reg["progression_index"], int): return False
            if "quest_chains" not in reg or not isinstance(reg["quest_chains"], list): return False
            for chain in reg["quest_chains"]:
                if not isinstance(chain, dict): return False
                for f in ["chain_id", "title"]:
                    if f not in chain or not isinstance(chain[f], str): return False
                if "quests" not in chain or not isinstance(chain["quests"], list): return False
                if "dependency_chain_id" not in chain: return False
        return True

    def heal_campaign(self, data: dict, theme: str, region_count: int) -> dict:
        if not isinstance(data, dict): data = {}
        healed = {
            "theme": data.get("theme") or theme or "Generic Campaign Theme",
            "story_arcs": [],
            "regions": []
        }
        
        for arc in data.get("story_arcs", []):
            if not isinstance(arc, dict): continue
            healed["story_arcs"].append({
                "arc_id": str(arc.get("arc_id") or uuid.uuid4().hex[:8]),
                "title": str(arc.get("title") or "Unnamed Act"),
                "description": str(arc.get("description") or "Narrative description."),
                "milestone": str(arc.get("milestone") or "Narrative climax.")
            })
            
        if not healed["story_arcs"]:
            healed["story_arcs"].append({
                "arc_id": "act_01",
                "title": "Act I: Arrival",
                "description": "The heroes arrive and establish their main camp.",
                "milestone": "Defeat the outpost commander."
            })
            
        for idx, reg in enumerate(data.get("regions", [])):
            if not isinstance(reg, dict): continue
            healed_reg = {
                "region_name": str(reg.get("region_name") or f"Region {idx+1}"),
                "progression_index": int(reg.get("progression_index") if reg.get("progression_index") is not None else idx),
                "quest_chains": []
            }
            for chain in reg.get("quest_chains", []):
                if not isinstance(chain, dict): continue
                healed_reg["quest_chains"].append({
                    "chain_id": str(chain.get("chain_id") or uuid.uuid4().hex[:8]),
                    "title": str(chain.get("title") or "Generic Questline"),
                    "quests": [str(q) for q in chain.get("quests", [])] if isinstance(chain.get("quests"), list) else ["Default Objective"],
                    "dependency_chain_id": chain.get("dependency_chain_id") if isinstance(chain.get("dependency_chain_id"), str) else None
                })
            healed["regions"].append(healed_reg)
            
        while len(healed["regions"]) < region_count:
            idx = len(healed["regions"])
            healed["regions"].append({
                "region_name": f"Area {idx+1}",
                "progression_index": idx,
                "quest_chains": [
                    {
                        "chain_id": f"chain_{idx+1}_a",
                        "title": f"Explore Area {idx+1}",
                        "quests": ["Find local contact", "Unlock gateway"],
                        "dependency_chain_id": None
                    }
                ]
            })
            
        return healed

    # ══════════════════════════════════════════════════════════════════
    #  DIALOGUE TREE BUILDER (Priority 2)
    # ══════════════════════════════════════════════════════════════════

    def generate_dialogue_tree(self, npc_context: str, topic: str, tone: str, pattern_id: str = None) -> dict:
        pattern_desc = "Realistic dialogue flow with distinct character voices."
        pattern_name = "Interactive Dialogue Branching"
        
        if pattern_id:
            for p in self.db.read_db("dialogue_patterns.json"):
                if p.get("id") == pattern_id:
                    pattern_name = p.get("name")
                    pattern_desc = p.get("description")
                    break
                    
        system_prompt = (
            "You are an expert game dialogue designer. Generate a branching dialogue tree.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"tree_id\": \"string\",\n"
            "  \"npc_name\": \"string\",\n"
            "  \"nodes\": [\n"
            "    {\n"
            "      \"node_id\": \"string\",\n"
            "      \"speaker\": \"string\",\n"
            "      \"text\": \"string\",\n"
            "      \"choices\": [\n"
            "        { \"text\": \"string\", \"target_node_id\": \"string\", \"condition\": \"string\" or null, \"consequence\": \"string\" or null }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate a branching dialogue tree for an NPC named '{npc_context}' on the topic: '{topic}' with a '{tone}' tone.\n"
            f"Leverage this dialogue pattern: '{pattern_name}' - {pattern_desc}.\n"
            "Provide at least 3 nodes showing clear choice branches, conditions (e.g. Reputation check) and consequences (e.g. triggers quest)."
        )
        
        # Check for World Simulation context
        sim_context = ""
        try:
            from modules.world_simulation.services.simulation_database import SimulationDatabase
            sim_db = SimulationDatabase()
            
            world_state = sim_db.read_db("world_state.json")
            reputation = sim_db.read_db("reputation.json")
            npc_memories = sim_db.read_db("npc_memory.json")
            
            # Find specific NPC memory by searching npc_context
            npc_mem = None
            for nid, mem in npc_memories.items():
                if mem.get("name") in npc_context or npc_context in mem.get("name"):
                    npc_mem = mem
                    break
            
            active_camp = world_state.get("campaign_progress", {}).get("current_campaign_id")
            
            sim_context = "\n=== PERSISTENT WORLD SIMULATION CONTEXT ===\n"
            if world_state.get("active_events"):
                sim_context += f"Active World Events: {json.dumps(world_state['active_events'])}\n"
            if world_state.get("kingdom_status"):
                sim_context += f"Kingdom Status: {json.dumps(world_state['kingdom_status'])}\n"
            if active_camp:
                sim_context += f"Active Campaign: {active_camp}\n"
            if npc_mem:
                if npc_mem.get("memories"):
                    sim_context += f"NPC Memories of past events: {json.dumps(npc_mem['memories'])}\n"
                if npc_mem.get("relationships"):
                    sim_context += f"NPC Relationship towards Player: {json.dumps(npc_mem['relationships'].get('player', {}))}\n"
                if npc_mem.get("faction_standing"):
                    sim_context += f"NPC Faction Standings: {json.dumps(npc_mem['faction_standing'])}\n"
            
            player_rep = reputation.get("player", {})
            if player_rep:
                sim_context += f"Player Faction Reputations: {json.dumps(player_rep.get('factions', {}))}\n"
                sim_context += f"Player NPC Reputations: {json.dumps(player_rep.get('npcs', {}))}\n"
                
            sim_context += "\nIMPORTANT: You must integrate the PERSISTENT WORLD SIMULATION CONTEXT into the dialogue tree. The NPC's dialogue, attitudes, and choices/conditions/consequences must react dynamically to their memories, the player's reputation, and active events.\n"
        except Exception:
            pass
            
        if sim_context:
            user_prompt += sim_context
            
        try:
            raw_data = self._call_llm_json(system_prompt, user_prompt)
        except Exception:
            raw_data = {}
            
        return self.heal_dialogue(raw_data, npc_context)

    def validate_dialogue(self, data: dict) -> bool:
        if not isinstance(data, dict): return False
        if "tree_id" not in data or not isinstance(data["tree_id"], str): return False
        if "npc_name" not in data or not isinstance(data["npc_name"], str): return False
        if "nodes" not in data or not isinstance(data["nodes"], list): return False
        for node in data["nodes"]:
            if not isinstance(node, dict): return False
            for f in ["node_id", "speaker", "text"]:
                if f not in node or not isinstance(node[f], str): return False
            if "choices" not in node or not isinstance(node["choices"], list): return False
            for choice in node["choices"]:
                if not isinstance(choice, dict): return False
                for f in ["text", "target_node_id"]:
                    if f not in choice or not isinstance(choice[f], str): return False
                if "condition" not in choice or "consequence" not in choice: return False
        return True

    def heal_dialogue(self, data: dict, default_npc: str) -> dict:
        if not isinstance(data, dict): data = {}
        healed = {
            "tree_id": data.get("tree_id") or f"dialogue_{uuid.uuid4().hex[:8]}",
            "npc_name": data.get("npc_name") or default_npc or "Unknown NPC",
            "nodes": []
        }
        
        for n in data.get("nodes", []):
            if not isinstance(n, dict): continue
            healed_node = {
                "node_id": str(n.get("node_id") or uuid.uuid4().hex[:8]),
                "speaker": str(n.get("speaker") or healed["npc_name"]),
                "text": str(n.get("text") or "..."),
                "choices": []
            }
            for c in n.get("choices", []):
                if not isinstance(c, dict): continue
                healed_node["choices"].append({
                    "text": str(c.get("text") or "Continue"),
                    "target_node_id": str(c.get("target_node_id") or "exit"),
                    "condition": c.get("condition") if isinstance(c.get("condition"), str) else None,
                    "consequence": c.get("consequence") if isinstance(c.get("consequence"), str) else None
                })
            healed["nodes"].append(healed_node)
            
        if not healed["nodes"]:
            healed["nodes"].append({
                "node_id": "start",
                "speaker": healed["npc_name"],
                "text": "Hello traveler. What brings you to these lands?",
                "choices": [
                    {"text": "Just looking around.", "target_node_id": "neutral_response", "condition": None, "consequence": None},
                    {"text": "I'm looking for work.", "target_node_id": "quest_offer", "condition": None, "consequence": "GiveQuest_01"}
                ]
            })
            healed["nodes"].append({
                "node_id": "neutral_response",
                "speaker": healed["npc_name"],
                "text": "Safe travels then. Be careful of wolves.",
                "choices": []
            })
            healed["nodes"].append({
                "node_id": "quest_offer",
                "speaker": healed["npc_name"],
                "text": "Indeed? Go clear the wolves from the northern grove.",
                "choices": []
            })
            
        return healed

    # ══════════════════════════════════════════════════════════════════
    #  QUEST FORGE (Priority 3)
    # ══════════════════════════════════════════════════════════════════

    def generate_quest(self, quest_type: str, pattern_id: str = None) -> dict:
        pattern_desc = "Classic conflict driving stakes and objective structures."
        pattern_name = "Heroic Quest Conflict"
        
        if pattern_id:
            for p in self.db.read_db("conflict_patterns.json") + self.db.read_db("scene_patterns.json"):
                if p.get("id") == pattern_id:
                    pattern_name = p.get("name")
                    pattern_desc = p.get("description")
                    break
                    
        system_prompt = (
            "You are an expert quest designer. Generate a structured quest file.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"quest_id\": \"string\",\n"
            "  \"title\": \"string\",\n"
            "  \"description\": \"string\",\n"
            "  \"quest_type\": \"string\",\n"
            "  \"objectives\": [\n"
            "    { \"objective_id\": \"string\", \"description\": \"string\", \"condition\": \"string\" }\n"
            "  ],\n"
            "  \"rewards\": [\n"
            "    { \"reward_type\": \"string\", \"amount\": \"string\" }\n"
            "  ],\n"
            "  \"outcomes\": [\n"
            "    { \"outcome_id\": \"string\", \"description\": \"string\" }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate a '{quest_type}' quest. Ground it in this conflict/scene pattern: '{pattern_name}' - {pattern_desc}.\n"
            "Structure logical objectives, rewards (gold, xp, reputation), and narrative outcomes."
        )
        
        try:
            raw_data = self._call_llm_json(system_prompt, user_prompt)
        except Exception:
            raw_data = {}
            
        return self.heal_quest(raw_data, quest_type)

    def validate_quest(self, data: dict) -> bool:
        if not isinstance(data, dict): return False
        for f in ["quest_id", "title", "description", "quest_type"]:
            if f not in data or not isinstance(data[f], str): return False
        if data["quest_type"] not in ["Main", "Side", "Faction", "Companion", "Random Event"]: return False
        
        if "objectives" not in data or not isinstance(data["objectives"], list): return False
        for obj in data["objectives"]:
            if not isinstance(obj, dict): return False
            for f in ["objective_id", "description", "condition"]:
                if f not in obj or not isinstance(obj[f], str): return False
                
        if "rewards" not in data or not isinstance(data["rewards"], list): return False
        for rwd in data["rewards"]:
            if not isinstance(rwd, dict): return False
            for f in ["reward_type", "amount"]:
                if f not in rwd or not isinstance(rwd[f], str): return False
                
        if "outcomes" not in data or not isinstance(data["outcomes"], list): return False
        for otc in data["outcomes"]:
            if not isinstance(otc, dict): return False
            for f in ["outcome_id", "description"]:
                if f not in otc or not isinstance(otc[f], str): return False
        return True

    def heal_quest(self, data: dict, quest_type: str) -> dict:
        if not isinstance(data, dict): data = {}
        healed = {
            "quest_id": data.get("quest_id") or f"quest_{uuid.uuid4().hex[:8]}",
            "title": data.get("title") or "A New Adventure",
            "description": data.get("description") or "No description provided.",
            "quest_type": data.get("quest_type") if data.get("quest_type") in ["Main", "Side", "Faction", "Companion", "Random Event"] else quest_type,
            "objectives": [],
            "rewards": [],
            "outcomes": []
        }
        
        for obj in data.get("objectives", []):
            if not isinstance(obj, dict): continue
            healed["objectives"].append({
                "objective_id": str(obj.get("objective_id") or uuid.uuid4().hex[:8]),
                "description": str(obj.get("description") or "Perform task."),
                "condition": str(obj.get("condition") or "TriggerComplete")
            })
            
        if not healed["objectives"]:
            healed["objectives"].append({
                "objective_id": "obj_01",
                "description": "Speak to the local merchant.",
                "condition": "TalkToMerchant"
            })
            
        for rwd in data.get("rewards", []):
            if not isinstance(rwd, dict): continue
            healed["rewards"].append({
                "reward_type": str(rwd.get("reward_type") or "Experience"),
                "amount": str(rwd.get("amount") or "100")
            })
            
        if not healed["rewards"]:
            healed["rewards"].append({"reward_type": "Gold", "amount": "50"})
            
        for otc in data.get("outcomes", []):
            if not isinstance(otc, dict): continue
            healed["outcomes"].append({
                "outcome_id": str(otc.get("outcome_id") or uuid.uuid4().hex[:8]),
                "description": str(otc.get("description") or "The quest was completed successfully.")
            })
            
        if not healed["outcomes"]:
            healed["outcomes"].append({
                "outcome_id": "outcome_success",
                "description": "The town's safety was secured."
            })
            
        return healed

    # ══════════════════════════════════════════════════════════════════
    #  NPC STUDIO (Priority 4)
    # ══════════════════════════════════════════════════════════════════

    def generate_npc(self, pattern_id: str = None) -> dict:
        pattern_desc = "Strong character archetype with deep internal motivations."
        pattern_name = "Tolkien Archetype"
        
        if pattern_id:
            for p in self.db.read_db("character_patterns.json"):
                if p.get("id") == pattern_id:
                    pattern_name = p.get("name")
                    pattern_desc = p.get("description")
                    break
                    
        system_prompt = (
            "You are an expert RPG game writer. Generate a structured NPC sheet.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"npc_id\": \"string\",\n"
            "  \"name\": \"string\",\n"
            "  \"archetype\": \"string\",\n"
            "  \"motivation\": \"string\",\n"
            "  \"secret\": \"string\",\n"
            "  \"faction\": \"string\",\n"
            "  \"relationships\": [\n"
            "    { \"target_npc\": \"string\", \"relation_type\": \"string\", \"level\": integer }\n"
            "  ],\n"
            "  \"dialogue_style\": \"string\",\n"
            "  \"quest_hooks\": [ \"string\" ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate a game NPC. Ground this design in the character pattern: '{pattern_name}' - {pattern_desc}.\n"
            "Ensure they have a unique name, strong motivation, relationships, dialogue style description, and quest hooks."
        )
        
        try:
            raw_data = self._call_llm_json(system_prompt, user_prompt)
        except Exception:
            raw_data = {}
            
        return self.heal_npc(raw_data)

    def validate_npc(self, data: dict) -> bool:
        if not isinstance(data, dict): return False
        required_fields = ["npc_id", "name", "archetype", "motivation", "secret", "faction", "relationships", "dialogue_style", "quest_hooks"]
        for f in required_fields:
            if f not in data: return False
        if not isinstance(data["relationships"], list) or not isinstance(data["quest_hooks"], list): return False
        for rel in data["relationships"]:
            if not isinstance(rel, dict): return False
            for f in ["target_npc", "relation_type"]:
                if f not in rel or not isinstance(rel[f], str): return False
            if "level" not in rel or not isinstance(rel["level"], int): return False
        return True

    def heal_npc(self, data: dict) -> dict:
        if not isinstance(data, dict): data = {}
        healed = {
            "npc_id": data.get("npc_id") or f"npc_{uuid.uuid4().hex[:8]}",
            "name": data.get("name") or "Eldrin the Wise",
            "archetype": data.get("archetype") or "Sage",
            "motivation": data.get("motivation") or "Reclaim lost scrolls.",
            "secret": data.get("secret") or "He was once an exile.",
            "faction": data.get("faction") or "Mages Guild",
            "relationships": [],
            "dialogue_style": data.get("dialogue_style") or "Eloquent, speaks in metaphors.",
            "quest_hooks": [str(h) for h in data.get("quest_hooks", [])] if isinstance(data.get("quest_hooks"), list) else []
        }
        
        for rel in data.get("relationships", []):
            if not isinstance(rel, dict): continue
            healed["relationships"].append({
                "target_npc": str(rel.get("target_npc") or "Unknown NPC"),
                "relation_type": str(rel.get("relation_type") or "Neutral"),
                "level": int(rel.get("level") if rel.get("level") is not None else 0)
            })
            
        if not healed["relationships"]:
            healed["relationships"].append({
                "target_npc": "The King",
                "relation_type": "Adviser",
                "level": 80
            })
            
        if not healed["quest_hooks"]:
            healed["quest_hooks"].append("The Lost Archive scroll needs retrieval.")
            
        return healed

    # ══════════════════════════════════════════════════════════════════
    #  LORE ENGINE (Priority 5)
    # ══════════════════════════════════════════════════════════════════

    def generate_lore(self, category: str, pattern_id: str = None) -> dict:
        pattern_desc = "Cohesive lore establishing history, culture, and key facts."
        pattern_name = "Ancient Worldbuilding"
        
        if pattern_id:
            for p in self.db.read_db("worldbuilding_patterns.json"):
                if p.get("id") == pattern_id:
                    pattern_name = p.get("name")
                    pattern_desc = p.get("description")
                    break
                    
        system_prompt = (
            "You are an expert world builder. Generate a lore database asset.\n"
            "You must output a JSON object adhering exactly to this schema:\n"
            "{\n"
            "  \"lore_id\": \"string\",\n"
            "  \"name\": \"string\",\n"
            "  \"category\": \"string\",\n"
            "  \"summary\": \"string\",\n"
            "  \"historical_events\": [\n"
            "    { \"event_name\": \"string\", \"date\": \"string\", \"description\": \"string\" }\n"
            "  ],\n"
            "  \"core_beliefs\": [ \"string\" ],\n"
            "  \"key_figures\": [\n"
            "    { \"name\": \"string\", \"role\": \"string\", \"description\": \"string\" }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate lore for category '{category}'. Ground this in this worldbuilding pattern: '{pattern_name}' - {pattern_desc}.\n"
            "Structure clear beliefs, events, and key figures."
        )
        
        try:
            raw_data = self._call_llm_json(system_prompt, user_prompt)
        except Exception:
            raw_data = {}
            
        return self.heal_lore(raw_data, category)

    def validate_lore(self, data: dict) -> bool:
        if not isinstance(data, dict): return False
        required_fields = ["lore_id", "name", "category", "summary", "historical_events", "core_beliefs", "key_figures"]
        for f in required_fields:
            if f not in data: return False
        if data["category"] not in ["Kingdom", "Culture", "Religion", "Guild", "Historical Event"]: return False
        
        if not isinstance(data["historical_events"], list) or not isinstance(data["core_beliefs"], list) or not isinstance(data["key_figures"], list):
            return False
            
        for evt in data["historical_events"]:
            if not isinstance(evt, dict): return False
            for f in ["event_name", "date", "description"]:
                if f not in evt or not isinstance(evt[f], str): return False
                
        for fig in data["key_figures"]:
            if not isinstance(fig, dict): return False
            for f in ["name", "role", "description"]:
                if f not in fig or not isinstance(fig[f], str): return False
        return True

    def heal_lore(self, data: dict, category: str) -> dict:
        if not isinstance(data, dict): data = {}
        healed = {
            "lore_id": data.get("lore_id") or f"lore_{uuid.uuid4().hex[:8]}",
            "name": data.get("name") or "The Kingdom of Silvergard",
            "category": data.get("category") if data.get("category") in ["Kingdom", "Culture", "Religion", "Guild", "Historical Event"] else category,
            "summary": data.get("summary") or "A peaceful kingdom nestled between mountains.",
            "historical_events": [],
            "core_beliefs": [str(b) for b in data.get("core_beliefs", [])] if isinstance(data.get("core_beliefs"), list) else [],
            "key_figures": []
        }
        
        for evt in data.get("historical_events", []):
            if not isinstance(evt, dict): continue
            healed["historical_events"].append({
                "event_name": str(evt.get("event_name") or "Great Battle"),
                "date": str(evt.get("date") or "Year 0"),
                "description": str(evt.get("description") or "Historical clash.")
            })
            
        if not healed["historical_events"]:
            healed["historical_events"].append({
                "event_name": "The Founding",
                "date": "Year 100 AE",
                "description": "Silvergard was established by King Silverheart."
            })
            
        if not healed["core_beliefs"]:
            healed["core_beliefs"].append("Honor above all.")
            
        for fig in data.get("key_figures", []):
            if not isinstance(fig, dict): continue
            healed["key_figures"].append({
                "name": str(fig.get("name") or "Lord Commander"),
                "role": str(fig.get("role") or "Defender"),
                "description": str(fig.get("description") or "Protects the realm.")
            })
            
        if not healed["key_figures"]:
            healed["key_figures"].append({
                "name": "King Alistair",
                "role": "Ruler",
                "description": "The current monarch of Silvergard."
            })
            
        return healed
