"""
story_manager.py — All filesystem operations for StoryForge AI.

This module is deliberately free of PySide6 imports so that future AI
modules (Ollama, analysis engines, etc.) can consume it directly.

Design rules enforced here:
  • Every path built with pathlib.Path (no hardcoded strings).
  • Every JSON read/write is wrapped in try/except.
  • Missing or corrupted JSON files are silently recreated with defaults.
  • Story names are sanitized for Windows filenames.
  • Duplicate folder names get an auto-incremented suffix (_1, _2, …).
  • Story IDs are UUID4 strings.
  • All text I/O uses UTF-8 encoding.
"""

import json
import re
import shutil
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from models.story import Story
from models.workspace_data import WorkspaceData
from utils.constants import (
    STORIES_DIR,
    GLOBAL_DIR,
    INVALID_FILENAME_CHARS,
    DEFAULT_STORY_MD,
    DEFAULT_METADATA,
    DEFAULT_MEMORY,
    DEFAULT_ANALYSIS,
    DEFAULT_CHAT_HISTORY,
    DEFAULT_FEATURE_LIBRARY,
    DEFAULT_USER_PROFILE,
    DEFAULT_CONSISTENCY,
    DEFAULT_TRAINING_PROFILE,
)


class StoryManager:
    """
    Manages CRUD operations for stories stored on the local filesystem.

    The UI layer must delegate *all* file operations to this class.
    """

    def __init__(
        self,
        stories_dir: Optional[Path] = None,
        global_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the manager and ensure required directories exist.

        Parameters
        ----------
        stories_dir : Path, optional
            Override the default ``stories/`` directory (useful for testing).
        global_dir : Path, optional
            Override the default ``global/`` directory.
        """
        self._stories_dir: Path = stories_dir or STORIES_DIR
        self._global_dir: Path = global_dir or GLOBAL_DIR
        self._ensure_directories()

    # ══════════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ══════════════════════════════════════════════════════════════════

    def create_story(self, title: str, genre: str = "") -> Story:
        """
        Create a new story project on disk.

        1. Sanitize *title* for Windows filenames.
        2. Deduplicate the folder name (``Story``, ``Story_1``, …).
        3. Generate a UUID4 story ID.
        4. Write all five template files into the new folder.

        Parameters
        ----------
        title : str
            Human-readable story title (will be sanitized).
        genre : str, optional
            Genre tag stored in metadata.

        Returns
        -------
        Story
            The newly created Story object.

        Raises
        ------
        ValueError
            If *title* is empty or becomes empty after sanitization.
        """
        safe_title: str = self._sanitize_name(title)
        if not safe_title:
            raise ValueError("Story title cannot be empty after sanitization.")

        # Resolve a unique folder name on disk
        folder_name: str = self._unique_folder_name(safe_title)
        folder_path: Path = self._stories_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        # Identity
        story_id: str = str(uuid.uuid4())
        created_at: str = datetime.now().isoformat()

        # Populate metadata
        metadata: dict = deepcopy(DEFAULT_METADATA)
        metadata["id"] = story_id
        metadata["title"] = safe_title
        metadata["genre"] = genre
        metadata["created_at"] = created_at

        # Write all story files
        self._write_json(folder_path / "metadata.json", metadata)
        self._write_json(folder_path / "memory.json", deepcopy(DEFAULT_MEMORY))
        self._write_json(folder_path / "analysis.json", deepcopy(DEFAULT_ANALYSIS))
        self._write_json(folder_path / "chat_history.json", deepcopy(DEFAULT_CHAT_HISTORY))
        self._write_json(folder_path / "consistency.json", deepcopy(DEFAULT_CONSISTENCY))
        self._write_text(
            folder_path / "story.md",
            DEFAULT_STORY_MD.format(title=safe_title),
        )

        return Story(
            id=story_id,
            title=safe_title,
            genre=genre,
            created_at=created_at,
            linked_stories=[],
            folder_path=folder_path,
        )

    def list_stories(self) -> List[Story]:
        """
        Scan ``stories/`` and return a ``Story`` for every valid sub-folder.

        Folders whose ``metadata.json`` lacks an ``id`` field are skipped.
        Corrupted JSON files are auto-healed with defaults before reading.
        """
        stories: List[Story] = []

        if not self._stories_dir.is_dir():
            return stories

        for entry in sorted(self._stories_dir.iterdir()):
            if not entry.is_dir():
                continue

            metadata: dict = self._read_json(
                entry / "metadata.json", DEFAULT_METADATA
            )

            story_id: str = metadata.get("id", "")
            if not story_id:
                # Not a valid story folder — skip silently
                continue

            stories.append(
                Story(
                    id=story_id,
                    title=metadata.get("title", entry.name),
                    genre=metadata.get("genre", ""),
                    created_at=metadata.get("created_at", ""),
                    linked_stories=metadata.get("linked_stories", []),
                    folder_path=entry,
                )
            )

        return stories

    def load_story(self, story_id: str) -> Tuple[Story, str]:
        """
        Load a story's metadata and markdown content.

        Parameters
        ----------
        story_id : str
            UUID4 identifying the story.

        Returns
        -------
        tuple[Story, str]
            The Story object and the raw ``story.md`` text.

        Raises
        ------
        FileNotFoundError
            If no folder matches *story_id*.
        """
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        # Auto-heal any missing / corrupted files before loading
        self._heal_story_files(story)

        content: str = self._read_text(story.story_md_path)
        return story, content

    def save_story(self, story_id: str, content: str) -> None:
        """
        Persist updated markdown content for the given story.

        Parameters
        ----------
        story_id : str
            UUID4 identifying the story.
        content : str
            Full text to write into ``story.md`` (UTF-8, line-breaks preserved).

        Raises
        ------
        FileNotFoundError
            If no folder matches *story_id*.
        """
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        self._write_text(story.story_md_path, content)

    def delete_story(self, story_id: str) -> None:
        """
        Permanently remove a story's folder and all its contents.

        The UI layer is responsible for showing a confirmation dialog
        *before* calling this method.

        Raises
        ------
        FileNotFoundError
            If no folder matches *story_id*.
        """
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        shutil.rmtree(story.folder_path)

    def load_workspace(self, story_id: str) -> WorkspaceData:
        """Load all workspace data for a story in a single call.

        Parameters
        ----------
        story_id : str
            UUID4 identifying the story.

        Returns
        -------
        WorkspaceData
            A bundle containing the Story object, markdown content,
            memory dict, analysis dict, and chat-history list.

        Raises
        ------
        FileNotFoundError
            If no folder matches *story_id*.
        """
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        self._heal_story_files(story)

        content: str = self._read_text(story.story_md_path)
        memory: dict = self._read_json(story.memory_path, DEFAULT_MEMORY)
        analysis: dict = self._read_json(story.analysis_path, DEFAULT_ANALYSIS)
        chat_history: list = self._read_json(
            story.chat_history_path, DEFAULT_CHAT_HISTORY
        )
        consistency: dict = self._read_json(story.consistency_path, DEFAULT_CONSISTENCY)
        user_profile: dict = self.load_user_profile()
        training_profile: dict = self.load_training_profile()

        return WorkspaceData(
            story=story,
            content=content,
            memory=memory,
            analysis=analysis,
            chat_history=chat_history,
            consistency=consistency,
            user_profile=user_profile,
            training_profile=training_profile,
        )

    def update_memory(self, story_id: str, memory_dict: dict) -> None:
        """Overwrite the memory.json file with new data."""
        story = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
        self._write_json(story.memory_path, memory_dict)

    def update_analysis(self, story_id: str, analysis_dict: dict) -> None:
        """Overwrite the analysis.json file with new data."""
        story = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
        self._write_json(story.analysis_path, analysis_dict)

    def update_consistency(self, story_id: str, consistency_dict: dict) -> None:
        """Overwrite the consistency.json file with new data."""
        story = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
        self._write_json(story.consistency_path, consistency_dict)

    def load_user_profile(self) -> dict:
        """Load the global user_profile.json."""
        path = self._global_dir / "user_profile.json"
        return self._read_json(path, DEFAULT_USER_PROFILE)

    def update_user_profile(self, profile_dict: dict) -> None:
        """Overwrite the global user_profile.json file with new data."""
        path = self._global_dir / "user_profile.json"
        self._write_json(path, profile_dict)

    def load_training_profile(self) -> dict:
        """Load the global training_profile.json."""
        path = self._global_dir / "training_profile.json"
        return self._read_json(path, DEFAULT_TRAINING_PROFILE)

    def update_training_profile(self, profile_dict: dict) -> None:
        """Overwrite the global training_profile.json file with new data."""
        path = self._global_dir / "training_profile.json"
        self._write_json(path, profile_dict)

    def load_chat_history(self, story_id: str) -> list:
        """Return the parsed ``chat_history.json`` for a story.

        Parameters
        ----------
        story_id : str
            UUID4 identifying the story.

        Returns
        -------
        list
            The list of chat-message dicts.

        Raises
        ------
        FileNotFoundError
            If no folder matches *story_id*.
        """
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        history = self._read_json(story.chat_history_path, DEFAULT_CHAT_HISTORY)
        
        # Heal legacy chat history by adding missing IDs
        modified = False
        last_user_id = None
        for msg in history:
            if "id" not in msg:
                msg["id"] = str(uuid.uuid4())
                modified = True
            
            if msg.get("role") == "user":
                last_user_id = msg["id"]
            elif msg.get("role") == "assistant" and "parent_id" not in msg and last_user_id:
                msg["parent_id"] = last_user_id
                modified = True
                
        if modified:
            self._write_json(story.chat_history_path, history)
            
        return history

    def append_chat_message(
        self, story_id: str, role: str, content: str, message_id: str = None, parent_id: str = None
    ) -> dict:
        """Create a chat message, append it to ``chat_history.json``, and return it."""
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")

        msg_id = message_id or str(uuid.uuid4())
        message: dict = {
            "id": msg_id,
            "parent_id": parent_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if role == "assistant":
            message["story_insertions"] = []

        history: list = self._read_json(
            story.chat_history_path, DEFAULT_CHAT_HISTORY
        )
        history.append(message)
        self._write_json(story.chat_history_path, history)

        return message

    def update_chat_message(self, story_id: str, message_id: str, new_content: str) -> None:
        """Update the content of an existing chat message."""
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
            
        history: list = self._read_json(story.chat_history_path, DEFAULT_CHAT_HISTORY)
        for msg in history:
            if msg.get("id") == message_id:
                msg["content"] = new_content
                break
        self._write_json(story.chat_history_path, history)

    def delete_chat_message_and_children(self, story_id: str, message_id: str) -> None:
        """Delete a message and any child message (assistant response) associated with it."""
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
            
        history: list = self._read_json(story.chat_history_path, DEFAULT_CHAT_HISTORY)
        
        # Remove target and its children
        new_history = [
            msg for msg in history
            if msg.get("id") != message_id and msg.get("parent_id") != message_id
        ]
        
        self._write_json(story.chat_history_path, new_history)
        
    def record_story_insertion(self, story_id: str, message_id: str, inserted_text: str) -> None:
        """Record that text from an AI response was inserted into the story."""
        story: Optional[Story] = self._find_story_by_id(story_id)
        if story is None:
            raise FileNotFoundError(f"No story found with ID: {story_id}")
            
        history: list = self._read_json(story.chat_history_path, DEFAULT_CHAT_HISTORY)
        for msg in history:
            if msg.get("id") == message_id:
                if "story_insertions" not in msg:
                    msg["story_insertions"] = []
                msg["story_insertions"].append(inserted_text)
                break
        self._write_json(story.chat_history_path, history)

    # ══════════════════════════════════════════════════════════════════
    #  NAME SANITIZATION
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """
        Clean a user-supplied name so it is safe as a Windows folder name.

        Steps:
          1. Strip leading / trailing whitespace.
          2. Remove characters in ``INVALID_FILENAME_CHARS``.
          3. Collapse runs of whitespace into a single space.
          4. Strip trailing dots and spaces (Windows restriction).
        """
        name = name.strip()
        pattern = "[" + re.escape(INVALID_FILENAME_CHARS) + "]"
        name = re.sub(pattern, "", name)
        name = re.sub(r"\s+", " ", name).strip()
        name = name.rstrip(". ")
        return name

    def _unique_folder_name(self, base_name: str) -> str:
        """
        Return *base_name* if available, else *base_name_1*, *base_name_2*, etc.
        """
        candidate: str = base_name
        counter: int = 1
        while (self._stories_dir / candidate).exists():
            candidate = f"{base_name}_{counter}"
            counter += 1
        return candidate

    # ══════════════════════════════════════════════════════════════════
    #  LOOKUP HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _find_story_by_id(self, story_id: str) -> Optional[Story]:
        """
        Iterate through all story folders and return the one whose
        ``metadata.json`` contains a matching ``id`` field.
        """
        for story in self.list_stories():
            if story.id == story_id:
                return story
        return None

    # ══════════════════════════════════════════════════════════════════
    #  FILE-HEALING
    # ══════════════════════════════════════════════════════════════════

    def _heal_story_files(self, story: Story) -> None:
        """
        Ensure every expected file inside a story folder exists and
        contains valid JSON.  Missing or corrupted files are silently
        recreated with their default templates.
        """
        self._ensure_json_file(story.memory_path, DEFAULT_MEMORY)
        self._ensure_json_file(story.analysis_path, DEFAULT_ANALYSIS)
        self._ensure_json_file(story.chat_history_path, DEFAULT_CHAT_HISTORY)
        self._ensure_json_file(story.consistency_path, DEFAULT_CONSISTENCY)

        if not story.story_md_path.is_file():
            self._write_text(
                story.story_md_path,
                DEFAULT_STORY_MD.format(title=story.title),
            )

    # ══════════════════════════════════════════════════════════════════
    #  DIRECTORY BOOTSTRAP
    # ══════════════════════════════════════════════════════════════════

    def _ensure_directories(self) -> None:
        """
        Create ``stories/`` and ``global/`` if they don't exist, and seed
        global JSON files with their defaults.
        """
        self._stories_dir.mkdir(parents=True, exist_ok=True)
        self._global_dir.mkdir(parents=True, exist_ok=True)

        global_files: dict = {
            "feature_library.json": DEFAULT_FEATURE_LIBRARY,
            "user_profile.json": DEFAULT_USER_PROFILE,
            "training_profile.json": DEFAULT_TRAINING_PROFILE,
        }
        for filename, default in global_files.items():
            self._ensure_json_file(self._global_dir / filename, default)

    # ══════════════════════════════════════════════════════════════════
    #  LOW-LEVEL I/O  (every disk operation routes through these)
    # ══════════════════════════════════════════════════════════════════

    def _read_json(self, path: Path, default: object) -> dict | list:
        """
        Read and parse a JSON file.

        On *any* error (missing file, corrupt JSON, permission issue)
        the file is silently recreated from *default* and the default
        value is returned.  The application never crashes from bad JSON.
        """
        try:
            text: str = path.read_text(encoding="utf-8")
            return json.loads(text)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._write_json(path, deepcopy(default))
            return deepcopy(default)

    def _write_json(self, path: Path, data: object) -> None:
        """
        Serialise *data* to JSON with UTF-8 encoding and 2-space indent.
        """
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise IOError(f"Failed to write JSON to {path}: {exc}") from exc

    def _read_text(self, path: Path) -> str:
        """
        Read a text file with UTF-8 encoding.  Returns ``""`` on error.
        """
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return ""

    def _write_text(self, path: Path, content: str) -> None:
        """
        Write *content* to *path* with UTF-8 encoding, preserving
        whatever line-break style the caller provides.
        """
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise IOError(f"Failed to write text to {path}: {exc}") from exc

    def _ensure_json_file(self, path: Path, default: object) -> None:
        """
        If *path* does not exist or contains invalid JSON, overwrite it
        with a fresh copy of *default*.
        """
        try:
            text: str = path.read_text(encoding="utf-8")
            json.loads(text)  # validate only — discard the result
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._write_json(path, deepcopy(default))
