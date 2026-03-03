"""
Session Management Module

Manages conversation state for multi-NPC scenarios.

Key Components:
- NPCConversationState: Per-NPC state within a shared scenario
- ConversationSession: Container for a running conversation with multiple NPCs

Each NPC maintains its own:
- DialogueProcessor (with BDI pipeline and LLM integration)
- Current node position in the scenario graph
- Conversation history and choice log
- Terminal outcome (if conversation has ended)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from pne import DialogueProcessor, ConversationModel
from PNE_Models import NPCModel


@dataclass
class NPCConversationState:
    """
    Per-NPC conversation state inside a shared scenario.

    Each NPC participating in a scenario has its own independent state:
    - DialogueProcessor: Manages BDI (Belief-Desire-Intention) processing
    - Current node: Where this NPC is in the scenario graph
    - History: Complete transcript of exchanges with this NPC
    - Terminal outcome: Final result if conversation has ended

    This allows multiple NPCs to diverge to different paths in the same
    scenario based on their individual personalities and the player's
    interactions with each one.

    Attributes:
        npc_id: Unique identifier for this NPC
        npc: The NPC model containing personality, beliefs, and world state
        processor: DialogueProcessor handling BDI pipeline for this NPC
        scenario_id: ID of the scenario this conversation is part of
        current_node: Current position in the scenario graph (default: "start")
        is_complete: Whether this NPC's conversation has ended
        terminal_outcome: Final outcome data if conversation ended
        history: Fallout-style visible log of all exchanges
        choices_made: List of choice IDs the player has made with this NPC
    """

    npc_id: str
    npc: NPCModel
    processor: DialogueProcessor
    scenario_id: str
    current_node: str = "start"
    is_complete: bool = False
    terminal_outcome: Optional[Dict[str, Any]] = None

    # Judgement-based narrative progress (0=fail territory, 100=succeed territory, 50=neutral)
    # Drives terminal routing; modified by dice outcomes scaled by risk.
    judgement: int = 50

    # Recovery sub-turn state — set when main dice fails so the CLI loop
    # shows recovery choices on the next get_available_choices() call.
    recovery_mode: bool = False
    pending_recovery_choices: List[Dict[str, Any]] = field(default_factory=list)

    # Fallout-style visible log for this NPC
    history: List[Dict[str, Any]] = field(default_factory=list)
    choices_made: List[str] = field(default_factory=list)

    def conversation_model(self) -> ConversationModel:
        """
        Get the underlying ConversationModel from the DialogueProcessor.

        The ConversationModel tracks the full BDI state trajectory:
        beliefs, desires, intentions, and emotional responses over time.

        Returns:
            ConversationModel instance containing the conversation state
        """
        return self.processor.conversation

    @property
    def turn_count(self) -> int:
        """
        Get the current turn count for this NPC's conversation.

        Returns:
            Number of conversation turns completed
        """
        return self.processor.conversation.turn_count

    def add_exchange(
        self,
        speaker: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a dialogue exchange to the visible history log.

        This creates a Fallout-style conversation log with speaker,
        text, and optional metadata (thoughts, desires, intentions).

        Args:
            speaker: Name of the speaker ("Player", NPC name, or "Narrator")
            text: The dialogue text
            metadata: Optional dict containing:
                - thought: Internal thought reaction
                - desire: Current desire state
                - intention: Behavioral intention
                - interaction_outcome: Outcome data for this exchange
        """
        entry: Dict[str, Any] = {
            "turn": self.turn_count,
            "speaker": speaker,
            "text": text,
        }
        if metadata:
            entry["metadata"] = metadata
        self.history.append(entry)


@dataclass
class ConversationSession:
    """
    A running conversation session for a single scenario and one or more NPCs.

    The session manages:
    - Scenario structure (NPC-agnostic nodes, choices, transitions)
    - Multiple NPC states (each with independent BDI processing)
    - Shared player choice log (visible conversation history)

    Key Design:
    - Scenario is NPC-agnostic (same structure for any NPC)
    - Each NPC has its own BDI/LLM pipeline and memory
    - Player choices are shared across all NPCs
    - Routing is resolved per-NPC via TransitionResolver
    - Different NPCs can diverge to different nodes after same player choice

    Attributes:
        scenario_id: Unique identifier for the scenario
        scenario: Complete scenario data structure
        npc_states: Dict mapping npc_id to NPCConversationState
        player_choice_log: Global log of player choices (independent of NPC internals)
    """

    scenario_id: str
    scenario: Dict[str, Any]
    npc_states: Dict[str, NPCConversationState]  # npc_id -> state

    # Global visible choice history (independent of NPC internals)
    player_choice_log: List[Dict[str, Any]] = field(default_factory=list)

    def active_npcs(self) -> List[NPCConversationState]:
        """
        Get all NPCs that are still active in the conversation.

        An NPC is active if their conversation hasn't reached a terminal state.

        Returns:
            List of NPCConversationState objects for active NPCs
        """
        return [s for s in self.npc_states.values() if not s.is_complete]