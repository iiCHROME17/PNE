"""
Psychological Narrative Engine - Socialisation Filter Layer
Name: social.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any
from .player_input import PlayerDialogueInput
from .cognitive import ThoughtReaction


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
    """Converts internal thought into socially viable behaviour"""
    
    @staticmethod
    def filter(
        thought_reaction: ThoughtReaction,
        player_input: PlayerDialogueInput,
        npc
    ) -> BehaviouralIntention:
        """
        Determine how NPC will behaviourally respond
        """
        confrontation_level = 0.5
        intention_type = "neutral"
        emotional_expression = "direct"
        wildcard_triggered = False
        
        # High assertion + challenging input = challenge back
        if npc.social.assertion > 0.7:
            if player_input.authority_tone > 0.6:
                confrontation_level = 0.8
                intention_type = "Challenge Back"
        
        # High empathy + empathetic input = connect
        if npc.social.empathy > 0.6:
            if player_input.empathy_tone > 0.6:
                confrontation_level = 0.2
                intention_type = "Seek Connection"
        
        # Low conformity (high independence) = more unpredictable
        if npc.social.conf_indep > 0.7:
            confrontation_level += 0.2
        
        # Wildcard triggers
        if npc.social.wildcard:
            if npc.social.wildcard == "Martyr" and thought_reaction.emotional_valence < -0.3:
                wildcard_triggered = True
                intention_type = "Martyr Defense"
                emotional_expression = "explosive"
            elif npc.social.wildcard == "Napoleon" and player_input.authority_tone > 0.5:
                wildcard_triggered = True
                intention_type = "Assert Dominance"
                confrontation_level = 0.9
            elif npc.social.wildcard == "Inferiority" and player_input.authority_tone > 0.5:
                wildcard_triggered = True
                intention_type = "Submit"
                confrontation_level = 0.1
                emotional_expression = "suppressed"
        
        # Faction pressure
        if npc.social.faction and npc.social.social_position.value == "Boss":
            confrontation_level += 0.1  # Leaders more assertive
        
        return BehaviouralIntention(
            intention_type=intention_type,
            confrontation_level=min(1.0, confrontation_level),
            emotional_expression=emotional_expression,
            wildcard_triggered=wildcard_triggered
        )