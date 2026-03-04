"""
Psychological Narrative Engine (PNE) – Package Initialization
Author: Jerome Bawa

PNE is a modular, layered dialogue system for games and simulations. It models
NPC conversations as psychological processes rather than simple script trees.

At a high level, the engine:
- Accepts structured player dialogue input and skill information.
- Interprets NPC intent, cognition, desires, and social stance.
- Produces interaction outcomes and terminal outcomes for each dialogue turn.

Architecture overview
---------------------
The package is organised into several layers that form a processing pipeline:

- Enums (:mod:`pne.enums`)
  Core enumerations such as :class:`LanguageArt`, :class:`PlayerSkill`,
  and :class:`TerminalOutcomeType` used across the system.

- Conversation model (:mod:`pne.conversation`)
  :class:`ConversationModel` holds conversation state, history, and configuration.

- Intent layer (:mod:`pne.intent`)
  :class:`NPCIntent` captures what the NPC is currently trying to achieve or express.

- Player input (:mod:`pne.player_input`)
  :class:`PlayerDialogueInput` represents what the player said.
  :class:`PlayerSkillSet` represents their relevant skills for checks.

- Skill checks (:mod:`pne.skill_check`)
  :class:`SkillCheckSystem` runs checks based on :class:`PlayerSkillSet`,
  returning :class:`SkillCheckResult` objects that influence NPC responses.

- Cognitive layer (:mod:`pne.cognitive`)
  :class:`CognitiveInterpreter` converts dialogue context into internal
  :class:`ThoughtReaction` objects, modelling how the NPC thinks about the exchange.

- Desire layer (:mod:`pne.desire`)
  :class:`DesireState` tracks the NPC's current goals/motivations.
  :class:`DesireFormation` updates those desires over time from thoughts and outcomes.

- Social layer (:mod:`pne.social`)
  :class:`BehaviouralIntention` represents how the NPC plans to act socially.
  :class:`SocialisationFilter` adjusts intents and responses to fit the social context.

- Outcomes (:mod:`pne.outcomes`)
  :class:`InteractionOutcome` summarises the result of a single turn.
  :class:`TerminalOutcome` describes how/why a conversation ends.
  :class:`OutcomeIndex` is a helper for indexing and looking up outcomes.

- Ollama integration (:mod:`pne.ollama_integration`)
  :class:`OllamaResponseGenerator` connects the PNE structures to Ollama LLMs.

- Main processor (:mod:`pne.processor`)
  :class:`DialogueProcessor` orchestrates the full flow:
  player input → skill checks → cognitive/desire/social processing → outcomes.

In typical use you construct a ``ConversationModel``, create a ``DialogueProcessor``
for it, wrap raw player text as ``PlayerDialogueInput`` with a ``PlayerSkillSet``,
then call the processor to obtain structured outcomes that drive NPC behaviour.
"""

# Core Enums
from .enums import (
    LanguageArt,
    PlayerSkill,
    TerminalOutcomeType,
    Difficulty,
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
    DiceCheckResult,
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
    'Difficulty',
    
    # Core Models
    'ConversationModel',
    'NPCIntent',
    
    # Player Input
    'PlayerDialogueInput',
    'PlayerSkillSet',
    
    # Skill System
    'SkillCheckResult',
    'DiceCheckResult',
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