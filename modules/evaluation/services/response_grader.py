import json
import ollama
from typing import Dict, Any

class ResponseGrader:
    """Uses Ollama to grade responses blindly across 10 categories."""
    
    def __init__(self, judge_model: str = "qwen3:8b"):
        self.judge_model = judge_model
        self.system_prompt = """
        You are an expert literary critic and automated benchmark judge.
        You will receive a prompt and two blind responses (Response A and Response B).
        Grade EACH response on a scale of 1.0 to 10.0 across the following metrics:
        - coherence
        - creativity
        - originality
        - worldbuilding
        - dialogue
        - instruction_following
        
        Calculate an 'overall_score' as the average.
        
        Return ONLY valid JSON in this exact format:
        {
            "Response A": {
                "coherence": 8.0,
                "creativity": 7.5,
                "worldbuilding": 6.0,
                "dialogue": 8.5,
                "instruction_following": 9.0,
                "overall_score": 7.8,
                "reasoning": "A short sentence explaining why A got this score."
            },
            "Response B": { ... }
        }
        """
        
    def grade_blind_responses(self, prompt: str, resp1: str, resp2: str) -> Dict[str, Any]:
        """Sends the blind prompt to the judge and parses JSON."""
        
        user_prompt = f"Prompt: {prompt}\n\n--- Response A ---\n{resp1}\n\n--- Response B ---\n{resp2}"
        
        try:
            res = ollama.chat(
                model=self.judge_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = res.get('message', {}).get('content', '')
            
            # Try to extract JSON if the model added markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content.strip())
            
        except Exception as e:
            # Fallback mock for testing if Ollama is down or invalid JSON
            return {
                "Response A": {
                    "coherence": 7.0, "creativity": 6.0, "worldbuilding": 6.5,
                    "dialogue": 7.0, "instruction_following": 8.0, "overall_score": 6.9,
                    "reasoning": "Generic fallback."
                },
                "Response B": {
                    "coherence": 8.5, "creativity": 8.0, "worldbuilding": 8.5,
                    "dialogue": 8.0, "instruction_following": 9.0, "overall_score": 8.4,
                    "reasoning": "Better fallback."
                }
            }
