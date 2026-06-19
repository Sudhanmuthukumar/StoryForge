import json
from pathlib import Path
from copy import deepcopy

from core.story_manager import StoryManager
from services.graph_engine import GraphEngine

class ContextRanker:
    def __init__(self):
        self.rules = self._load_rules()
        self.max_chars = self.rules.get("max_context_chars", 8000)

    def _load_rules(self) -> dict:
        path = Path("c:/StoryForge AI/config/context_rules.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"max_context_chars": 8000, "importance_weights": {}}

    def _calculate_relevance(self, prompt: str, block: dict) -> float:
        """Calculate how relevant the block is to the prompt."""
        prompt_lower = prompt.lower()
        content_lower = block.get("content", "").lower()
        
        relevance = 0.1 # base
        
        # Keyword match bonus
        words = set(prompt_lower.split())
        match_count = sum(1 for w in words if len(w) > 3 and w in content_lower)
        if match_count > 0:
            relevance += min(0.9, match_count * 0.3)
            
        return min(1.0, relevance)

    def rank_and_filter(self, prompt: str, context_blocks: list) -> dict:
        """
        Rank blocks by (relevance * importance) and trim to max_context_chars.
        Returns a dict with 'selected' and 'dropped' blocks.
        """
        weights = self.rules.get("importance_weights", {})
        
        for block in context_blocks:
            src_type = block.get("source_type", "other")
            importance = weights.get(src_type, 0.5)
            block["importance"] = importance
            
            relevance = self._calculate_relevance(prompt, block)
            block["relevance"] = relevance
            
            block["_score"] = relevance * importance

        # Sort descending by score
        sorted_blocks = sorted(context_blocks, key=lambda x: x["_score"], reverse=True)
        
        selected = []
        dropped = []
        current_chars = 0
        
        for b in sorted_blocks:
            b_len = len(b.get("content", ""))
            if current_chars + b_len <= self.max_chars:
                selected.append(b)
                current_chars += b_len
            else:
                dropped.append(b)
                
        return {
            "selected": selected,
            "dropped": dropped,
            "total_chars": current_chars
        }
