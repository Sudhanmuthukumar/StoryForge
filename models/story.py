"""
story.py — Data model for a single Story project.

This is a plain dataclass with no filesystem or UI logic.
StoryManager is responsible for populating and persisting these objects.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Story:
    """Represents one story project stored on disk."""

    # ── Identity ──────────────────────────────────────────────────────
    id: str                                  # UUID4 string
    title: str                               # Human-readable display name
    genre: str = ""
    created_at: str = ""                     # ISO-8601 UTC timestamp
    linked_stories: List[str] = field(default_factory=list)

    # ── Filesystem ────────────────────────────────────────────────────
    folder_path: Path = field(default_factory=Path)

    # ── Derived file paths (read-only) ────────────────────────────────

    @property
    def story_md_path(self) -> Path:
        """Path to the story markdown file."""
        return self.folder_path / "story.md"

    @property
    def metadata_path(self) -> Path:
        """Path to the metadata JSON file."""
        return self.folder_path / "metadata.json"

    @property
    def memory_path(self) -> Path:
        """Path to the memory JSON file."""
        return self.folder_path / "memory.json"

    @property
    def analysis_path(self) -> Path:
        """Path to the analysis JSON file."""
        return self.folder_path / "analysis.json"

    @property
    def chat_history_path(self) -> Path:
        """Path to the chat-history JSON file."""
        return self.folder_path / "chat_history.json"

    @property
    def consistency_path(self) -> Path:
        """Path to the consistency JSON file."""
        return self.folder_path / "consistency.json"

    # ── Validation ────────────────────────────────────────────────────

    def is_valid(self) -> bool:
        """Return True when the folder and all five expected files exist."""
        return (
            self.folder_path.is_dir()
            and self.story_md_path.is_file()
            and self.metadata_path.is_file()
            and self.memory_path.is_file()
            and self.analysis_path.is_file()
            and self.chat_history_path.is_file()
            and self.consistency_path.is_file()
        )
