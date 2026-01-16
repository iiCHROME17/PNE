"""
Psychological Narrative Engine - Outcome Structures
Name: outcomes.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable
from .enums import TerminalOutcomeType
from .conversation import ConversationModel
from .social import BehaviouralIntention


@dataclass
class InteractionOutcome:
    """
    Micro-outcome: immediate conversational effect
    NOT terminal - just shifts NPC state
    """
    outcome_id: str
    stance_delta: Dict[str, float]  # Adjusts NPC attributes
    relation_delta: float  # Change to player_relation
    intention_shift: Optional[str]  # New NPC intention
    min_response: str  # Negative reaction variant
    max_response: str  # Positive reaction variant
    scripted: bool = False  # If true, no interpolation
    
    def get_response(self, emotional_valence: float) -> str:
        """
        Interpolate between min/max based on emotional valence
        """
        if self.scripted:
            return self.max_response if emotional_valence > 0 else self.min_response
        
        # Simple interpolation (can be enhanced)
        if emotional_valence > 0.3:
            return self.max_response
        elif emotional_valence < -0.3:
            return self.min_response
        else:
            return f"{self.min_response} But... {self.max_response}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'outcome_id': self.outcome_id,
            'stance_delta': self.stance_delta,
            'relation_delta': self.relation_delta,
            'intention_shift': self.intention_shift,
            'min_response': self.min_response,
            'max_response': self.max_response,
            'scripted': self.scripted
        }


@dataclass
class TerminalOutcome:
    """
    Terminal outcome: final result of conversation
    """
    terminal_id: TerminalOutcomeType
    condition: Callable  # Function that evaluates if this outcome triggers
    result: str  # What actually happens in game world
    final_dialogue: str  # NPC's closing line
    
    def evaluate(self, npc, conversation: ConversationModel) -> bool:
        """Check if this terminal outcome should trigger"""
        return self.condition(npc, conversation)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'terminal_id': self.terminal_id.value,
            'result': self.result,
            'final_dialogue': self.final_dialogue
        }


@dataclass
class OutcomeIndex:
    """
    Maps dialogue choices to possible outcomes
    """
    choice_id: str
    interaction_outcomes: List[InteractionOutcome]
    terminal_outcomes: List[TerminalOutcome]
    
    def get_interaction_outcome(self, behavioural_intention: BehaviouralIntention) -> InteractionOutcome:
        """
        Select appropriate interaction outcome based on NPC's behavioural intention
        """
        # Match intention type to outcome
        for outcome in self.interaction_outcomes:
            if behavioural_intention.intention_type.lower() in outcome.outcome_id.lower():
                return outcome
        
        # Default to first outcome
        return self.interaction_outcomes[0] if self.interaction_outcomes else None
    
    def check_terminal_outcomes(self, npc, conversation: ConversationModel) -> Optional[TerminalOutcome]:
        """
        Check if any terminal outcome condition is met
        """
        for terminal in self.terminal_outcomes:
            if terminal.evaluate(npc, conversation):
                return terminal
        return None