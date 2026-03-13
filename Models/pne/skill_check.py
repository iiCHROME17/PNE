"""
Psychological Narrative Engine - Skill Check System
Name: skill_check.py
Author: Jerome Bawa

Two complementary skill-check mechanisms live here:

``SkillCheckResult`` / ``perform_check``
    A legacy threshold-based check (player skill / 10 ± noise vs a derived
    NPC threshold).  Used internally by ``DialogueProcessor.process_dialogue``
    to gate ``apply_modifiers`` — i.e. whether the player's approach temporarily
    shifts an NPC attribute this turn.

``DiceCheckResult`` / ``roll_dice`` / ``success_probability``
    The primary 2-dice system used by the NarrativeEngine.  Both player and NPC
    roll a single biased d6; player_die >= npc_die → success.  Bias weights are
    derived from the player's skill level and the NPC's resistance threshold,
    respectively.  ``success_probability`` provides the pre-roll display percentage.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math
import random
from .enums import LanguageArt, PlayerSkill, Difficulty
from .player_input import PlayerDialogueInput, PlayerSkillSet


@dataclass
class SkillCheckResult:
    """Result of a legacy threshold-based skill check (used for NPC modifiers).

    Attributes:
        success: Whether the player's effective roll met or exceeded the NPC's
            resistance threshold.
        skill_used: The ``PlayerSkill`` that was checked.
        player_val: Raw player skill level (0–10) used for the roll.
        threshold: NPC-derived resistance threshold in [0.0, 1.0].
        margin: ``effective_value - threshold``; positive on success, negative on
            failure.  Larger margins produce stronger attribute modifiers.
    """

    success: bool
    skill_used: PlayerSkill
    player_val: int
    threshold: float
    margin: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (used in session log exports)."""
        return {
            "success": self.success,
            "skill_used": self.skill_used.value,
            "player_val": self.player_val,
            "threshold": self.threshold,
            "margin": self.margin,
        }


@dataclass
class DiceCheckResult:
    """Result of the primary 2-dice (player vs NPC) skill check.

    Both player and NPC roll a single biased d6.  ``player_die >= npc_die``
    constitutes a success (ties go to the player per spec).

    Attributes:
        success: ``True`` if ``player_die >= npc_die``.
        player_die: The player's rolled face value (1–6).
        npc_die: The NPC's rolled face value (1–6).
        skill_used: The ``PlayerSkill`` enum member that drove this check.
        player_bias: The player's die-weight bias parameter (0.0–1.0); higher
            values skew the die toward larger faces.
        npc_bias: The NPC's die-weight bias (their resistance threshold, 0.0–1.0);
            derived from ``calc_threshold``.
    """

    success: bool
    player_die: int     # 1–6
    npc_die: int        # 1–6
    skill_used: PlayerSkill
    player_bias: float  # 0.0–1.0
    npc_bias: float     # 0.0–1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (used in the engine's per-turn response)."""
        return {
            "success": self.success,
            "player_die": self.player_die,
            "npc_die": self.npc_die,
            "skill_used": self.skill_used.value,
            "player_bias": self.player_bias,
            "npc_bias": self.npc_bias,
        }


class SkillCheckSystem:
    """Centralised hub for all skill-check logic in the PNE.

    Class-level constants
    ---------------------
    DIFFICULTY_ADJ
        Additive bias adjustment applied to the player die-weight on top of the
        ``player_relation`` bonus set by the engine.  Positive → easier, negative → harder.
    LANGUAGE_ART_TO_SKILL
        Maps each ``LanguageArt`` to the ``PlayerSkill`` it draws from.
        ``LanguageArt.NEUTRAL`` maps to ``None``, meaning no dice check is performed.
    SKILL_MODIFIERS
        Per-skill list of ``(attr_path, modifier_fn)`` pairs applied to the NPC on
        a successful legacy threshold check.  Each function receives ``(npc, margin)``
        and returns the new attribute value (clamped by ``apply_modifiers``).
    """

    # Additive adjustment to the player die-weight bias per difficulty level.
    # Applied on top of the player_relation bias_adj in the engine.
    DIFFICULTY_ADJ: dict = {
        Difficulty.SIMPLE:   +0.15,
        Difficulty.STANDARD:  0.00,
        Difficulty.STRICT:   -0.15,
    }

    LANGUAGE_ART_TO_SKILL = {
        LanguageArt.CHALLENGE:    PlayerSkill.AUTHORITY,
        LanguageArt.DIPLOMATIC:   PlayerSkill.DIPLOMACY,
        LanguageArt.EMPATHETIC:   PlayerSkill.EMPATHY,
        LanguageArt.MANIPULATIVE: PlayerSkill.MANIPULATION,
        LanguageArt.NEUTRAL:      None,
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
        ],
    }

    @staticmethod
    def calc_threshold(npc, skill: PlayerSkill) -> float:
        """Derive the NPC's resistance threshold for the given skill (0.0–1.0).

        Higher thresholds make the NPC harder to influence with that approach.
        The formulas reflect each skill's psychological counterpart:

        - **AUTHORITY** scales with ``social.assertion`` — assertive NPCs resist commands.
        - **MANIPULATION** scales with ``cognitive.self_esteem`` — secure NPCs resist deceit.
        - **EMPATHY** scales inversely with ``social.empathy`` — empathetic NPCs are receptive.
        - **DIPLOMACY** scales inversely with ``cognitive.cog_flexibility`` — rigid NPCs resist reasoning.

        Args:
            npc: An ``NPCModel`` instance supplying ``cognitive`` and ``social`` attributes.
            skill: The ``PlayerSkill`` whose threshold is requested.

        Returns:
            Float in [0.0, 1.0] representing the NPC's resistance level.
        """
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
        npc,
    ) -> Optional[SkillCheckResult]:
        """Run the legacy threshold-based skill check for the current player choice.

        Returns ``None`` for ``LanguageArt.NEUTRAL`` choices (no check needed).
        The result is used only to gate ``apply_modifiers``; the engine uses the
        2-dice system (``roll_dice``) for the authoritative success/failure signal.

        Args:
            player_input: The parsed player choice including its ``language_art``.
            player_skills: The player's current skill levels.
            npc: The NPC being addressed (provides resistance thresholds).

        Returns:
            A ``SkillCheckResult``, or ``None`` if the choice uses ``NEUTRAL`` art.
        """
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
            margin=margin,
        )

    @staticmethod
    def apply_modifiers(npc, check_result: SkillCheckResult) -> None:
        """Apply temporary NPC attribute modifiers on a successful threshold check.

        Only called when ``check_result.success`` is ``True``.  Each modifier in
        ``SKILL_MODIFIERS`` is a lambda that computes the new attribute value from
        the NPC's current value and the check margin; the result is passed to
        ``npc.apply_temp_mod`` so it is automatically reversed at conversation end.

        Args:
            npc: The NPC whose attributes will be temporarily modified.
            check_result: The ``SkillCheckResult`` from ``perform_check``.
        """
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