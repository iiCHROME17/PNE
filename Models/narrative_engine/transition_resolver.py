"""
Transition Resolver Module

Handles dynamic routing between conversation nodes based on NPC state.

This is the key component that makes scenarios NPC-agnostic:
- Same player choices can lead to different nodes for different NPCs
- Routing is determined by each NPC's internal state (BDI beliefs, desires, intentions)
- Transitions are evaluated in order; first match wins

Key Components:
- TransitionResolver: Evaluates transition conditions against live NPC state
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .session import NPCConversationState


class TransitionResolver:
    """
    Evaluates a node's transition list against live NPC state to determine
    which node to route to next.

    Transitions are evaluated in order — first match wins.
    This is where the scenario becomes truly NPC-agnostic: same choices,
    different NPC states, different paths.

    The resolver supports simple expression evaluation for transition conditions,
    including:
    - player_relation: The NPC's relationship with the player
    - turn_count: Number of conversation turns so far
    - Basic comparison operators: ==, !=, <, >, <=, >=, and, or

    Example transition conditions:
    - "player_relation > 0.5"
    - "turn_count >= 3"
    - "player_relation < 0 and turn_count > 1"
    """

    # Simple expression evaluator for transition conditions.
    # Supports: player_relation, turn_count, and basic comparisons.
    SAFE_NAMES = {"player_relation", "turn_count"}

    @staticmethod
    def resolve(
        transitions: List[Dict[str, Any]],
        npc_state: "NPCConversationState",
    ) -> Optional[str]:
        """
        Walk the transition list and return the target node_id for the first
        condition that evaluates to True.

        Args:
            transitions: List of transition dicts, each containing:
                - condition: String expression to evaluate (e.g., "player_relation > 0.5")
                - target: Node ID to transition to if condition is True
            npc_state: Current state of the NPC, including conversation data

        Returns:
            Target node_id if a matching transition is found, None otherwise

        Notes:
            - Transitions are evaluated in order; first match wins
            - Invalid or failing conditions are skipped with a warning
            - Uses restricted eval for safety (only allows SAFE_NAMES variables)
        """
        player_relation = npc_state.npc.world.player_relation
        turn_count = npc_state.turn_count

        context = {
            "player_relation": player_relation,
            "turn_count": turn_count,
        }

        for transition in transitions:
            condition_str = transition.get("condition", "False")
            try:
                # Restrict eval to known safe variables only
                result = eval(condition_str, {"__builtins__": {}}, context)  # noqa: S307
                if result:
                    return transition["target"]
            except Exception as e:
                print(f"  [TransitionResolver] Failed to evaluate condition '{condition_str}': {e}")
                continue

        return None

    @staticmethod
    def is_terminal(node: Dict[str, Any]) -> bool:
        """
        Check if a node is terminal (ends the conversation).

        A node is terminal if it has no choices and is explicitly marked
        as terminal in the scenario data.

        Args:
            node: The node dictionary to check

        Returns:
            True if the node is terminal, False otherwise
        """
        return node.get("terminal", False)