"""
Transition Resolver Module

Handles deterministic FSM routing between conversation nodes.

Transition gates (all present gates must pass; first match wins):

1. condition      — Python expression, eval'd with {player_relation, turn_count}
                    e.g. "player_relation < 0.15"

2. intention_keywords — list[str] substrings matched against the
                        scenario-defined intention_shift for the chosen action.
                        e.g. ["Accept Player", "Accept Graduated"]

3. min_relation   — float hard floor; skipped if player_relation < value

Examples
--------
Hard condition gate:
    { "condition": "player_relation < 0.15", "target": "fail" }

Intention + relation gate:
    { "intention_keywords": ["Accept Player"], "min_relation": 0.5, "target": "succeed" }

Anti-softlock (condition only):
    { "condition": "turn_count >= 6", "target": "negotiate" }

Combined:
    { "condition": "turn_count <= 8", "intention_keywords": ["Transactional"], "target": "negotiate" }

Transitions are evaluated in order; first match wins.
Returns None if nothing matches (caller uses node's default_transition).
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .session import NPCConversationState


class TransitionResolver:
    """
    Evaluates a node's transition list against live NPC state to determine
    which node to route to next.
    """

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @staticmethod
    def resolve(
        transitions: List[Dict[str, Any]],
        npc_state: "NPCConversationState",
        intention_shift: Optional[str] = None,
    ) -> Optional[str]:
        """
        Walk the transition list and return the first matching target node_id.

        Parameters
        ----------
        transitions     : transition list from the current scenario node
        npc_state       : live NPC state (for relation + turn_count)
        intention_shift : the intention_shift string from the chosen interaction
                          outcome (scenario-defined, authoritative for FSM routing)

        Returns None if no transition matches (caller uses default_transition).
        """
        player_relation = npc_state.npc.world.player_relation
        turn_count = npc_state.turn_count
        eval_ctx = {"player_relation": player_relation, "turn_count": turn_count}

        for transition in transitions:
            if TransitionResolver._transition_matches(
                transition, eval_ctx, player_relation, intention_shift
            ):
                return transition["target"]

        return None

    @staticmethod
    def is_terminal(node: Dict[str, Any]) -> bool:
        """Check if a node is terminal (ends the conversation)."""
        return node.get("terminal", False)

    # ------------------------------------------------------------------ #
    # Private: transition evaluation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _transition_matches(
        transition: Dict[str, Any],
        eval_ctx: Dict[str, Any],
        player_relation: float,
        intention_shift: Optional[str],
    ) -> bool:
        """
        Returns True only when ALL guards present in this transition pass.

        Supported gate keys: "condition", "intention_keywords", "min_relation".
        Unknown keys (e.g. "_comment") are silently ignored.
        """
        # Guard 1: optional condition expression
        condition_str = transition.get("condition")
        if condition_str:
            try:
                result = eval(condition_str, {"__builtins__": {}}, eval_ctx)  # noqa: S307
                if not result:
                    return False
            except Exception as e:
                print(f"  [TransitionResolver] condition eval failed '{condition_str}': {e}")
                return False

        # Guard 2: optional intention_keywords match
        keywords: List[str] = transition.get("intention_keywords", [])
        if keywords:
            if not intention_shift:
                return False  # keywords required but no shift available
            shift_lower = intention_shift.lower()
            if not any(kw.lower() in shift_lower for kw in keywords):
                return False

        # Guard 3: optional min_relation floor
        min_rel = transition.get("min_relation")
        if min_rel is not None:
            if player_relation < float(min_rel):
                return False

        return True

    # ------------------------------------------------------------------ #
    # Private: NPC state extraction (kept for choice_filter compatibility)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _last_intention(npc_state: "NPCConversationState") -> Optional[str]:
        """Return the most recent intention_type from NPC conversation history.
        Used by choice_filter, not by transition resolution."""
        for entry in reversed(npc_state.history):
            meta = entry.get("metadata")
            if meta:
                intention = meta.get("intention")
                if intention:
                    return intention.get("intention_type")
        return None
