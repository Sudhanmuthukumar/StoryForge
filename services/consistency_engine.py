import json
from pathlib import Path

CONFIG_PATH = Path("c:/StoryForge AI/config/consistency_rules.json")

class ConsistencyEngine:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "fact_conflicts": {},
                "character_conflicts": {},
                "relationship_conflicts": {}
            }

    def check_consistency(self, memory_dict: dict, analysis_dict: dict) -> dict:
        """Analyzes structured memory and analysis data for continuity contradictions."""
        consistency = {
            "consistency_score": 100,
            "fact_conflicts": [],
            "relationship_conflicts": [],
            "character_conflicts": [],
            "continuity_conflicts": [],
            "flags": []
        }

        chars = memory_dict.get("characters", [])
        rels = memory_dict.get("relationships", [])

        penalties = {"Critical": 25, "High": 15, "Medium": 10, "Low": 5}
        total_penalty = 0

        def _add_conflict(category: str, rule: dict, name: str, evidence: list):
            nonlocal total_penalty
            sev = rule.get("severity", "Medium")
            total_penalty += penalties.get(sev, 10)
            consistency[category].append({
                "severity": sev,
                "type": "Logic Contradiction",
                "issue": f"{name}: {rule.get('issue', 'Conflict found')}",
                "evidence": evidence,
                "recommendation": rule.get("recommendation", "Review consistency.")
            })

        # --- Rule 3: Relationship Conflicts ---
        # Look for multiple types between the same pair
        pair_types = {}
        for r in rels:
            pair = tuple(sorted([r.get("source", ""), r.get("target", "")]))
            if pair not in pair_types:
                pair_types[pair] = []
            pair_types[pair].append(r.get("type"))

        sib_spouse = self.rules.get("relationship_conflicts", {}).get("sibling_spouse", {})
        if sib_spouse:
            for pair, types in pair_types.items():
                if sib_spouse.get("type_a") in types and sib_spouse.get("type_b") in types:
                    _add_conflict("relationship_conflicts", sib_spouse, f"{pair[0]} & {pair[1]}", types)

        # --- Character level conflicts ---
        for char in chars:
            name = char.get("name", "Unknown")
            facts = char.get("known_facts", [])
            fears = [f.get("value") for f in char.get("fears", [])]
            traits = [t.get("value") for t in char.get("traits", [])]

            # Rule 1: Fact Conflicts
            alive_dead = self.rules.get("fact_conflicts", {}).get("alive_dead", {})
            if alive_dead:
                has_a, has_b = False, False
                ev_a, ev_b = "", ""
                for fact in facts:
                    fact_lower = fact.lower()
                    if any(kw in fact_lower for kw in alive_dead.get("keywords_a", [])):
                        has_a = True
                        ev_a = fact
                    if any(kw in fact_lower for kw in alive_dead.get("keywords_b", [])):
                        has_b = True
                        ev_b = fact
                
                if has_a and has_b:
                    _add_conflict("fact_conflicts", alive_dead, name, [ev_a, ev_b])

            # Rule 2: Character Conflicts (Fear vs Action)
            fear_action = self.rules.get("character_conflicts", {}).get("fear_vs_action", {})
            if fear_action:
                fear_val = fear_action.get("fear")
                if fear_val in fears:
                    for fact in facts:
                        if any(kw in fact.lower() for kw in fear_action.get("action_keywords", [])):
                            _add_conflict("character_conflicts", fear_action, name, [f"Fear: {fear_val}", f"Action: {fact}"])

            # Rule 4: Trait Contradictions
            trait_contra = self.rules.get("character_conflicts", {}).get("trait_contradiction", {})
            if trait_contra:
                t_a = trait_contra.get("trait_a")
                t_b = trait_contra.get("trait_b")
                if t_a in traits and t_b in traits:
                    _add_conflict("character_conflicts", trait_contra, name, [t_a, t_b])

        # --- Scoring ---
        # Formula: 100 - (Critical*25 + High*15 + Medium*10 + Low*5)
        # Bounded between 0 and 100
        score = 100 - total_penalty
        consistency["consistency_score"] = max(0, min(100, score))

        return consistency
