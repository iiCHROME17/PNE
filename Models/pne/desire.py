"""
Psychological Narrative Engine - Desire Formation Layer
Name: desire.py
Author: Jerome Bawa

Converts subjective beliefs into goal-oriented desires
This is the missing BDI link between:
- What NPC BELIEVES is happening (Cognitive)
- What NPC WANTS in response (Desire)
- What NPC will DO (Social/Behavioral)
"""

from dataclasses import dataclass
from typing import Dict, Any
from .cognitive import ThoughtReaction
from .player_input import PlayerDialogueInput


@dataclass
class DesireState:
    """NPC's desire in response to player input"""
    immediate_desire: str  # "Test their sincerity" / "Find common ground" / "Protect the cause"
    desire_type: str  # "information-seeking" / "affiliation" / "protection" / "dominance"
    intensity: float  # 0-1, how strongly NPC wants this
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'immediate_desire': self.immediate_desire,
            'desire_type': self.desire_type,
            'intensity': self.intensity
        }


class DesireFormation:
    """
    Transforms NPC's subjective belief into goal-oriented desire
    
    Architecture:
    BELIEF → DESIRE → INTENTION
    "They claim empathy" → "Test if sincere" → "Question them directly"
    """
    
    @staticmethod
    def form_desire(
        thought_reaction: ThoughtReaction,
        player_input: PlayerDialogueInput,
        npc,
        npc_intent
    ) -> DesireState:
        """
        Given NPC's belief about player's words,
        what does NPC WANT?
        """
        
        belief = thought_reaction.subjective_belief.lower()
        valence = thought_reaction.emotional_valence
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 1: Uncertainty → Information Seeking
        # ═══════════════════════════════════════════════════════════
        if any(word in belief for word in ["unclear", "unsure", "testing", "cheap", "words"]):
            # NPC doesn't trust the words yet
            if npc.cognitive.self_esteem > 0.6:
                # Confident NPCs probe directly
                return DesireState(
                    immediate_desire="Test their commitment and sincerity",
                    desire_type="information-seeking",
                    intensity=0.7
                )
            else:
                # Insecure NPCs assume the worst
                return DesireState(
                    immediate_desire="Protect myself from being deceived",
                    desire_type="protection",
                    intensity=0.8
                )
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 2: Perceived Sincerity → Affiliation
        # ═══════════════════════════════════════════════════════════
        if any(word in belief for word in ["genuine", "sincere", "authentic", "real", "honest"]):
            if npc.social.empathy > 0.5:
                return DesireState(
                    immediate_desire="Find common ground and build trust",
                    desire_type="affiliation",
                    intensity=0.6
                )
            else:
                # Low empathy NPC still cautious even if they believe sincerity
                return DesireState(
                    immediate_desire="Acknowledge but remain guarded",
                    desire_type="information-seeking",
                    intensity=0.4
                )
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 3: Perceived Threat → Protection/Dominance
        # ═══════════════════════════════════════════════════════════
        if any(word in belief for word in ["manipulative", "threat", "challenging", "attack", "deceive"]):
            if npc.social.wildcard == "Martyr":
                # Martyr complex: protect the cause at all costs
                return DesireState(
                    immediate_desire="Defend the cause and test their loyalty",
                    desire_type="protection",
                    intensity=0.9
                )
            elif npc.social.assertion > 0.7:
                # Assertive NPCs push back
                return DesireState(
                    immediate_desire="Assert dominance and challenge them back",
                    desire_type="dominance",
                    intensity=0.8
                )
            else:
                # Less assertive NPCs withdraw
                return DesireState(
                    immediate_desire="Maintain boundaries and de-escalate",
                    desire_type="protection",
                    intensity=0.6
                )
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 4: Opportunistic Detection → Suspicion
        # ═══════════════════════════════════════════════════════════
        if any(word in belief for word in ["opportunistic", "using", "exploit", "advantage"]):
            return DesireState(
                immediate_desire="Scrutinize their true motives",
                desire_type="information-seeking",
                intensity=0.8
            )
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 5: Ideological Alignment → Affiliation
        # ═══════════════════════════════════════════════════════════
        if player_input.ideology_alignment:
            if player_input.ideology_alignment in npc.social.ideology:
                alignment_strength = npc.social.ideology[player_input.ideology_alignment]
                if alignment_strength > 0.6:
                    return DesireState(
                        immediate_desire="Explore shared values and goals",
                        desire_type="affiliation",
                        intensity=alignment_strength
                    )
        
        # ═══════════════════════════════════════════════════════════
        # PATTERN 6: Emotional Valence-Based Defaults
        # ═══════════════════════════════════════════════════════════
        if valence < -0.3:
            # Negative emotional reaction
            return DesireState(
                immediate_desire="Maintain distance and protect boundaries",
                desire_type="protection",
                intensity=0.6
            )
        elif valence > 0.3:
            # Positive emotional reaction
            return DesireState(
                immediate_desire="Explore potential connection",
                desire_type="affiliation",
                intensity=0.5
            )
        
        # ═══════════════════════════════════════════════════════════
        # DEFAULT: Based on NPC's Long-Term Goals
        # ═══════════════════════════════════════════════════════════
        long_term = npc_intent.long_term_desire.lower()
        
        if "protect" in long_term or "secure" in long_term:
            return DesireState(
                immediate_desire="Evaluate if they align with our mission",
                desire_type="information-seeking",
                intensity=0.5
            )
        elif "power" in long_term or "control" in long_term:
            return DesireState(
                immediate_desire="Assess if they can be useful",
                desire_type="information-seeking",
                intensity=0.6
            )
        else:
            return DesireState(
                immediate_desire="Understand their true intentions",
                desire_type="information-seeking",
                intensity=0.5
            )