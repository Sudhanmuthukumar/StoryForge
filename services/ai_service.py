import ollama
from httpx import ConnectError
import json
from pathlib import Path

class AIService:
    def __init__(self, model: str | None = None):
        self.config_path = Path("c:/StoryForge AI/config/ai_settings.json")
        self.model = model if model is not None else self._load_model()

    def _load_model(self) -> str:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("model", "qwen3:8b")
        except (FileNotFoundError, json.JSONDecodeError):
            return "qwen3:8b"

    def save_model(self, model_name: str) -> None:
        self.model = model_name
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"model": model_name}, f, indent=2)

    def get_available_models(self) -> list:
        try:
            resp = ollama.list()
            if hasattr(resp, 'models'):
                models = resp.models
            else:
                models = resp.get("models", [])
            
            result = []
            for m in models:
                name = getattr(m, 'model', None)
                if not name and isinstance(m, dict):
                    name = m.get("model") or m.get("name")
                if name:
                    result.append(name)
            return result
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []

    def generate_edit(self, action: str, text: str, blocks: list = None) -> str:
        """Generate a direct text edit based on action."""
        if blocks is None:
            blocks = []
        prompts = {
            "fix_grammar": "Correct the grammar, spelling, and punctuation of the following text. Do not change the meaning or style. Output ONLY the corrected text, no conversational filler or markdown formatting.",
            "improve_writing": "Enhance the prose, vocabulary, and descriptions of the following text to make it more engaging. Output ONLY the improved text, no conversational filler.",
            "rewrite": "Rewrite the following passage in an alternative style or structure while preserving the original intent. Output ONLY the rewritten text, no conversational filler.",
            "expand": "Expand the following short passage into a richer, more detailed scene. Add sensory details and depth. Output ONLY the expanded text, no conversational filler.",
            "improve_dialogue": "Improve the emotional impact and natural flow of this dialogue. Make characters sound distinct. Output ONLY the improved dialogue, no conversational filler.",
            "continue_writing": "Read the provided text and write the next logical continuation of the story. Match the exact tone, perspective, and tense of the passage. Provide ONLY the new continuation text, do NOT repeat the original text and do NOT include conversational filler."
        }
        
        system_prompt = prompts.get(action, "Edit the following text. Output ONLY the edited text.")
        user_content = self.build_edit_prompt_content(text, blocks)
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            # Clean up the response in case model still outputs quotes or tags
            out = response["message"]["content"].strip()
            if out.startswith('"') and out.endswith('"'):
                out = out[1:-1]
            return out
        except Exception as e:
            return f"[Error generating edit: {str(e)}]"

    def build_edit_prompt_content(self, text: str, blocks: list = None) -> str:
        if not blocks:
            return text
            
        context_text = "=== BACKGROUND CONTEXT ===\n"
        for b in blocks:
            context_text += f"[{b.get('source_type', 'UNKNOWN').upper()}] {b.get('source', '')}\n{b.get('content', '')}\n\n"
            
        return f"{context_text}\n=== TARGET TEXT ===\n{text}"

    def get_edit_system_prompt(self, action: str) -> str:
        prompts = {
            "fix_grammar": "Correct the grammar, spelling, and punctuation of the following text. Do not change the meaning or style. Output ONLY the corrected text, no conversational filler or markdown formatting.",
            "improve_writing": "Enhance the prose, vocabulary, and descriptions of the following text to make it more engaging. Output ONLY the improved text, no conversational filler.",
            "rewrite": "Rewrite the following passage in an alternative style or structure while preserving the original intent. Output ONLY the rewritten text, no conversational filler.",
            "expand": "Expand the following short passage into a richer, more detailed scene. Add sensory details and depth. Output ONLY the expanded text, no conversational filler.",
            "improve_dialogue": "Improve the emotional impact and natural flow of this dialogue. Make characters sound distinct. Output ONLY the improved dialogue, no conversational filler.",
            "continue_writing": "Read the provided text and write the next logical continuation of the story. Match the exact tone, perspective, and tense of the passage. Provide ONLY the new continuation text, do NOT repeat the original text and do NOT include conversational filler."
        }
        return prompts.get(action, "Edit the following text. Output ONLY the edited text.")

    def generate_variations(self, text: str, blocks: list = None) -> str:
        """Generate 3 draft variations using clear headers."""
        if blocks is None:
            blocks = []
            
        system_prompt = (
            "You are an expert editor. Provide 3 distinct variations of the following passage.\n"
            "Variation A should be more emotional.\n"
            "Variation B should be more action-oriented or fast-paced.\n"
            "Variation C should be more dialogue-heavy or character-focused.\n\n"
            "You MUST use EXACTLY the following format:\n\n"
            "=== VERSION A ===\n(text for variation A)\n\n"
            "=== VERSION B ===\n(text for variation B)\n\n"
            "=== VERSION C ===\n(text for variation C)\n\n"
            "Do not include any conversational filler."
        )
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[Error generating variations: {str(e)}]"

    def build_prompt(self, user_message: str, context_blocks: list) -> str:
        prompt = "=== CONTEXT ===\n"
        for block in context_blocks:
            prompt += f"\n[{block.get('source_type', 'UNKNOWN').upper()}] {block.get('source', '')}\n"
            prompt += f"{block.get('content', '')}\n"
        
        prompt += "\n=== USER ===\n"
        prompt += f"{user_message}\n"
        return prompt

    def generate_response(self, user_message: str, context_blocks: list) -> str:
        prompt = self.build_prompt(user_message, context_blocks)
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except ollama.ResponseError as e:
            if e.status_code == 404:
                return f"⚠️ Model not found.\n\nRun:\nollama pull {self.model}"
            return f"⚠️ AI error:\n\n{str(e)}"
        except ConnectError:
            return "⚠️ Ollama is not running.\nStart it with:\n\nollama serve"
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str:
                return "⚠️ AI generation timed out."
            return f"⚠️ AI error:\n\n{str(e)}"

    def stream_response(self, user_message: str, context_blocks: list):
        """Yields chunks of the response from Ollama."""
        prompt = self.build_prompt(user_message, context_blocks)
        try:
            response_stream = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in response_stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except ollama.ResponseError as e:
            if e.status_code == 404:
                yield f"⚠️ Model not found.\n\nRun:\nollama pull {self.model}"
            else:
                yield f"⚠️ AI error:\n\n{str(e)}"
        except ConnectError:
            yield "⚠️ Ollama is not running.\nStart it with:\n\nollama serve"
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str:
                yield "⚠️ AI generation timed out."
            else:
                yield f"⚠️ AI error:\n\n{str(e)}"
