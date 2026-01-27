"""
Psychological Narrative Engine - Socialisation Filter Layer
Name: social.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any
from .player_input import PlayerDialogueInput
from .cognitive import ThoughtReaction
from .desire import DesireState


@dataclass
class BehaviouralIntention:
    """NPC's intended response behavior (not yet dialogue)"""
    intention_type: str  # "Challenge Back", "De-escalate", "Seek Compromise", etc.
    confrontation_level: float  # 0-1 scale
    emotional_expression: str  # "suppressed", "direct", "explosive"
    wildcard_triggered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'intention_type': self.intention_type,
            'confrontation_level': self.confrontation_level,
            'emotional_expression': self.emotional_expression,
            'wildcard_triggered': self.wildcard_triggered
        }


class SocialisationFilter:
    """
    Converts desire into socially viable behavioral intention
    
    Architecture:
    DESIRE → INTENTION (modulated by social constraints)
    "Test their sincerity" → "Challenge to Reveal Truth" (if assertive)
    "Test their sincerity" → "Carefully Question" (if less assertive)
    """
    
    @staticmethod
    def filter(
        thought_reaction: ThoughtReaction,
        desire_state: DesireState,
        player_input: PlayerDialogueInput,
        npc
    ) -> BehaviouralIntention:
        """
        Given what NPC WANTS (desire),
        how will they ACT (intention)?
        
        Social constraints modulate raw desire into socially viable behavior
        """
        
        desire = desire_state.immediate_desire.lower()
        desire_type = desire_state.desire_type
        intensity = desire_state.intensity
        
        # ═══════════════════════════════════════════════════════════
        # DESIRE TYPE: Information Seeking
        # ═══════════════════════════════════════════════════════════
        if desire_type == "information-seeking":
            if "test" in desire or "probe" in desire or "scrutinize" in desire:
                if npc.social.assertion > 0.7:
                    # High assertion = direct challenging questions
                    return BehaviouralIntention(
                        intention_type="Challenge to Reveal Truth",
                        confrontation_level=min(0.9, 0.6 + (intensity * 0.2)),
                        emotional_expression="direct"
                    )
                else:
                    # Lower assertion = careful probing
                    return BehaviouralIntention(
                        intention_type="Carefully Question Motives",
                        confrontation_level=0.3 + (intensity * 0.2),
                        emotional_expression="measured"
                    )
            
            elif "evaluate" in desire or "assess" in desire or "understand" in desire:
                return BehaviouralIntention(
                    intention_type="Neutral Evaluation",
                    confrontation_level=0.4,
                    emotional_expression="analytical"
                )
        
        # ═══════════════════════════════════════════════════════════
        # DESIRE TYPE: Affiliation
        # ═══════════════════════════════════════════════════════════
        elif desire_type == "affiliation":
            if "common ground" in desire or "trust" in desire or "build" in desire:
                if npc.social.empathy > 0.5:
                    return BehaviouralIntention(
                        intention_type="Seek Connection",
                        confrontation_level=0.2,
                        emotional_expression="open"
                    )
                else:
                    # Low empathy dampens affiliation attempt
                    return BehaviouralIntention(
                        intention_type="Cautious Openness",
                        confrontation_level=0.4,
                        emotional_expression="guarded"
                    )
            
            elif "explore" in desire or "shared" in desire:
                return BehaviouralIntention(
                    intention_type="Explore Common Ground",
                    confrontation_level=0.3,
                    emotional_expression="curious"
                )
            
            elif "acknowledge" in desire:
                return BehaviouralIntention(
                    intention_type="Acknowledge with Reservation",
                    confrontation_level=0.5,
                    emotional_expression="cautious"
                )
        
        # ═══════════════════════════════════════════════════════════
        # DESIRE TYPE: Protection
        # ═══════════════════════════════════════════════════════════
        elif desire_type == "protection":
            if "defend" in desire or "cause" in desire:
                if npc.social.wildcard == "Martyr":
                    # Martyr complex = passionate defense
                    return BehaviouralIntention(
                        intention_type="Defend Cause Passionately",
                        confrontation_level=0.8,
                        emotional_expression="explosive",
                        wildcard_triggered=True
                    )
                else:
                    return BehaviouralIntention(
                        intention_type="Establish Boundaries",
                        confrontation_level=0.6,
                        emotional_expression="firm"
                    )
            
            elif "protect" in desire or "deceived" in desire:
                return BehaviouralIntention(
                    intention_type="Maintain Distance",
                    confrontation_level=0.5,
                    emotional_expression="suspicious"
                )
            
            elif "boundaries" in desire or "de-escalate" in desire:
                return BehaviouralIntention(
                    intention_type="De-escalate and Withdraw",
                    confrontation_level=0.3,
                    emotional_expression="controlled"
                )
        
        # ═══════════════════════════════════════════════════════════
        # DESIRE TYPE: Dominance
        # ═══════════════════════════════════════════════════════════
        elif desire_type == "dominance":
            if "assert" in desire or "challenge" in desire:
                if npc.social.wildcard == "Napoleon":
                    return BehaviouralIntention(
                        intention_type="Assert Dominance Aggressively",
                        confrontation_level=0.9,
                        emotional_expression="aggressive",
                        wildcard_triggered=True
                    )
                else:
                    return BehaviouralIntention(
                        intention_type="Challenge Back",
                        confrontation_level=0.7,
                        emotional_expression="assertive"
                    )
        
        # ═══════════════════════════════════════════════════════════
        # WILDCARD OVERRIDES (can override desire-based logic)
        # ═══════════════════════════════════════════════════════════
        if npc.social.wildcard:
            if npc.social.wildcard == "Inferiority" and player_input.authority_tone > 0.5:
                return BehaviouralIntention(
                    intention_type="Submit",
                    confrontation_level=0.1,
                    emotional_expression="suppressed",
                    wildcard_triggered=True
                )
        
        # ═══════════════════════════════════════════════════════════
        # FACTION/POSITION MODIFIERS
        # ═══════════════════════════════════════════════════════════
        confrontation_level = 0.5
        if npc.social.faction and npc.social.social_position.value == "Boss":
            confrontation_level += 0.1  # Leaders more assertive
        
        # High independence = more unpredictable
        if npc.social.conf_indep > 0.7:
            confrontation_level += 0.1
        
        # ═══════════════════════════════════════════════════════════
        # DEFAULT
        # ═══════════════════════════════════════════════════════════
        return BehaviouralIntention(
            intention_type="Neutral Response",
            confrontation_level=min(1.0, confrontation_level),
            emotional_expression="direct"
        )