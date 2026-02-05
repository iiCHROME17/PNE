"""
Psychological Narrative Engine - Multi-NPC Conversation Engine

A Fallout-style psychological narrative engine where:
- Player choices are visible and structured (node/choice tree)
- NPC responses are generated via the BDI+LLM pipeline
- Scenarios are NPC-agnostic; NPC individuality is injected at runtime
- Multiple NPCs can participate independently in the same scenario
- Routing between nodes is DYNAMIC: driven by NPC BDI state + player_relation

Author: Jerome Bawa (original), refactor by AI assistant
"""

from .engine import NarrativeEngine
from .session import ConversationSession, NPCConversationState
from .scenario_loader import ScenarioLoader
from .transition_resolver import TransitionResolver

__all__ = [
    "NarrativeEngine",
    "ConversationSession",
    "NPCConversationState",
    "ScenarioLoader",
    "TransitionResolver",
]

__version__ = "1.0.0"