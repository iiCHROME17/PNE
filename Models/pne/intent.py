"""
Psychological Narrative Engine - NPC Intent Layer (Purpose/Meta Layer)
Name: intent.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class NPCIntent:
    """
    BDI Model: Beliefs, Desires, Intentions
    Defines NPC's purpose in the conversation
    """
    baseline_belief: str  # Core belief about situation
    long_term_desire: str  # What NPC ultimately wants
    immediate_intention: str  # Current goal (e.g., "Protect Door", "Test Player")
    stakes: str  # What's at risk
    
    def shift_intention(self, new_intention: str):
        """Update NPC's immediate intention"""
        self.immediate_intention = new_intention
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'baseline_belief': self.baseline_belief,
            'long_term_desire': self.long_term_desire,
            'immediate_intention': self.immediate_intention,
            'stakes': self.stakes
        }