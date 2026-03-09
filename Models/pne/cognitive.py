"""
Psychological Narrative Engine - Cognitive Interpretation Layer
Name: cognitive.py
Author: Jerome Bawa

Thought generation is now template-based (CognitiveThoughtMatcher) rather than
LLM-driven, removing the second Ollama round-trip per turn.
Emotional valence is unchanged — still computed from NPC cognitive state + tone.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from .player_input import PlayerDialogueInput
from .cognitive_thought_matcher import CognitiveThoughtMatcher


@dataclass
class ThoughtReaction:
    """NPC's internal subjective thought (not spoken)"""
    internal_thought: str   # First-person emotional reaction
    subjective_belief: str  # What NPC interprets is happening
    cognitive_state: Dict[str, float]  # {self_esteem, locus_of_control, cog_flexibility}
    emotional_valence: float  # -1.0 (negative) to 1.0 (positive)
    bias_type: str = field(default="cynical_realism")  # matched cognitive bias template

    def to_dict(self) -> Dict[str, Any]:
        return {
            "internal_thought": self.internal_thought,
            "subjective_belief": self.subjective_belief,
            "cognitive_state": self.cognitive_state,
            "emotional_valence": self.emotional_valence,
            "bias_type": self.bias_type,
        }


class CognitiveInterpreter:
    """
    Processes player input through the NPC's cognitive model.

    Thought and belief are now selected from cognitive_thoughts.json via
    CognitiveThoughtMatcher — no LLM call. Emotional valence is computed
    with the original rules-based scorer.

    Constructor accepts legacy (base_url, model) arguments for compatibility
    with existing processor.py call-sites; they are silently ignored.
    """

    def __init__(self, *args, **kwargs):
        self._matcher = CognitiveThoughtMatcher()

    def interpret(self, player_input: PlayerDialogueInput, npc) -> ThoughtReaction:
        """Match a cognitive template and compute emotional valence."""
        bias_type, internal_thought, subjective_belief = self._matcher.match(player_input, npc)
        emotional_valence = self._calculate_emotional_valence(player_input, npc)

        return ThoughtReaction(
            internal_thought=internal_thought,
            subjective_belief=subjective_belief,
            cognitive_state={
                "self_esteem": npc.cognitive.self_esteem,
                "locus_of_control": npc.cognitive.locus_of_control,
                "cog_flexibility": npc.cognitive.cog_flexibility,
            },
            emotional_valence=emotional_valence,
            bias_type=bias_type,
        )

    def _calculate_emotional_valence(self, player_input: PlayerDialogueInput, npc) -> float:
        """Calculate emotional reaction based on cognitive state and input tones."""
        valence = 0.0

        # Low self-esteem reacts negatively to authority/manipulation
        if npc.cognitive.self_esteem < 0.4:
            valence -= (player_input.authority_tone * 0.3)
            valence -= (player_input.manipulation_tone * 0.5)

        # External locus attributes hostility to others
        if npc.cognitive.locus_of_control < 0.5:
            valence -= (player_input.authority_tone * 0.4)

        # High flexibility responds positively to diplomacy
        if npc.cognitive.cog_flexibility > 0.6:
            valence += (player_input.diplomacy_tone * 0.4)
            valence += (player_input.empathy_tone * 0.3)

        # Rigid thinking resists persuasion
        if npc.cognitive.cog_flexibility < 0.4:
            valence -= (player_input.diplomacy_tone * 0.2)

        return max(-1.0, min(1.0, valence))
