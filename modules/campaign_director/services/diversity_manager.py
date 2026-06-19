"""
diversity_manager.py — Prevents narrative stagnation by tracking quest type balance and faction focus.

Checks recent event and quest history to:
1. Ensure quest types are balanced (no type dominates)
2. Direct focus to neglected factions and NPCs
3. Prevent repetitive event patterns
"""

from typing import Dict, List, Any, Optional
from collections import Counter


class DiversityManager:
    """Analyzes narrative diversity and recommends focus areas."""

    # Expected quest type distribution for balance
    QUEST_TYPES = ["Main", "Side", "Faction", "Personal", "Exploration", "Combat", "Diplomacy"]
    
    # Ideal distribution weights (should sum to ~1.0)
    IDEAL_DISTRIBUTION = {
        "Main": 0.15,
        "Side": 0.20,
        "Faction": 0.20,
        "Personal": 0.10,
        "Exploration": 0.15,
        "Combat": 0.10,
        "Diplomacy": 0.10,
    }

    def __init__(self):
        pass

    def analyze_diversity(
        self,
        world_state: Dict[str, Any],
        event_history: List[Dict[str, Any]],
        npc_memories: Dict[str, Any],
        reputation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze narrative diversity across quests, factions, NPCs, and events.
        
        Returns:
            Dictionary with diversity scores, imbalances, and recommendations.
        """
        quest_analysis = self._analyze_quest_diversity(world_state)
        faction_analysis = self._analyze_faction_coverage(event_history, reputation)
        npc_analysis = self._analyze_npc_engagement(npc_memories)
        event_analysis = self._analyze_event_variety(event_history)

        # Compute overall diversity score (0.0 = totally repetitive, 1.0 = perfectly diverse)
        scores = [
            quest_analysis["diversity_score"],
            faction_analysis["diversity_score"],
            npc_analysis["engagement_score"],
            event_analysis["variety_score"],
        ]
        overall = round(sum(scores) / len(scores), 3) if scores else 0.5

        recommendations = self._generate_recommendations(
            quest_analysis, faction_analysis, npc_analysis, event_analysis
        )

        return {
            "overall_diversity": overall,
            "quest_diversity": quest_analysis,
            "faction_coverage": faction_analysis,
            "npc_engagement": npc_analysis,
            "event_variety": event_analysis,
            "recommendations": recommendations,
        }

    def _analyze_quest_diversity(self, world_state: Dict) -> Dict[str, Any]:
        """Analyze distribution of quest types against ideal distribution."""
        dm_data = world_state.get("dungeon_master", {})
        quests = dm_data.get("generated_quests", [])
        completed = world_state.get("completed_quests", [])

        # Count quest types
        type_counter = Counter()
        for q in quests:
            qtype = q.get("quest_type", "Side")
            type_counter[qtype] += 1

        total = sum(type_counter.values())
        if total == 0:
            return {
                "diversity_score": 0.5,
                "type_distribution": {},
                "missing_types": list(self.QUEST_TYPES),
                "dominant_type": None,
            }

        # Compute actual distribution
        actual_dist = {qtype: count / total for qtype, count in type_counter.items()}

        # Compute deviation from ideal
        deviation_sum = 0.0
        for qtype in self.QUEST_TYPES:
            ideal = self.IDEAL_DISTRIBUTION.get(qtype, 0.1)
            actual = actual_dist.get(qtype, 0.0)
            deviation_sum += abs(ideal - actual)

        # Diversity score = 1 - normalized deviation
        diversity_score = max(0.0, 1.0 - (deviation_sum / 2.0))

        # Identify missing types
        missing = [qt for qt in self.QUEST_TYPES if qt not in type_counter]

        # Identify dominant type
        dominant = type_counter.most_common(1)[0][0] if type_counter else None

        return {
            "diversity_score": round(diversity_score, 3),
            "type_distribution": dict(type_counter),
            "missing_types": missing,
            "dominant_type": dominant,
            "total_quests": total,
            "completed_quests": len(completed),
        }

    def _analyze_faction_coverage(self, event_history: List, reputation: Dict) -> Dict[str, Any]:
        """Analyze how evenly factions are covered in events and reputation."""
        faction_relations = reputation.get("faction_relations", {})
        all_factions = set(faction_relations.keys())

        # Count faction mentions in recent events
        recent = event_history[-20:] if event_history else []
        faction_mentions = Counter()
        for event in recent:
            for entity in event.get("affected_entities", []):
                if entity in all_factions:
                    faction_mentions[entity] += 1

        # Compute coverage score
        if not all_factions:
            return {
                "diversity_score": 0.5,
                "faction_mentions": {},
                "neglected_factions": [],
                "over_represented": [],
            }

        total_mentions = sum(faction_mentions.values())
        if total_mentions == 0:
            return {
                "diversity_score": 0.3,
                "faction_mentions": {},
                "neglected_factions": list(all_factions),
                "over_represented": [],
            }

        ideal_per_faction = total_mentions / len(all_factions)
        deviation = sum(
            abs(faction_mentions.get(f, 0) - ideal_per_faction)
            for f in all_factions
        )
        diversity_score = max(0.0, 1.0 - (deviation / (total_mentions * 2)))

        # Identify neglected and over-represented factions
        neglected = [f for f in all_factions if faction_mentions.get(f, 0) < ideal_per_faction * 0.3]
        over_rep = [f for f in all_factions if faction_mentions.get(f, 0) > ideal_per_faction * 2.0]

        return {
            "diversity_score": round(diversity_score, 3),
            "faction_mentions": dict(faction_mentions),
            "neglected_factions": neglected,
            "over_represented": over_rep,
        }

    def _analyze_npc_engagement(self, npc_memories: Dict) -> Dict[str, Any]:
        """Analyze NPC engagement levels across the world."""
        if not npc_memories:
            return {
                "engagement_score": 0.5,
                "total_npcs": 0,
                "active_npcs": 0,
                "dormant_npcs": 0,
                "most_engaged": [],
                "least_engaged": [],
            }

        engagement_scores = []
        for npc_id, mem in npc_memories.items():
            memory_count = len(mem.get("memories", []))
            interaction_count = len(mem.get("interactions", []))
            quest_count = len(mem.get("quest_outcomes", {}))

            # Engagement = weighted sum of activities
            engagement = (memory_count * 0.3 + interaction_count * 0.5 + quest_count * 0.2)
            engagement_scores.append({
                "npc_id": npc_id,
                "name": mem.get("name", "Unknown"),
                "engagement": engagement,
                "memories": memory_count,
                "interactions": interaction_count,
                "quests": quest_count,
            })

        engagement_scores.sort(key=lambda x: x["engagement"], reverse=True)

        active = sum(1 for e in engagement_scores if e["engagement"] > 1.0)
        dormant = len(engagement_scores) - active

        # Engagement score = ratio of active NPCs
        total = len(engagement_scores)
        score = active / total if total > 0 else 0.5

        return {
            "engagement_score": round(min(1.0, score), 3),
            "total_npcs": total,
            "active_npcs": active,
            "dormant_npcs": dormant,
            "most_engaged": [e["name"] for e in engagement_scores[:3]],
            "least_engaged": [e["name"] for e in engagement_scores[-3:]] if len(engagement_scores) >= 3 else [],
        }

    def _analyze_event_variety(self, event_history: List) -> Dict[str, Any]:
        """Analyze variety in event types to detect repetition."""
        if not event_history:
            return {
                "variety_score": 0.5,
                "type_distribution": {},
                "repetition_detected": False,
            }

        recent = event_history[-30:]
        type_counter = Counter(e.get("type", "Unknown") for e in recent)
        total = sum(type_counter.values())

        # Check if any single type dominates > 60%
        dominant_pct = max(count / total for count in type_counter.values()) if total > 0 else 0
        repetition = dominant_pct > 0.6

        # Variety = number of unique types / expected types
        unique_types = len(type_counter)
        expected_types = min(5, total)  # Expect at least 5 different types
        variety_score = min(1.0, unique_types / max(expected_types, 1))

        return {
            "variety_score": round(variety_score, 3),
            "type_distribution": dict(type_counter),
            "repetition_detected": repetition,
            "dominant_type": type_counter.most_common(1)[0][0] if type_counter else None,
            "dominant_percentage": round(dominant_pct, 3),
        }

    def _generate_recommendations(
        self,
        quest_analysis: Dict,
        faction_analysis: Dict,
        npc_analysis: Dict,
        event_analysis: Dict,
    ) -> List[Dict[str, Any]]:
        """Generate actionable diversity recommendations."""
        recommendations = []

        # Quest type recommendations
        if quest_analysis.get("missing_types"):
            for missing_type in quest_analysis["missing_types"][:2]:
                recommendations.append({
                    "type": "diversity",
                    "priority": "medium",
                    "description": f"No '{missing_type}' quests generated yet. Consider spawning a {missing_type} quest.",
                    "target_metric": "quest_diversity",
                    "current_value": quest_analysis["diversity_score"],
                    "target_value": 0.7,
                })

        if quest_analysis.get("dominant_type"):
            dom = quest_analysis["dominant_type"]
            dist = quest_analysis.get("type_distribution", {})
            if dist.get(dom, 0) > 3:
                recommendations.append({
                    "type": "diversity",
                    "priority": "high",
                    "description": f"'{dom}' quests are over-represented ({dist[dom]} instances). Diversify quest types.",
                    "target_metric": "quest_diversity",
                    "current_value": quest_analysis["diversity_score"],
                    "target_value": 0.8,
                })

        # Faction coverage recommendations
        for neglected in faction_analysis.get("neglected_factions", [])[:2]:
            recommendations.append({
                "type": "faction_focus",
                "priority": "medium",
                "description": f"Faction '{neglected}' is neglected in recent events. Generate events involving this faction.",
                "target_metric": "faction_coverage",
                "current_value": faction_analysis["diversity_score"],
                "target_value": 0.7,
            })

        # NPC engagement recommendations
        if npc_analysis.get("dormant_npcs", 0) > npc_analysis.get("active_npcs", 0):
            recommendations.append({
                "type": "diversity",
                "priority": "low",
                "description": f"{npc_analysis['dormant_npcs']} NPCs are dormant with no recent activity. Involve them in quests or events.",
                "target_metric": "npc_engagement",
                "current_value": npc_analysis["engagement_score"],
                "target_value": 0.5,
            })

        # Event variety recommendations
        if event_analysis.get("repetition_detected"):
            dom = event_analysis.get("dominant_type", "Unknown")
            recommendations.append({
                "type": "diversity",
                "priority": "high",
                "description": f"Event type '{dom}' dominates at {event_analysis['dominant_percentage']*100:.0f}%. Introduce more varied events.",
                "target_metric": "event_variety",
                "current_value": event_analysis["variety_score"],
                "target_value": 0.7,
            })

        return recommendations
