"""
constants.py — Application-wide constants and default file templates.

All paths use pathlib.Path. No hardcoded path strings.
Templates are deep-copied by StoryManager before use, so mutating
the originals here is harmless but still avoided by convention.
"""

from pathlib import Path

# ── Application metadata ─────────────────────────────────────────────
APP_NAME: str = "StoryForge AI"
APP_VERSION: str = "0.1.0"

# ── Directory paths (resolved relative to the project root) ──────────
APP_ROOT: Path = Path(__file__).resolve().parent.parent
STORIES_DIR: Path = APP_ROOT / "stories"
GLOBAL_DIR: Path = APP_ROOT / "global"
UNIVERSES_DIR: Path = APP_ROOT / "universes"

# ── Filename-sanitization constants ──────────────────────────────────
# Characters that are illegal in Windows file / folder names.
INVALID_FILENAME_CHARS: str = '<>:"/\\|?*'

# ── Default story-file templates ─────────────────────────────────────

DEFAULT_STORY_MD: str = "# {title}\n\nStart writing your story here...\n"

DEFAULT_METADATA: dict = {
    "id": "",
    "title": "",
    "genre": "",
    "created_at": "",
    "linked_stories": [],
}

DEFAULT_MEMORY: dict = {
    "characters": [],
    "relationships": [],
    "events": [],
    "locations": [],
    "organizations": [],
    "artifacts": [],
    "themes": [],
}

DEFAULT_ANALYSIS: dict = {
    "story_dna": {},
    "features": {},
    "critiques": [],
    "strengths": [],
    "weaknesses": [],
}

DEFAULT_CHAT_HISTORY: list = []

DEFAULT_CONSISTENCY: dict = {
    "consistency_score": 100,
    "fact_conflicts": [],
    "relationship_conflicts": [],
    "character_conflicts": [],
    "continuity_conflicts": [],
    "flags": []
}

# ── Default global-file templates ────────────────────────────────────

DEFAULT_FEATURE_LIBRARY: dict = {
    "features": [],
    "categories": [],
    "version": "1.0",
}

DEFAULT_USER_PROFILE: dict = {
    "explicit_preferences": {},
    "implicit_preferences": {
        "genres": {},
        "themes": {},
        "character_types": {},
        "relationship_types": {},
        "writing_style": {}
    },
    "preference_history": [],
    "training_profile": {}
}

DEFAULT_TRAINING_PROFILE: dict = {
    "documents_processed": 0,
    "total_words": 0,
    "genres": {},
    "themes": {},
    "character_patterns": {},
    "relationship_patterns": {},
    "style_fingerprint": {
        "dialogue_ratio": 0.0,
        "description_ratio": 0.0,
        "average_sentence_length": 0.0,
        "average_paragraph_length": 0.0
    },
    "worldbuilding_patterns": {},
    "training_history": []
}

# ── Default universe templates ───────────────────────────────────────

DEFAULT_UNIVERSE_METADATA: dict = {
    "universe_id": "",
    "name": "",
    "stories": [],
    "created_at": "",
    "updated_at": ""
}

DEFAULT_UNIVERSE_MEMORY: dict = {
    "characters": [],
    "locations": [],
    "themes": [],
    "events": [],
    "organizations": [],
    "artifacts": []
}

DEFAULT_UNIVERSE_RELATIONSHIPS: dict = {
    "cross_story_links": [],
    "universe_conflicts": []
}

DEFAULT_UNIVERSE_TIMELINE: dict = {
    "timeline_entries": []
}

DEFAULT_UNIVERSE_GRAPH: dict = {
    "nodes": [],
    "edges": [],
    "statistics": {}
}
