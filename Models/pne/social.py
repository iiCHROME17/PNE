"""
Psychological Narrative Engine - Socialisation Filter Layer
Name: social.py
Author: Jerome Bawa (original), registry-driven rewrite by AI assistant

KEY CHANGE
----------
SocialisationFilter now selects intentions from the canonical
INTENTION_REGISTRY (pne/intention_registry.py) rather than returning
hard-coded strings.  This means:

  * Every intention_type that reaches the LLM prompt IS a registry name.
  * TransitionResolver.outcome_match keywords reliably find matches.
  * Scenario authors only need to reference INTENTION_NAMES in transitions.

Workflow:
  DESIRE → filter candidates from INTENTION_REGISTRY
         → score each candidate
         → return the highest-scoring BehaviouralIntention
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .player_input import PlayerDialogueInput
from .cognitive import ThoughtReaction
from .desire import DesireState
from .intention_registry import INTENTION_REGISTRY, IntentionTemplate, INTENTION_BY_NAME


@dataclass
class BehaviouralIntention:
    """NPC's intended response behavior (not yet dialogue)"""
    intention_type: str        # Canonical name from INTENTION_REGISTRY
    confrontation_level: float # 0–1
    emotional_expression: str  # "suppressed", "direct", "explosive", …
    wildcard_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intention_type": self.intention_type,
            "confrontation_level": self.confrontation_level,
            "emotional_expression": self.emotional_expression,
            "wildcard_triggered": self.wildcard_triggered,
        }


class SocialisationFilter:
    """
    Converts desire into a socially viable BehaviouralIntention by selecting
    the best-matching template from INTENTION_REGISTRY.

    Selection algorithm
    -------------------
    1. Pre-filter: keep only templates whose desire_type matches.
    2. Score each surviving template (0–1):
         - keyword overlap between desire text and template.desire_keywords
         - confrontation band fit (is NPC's natural confrontation level in range?)
         - wildcard gate (hard exclude if wildcard_required doesn't match)
         - NPC attribute conditions
    3. Return the highest-scoring template wrapped in BehaviouralIntention.
    4. If no template survives, fall back to "Neutral Response".
    """

    # NPC confrontation tendency is derived from social.assertion + social.conf_indep
    _ASSERT_WEIGHT = 0.7
    _INDEP_WEIGHT = 0.3

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @staticmethod
    def filter(
        thought_reaction: ThoughtReaction,
        desire_state: DesireState,
        player_input: PlayerDialogueInput,
        npc,
    ) -> BehaviouralIntention:
        """
        Given what the NPC WANTS, decide HOW they will act.
        Always returns a BehaviouralIntention whose intention_type is a
        canonical INTENTION_REGISTRY name.
        """
        # ── 0. Wildcard hard-overrides (bypass desire logic entirely) ────
        override = SocialisationFilter._check_wildcard_override(player_input, npc)
        if override:
            return override

        # ── 1. Compute NPC's natural confrontation tendency ──────────────
        npc_confrontation = SocialisationFilter._npc_confrontation(npc)

        # ── 2. Filter registry to matching desire_type ──────────────────
        candidates = [
            t for t in INTENTION_REGISTRY
            if t.desire_type == desire_state.desire_type or t.desire_type == ""
        ]

        # ── 3. Score each candidate ──────────────────────────────────────
        best_template: Optional[IntentionTemplate] = None
        best_score = -1.0

        for template in candidates:
            score = SocialisationFilter._score(
                template, desire_state, npc, npc_confrontation
            )
            if score > best_score:
                best_score = score
                best_template = template

        # ── 4. Build BehaviouralIntention from best template ─────────────
        if best_template is None or best_template.name == "Neutral Response":
            return SocialisationFilter._neutral_fallback(npc_confrontation)

        confrontation = SocialisationFilter._clamp_confrontation(
            npc_confrontation, best_template, desire_state.intensity
        )

        wildcard_triggered = (
            best_template.wildcard_required is not None
            and getattr(npc.social, "wildcard", None) == best_template.wildcard_required
        )

        return BehaviouralIntention(
            intention_type=best_template.name,
            confrontation_level=confrontation,
            emotional_expression=best_template.emotional_expression,
            wildcard_triggered=wildcard_triggered,
        )

    # ------------------------------------------------------------------ #
    # Scoring helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _score(
        template: IntentionTemplate,
        desire_state: DesireState,
        npc,
        npc_confrontation: float,
    ) -> float:
        """
        Score how well this template fits the current desire + NPC profile.
        Returns a float; higher = better fit.  Negative = hard exclude.
        """
        # ── Hard gate: wildcard_required must match NPC wildcard ─────────
        npc_wildcard = getattr(npc.social, "wildcard", None)
        if template.wildcard_required and template.wildcard_required != npc_wildcard:
            return -1.0

        # ── Hard gate: NPC attribute conditions ─────────────────────────
        if not SocialisationFilter._check_npc_conditions(template, npc):
            return -1.0

        score = 0.0

        # ── Keyword overlap (0–0.5) ──────────────────────────────────────
        desire_text = desire_state.immediate_desire.lower()
        if template.desire_keywords:
            matches = sum(1 for kw in template.desire_keywords if kw.lower() in desire_text)
            score += 0.5 * (matches / len(template.desire_keywords))
        else:
            # Fallback template (no keywords) gets a small base score
            score += 0.05

        # ── Confrontation band fit (0–0.4) ────────────────────────────────
        if template.confrontation_min <= npc_confrontation <= template.confrontation_max:
            score += 0.4
        else:
            # Partial credit if close
            distance = min(
                abs(npc_confrontation - template.confrontation_min),
                abs(npc_confrontation - template.confrontation_max),
            )
            score += max(0.0, 0.4 - distance * 0.8)

        # ── Intensity bonus (0–0.1): high intensity → higher confrontation ─
        if desire_state.intensity > 0.7 and template.confrontation_max > 0.6:
            score += 0.1

        return score

    @staticmethod
    def _check_npc_conditions(template: IntentionTemplate, npc) -> bool:
        """
        Evaluate npc_conditions dict, e.g. {"social.assertion": (">", 0.7)}
        Returns False if ANY condition fails.
        """
        for attr_path, (op, threshold) in template.npc_conditions.items():
            try:
                value = npc.get_attribute(attr_path)
            except Exception:
                # If we can't resolve the attribute, skip this condition
                continue
            ops = {">": float.__gt__, ">=": float.__ge__,
                   "<": float.__lt__, "<=": float.__le__, "==": float.__eq__}
            fn = ops.get(op)
            if fn and not fn(float(value), float(threshold)):
                return False
        return True

    # ------------------------------------------------------------------ #
    # Wildcard overrides
    # ------------------------------------------------------------------ #

    @staticmethod
    def _check_wildcard_override(player_input: PlayerDialogueInput, npc) -> Optional[BehaviouralIntention]:
        """
        Hard overrides triggered by wildcard + player tone regardless of desire.
        These bypass the normal desire→intention flow.
        """
        wildcard = getattr(npc.social, "wildcard", None)
        if not wildcard:
            return None

        if wildcard == "Inferiority" and player_input.authority_tone > 0.5:
            template = INTENTION_BY_NAME.get("Submit")
            if template:
                return BehaviouralIntention(
                    intention_type=template.name,
                    confrontation_level=0.1,
                    emotional_expression=template.emotional_expression,
                    wildcard_triggered=True,
                )

        return None

    # ------------------------------------------------------------------ #
    # Utility
    # ------------------------------------------------------------------ #

    @staticmethod
    def _npc_confrontation(npc) -> float:
        """Derive NPC's natural confrontation level from social attributes."""
        assertion = getattr(npc.social, "assertion", 0.5)
        conf_indep = getattr(npc.social, "conf_indep", 0.5)
        return min(1.0, (
            assertion * SocialisationFilter._ASSERT_WEIGHT
            + conf_indep * SocialisationFilter._INDEP_WEIGHT
        ))

    @staticmethod
    def _clamp_confrontation(
        npc_confrontation: float,
        template: IntentionTemplate,
        intensity: float,
    ) -> float:
        """
        Derive the actual confrontation value for this turn.
        Clamp to the template's valid range, then nudge by intensity.
        """
        base = max(template.confrontation_min,
                   min(template.confrontation_max, npc_confrontation))
        # Intensity nudges toward the upper half of the band
        band = template.confrontation_max - template.confrontation_min
        nudge = band * 0.3 * intensity
        result = min(template.confrontation_max, base + nudge)
        return round(result, 4)

    @staticmethod
    def _neutral_fallback(npc_confrontation: float) -> BehaviouralIntention:
        template = INTENTION_BY_NAME.get("Neutral Response")
        confrontation = npc_confrontation if template is None else max(
            template.confrontation_min,
            min(template.confrontation_max, npc_confrontation)
        )
        return BehaviouralIntention(
            intention_type="Neutral Response",
            confrontation_level=round(confrontation, 4),
            emotional_expression="direct",
        )