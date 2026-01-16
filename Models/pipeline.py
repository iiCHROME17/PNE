"""
Psychological Narrative Engine - Compatibility Wrapper
Name: pipeline.py (ROOT LEVEL)
Author: Jerome Bawa

This file maintains backwards compatibility with existing code that imports from pipeline.
All functionality has been refactored into the pne package for better modularity.

USAGE:
------
Old code (still works):
    from pipeline import DialogueProcessor, LanguageArt, PlayerSkillSet

New code (recommended):
    from pne import DialogueProcessor, LanguageArt, PlayerSkillSet
    # or
    from pne.processor import DialogueProcessor
    from pne.enums import LanguageArt
    from pne.player_input import PlayerSkillSet
"""

# Re-export all core functionality from the pne package
from pne.enums import (
    LanguageArt,
    PlayerSkill,
    TerminalOutcomeType
)

from pne.conversation import ConversationModel

from pne.intent import NPCIntent

from pne.player_input import (
    PlayerDialogueInput,
    PlayerSkillSet
)

from pne.skill_check import (
    SkillCheckResult,
    SkillCheckSystem
)

from pne.cognitive import (
    ThoughtReaction,
    CognitiveInterpreter
)

from pne.social import (
    BehaviouralIntention,
    SocialisationFilter
)

from pne.outcomes import (
    InteractionOutcome,
    TerminalOutcome,
    OutcomeIndex
)

from pne.ollama_integration import OllamaResponseGenerator

from pne.processor import DialogueProcessor


# Maintain the exact same public interface as the original pipeline.py
__all__ = [
    # Enums
    'LanguageArt',
    'PlayerSkill',
    'TerminalOutcomeType',
    
    # Core Models
    'ConversationModel',
    'NPCIntent',
    
    # Player Input
    'PlayerDialogueInput',
    'PlayerSkillSet',
    
    # Skill System
    'SkillCheckResult',
    'SkillCheckSystem',
    
    # Cognitive Layer
    'ThoughtReaction',
    'CognitiveInterpreter',
    
    # Social Layer
    'BehaviouralIntention',
    'SocialisationFilter',
    
    # Outcomes
    'InteractionOutcome',
    'TerminalOutcome',
    'OutcomeIndex',
    
    # Ollama Integration
    'OllamaResponseGenerator',
    
    # Main Processor
    'DialogueProcessor',
]


# Optional: Add deprecation notice for future migration
import warnings

def _show_migration_notice():
    """Display migration notice on first import (optional)"""
    warnings.simplefilter('once', DeprecationWarning)
    warnings.warn(
        "Importing from 'pipeline' is deprecated. "
        "Please migrate to 'from pne import ...' for cleaner imports. "
        "See README_REFACTOR.md for migration guide.",
        DeprecationWarning,
        stacklevel=3
    )

# Uncomment the line below to enable migration warnings
# _show_migration_notice()