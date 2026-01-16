"""
Psychological Narrative Engine - Conversation Containment
Name: conversation.py
Author: Jerome Bawa
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ConversationModel:
    """Container for conversation metadata and state"""
    conversation_id: str
    stage: str  # Current phase of conversation
    topic: str  # Active subject being discussed
    turn_count: int = 0
    history: List[str] = field(default_factory=list)
    
    def advance_turn(self):
        """Increment turn counter"""
        self.turn_count += 1
    
    def add_exchange(self, player_line: str, npc_line: str):
        """Add dialogue exchange to history"""
        self.history.append(f"Player: {player_line}")
        self.history.append(f"NPC: {npc_line}")
        self.advance_turn()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'conversation_id': self.conversation_id,
            'stage': self.stage,
            'topic': self.topic,
            'turn_count': self.turn_count,
            'history': self.history
        }