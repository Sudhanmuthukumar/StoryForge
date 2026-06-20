# Model Weights Policy

StoryForge is a narrative framework and training pipeline, **not a model distribution platform**.

To maintain repository hygiene, strict limits on binary weight distribution are enforced.

## Strictly Prohibited Files
StoryForge must **not** distribute or check in:
- HuggingFace base models (`.bin`, `.safetensors`, `.pt`, `.pth`)
- Ollama model files (`.gguf`, etc.)
- LoRA adapters
- Training checkpoints
- Cached model shards
- Output datasets or runtime model caches

## Repository Scope
The StoryForge GitHub repository should contain **only**:
- Source code (Python modules, scripts)
- Configurations (`.json`, `.yaml`)
- Documentation (`.md`)
- Runtime heuristics/assets (`knowledge_engine` patterns)
- Examples

Users are expected to pull their own base models via HuggingFace or Ollama.
