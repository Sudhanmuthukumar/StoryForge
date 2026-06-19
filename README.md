# StoryForge V1.0.0

StoryForge is a deterministic narrative and world-state engine designed to generate dynamic RPG game assets. It provides tools for concepting story outlines, designing intelligent NPCs, building factions, generating quest chains, and simulating deterministic world state changes—all of which export natively to Unreal Engine.

## Features
- **Creator Suite**: UI-driven (PyQt6) tools to orchestrate narrative generation.
- **Game Narrative Toolkit**: Specialized tools to generate Factions, NPCs, Quest Chains, and Campaigns.
- **NPC Intelligence**: Stateful generation of NPC Memories, Goals, Relationships, and Reaction Logic.
- **World State Engine**: A reactive logic system that mutates global metrics (Security, Prosperity, Stability, etc.) based on game events.
- **Unreal Export Layer**: Native JSON, YAML, and flattened CSV exports tailored specifically for Unreal Engine DataTables.
- **Knowledge Engine**: The underlying pattern database (v1, v2, v3, v4) extracted from classic fantasy literature to drive heuristic, LLM-free asset composition.

## Quick Start
See [INSTALLATION.md](INSTALLATION.md) for setup instructions.
See [USER_GUIDE.md](USER_GUIDE.md) for how to use the Creator Suite.
See [UNREAL_EXPORT_GUIDE.md](UNREAL_EXPORT_GUIDE.md) for details on integrating StoryForge with Unreal Engine.

## Training Validation Sources
StoryForge validation, benchmarking, and experimental training runs were conducted using a curated selection of public domain and literary texts across multiple genres (including Epic Fantasy, Dark Fantasy, Horror, Sci-Fi, and Political Intrigue). 

For a complete list of authors, texts, and their usage within the system, see [TRAINING_DATA_SOURCES.md](TRAINING_DATA_SOURCES.md).
