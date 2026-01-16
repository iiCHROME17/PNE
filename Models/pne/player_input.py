"""
Psychological Narrative Engine - Player Input Structures
Name: player_input.py
Author: Jerome Bawa
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .enums import LanguageArt, PlayerSkill


@dataclass
class PlayerDialogueInput:
    """Structured Player dialogue"""
    choice_text: str
    language_art: LanguageArt
    contextual_references: List[str] = field(default_factory=list)
    
    # Parsed traits from choice text
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    ideology_alignment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_text": self.choice_text,
            "language_art": self.language_art.value,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "ideology_alignment": self.ideology_alignment,
            "contextual_references": self.contextual_references
        }


@dataclass
class PlayerSkillSet:
    """Player's skill proficiencies (0-10 scale)"""
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
        skill_map = {
            PlayerSkill.AUTHORITY: self.authority,
            PlayerSkill.DIPLOMACY: self.diplomacy,
            PlayerSkill.EMPATHY: self.empathy,
            PlayerSkill.MANIPULATION: self.manipulation
        }
        return skill_map[skill]
    
    def get_skill_normalized(self, skill: PlayerSkill) -> float:
        return self.get_skill(skill) / 10.0