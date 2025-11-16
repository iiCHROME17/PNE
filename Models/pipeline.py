"""
Psychological Narrative Engine - Dialogue Pipeline
Author: Jerome Bawa 
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any , Tuple
from enum import Enum
import json
import random
#Enums--------------------------------------
class LanguageArt(Enum):
    """Player Dialogue Approaches"""
    CHALLENGE = "challenge"
    DIPLOMATIC = "diplomatic"
    EMPATHETIC = "empathetic"
    MANIPULATIVE = "manipulative"
    NEUTRAL = "neutral"

class PlayerSkill(Enum):
    """PLayer's skill proficiencies"""
    AUTHORITY = "authority"
    DIPLOMACY = "diplomacy"
    EMPATHY = "empathy"
    MANIPULATION = "manipulation"

#Player Input Structure----------------------
class PlayerDialogueInput:
    """Structured Player dialogue"""
    choice_text: str
    language_art: LanguageArt

    #Parsed traits from choice text
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    idelogy_alignment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_text": self.choice_text,
            "language_art": self.language_art.value,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "idelogy_alignment": self.idelogy_alignment
        }
    
@dataclass
class PlayerSkillSet:
    """Player's skill proficiencies"""
    authority: int = 0
    diplomacy: int = 0
    empathy: int = 0
    manipulation: int = 0

    def __post_init__(self):
        """Validate skill values are within acceptable range"""
        for attr in ["authority", "diplomacy", "empathy", "manipulation"]:
            value = getattr(self, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} skill must be between 0 and 10, got {value}")
            
    def get_skill(self, skill: PlayerSkill) -> float:
        """Retrieve skill value by PlayerSkill enum"""
        skill_map = {
            PlayerSkill.AUTHORITY: self.authority,
            PlayerSkill.DIPLOMACY: self.diplomacy,
            PlayerSkill.EMPATHY: self.empathy,
            PlayerSkill.MANIPULATION: self.manipulation
        }
        return skill_map[skill]

#Skill Check System----------------------
@dataclass
class SkillCheckResult:
    """Result of a skill check"""
    success: bool
    skill_used: PlayerSkill
    player_val : int
    threshold: float
    margin: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_used": self.skill_used.value,
            "player_val": self.player_val,
            "threshold": self.threshold,
            "margin": self.margin
        }
    
class SkillCheckSystem:
    """Handles skill checks based on player input and NPC modifier application"""
    #Map LanguageArt to PlayerSkill
    LANGUAGE_ART_TO_SKILL = {
        LanguageArt.CHALLENGE: PlayerSkill.AUTHORITY,
        LanguageArt.DIPLOMATIC: PlayerSkill.DIPLOMACY,
        LanguageArt.EMPATHETIC: PlayerSkill.EMPATHY,
        LanguageArt.MANIPULATIVE: PlayerSkill.MANIPULATION,
        LanguageArt.NEUTRAL: None
    }

    #Map skill to NPC attribute modifiers
    SKILL_MODIFIERS = {
        PlayerSkill.AUTHORITY: [
            ('social.assertion', lambda npc, margin: npc.social.assertion * (1 - margin * 0.5))
        ],
        PlayerSkill.MANIPULATION: [
            ('cognitive.self_esteem', lambda npc, margin: npc.cognitive.self_esteem * (1 - margin * 0.5))
        ],
        PlayerSkill.DIPLOMACY: [
            ('cognitive.cog_flexibility', lambda npc, margin: npc.cognitive.cog_flexibility * (1 + margin * 0.5))
        ],
        PlayerSkill.EMPATHY: [
            ('social.empathy', lambda npc, margin: npc.social.empathy * (1 + margin * 0.5))
        ]
    }

@staticmethod
def calc_threshold(npc, skill: PlayerSkill) -> float:
    """Calculate skill check threshold based on NPC attributes,
    
    higher attributes make checks harder"""

    if skill == PlayerSkill.AUTHORITY:
        #High Assertion = hard to intimidate
        return 0.3 + (npc.social.assertion * 0.4)
    
    elif skill == PlayerSkill.MANIPULATION:
        #High Self-Esteem = hard to manipulate
        return 0.2 + (npc.cognitive.self_esteem * 0.5)
    
    elif skill == PlayerSkill.EMPATHY:
        #High Empathy = Easy to connect with
        return 0.4 - (npc.social.empathy * 0.2)
    
    elif skill == PlayerSkill.DIPLOMACY:
        #High Cognitive Flexibility = Easy to persuade
        return 0.3 - (npc.cognitive.cog_flexibility * 0.3)
    
    return 0.5  # Neutral baseline

@staticmethod
def perform_check(
    player_input: PlayerDialogueInput,
    player_skills: PlayerSkillSet,
    npc
) -> Optional[SkillCheckResult]:
    """Perform skill check based on player input and NPC attributes.
    Returns None if language art doesn't trigger skill check."""

    skill = SkillCheckSystem.LANGUAGE_ART_TO_SKILL.get(player_input.language_art)
    if skill is None:
        return None
    
    player_val = player_skills.get_skill(skill)
    threshold = SkillCheckSystem.calc_threshold(npc, skill)

    #Determine success with randomness
    roll = random.uniform(-0.1, 0.1)  # Small randomness factor
    eff_val = player_val  + roll  # Normalize skill to [0,1]

    success = eff_val >= threshold
    margin = eff_val - threshold

    return SkillCheckResult(
        success=success,
        skill_used=skill,
        player_val=player_val,
        threshold=threshold,
        margin=margin
    )

@staticmethod
def apply_modifier(npc, check_result: SkillCheckResult):
    """Apply NPC attribute modifiers based on skill check result"""
    if not check_result.success:
        return
    
    modifiers = SkillCheckSystem.SKILL_MODIFIERS.get(check_result.skill_used, [])

    for attr_path, mod_func in modifiers:

        new_value = mod_func(npc, check_result.margin)
        npc.apply_temp_mod(attr_path,new_value)

#Cognitive Filter----------------------
"""Cognitive filter to adjust dialogue based on NPC traits"""