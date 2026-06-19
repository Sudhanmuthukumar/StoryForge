"""
workspace_data.py — Single transport object for all workspace data.

When the UI opens a story, it needs the Story metadata, the markdown
content, memory, analysis, and chat history all at once.  Rather than
passing five separate variables through layers of code, this dataclass
bundles them into one value that any consumer can destructure.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from models.story import Story


@dataclass
class WorkspaceData:
    """All data needed to display and interact with an open story workspace.

    Attributes
    ----------
    story : Story
        The Story object parsed from ``metadata.json``.
    content : str
        Raw text content of ``story.md``.
    memory : dict
        Parsed contents of ``memory.json``.
    analysis : dict
        Parsed contents of ``analysis.json``.
    chat_history : list
        Parsed contents of ``chat_history.json``.
    consistency : dict
        Parsed contents of ``consistency.json``.
    user_profile : dict
        Parsed contents of global ``user_profile.json``.
    training_profile : dict
        Parsed contents of global ``training_profile.json``.
    """

    story: Story
    content: str = ""
    memory: Dict = field(default_factory=dict)
    analysis: Dict = field(default_factory=dict)
    chat_history: List = field(default_factory=list)
    consistency: Dict = field(default_factory=dict)
    user_profile: Dict = field(default_factory=dict)
    training_profile: Dict = field(default_factory=dict)
