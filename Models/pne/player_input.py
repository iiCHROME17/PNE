"""
Psychological Narrative Engine - Player Input Structures
Name: player_input.py
Author: Jerome Bawa

Defines the data structures that represent a player's chosen dialogue option
and their overall skill proficiency.  These objects flow through the entire BDI
pipeline — from the NarrativeEngine down to CognitiveInterpreter, DesireFormation,
and SocialisationFilter — so every layer has access to exactly the same snapshot
of what the player said and how they said it.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .enums import LanguageArt, PlayerSkill


@dataclass
class PlayerDialogueInput:
    """Structured representation of a single player dialogue choice.

    Created by ``ScenarioLoader.parse_player_input()`` from a scenario choice
    dict and passed unchanged through the full BDI pipeline each turn.

    Attributes:
        choice_text: The display text of the selected choice, shown verbatim in
            the conversation log (e.g. ``"I can prove my loyalty to your cause"``).
        language_art: The rhetorical category of the choice, which determines
            which player skill is used for the dice check (``LanguageArt``).
        contextual_references: Optional list of world-state tags the choice
            references (e.g. ``["faction_rebellion", "prior_meeting"]``).
            Used by the cognitive matcher for contextual scoring.
        authority_tone: How strongly authoritative / commanding this choice
            reads, on a 0.0–1.0 scale.  Drives wildcard overrides such as
            the ``"Inferiority"`` hard-submit.
        diplomacy_tone: Perceived diplomatic / conciliatory quality (0.0–1.0).
        empathy_tone: Perceived emotional understanding or vulnerability (0.0–1.0).
        manipulation_tone: Perceived persuasive or deceptive quality (0.0–1.0).
        ideology_alignment: Optional ideology keyword indicating which faction
            worldview the choice appeals to (e.g. ``"collectivism"``).
            Matched against the NPC's ``social.ideology`` dict in desire
            formation (Pattern 5).
    """

    choice_text: str
    language_art: LanguageArt
    contextual_references: List[str] = field(default_factory=list)

    # Rhetorical tone signals parsed from the choice definition (0.0–1.0 each)
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    ideology_alignment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (used in session log exports)."""
        return {
            "choice_text": self.choice_text,
            "language_art": self.language_art.value,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "ideology_alignment": self.ideology_alignment,
            "contextual_references": self.contextual_references,
        }


@dataclass
class PlayerSkillSet:
    """The player's four language-art skill levels on a 0–10 integer scale.

    Skill values directly influence the player die-weight bias during the
    ``SkillCheckSystem.roll_dice()`` call: a skill of 10 produces a heavily
    top-weighted d6, while 0 produces a bottom-weighted one.

    Attributes:
        authority:    Skill at issuing commands, assertions, and challenges.
        diplomacy:    Skill at reasoned argument and cooperative framing.
        empathy:      Skill at emotional connection and personal appeal.
        manipulation: Skill at misdirection, flattery, and subtle persuasion.

    Raises:
        ValueError: If any skill value falls outside the valid 0–10 range.
    """

    authority: int = 0
    diplomacy: int = 0
    empathy: int = 0
    manipulation: int = 0

    def __post_init__(self):
        for attr in ["authority", "diplomacy", "empathy", "manipulation"]:
            value = getattr(self, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} skill must be between 0 and 10, got {value}")

    def get_skill(self, skill: PlayerSkill) -> int:
        """Return the raw integer value (0–10) for the given skill.

        Args:
            skill: The ``PlayerSkill`` enum member to look up.

        Returns:
            Integer skill value in [0, 10].
        """
        skill_map = {
            PlayerSkill.AUTHORITY: self.authority,
            PlayerSkill.DIPLOMACY: self.diplomacy,
            PlayerSkill.EMPATHY: self.empathy,
            PlayerSkill.MANIPULATION: self.manipulation,
        }
        return skill_map[skill]

    def get_skill_normalized(self, skill: PlayerSkill) -> float:
        """Return the skill value normalised to the 0.0–1.0 range.

        Convenience wrapper around ``get_skill`` used when a continuous
        probability input is required (e.g. dice bias calculations).

        Args:
            skill: The ``PlayerSkill`` enum member to normalise.

        Returns:
            Float in [0.0, 1.0] equal to ``get_skill(skill) / 10.0``.
        """
        return self.get_skill(skill) / 10.0