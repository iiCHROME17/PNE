"""
Psychological Narrative Engine - Desire Formation Layer
Name: desire.py
Author: Jerome Bawa

Converts subjective beliefs into goal-oriented desires.
This is the missing BDI link between:
- What NPC BELIEVES is happening (Cognitive)
- What NPC WANTS in response (Desire)
- What NPC will DO (Social/Behavioral)

The bias_type from ThoughtReaction is used as a post-pattern modifier:
it can sharpen the desire_type and boost intensity based on the NPC's
cognitive bias profile, producing genuinely different desire states across
NPCs who receive the same player choice.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from .cognitive import ThoughtReaction
from .player_input import PlayerDialogueInput


@dataclass
class DesireState:
    """NPC's desire in response to player input"""
    immediate_desire: str   # "Test their sincerity", "Find common ground", etc.
    desire_type: str        # "information-seeking" | "affiliation" | "protection" | "dominance"
    intensity: float        # 0.0–1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "immediate_desire": self.immediate_desire,
            "desire_type": self.desire_type,
            "intensity": self.intensity,
        }


# ── Bias → desire modifier ─────────────────────────────────────────────────
# Applied after the 6 belief-keyword patterns.
# desire_type=None means "keep whatever the pattern selected".
# intensity_boost is additive (capped at 1.0).
BIAS_TO_DESIRE_MODIFIER: Dict[str, Dict] = {
    "hostile_attribution": {"desire_type": "protection",          "intensity_boost": 0.2},
    "optimism_bias":       {"desire_type": "affiliation",         "intensity_boost": 0.15},
    "confirmation_bias":   {"desire_type": "information-seeking", "intensity_boost": 0.1},
    "empathy_resonance":   {"desire_type": "affiliation",         "intensity_boost": 0.25},
    "cynical_realism":     {"desire_type": None,                  "intensity_boost": 0.0},
    "ideological_filter":  {"desire_type": None,                  "intensity_boost": 0.15},
    "self_referential":    {"desire_type": "dominance",           "intensity_boost": 0.1},
    "projection":          {"desire_type": "protection",          "intensity_boost": 0.1},
    "in_group_bias":       {"desire_type": None,                  "intensity_boost": 0.2},
    "black_white_thinking":{"desire_type": "dominance",           "intensity_boost": 0.3},
    "scarcity_mindset":    {"desire_type": "protection",          "intensity_boost": 0.25},
}


class DesireFormation:
    """
    Transforms NPC's subjective belief into goal-oriented desire.

    Architecture:
    BELIEF → DESIRE → INTENTION
    "They claim empathy" → "Test if sincere" → "Question them directly"

    After the 6 belief-keyword patterns resolve the base desire, the NPC's
    cognitive bias_type applies a modifier that can override desire_type and
    boost intensity — giving different NPCs different reactions to the same input.
    """

    @staticmethod
    def form_desire(
        thought_reaction: ThoughtReaction,
        player_input: PlayerDialogueInput,
        npc,
        npc_intent,
    ) -> DesireState:
        """
        Given NPC's belief about the player's words, what does the NPC WANT?

        Runs 6 belief-keyword patterns to determine a base desire, then
        applies the cognitive bias modifier from thought_reaction.bias_type.
        """
        belief = thought_reaction.subjective_belief.lower()
        valence = thought_reaction.emotional_valence

        # ── Base desire: pattern matching ─────────────────────────────
        immediate_desire: str
        desire_type: str
        intensity: float

        # PATTERN 1: Uncertainty → Information Seeking
        if any(w in belief for w in ["unclear", "unsure", "testing", "cheap", "words"]):
            if npc.cognitive.self_esteem > 0.6:
                immediate_desire = "Test their commitment and sincerity"
                desire_type = "information-seeking"
                intensity = 0.7
            else:
                immediate_desire = "Protect myself from being deceived"
                desire_type = "protection"
                intensity = 0.8

        # PATTERN 2: Perceived Sincerity → Affiliation
        elif any(w in belief for w in ["genuine", "sincere", "authentic", "real", "honest"]):
            if npc.social.empathy > 0.5:
                immediate_desire = "Find common ground and build trust"
                desire_type = "affiliation"
                intensity = 0.6
            else:
                immediate_desire = "Acknowledge but remain guarded"
                desire_type = "information-seeking"
                intensity = 0.4

        # PATTERN 3: Perceived Threat → Protection/Dominance
        elif any(w in belief for w in ["manipulative", "threat", "challenging", "attack", "deceive"]):
            if npc.social.wildcard == "Martyr":
                immediate_desire = "Defend the cause and test their loyalty"
                desire_type = "protection"
                intensity = 0.9
            elif npc.social.assertion > 0.7:
                immediate_desire = "Assert dominance and challenge them back"
                desire_type = "dominance"
                intensity = 0.8
            else:
                immediate_desire = "Maintain boundaries and de-escalate"
                desire_type = "protection"
                intensity = 0.6

        # PATTERN 4: Opportunistic Detection → Suspicion
        elif any(w in belief for w in ["opportunistic", "using", "exploit", "advantage"]):
            immediate_desire = "Scrutinize their true motives"
            desire_type = "information-seeking"
            intensity = 0.8

        # PATTERN 5: Ideological Alignment → Affiliation
        elif player_input.ideology_alignment and player_input.ideology_alignment in npc.social.ideology:
            alignment_strength = npc.social.ideology[player_input.ideology_alignment]
            if alignment_strength > 0.6:
                immediate_desire = "Explore shared values and goals"
                desire_type = "affiliation"
                intensity = alignment_strength
            else:
                immediate_desire = "Understand their true intentions"
                desire_type = "information-seeking"
                intensity = 0.5

        # PATTERN 6: Emotional Valence Defaults
        elif valence < -0.3:
            immediate_desire = "Maintain distance and protect boundaries"
            desire_type = "protection"
            intensity = 0.6
        elif valence > 0.3:
            immediate_desire = "Explore potential connection"
            desire_type = "affiliation"
            intensity = 0.5

        # DEFAULT: Long-term goal driven
        else:
            long_term = npc_intent.long_term_desire.lower()
            if "protect" in long_term or "secure" in long_term:
                immediate_desire = "Evaluate if they align with our mission"
                desire_type = "information-seeking"
                intensity = 0.5
            elif "power" in long_term or "control" in long_term:
                immediate_desire = "Assess if they can be useful"
                desire_type = "information-seeking"
                intensity = 0.6
            else:
                immediate_desire = "Understand their true intentions"
                desire_type = "information-seeking"
                intensity = 0.5

        # ── Bias modifier ─────────────────────────────────────────────
        mod = BIAS_TO_DESIRE_MODIFIER.get(thought_reaction.bias_type, {})
        if mod.get("desire_type"):
            desire_type = mod["desire_type"]
        intensity = min(1.0, intensity + mod.get("intensity_boost", 0.0))

        return DesireState(
            immediate_desire=immediate_desire,
            desire_type=desire_type,
            intensity=intensity,
        )
