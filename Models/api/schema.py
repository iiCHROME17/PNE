"""Pydantic request/response models for the PNE REST API.

These schemas define the contract between the FastAPI server (api/main.py)
and any HTTP or WebSocket client (e.g. a game front-end or the PNE CLI).
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from config import OLLAMA_MODEL


class CreateSessionRequest(BaseModel):
    """Request body for ``POST /session`` — starts a new conversation session.

    Attributes:
        npc_paths: Absolute or relative filesystem paths to one or more NPC
            JSON definition files (e.g. ``["npcs/elara.json"]``).
        scenario_path: Filesystem path to the scenario JSON file that defines
            the dialogue tree, nodes, and transitions.
        difficulty: Difficulty preset that adjusts the player dice-weight bias.
            One of ``"SIMPLE"``, ``"STANDARD"`` (default), or ``"STRICT"``.
        player_skills: Mapping of the four language-art skills to their starting
            values on a 0–10 scale.  Defaults to 5 across the board.
        use_ollama: Whether to route NPC dialogue generation through a local
            Ollama instance.  Set to ``False`` for deterministic fallback text.
        ollama_model: Ollama model tag to use (e.g. ``"llama3.2:1b"``).
            Only meaningful when ``use_ollama`` is ``True``.
    """

    npc_paths: List[str]
    scenario_path: str
    difficulty: str = "STANDARD"
    player_skills: Dict[str, int] = Field(
        default={
            "authority": 5,
            "diplomacy": 5,
            "empathy": 5,
            "manipulation": 5,
        }
    )
    use_ollama: bool = True
    ollama_model: str = OLLAMA_MODEL


class ChoiceItem(BaseModel):
    """A single player-dialogue option returned by ``GET /session/{id}/choices``.

    Attributes:
        index: 1-based display index used to submit this choice back via
            ``POST /session/{id}/choice``.
        choice_id: Canonical string identifier from the scenario JSON, used
            internally for filtering, recovery tracking, and transition routing.
        text: Human-readable dialogue text shown to the player.
        language_art: The rhetorical skill category this choice uses
            (e.g. ``"challenge"``, ``"diplomatic"``, ``"empathetic"``,
            ``"manipulative"``, or ``"neutral"``).
        success_pct: Pre-roll success probability as an integer percentage
            (0–100), computed analytically before the actual dice roll.
    """

    index: int
    choice_id: str
    text: str
    language_art: str
    success_pct: int


class ChoicesResponse(BaseModel):
    """Response body for ``GET /session/{id}/choices``.

    Attributes:
        node_id: The current dialogue-tree node the session is on.
        in_recovery: ``True`` when the previous choice failed a skill check and
            the session is now offering recovery options instead of the node's
            normal choices.
        choices: Ordered list of available player choices, filtered and
            coherence-scored by the engine.
    """

    node_id: str
    in_recovery: bool
    choices: List[ChoiceItem]


class SaveResponse(BaseModel):
    """Response body for ``POST /session/{id}/save``.

    Attributes:
        saved: List of NPC IDs whose updated state was successfully persisted
            to disk.  IDs absent from this list were not saved (e.g. already
            complete or no changes detected).
    """

    saved: List[str]
