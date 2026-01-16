"""
Psychological Narrative Engine - Skill Check System
Name: skill_check.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import random
from .enums import LanguageArt, PlayerSkill
from .player_input import PlayerDialogueInput, PlayerSkillSet


@dataclass
class SkillCheckResult:
    """Result of a skill check"""
    success: bool
    skill_used: PlayerSkill
    player_val: int
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
    """Handles skill checks based on player input"""
    
    LANGUAGE_ART_TO_SKILL = {
        LanguageArt.CHALLENGE: PlayerSkill.AUTHORITY,
        LanguageArt.DIPLOMATIC: PlayerSkill.DIPLOMACY,
        LanguageArt.EMPATHETIC: PlayerSkill.EMPATHY,
        LanguageArt.MANIPULATIVE: PlayerSkill.MANIPULATION,
        LanguageArt.NEUTRAL: None
    }

    SKILL_MODIFIERS = {
        PlayerSkill.AUTHORITY: [
            ('social.assertion', lambda npc, margin: npc.social.assertion * (1 - margin * 0.5))
        ],
        PlayerSkill.MANIPULATION: [
            ('cognitive.self_esteem', lambda npc, margin: npc.cognitive.self_esteem * (1 - margin * 0.5))
        ],
        PlayerSkill.DIPLOMACY: [
            ('cognitive.cog_flexibility', lambda npc, margin: min(1.0, npc.cognitive.cog_flexibility * (1 + margin * 0.5)))
        ],
        PlayerSkill.EMPATHY: [
            ('social.empathy', lambda npc, margin: min(1.0, npc.social.empathy * (1 + margin * 0.5)))
        ]
    }

    @staticmethod
    def calc_threshold(npc, skill: PlayerSkill) -> float:
        if skill == PlayerSkill.AUTHORITY:
            return 0.3 + (npc.social.assertion * 0.4)
        elif skill == PlayerSkill.MANIPULATION:
            return 0.2 + (npc.cognitive.self_esteem * 0.5)
        elif skill == PlayerSkill.EMPATHY:
            return 0.4 - (npc.social.empathy * 0.2)
        elif skill == PlayerSkill.DIPLOMACY:
            return 0.3 - (npc.cognitive.cog_flexibility * 0.3)
        return 0.5

    @staticmethod
    def perform_check(
        player_input: PlayerDialogueInput,
        player_skills: PlayerSkillSet,
        npc
    ) -> Optional[SkillCheckResult]:
        skill = SkillCheckSystem.LANGUAGE_ART_TO_SKILL.get(player_input.language_art)
        if skill is None:
            return None
        
        player_val = player_skills.get_skill(skill)
        threshold = SkillCheckSystem.calc_threshold(npc, skill)
        roll = random.uniform(-0.1, 0.1)
        eff_val = (player_val / 10.0) + roll
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
    def apply_modifiers(npc, check_result: SkillCheckResult):
        if not check_result.success:
            return
        
        modifiers = SkillCheckSystem.SKILL_MODIFIERS.get(check_result.skill_used, [])
        for attr_path, mod_func in modifiers:
            new_value = mod_func(npc, abs(check_result.margin))
            npc.apply_temp_mod(attr_path, new_value)