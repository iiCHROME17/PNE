"""
Transition Resolver Module

Handles dynamic routing between conversation nodes based on NPC state.

Supports TWO transition styles (combinable):

1. Simple condition:
   { "condition": "player_relation > 0.5", "target": "succeed" }

2. Outcome-match (confidence-based):
   {
     "outcome_match": {
       "intention_keywords": ["Accept Player", "Seek Connection"],
       "relation_target": 0.7,
       "relation_tolerance": 0.2,
       "desire_types": ["affiliation"],          # optional +0.10 bonus
       "min_desire_intensity": 0.4               # optional hard gate
     },
     "min_confidence": 0.6,
     "condition": "turn_count <= 6",             # optional extra guard
     "target": "succeed"
   }

Both can appear in the same transition — both must pass.
Transitions evaluated in order; first match wins.

Confidence formula
------------------
  keyword_score  = 1.0 if any intention_keyword found in last intention_type
  relation_score = 1 - clamp(|player_relation - relation_target| / tolerance)
  confidence     = 0.6 * keyword_score + 0.4 * relation_score
  + 0.10 bonus if desire_types matches last desire_type (capped at 1.0)

intention_keywords match against canonical INTENTION_REGISTRY names, e.g.:
  "Accept Player for Trial", "Challenge to Reveal Truth", "Seek Connection"
Substring matching is used so "Accept Player" matches "Accept Player for Trial".
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
    ) -> Optional[str]:
        """
        Walk the transition list and return the first matching target node_id.
        Returns None if no transition matches (caller uses default_transition).
        """
        player_relation = npc_state.npc.world.player_relation
        turn_count = npc_state.turn_count

        last_intention = TransitionResolver._last_intention(npc_state)
        last_desire_type, last_desire_intensity = TransitionResolver._last_desire(npc_state)

        eval_ctx = {"player_relation": player_relation, "turn_count": turn_count}

        for transition in transitions:
            if TransitionResolver._transition_matches(
                transition,
                eval_ctx,
                player_relation,
                last_intention,
                last_desire_type,
                last_desire_intensity,
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
        last_intention: Optional[str],
        last_desire_type: Optional[str],
        last_desire_intensity: Optional[float],
    ) -> bool:
        """
        Returns True only when ALL guards present in this transition pass.
        Guard keys: "condition" and/or "outcome_match".
        Unknown keys (e.g. "_comment") are silently ignored.
        """
        # Guard 1: optional simple condition expression
        condition_str = transition.get("condition")
        if condition_str:
            try:
                result = eval(condition_str, {"__builtins__": {}}, eval_ctx)  # noqa: S307
                if not result:
                    return False
            except Exception as e:
                print(f"  [TransitionResolver] condition eval failed '{condition_str}': {e}")
                return False

        # Guard 2: optional outcome_match confidence block
        outcome_match = transition.get("outcome_match")
        if outcome_match:
            confidence = TransitionResolver._compute_confidence(
                outcome_match,
                player_relation,
                last_intention,
                last_desire_type,
                last_desire_intensity,
            )
            min_conf = float(transition.get("min_confidence", 0.5))
            if confidence < min_conf:
                return False

        return True

    # ------------------------------------------------------------------ #
    # Private: confidence scoring
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_confidence(
        outcome_match: Dict[str, Any],
        player_relation: float,
        last_intention: Optional[str],
        last_desire_type: Optional[str] = None,
        last_desire_intensity: Optional[float] = None,
    ) -> float:
        """
        Score how well the NPC's current state matches this outcome_match spec.

        Supported outcome_match fields
        ----------------------------------
        intention_keywords   list[str]   substrings of canonical intention names
        relation_target      float       ideal player_relation
        relation_tolerance   float       acceptable deviation (default 0.25)
        desire_types         list[str]   substrings of desire_type for +0.10 bonus
        min_desire_intensity float       hard gate — 0.0 returned if not met

        Unknown fields are silently ignored.
        """
        # Hard gate: desire intensity
        min_intensity = outcome_match.get("min_desire_intensity")
        if min_intensity is not None:
            if last_desire_intensity is None or last_desire_intensity < min_intensity:
                return 0.0

        # Keyword score (0-1)
        keyword_score = 0.0
        keywords: List[str] = outcome_match.get("intention_keywords", [])
        if keywords:
            if last_intention:
                intention_lower = last_intention.lower()
                for kw in keywords:
                    if kw.lower() in intention_lower:
                        keyword_score = 1.0
                        break
            # keyword_score stays 0 if no last_intention and keywords required
        else:
            keyword_score = 1.0  # No keywords specified -> full score

        # Relation score (0-1)
        relation_score = 1.0
        relation_target = outcome_match.get("relation_target")
        if relation_target is not None:
            tolerance = float(outcome_match.get("relation_tolerance", 0.25))
            distance = abs(player_relation - float(relation_target))
            relation_score = max(0.0, 1.0 - distance / max(tolerance, 0.01))

        confidence = 0.6 * keyword_score + 0.4 * relation_score

        # Desire-type bonus (+0.10 if match, capped at 1.0)
        desire_types: List[str] = outcome_match.get("desire_types", [])
        if desire_types and last_desire_type:
            desire_lower = last_desire_type.lower()
            if any(dt.lower() in desire_lower for dt in desire_types):
                confidence = min(1.0, confidence + 0.10)

        return confidence

    # ------------------------------------------------------------------ #
    # Private: NPC state extraction
    # ------------------------------------------------------------------ #

    @staticmethod
    def _last_intention(npc_state: "NPCConversationState") -> Optional[str]:
        """Return the most recent intention_type from NPC conversation history."""
        for entry in reversed(npc_state.history):
            meta = entry.get("metadata")
            if meta:
                intention = meta.get("intention")
                if intention:
                    return intention.get("intention_type")
        return None

    @staticmethod
    def _last_desire(
        npc_state: "NPCConversationState",
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Return (desire_type, intensity) from the most recent NPC history entry
        that has desire metadata.  Returns (None, None) if not found.
        """
        for entry in reversed(npc_state.history):
            meta = entry.get("metadata")
            if meta:
                desire = meta.get("desire")
                if desire:
                    return desire.get("desire_type"), desire.get("intensity")
        return None, None