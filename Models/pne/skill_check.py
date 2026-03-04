"""
Psychological Narrative Engine - Skill Check System
Name: skill_check.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math
import random
from .enums import LanguageArt, PlayerSkill, Difficulty
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


@dataclass
class DiceCheckResult:
    """Result of a 2-dice (player vs NPC) skill check"""
    success: bool
    player_die: int     # 1-6
    npc_die: int        # 1-6
    skill_used: PlayerSkill
    player_bias: float  # 0.0-1.0
    npc_bias: float     # 0.0-1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "player_die": self.player_die,
            "npc_die": self.npc_die,
            "skill_used": self.skill_used.value,
            "player_bias": self.player_bias,
            "npc_bias": self.npc_bias,
        }


class SkillCheckSystem:
    """Handles skill checks based on player input"""

    # Additive adjustment to the player die-weight bias per difficulty level.
    # Applied on top of the player_relation bias_adj in the engine.
    DIFFICULTY_ADJ: dict = {
        Difficulty.SIMPLE:   +0.15,
        Difficulty.STANDARD:  0.00,
        Difficulty.STRICT:   -0.15,
    }

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

    # ------------------------------------------------------------------ #
    # 2-Dice System
    # ------------------------------------------------------------------ #

    @staticmethod
    def _weighted_d6(bias: float) -> List[float]:
        """6-element probability list for a d6 weighted toward high faces when bias is high.

        bias=0 → uniform; bias=1 → heavily weighted toward 6.
        Uses P(face k) ∝ exp(bias * k) for k=1..6.
        """
        weights = [math.exp(bias * k) for k in range(1, 7)]
        total = sum(weights)
        return [w / total for w in weights]

    @staticmethod
    def success_probability(
        player_skill: int, npc, skill: "PlayerSkill", bias_adj: float = 0.0
    ) -> int:
        """Pre-roll success probability as integer percentage 0-100.

        Computed analytically: P(player_die >= npc_die) across all face combinations.
        Use this for the (X%) display before the actual roll.

        bias_adj shifts the player die weighting up or down (e.g. +0.1 for high relation).
        """
        player_bias = max(0.0, min(1.0, player_skill / 10.0 + bias_adj))
        npc_bias = SkillCheckSystem.calc_threshold(npc, skill)
        pp = SkillCheckSystem._weighted_d6(player_bias)
        np_ = SkillCheckSystem._weighted_d6(npc_bias)
        p_success = sum(
            pp[p] * np_[n]
            for p in range(6) for n in range(6)
            if (p + 1) >= (n + 1)
        )
        return round(p_success * 100)

    @staticmethod
    def roll_dice(
        player_skill: int, npc, skill: "PlayerSkill", bias_adj: float = 0.0
    ) -> DiceCheckResult:
        """Roll both weighted d6 dice and return the result.

        player_die >= npc_die → success (equal = instant success per spec).
        bias_adj shifts the player die weighting (e.g. +0.1 for high relation).
        """
        player_bias = max(0.0, min(1.0, player_skill / 10.0 + bias_adj))
        npc_bias = SkillCheckSystem.calc_threshold(npc, skill)
        pp = SkillCheckSystem._weighted_d6(player_bias)
        np_ = SkillCheckSystem._weighted_d6(npc_bias)
        player_die = random.choices(range(1, 7), weights=pp)[0]
        npc_die = random.choices(range(1, 7), weights=np_)[0]
        return DiceCheckResult(
            success=(player_die >= npc_die),
            player_die=player_die,
            npc_die=npc_die,
            skill_used=skill,
            player_bias=player_bias,
            npc_bias=npc_bias,
        )