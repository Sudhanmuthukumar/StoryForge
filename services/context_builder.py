import json
from pathlib import Path

from core.story_manager import StoryManager
from services.graph_engine import GraphEngine

class ContextBuilder:
    def __init__(self):
        self.story_manager = StoryManager()
        self.graph_engine = GraphEngine()

    def build_blocks(self, prompt: str, story_id: str, universe_id: str = None) -> list:
        """
        Gathers memory, consistency, and graph neighbors into unified Context Blocks.
        """
        blocks = []
        prompt_lower = prompt.lower()
        
        # 1. Story Data
        if story_id:
            try:
                story = self.story_manager._find_story_by_id(story_id)
                if story:
                    mem = self.story_manager._read_json(story.memory_path, {})
                    con = self.story_manager._read_json(story.consistency_path, {})
                    ana = self.story_manager._read_json(story.analysis_path, {})
                    
                    # Characters
                    for c in mem.get("characters", []):
                        name = c.get("name", "") if isinstance(c, dict) else c
                        content = json.dumps(c)
                        blocks.append({
                            "source": f"Story: {story.title}",
                            "source_type": "characters",
                            "content": f"Character: {name}\nDetails: {content}"
                        })
                        
                    # Relationships
                    for r in mem.get("relationships", []):
                        blocks.append({
                            "source": f"Story: {story.title}",
                            "source_type": "relationships",
                            "content": f"Relationship: {json.dumps(r)}"
                        })
                        
                    # Consistency Warnings
                    for warn in con.get("fact_conflicts", []) + con.get("character_conflicts", []):
                        blocks.append({
                            "source": f"Story: {story.title}",
                            "source_type": "consistency",
                            "content": f"Warning: {warn}"
                        })
                        
            except FileNotFoundError:
                pass
                
        # 2. Universe Data & Graph
        if universe_id:
            try:
                u_data = self.story_manager._read_json(
                    Path(f"c:/StoryForge AI/universes/{universe_id}/universe_relationships.json"), {}
                )
                graph = self.graph_engine.load_graph(universe_id)
                
                # Universe Conflicts
                for conf in u_data.get("universe_conflicts", []):
                    blocks.append({
                        "source": f"Universe: {universe_id}",
                        "source_type": "consistency",
                        "content": f"Warning: {conf}"
                    })
                    
                # Graph Neighbors
                # Check prompt for node names
                for node in graph.get("nodes", []):
                    if node["name"].lower() in prompt_lower:
                        neighbors = self.graph_engine.get_neighbors(graph, node["id"])
                        if neighbors:
                            names = [n["name"] for n in neighbors]
                            blocks.append({
                                "source": f"Graph: {universe_id}",
                                "source_type": "universe",
                                "content": f"{node['name']} is connected to: {', '.join(names)}"
                            })
                            
            except FileNotFoundError:
                pass

        # 3. Preferences & Training
        try:
            prof = self.story_manager.load_user_profile()
            train = self.story_manager.load_training_profile()
            blocks.append({
                "source": "User Profile",
                "source_type": "preferences",
                "content": f"Style Preferences: {json.dumps(prof.get('implicit_preferences', {}))}"
            })
            blocks.append({
                "source": "Training Profile",
                "source_type": "training",
                "content": f"Style Fingerprint: {json.dumps(train.get('style_fingerprint', {}))}"
            })
        except Exception:
            pass

        return blocks
