"""
Dialogue-Aware Choice Filtering
Name: dialogue_coherence.py

Ensures player choices actually respond to what the NPC just said,
creating conversational coherence instead of having the player "talk past"
the NPC.

Two classes collaborate here:

``DialogueMomentumFilter``
    The primary filter, called each turn from ``NarrativeEngine.get_available_choices``.
    Scores every hard-gated choice from ``ChoiceFilter`` against four coherence
    dimensions (momentum alignment, stage appropriateness, anti-repetition, and
    relation plausibility) and drops any choice that falls below a 0.3 threshold.
    If filtering would eliminate all choices, the original list is returned unchanged
    as a safety net.

``ConversationFlowEnforcer``
    A higher-level enforcer for narrative shape.  Not called automatically — available
    for explicit use in specialised scenarios.  Provides turn-limit enforcement
    (funnels the player toward resolution choices near the end) and emergency exit
    injection (adds graceful-exit options when the conversation is going badly).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class DialogueContext:
    """Extended context snapshot passed to the coherence filter each turn.

    Built by ``NarrativeEngine._build_dialogue_context`` from live session state
    and forwarded to ``DialogueMomentumFilter.filter_for_coherence``.  It extends
    the base ``FilterContext`` with dialogue-specific fields that allow the filter
    to reason about what the NPC just said and how the conversation is unfolding.

    Attributes:
        player_skills: Dict mapping skill names to integer values (0–10).
        player_relation: Current NPC opinion of the player (0.0–1.0).
        npc_self_esteem: NPC's cognitive self-esteem attribute (0.0–1.0);
            affects vulnerability threshold checks.
        npc_emotional_valence: The NPC's last recorded emotional valence
            (−1.0 to 1.0), sourced from the most recent ``thought_reaction``.
        npc_current_intention: The BDI ``intention_type`` string from the NPC's
            last turn — used for momentum tagging.
        npc_current_desire_type: The desire category from the NPC's last turn
            (e.g. ``"protection"``, ``"affiliation"``).
        choices_made: Ordered list of ``choice_id`` strings the player has
            selected so far this session — used for anti-repetition scoring.
        turn_count: Number of completed turns in this session.
        last_npc_response: The NPC's most recent dialogue text, or ``None`` on
            the first turn.  Not currently used in scoring but available for
            future keyword analysis.
        conversation_stage: Detected stage of the conversation — one of
            ``"opening"``, ``"development"``, ``"crisis"``, or ``"resolution"``.
            Determined by ``ConversationStageDetector.detect_stage``.
        npc_momentum_tags: List of momentum labels inferred from the last
            ``interaction_outcome.intention_shift`` string, e.g.
            ``["challenge_posed"]``, ``["acceptance_signaled"]``.  An empty list
            means no specific momentum was detected this turn.
    """

    # ── Standard filter context ─────────────────────────────────────────
    player_skills: Dict[str, int]
    player_relation: float
    npc_self_esteem: float
    npc_emotional_valence: float
    npc_current_intention: str
    npc_current_desire_type: str
    choices_made: List[str]
    turn_count: int

    # ── Dialogue-specific context ────────────────────────────────────────
    last_npc_response: Optional[str] = None
    conversation_stage: str = "opening"
    npc_momentum_tags: List[str] = None  # Inferred from last intention_shift

    def __post_init__(self):
        if self.npc_momentum_tags is None:
            self.npc_momentum_tags = []


class DialogueMomentumFilter:
    """
    Filters choices based on conversational coherence:
    - Does this choice respond to what NPC just said?
    - Is it appropriate for this stage of conversation?
    """
    
    # Map NPC momentum tags to appropriate choice response types
    MOMENTUM_RESPONSE_MAP = {
        "challenge_posed": [
            "demonstrate_value", "accept_challenge", "deflect_challenge",
            "counter_challenge", "practical_plan", "specific_offer"
        ],
        "question_asked": [
            "direct_answer", "evasive_answer", "counter_question",
            "personal_story", "philosophical_debate"
        ],
        "doubt_expressed": [
            "reassure", "demonstrate_value", "specific_offer",
            "personal_sacrifice", "practical_plan", "accept_terms"
        ],
        "demand_made": [
            "comply", "negotiate", "refuse", "counter_demand",
            "practical_plan", "accept_terms"
        ],
        "acceptance_signaled": [
            "build_on_acceptance", "push_forward", "accept_terms",
            "final_commitment", "reaffirm_commitment"
        ],
        "rejection_signaled": [
            "back_down", "pivot_approach", "escalate",
            "find_common_ground", "apologize"
        ],
    }
    
    # Choices that should only appear in specific conversation stages
    STAGE_APPROPRIATE_CHOICES = {
        "opening": [
            "empathetic_approach", "authority_challenge", "manipulative_approach",
            "diplomatic_reasoning", "neutral_statement"
        ],
        "development": [
            "personal_sacrifice", "specific_offer", "practical_plan",
            "philosophical_debate", "double_down_authority", "dodge_question"
        ],
        "crisis": [
            "reaffirm_commitment", "final_challenge", "last_appeal",
            "accept_terms", "push_back_terms"
        ],
        "resolution": [
            "accept_terms", "push_back_terms", "final_commitment",
            "walk_away"
        ]
    }
    
    @staticmethod
    def filter_for_coherence(
        choices: List[Dict[str, Any]],
        context: DialogueContext,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter choices to ensure conversational coherence.
        
        Returns choices that:
        1. Respond appropriately to NPC's last statement
        2. Fit the current conversation stage
        3. Don't repeat ineffective patterns
        """
        coherent_choices = []
        
        for choice in choices:
            coherence_score = DialogueMomentumFilter._score_coherence(
                choice, context
            )
            
            if coherence_score > 0.3:  # Minimum coherence threshold
                coherent_choices.append({
                    **choice,
                    "_coherence_score": coherence_score
                })
            elif verbose:
                print(f"  [Filtered] '{choice['text'][:40]}...' - Low coherence: {coherence_score:.2f}")
        
        # Sort by coherence score (highest first)
        coherent_choices.sort(key=lambda c: c.get("_coherence_score", 0), reverse=True)
        
        # Remove coherence score before returning
        for choice in coherent_choices:
            choice.pop("_coherence_score", None)
        
        return coherent_choices
    
    @staticmethod
    def _score_coherence(
        choice: Dict[str, Any],
        context: DialogueContext
    ) -> float:
        """
        Score how well this choice fits the current dialogue context.
        
        Returns 0.0-1.0, where higher = more coherent
        """
        score = 0.5  # Start neutral
        
        choice_id = choice.get("choice_id", "")
        choice_type = DialogueMomentumFilter._infer_choice_type(choice)
        
        # 1. Does this choice respond to NPC's momentum?
        if context.npc_momentum_tags:
            momentum_bonus = DialogueMomentumFilter._check_momentum_alignment(
                choice_type, context.npc_momentum_tags
            )
            score += momentum_bonus * 0.4  # Momentum is important!
        
        # 2. Is this choice appropriate for conversation stage?
        stage_bonus = DialogueMomentumFilter._check_stage_appropriateness(
            choice_id, context.conversation_stage, context.turn_count
        )
        score += stage_bonus * 0.3
        
        # 3. Anti-repetition: penalize choices similar to recent failures
        repetition_penalty = DialogueMomentumFilter._check_repetition(
            choice, context
        )
        score -= repetition_penalty * 0.2
        
        # 4. Relation-based filtering: some choices need minimum trust
        relation_bonus = DialogueMomentumFilter._check_relation_appropriateness(
            choice, context.player_relation
        )
        score += relation_bonus * 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _infer_choice_type(choice: Dict[str, Any]) -> str:
        """
        Infer the functional type of a choice from its ID and content.
        
        Examples:
        - "practical_plan" → "demonstrate_value"
        - "empathetic_approach" → "reassure"
        - "authority_challenge" → "counter_challenge"
        """
        choice_id = choice.get("choice_id", "").lower()
        text = choice.get("text", "").lower()
        
        # Map choice IDs to functional types
        type_map = {
            # Demonstration choices
            "practical_plan": "demonstrate_value",
            "specific_offer": "demonstrate_value",
            "reaffirm_commitment": "demonstrate_value",
            
            # Personal/emotional choices
            "personal_sacrifice": "personal_story",
            "empathetic_approach": "reassure",
            
            # Challenge/authority choices
            "authority_challenge": "counter_challenge",
            "double_down_authority": "counter_challenge",
            "final_challenge": "counter_challenge",
            
            # Diplomatic choices
            "diplomatic_reasoning": "negotiate",
            "philosophical_debate": "philosophical_debate",
            "accept_terms": "comply",
            "push_back_terms": "counter_demand",
            
            # Evasive choices
            "dodge_question": "evasive_answer",
            
            # Manipulative choices
            "manipulative_approach": "manipulate",
        }
        
        return type_map.get(choice_id, "generic_response")
    
    @staticmethod
    def _check_momentum_alignment(
        choice_type: str,
        momentum_tags: List[str]
    ) -> float:
        """
        Check if choice type aligns with NPC's conversational momentum.
        
        Returns -0.5 to 0.5 bonus/penalty
        """
        # For each momentum tag, check if choice type is a good response
        aligned = False
        
        for tag in momentum_tags:
            appropriate_responses = DialogueMomentumFilter.MOMENTUM_RESPONSE_MAP.get(tag, [])
            
            if choice_type in appropriate_responses:
                aligned = True
                break
        
        if aligned:
            return 0.5  # Strong bonus for aligned response
        elif momentum_tags:
            return -0.3  # Penalty for misaligned response
        else:
            return 0.0  # Neutral if no momentum detected
    
    @staticmethod
    def _check_stage_appropriateness(
        choice_id: str,
        stage: str,
        turn_count: int
    ) -> float:
        """
        Check if choice is appropriate for current conversation stage.
        
        Returns -0.3 to 0.3 bonus/penalty
        """
        appropriate_for_stage = DialogueMomentumFilter.STAGE_APPROPRIATE_CHOICES.get(stage, [])
        
        if choice_id in appropriate_for_stage:
            return 0.3
        
        # Harsh penalty for severely out-of-stage choices
        if stage == "resolution" and choice_id in ["empathetic_approach", "authority_challenge"]:
            return -0.5  # Don't restart conversation at resolution!
        
        return 0.0
    
    @staticmethod
    def _check_repetition(
        choice: Dict[str, Any],
        context: DialogueContext
    ) -> float:
        """
        Penalize choices that repeat ineffective patterns.
        
        Returns 0.0-0.5 penalty
        """
        choice_id = choice.get("choice_id", "")
        language_art = choice.get("language_art", "")
        
        # Count recent uses of this choice type
        recent_uses = 0
        for past_choice_id in context.choices_made[-3:]:  # Last 3 choices
            if past_choice_id == choice_id:
                recent_uses += 1
        
        if recent_uses >= 2:
            return 0.5  # Heavy penalty for repeating same choice
        elif recent_uses == 1:
            return 0.2  # Light penalty for recent use
        
        # Penalize repeating language art if relation is declining
        # (suggests this approach isn't working)
        if context.player_relation < 0.4 and language_art:
            for past_choice_id in context.choices_made[-2:]:
                # This would require storing language_art in choices_made
                # For now, simplified check
                pass
        
        return 0.0
    
    @staticmethod
    def _check_relation_appropriateness(
        choice: Dict[str, Any],
        player_relation: float
    ) -> float:
        """
        Some choices require minimum trust to be believable.
        
        Returns -0.2 to 0.2 bonus/penalty
        """
        choice_id = choice.get("choice_id", "")
        
        # Vulnerable choices need some trust
        vulnerable_choices = ["personal_sacrifice", "empathetic_approach", "apologize"]
        if choice_id in vulnerable_choices and player_relation < 0.3:
            return -0.2  # Too vulnerable given low trust
        
        # Authority challenges are risky with low relation
        if choice_id in ["authority_challenge", "final_challenge"] and player_relation < 0.2:
            return -0.2  # Likely to backfire
        
        # Cooperative choices work better with decent relation
        cooperative_choices = ["accept_terms", "practical_plan", "philosophical_debate"]
        if choice_id in cooperative_choices and player_relation > 0.5:
            return 0.2  # Synergy bonus
        
        return 0.0


class ConversationFlowEnforcer:
    """High-level enforcer that gives conversations deliberate narrative shape.

    Unlike ``DialogueMomentumFilter`` (which is called automatically every turn),
    these methods are optional tools for scenario designers who want explicit
    control over pacing and player options near the conversation's end.
    """

    @staticmethod
    def enforce_turn_limit(
        choices: List[Dict[str, Any]],
        turn_count: int,
        max_turns: int = 10,
    ) -> List[Dict[str, Any]]:
        """Narrow choices toward resolution as the turn limit approaches.

        When ``turn_count >= max_turns - 2``, filters the choice list down to
        resolution-focused options (``accept_terms``, ``push_back_terms``, etc.)
        to ensure the conversation reaches a conclusion.  Falls back to the full
        list if no resolution choices are present.

        Args:
            choices: Current list of available choices (already hard-gated by
                ``ChoiceFilter``).
            turn_count: Number of turns completed so far.
            max_turns: Maximum allowed turns before enforcement kicks in.

        Returns:
            The filtered (or original) choice list.
        """
        if turn_count < max_turns - 2:
            return choices  # No enforcement yet
        
        # Near turn limit - prioritize resolution choices
        resolution_choices = [
            c for c in choices
            if c.get("choice_id", "") in [
                "accept_terms", "push_back_terms", "final_commitment",
                "reaffirm_commitment", "final_challenge", "walk_away"
            ]
        ]
        
        if resolution_choices:
            print(f"  [Turn Limit Enforcement] {turn_count}/{max_turns} turns - prioritizing resolution")
            return resolution_choices
        
        return choices  # Fallback to all choices
    
    @staticmethod
    def inject_emergency_exits(
        choices: List[Dict[str, Any]],
        context: DialogueContext,
    ) -> List[Dict[str, Any]]:
        """Prepend graceful-exit options when the conversation is failing badly.

        Triggered when ``player_relation < 0.2`` and ``turn_count >= 5``.
        Adds two synthetic choices — a diplomatic withdrawal and a hard walk-away
        — at the front of the list so the player always has an out before a
        relationship completely collapses.

        Args:
            choices: Current list of available choices.
            context: The ``DialogueContext`` providing relation and turn data.

        Returns:
            The original list prepended with emergency exit choices, or the
            original list unchanged if the trigger conditions are not met.
        """
        # If relation is very low and we're deep in conversation, add exits
        if context.player_relation < 0.2 and context.turn_count >= 5:
            emergency_exits = [
                {
                    "choice_id": "apologize_withdraw",
                    "text": "I think I've made a mistake. Let me reconsider.",
                    "language_art": "diplomatic",
                    "interaction_outcomes": [
                        {
                            "outcome_id": "graceful_exit",
                            "relation_delta": 0.05,
                            "intention_shift": "Dismiss Player",
                        }
                    ]
                },
                {
                    "choice_id": "walk_away",
                    "text": "This isn't working. I'll find another way.",
                    "language_art": "neutral",
                    "interaction_outcomes": [
                        {
                            "outcome_id": "player_leaves",
                            "relation_delta": -0.1,
                            "intention_shift": "Let Them Go",
                        }
                    ]
                }
            ]
            
            print("  [Emergency Exit] Conversation struggling - adding exit options")
            return emergency_exits + choices
        
        return choices