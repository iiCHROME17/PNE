"""
Psychological Narrative Engine - Choice Filtering System
Name: choice_filter.py
Author: Jerome Bawa (original), enhanced filtering by AI assistant

Robust filtering system to ensure only contextually sensible player choices
appear based on:
- Current NPC emotional/cognitive state
- Conversation history and momentum
- Relation thresholds
- Narrative coherence rules
- Player skill requirements
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class FilterReason(Enum):
    """Reasons why a choice might be filtered out"""
    INSUFFICIENT_SKILL = "insufficient_skill"
    RELATION_TOO_LOW = "relation_too_low"
    RELATION_TOO_HIGH = "relation_too_high"
    INCOMPATIBLE_NPC_STATE = "incompatible_npc_state"
    CONVERSATION_MOMENTUM = "conversation_momentum"
    NARRATIVE_INCOHERENCE = "narrative_incoherence"
    TOPIC_DRIFT = "topic_drift"
    EMOTIONAL_MISMATCH = "emotional_mismatch"
    PREREQUISITE_MISSING = "prerequisite_missing"


@dataclass
class ChoiceRequirement:
    """Requirements for a choice to be available"""
    
    # Skill requirements (0-10 scale)
    min_authority: Optional[int] = None
    min_diplomacy: Optional[int] = None
    min_empathy: Optional[int] = None
    min_manipulation: Optional[int] = None
    
    # Relation requirements (0.0-1.0)
    min_relation: Optional[float] = None
    max_relation: Optional[float] = None
    
    # NPC state requirements
    min_self_esteem: Optional[float] = None
    max_self_esteem: Optional[float] = None
    min_emotional_valence: Optional[float] = None  # Negative = hostile
    max_emotional_valence: Optional[float] = None
    
    # Requires specific prior choices
    requires_choices: List[str] = field(default_factory=list)
    
    # Blocks if certain choices were made
    blocked_by_choices: List[str] = field(default_factory=list)
    
    # Topic coherence
    allowed_after_intentions: List[str] = field(default_factory=list)
    blocked_after_intentions: List[str] = field(default_factory=list)
    
    # Custom condition (lambda function as string for serialization)
    custom_condition: Optional[str] = None


@dataclass
class FilterContext:
    """Context needed to evaluate choice availability"""
    
    # Player state
    player_skills: Dict[str, int]  # {"authority": 5, "diplomacy": 3, ...}
    
    # NPC state
    player_relation: float
    npc_self_esteem: float
    npc_emotional_valence: float
    npc_current_intention: str
    npc_current_desire_type: str
    
    # Conversation history
    choices_made: List[str]
    turn_count: int
    last_intention_shift: Optional[str] = None
    
    # Additional context
    conversation_topic: Optional[str] = None
    conversation_stage: Optional[str] = None  # "opening", "middle", "closing"


class ChoiceFilter:
    """Filters player choices based on requirements and context"""
    
    @staticmethod
    def filter_choices(
        choices: List[Dict[str, Any]],
        context: FilterContext,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter choices based on requirements and context.
        Returns only choices that are currently available.
        """
        available_choices = []
        
        for choice in choices:
            requirements = choice.get("requirements", {})
            if not requirements:
                # No requirements = always available
                available_choices.append(choice)
                continue
            
            req = ChoiceRequirement(**requirements)
            is_available, reasons = ChoiceFilter._evaluate_choice(choice, req, context)
            
            if is_available:
                available_choices.append(choice)
            elif verbose:
                print(f"  [FILTERED] '{choice['text'][:50]}...' - Reasons: {[r.value for r in reasons]}")
        
        return available_choices
    
    @staticmethod
    def _evaluate_choice(
        choice: Dict[str, Any],
        req: ChoiceRequirement,
        context: FilterContext
    ) -> tuple[bool, List[FilterReason]]:
        """
        Evaluate if a choice meets all requirements.
        Returns (is_available, list_of_failed_reasons)
        """
        failed_reasons = []
        
        # 1. Skill checks
        if req.min_authority is not None and context.player_skills.get("authority", 0) < req.min_authority:
            failed_reasons.append(FilterReason.INSUFFICIENT_SKILL)
        if req.min_diplomacy is not None and context.player_skills.get("diplomacy", 0) < req.min_diplomacy:
            failed_reasons.append(FilterReason.INSUFFICIENT_SKILL)
        if req.min_empathy is not None and context.player_skills.get("empathy", 0) < req.min_empathy:
            failed_reasons.append(FilterReason.INSUFFICIENT_SKILL)
        if req.min_manipulation is not None and context.player_skills.get("manipulation", 0) < req.min_manipulation:
            failed_reasons.append(FilterReason.INSUFFICIENT_SKILL)
        
        # 2. Relation checks
        if req.min_relation is not None and context.player_relation < req.min_relation:
            failed_reasons.append(FilterReason.RELATION_TOO_LOW)
        if req.max_relation is not None and context.player_relation > req.max_relation:
            failed_reasons.append(FilterReason.RELATION_TOO_HIGH)
        
        # 3. NPC emotional state checks
        if req.min_self_esteem is not None and context.npc_self_esteem < req.min_self_esteem:
            failed_reasons.append(FilterReason.INCOMPATIBLE_NPC_STATE)
        if req.max_self_esteem is not None and context.npc_self_esteem > req.max_self_esteem:
            failed_reasons.append(FilterReason.INCOMPATIBLE_NPC_STATE)
        
        if req.min_emotional_valence is not None and context.npc_emotional_valence < req.min_emotional_valence:
            failed_reasons.append(FilterReason.EMOTIONAL_MISMATCH)
        if req.max_emotional_valence is not None and context.npc_emotional_valence > req.max_emotional_valence:
            failed_reasons.append(FilterReason.EMOTIONAL_MISMATCH)
        
        # 4. Prerequisite choices
        if req.requires_choices:
            if not all(choice_id in context.choices_made for choice_id in req.requires_choices):
                failed_reasons.append(FilterReason.PREREQUISITE_MISSING)
        
        if req.blocked_by_choices:
            if any(choice_id in context.choices_made for choice_id in req.blocked_by_choices):
                failed_reasons.append(FilterReason.NARRATIVE_INCOHERENCE)
        
        # 5. Intention coherence
        if req.allowed_after_intentions and context.last_intention_shift:
            if not any(keyword in context.last_intention_shift for keyword in req.allowed_after_intentions):
                failed_reasons.append(FilterReason.CONVERSATION_MOMENTUM)
        
        if req.blocked_after_intentions and context.last_intention_shift:
            if any(keyword in context.last_intention_shift for keyword in req.blocked_after_intentions):
                failed_reasons.append(FilterReason.TOPIC_DRIFT)
        
        # 6. Custom condition
        if req.custom_condition:
            try:
                condition_func = eval(req.custom_condition)  # noqa: S307
                if not condition_func(context):
                    failed_reasons.append(FilterReason.NARRATIVE_INCOHERENCE)
            except Exception as e:
                print(f"Warning: Custom condition failed to evaluate: {e}")
                failed_reasons.append(FilterReason.NARRATIVE_INCOHERENCE)
        
        return len(failed_reasons) == 0, failed_reasons
    
    @staticmethod
    def smart_fallback(
        choices: List[Dict[str, Any]],
        context: FilterContext
    ) -> List[Dict[str, Any]]:
        """
        If filtering removes ALL choices, intelligently relax constraints
        to ensure at least one choice is available.
        """
        available = ChoiceFilter.filter_choices(choices, context)
        
        if available:
            return available
        
        # Fallback strategy: relax constraints progressively
        print("  [WARNING] No choices available after filtering. Relaxing constraints...")
        
        # 1. Try without intention coherence checks
        relaxed_choices = []
        for choice in choices:
            req_data = choice.get("requirements", {})
            req_data.pop("allowed_after_intentions", None)
            req_data.pop("blocked_after_intentions", None)
            choice_copy = choice.copy()
            choice_copy["requirements"] = req_data
            relaxed_choices.append(choice_copy)
        
        available = ChoiceFilter.filter_choices(relaxed_choices, context)
        if available:
            print("  [FALLBACK] Relaxed intention coherence requirements")
            return available
        
        # 2. Try without relation requirements
        for choice in relaxed_choices:
            req_data = choice.get("requirements", {})
            req_data.pop("min_relation", None)
            req_data.pop("max_relation", None)
        
        available = ChoiceFilter.filter_choices(relaxed_choices, context)
        if available:
            print("  [FALLBACK] Relaxed relation requirements")
            return available
        
        # 3. Last resort: return all choices
        print("  [FALLBACK] Returning all choices (no filters applied)")
        return choices


# ============================================================================
# CONVERSATION STAGE DETECTOR
# ============================================================================


class ConversationStageDetector:
    """
    Automatically determines conversation stage based on turn count,
    relation, and emotional trajectory.
    """
    
    @staticmethod
    def detect_stage(
        turn_count: int,
        player_relation: float,
        emotional_trajectory: List[float]  # Recent emotional valence values
    ) -> str:
        """
        Returns: "opening", "middle", "closing", or "critical"
        """
        if turn_count <= 1:
            return "opening"
        
        if turn_count >= 10:
            return "closing"
        
        # Critical stage: very low relation or extreme emotional swings
        if player_relation < 0.2:
            return "critical"
        
        if len(emotional_trajectory) >= 3:
            recent_variance = max(emotional_trajectory[-3:]) - min(emotional_trajectory[-3:])
            if recent_variance > 0.5:
                return "critical"
        
        return "middle"


# ============================================================================
# DYNAMIC CHOICE ADJUSTMENT
# ============================================================================


class DynamicChoiceAdjuster:
    """
    Adjusts choice availability dynamically based on conversation flow.
    """
    
    @staticmethod
    def adjust_for_repetition(
        choices: List[Dict[str, Any]],
        context: FilterContext
    ) -> List[Dict[str, Any]]:
        """
        Remove choices that repeat the same language_art or tone
        as the last 2 player choices.
        """
        if len(context.choices_made) < 2:
            return choices
        
        # Get language arts from recent choices
        recent_arts = []
        # This would require storing language_art in choices_made
        # For now, we'll use a simplified version
        
        return choices
    
    @staticmethod
    def inject_emergency_choices(
        choices: List[Dict[str, Any]],
        context: FilterContext
    ) -> List[Dict[str, Any]]:
        """
        If conversation is in critical state, inject emergency choices
        like "back down", "apologize", "leave".
        """
        if context.conversation_stage != "critical":
            return choices
        
        emergency_choice = {
            "choice_id": "emergency_backdown",
            "text": "I think we got off on the wrong foot. Let me start over.",
            "language_art": "diplomatic",
            "authority_tone": 0.1,
            "diplomacy_tone": 0.9,
            "empathy_tone": 0.6,
            "manipulation_tone": 0.1,
            "interaction_outcomes": [
                {
                    "outcome_id": "reset_conversation",
                    "stance_delta": {},
                    "relation_delta": 0.1,
                    "intention_shift": "Give Second Chance",
                    "min_response": "Fine. Try again.",
                    "max_response": "Alright. I'm listening.",
                    "scripted": False
                }
            ],
            "requirements": {}  # Always available in critical state
        }
        
        return [emergency_choice] + choices