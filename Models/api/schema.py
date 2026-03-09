"""Pydantic request/response models for the PNE API."""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any


class CreateSessionRequest(BaseModel):
    npc_paths: List[str]
    scenario_path: str
    difficulty: str = "STANDARD"
    player_skills: Dict[str, int] = {
        "authority": 5,
        "diplomacy": 5,
        "empathy": 5,
        "manipulation": 5,
    }
    use_ollama: bool = True
    ollama_model: str = "llama3.2:1b"


class ChoiceItem(BaseModel):
    index: int
    choice_id: str
    text: str
    language_art: str
    success_pct: int


class ChoicesResponse(BaseModel):
    node_id: str
    in_recovery: bool
    choices: List[ChoiceItem]


class SaveResponse(BaseModel):
    saved: List[str]  # npc_ids that were successfully written to disk
