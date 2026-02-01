"""
Psychological Narrative Engine - Package Initialization
Author: Jerome Bawa

This package provides a modular dialogue system implementing the Purpose-Output Model
with Conversation Containment, Interaction Outcomes, and Terminal Outcomes.
"""

# Core Enums
from .enums import (
    LanguageArt,
    PlayerSkill,
    TerminalOutcomeType
)

# Conversation Management
from .conversation import ConversationModel

# Intent Layer
from .intent import NPCIntent

# Player Input
from .player_input import (
    PlayerDialogueInput,
    PlayerSkillSet
)

# Skill Checks
from .skill_check import (
    SkillCheckResult,
    SkillCheckSystem
)

# Cognitive Layer
from .cognitive import (
    ThoughtReaction,
    CognitiveInterpreter
)

# Desire Layer
from .desire import (
    DesireState,
    DesireFormation,
)

# Social Layer
from .social import (
    BehaviouralIntention,
    SocialisationFilter
)

# Outcomes
from .outcomes import (
    InteractionOutcome,
    TerminalOutcome,
    OutcomeIndex
)

# Ollama Integration
from .ollama_integration import OllamaResponseGenerator

# Main Processor
from .processor import DialogueProcessor

__version__ = "1.0.0"

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
    
    # Cognitive
    'ThoughtReaction',
    'CognitiveInterpreter',

    # Desire
    'DesireState',
    'DesireFormation',
    
    # Social
    'BehaviouralIntention',
    'SocialisationFilter',
    
    # Outcomes
    'InteractionOutcome',
    'TerminalOutcome',
    'OutcomeIndex',
    
    # Ollama
    'OllamaResponseGenerator',
    
    # Main Processor
    'DialogueProcessor',
]