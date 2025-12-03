"""
Psychological Narrative Engine - Dialogue Pipeline (Refactored)
Name: pipeline.py
Author: Jerome Bawa 

Implements Purpose-Output Model with Conversation Containment,
Interaction Outcomes, and Terminal Outcomes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import json
import random
import requests

# ============================================================================
# ENUMS
# ============================================================================

class LanguageArt(Enum):
    """Player Dialogue Approaches (Rhetoric)"""
    CHALLENGE = "challenge"
    DIPLOMATIC = "diplomatic"
    EMPATHETIC = "empathetic"
    MANIPULATIVE = "manipulative"
    NEUTRAL = "neutral"


class PlayerSkill(Enum):
    """Player's skill proficiencies"""
    AUTHORITY = "authority"
    DIPLOMACY = "diplomacy"
    EMPATHY = "empathy"
    MANIPULATION = "manipulation"


class TerminalOutcomeType(Enum):
    """Terminal outcome types"""
    SUCCEED = "succeed"
    FAIL = "fail"
    NEGOTIATE = "negotiate"
    DELAY = "delay"
    ESCALATE = "escalate"


# ============================================================================
# CONVERSATION CONTAINMENT MODEL
# ============================================================================

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


# ============================================================================
# NPC INTENT LAYER (Purpose/Meta Layer)
# ============================================================================

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


# ============================================================================
# PLAYER INPUT STRUCTURES
# ============================================================================

@dataclass
class PlayerDialogueInput:
    """Structured Player dialogue"""
    choice_text: str
    language_art: LanguageArt
    contextual_references: List[str] = field(default_factory=list)
    
    # Parsed traits from choice text
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    ideology_alignment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_text": self.choice_text,
            "language_art": self.language_art.value,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "ideology_alignment": self.ideology_alignment,
            "contextual_references": self.contextual_references
        }


@dataclass
class PlayerSkillSet:
    """Player's skill proficiencies (0-10 scale)"""
    authority: int = 0
    diplomacy: int = 0
    empathy: int = 0
    manipulation: int = 0

    def __post_init__(self):
        for attr in ["authority", "diplomacy", "empathy", "manipulation"]:
            value = getattr(self, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} skill must be between 0 and 10, got {value}")
            
    def get_skill(self, skill: PlayerSkill) -> int:
        skill_map = {
            PlayerSkill.AUTHORITY: self.authority,
            PlayerSkill.DIPLOMACY: self.diplomacy,
            PlayerSkill.EMPATHY: self.empathy,
            PlayerSkill.MANIPULATION: self.manipulation
        }
        return skill_map[skill]
    
    def get_skill_normalized(self, skill: PlayerSkill) -> float:
        return self.get_skill(skill) / 10.0


# ============================================================================
# SKILL CHECK SYSTEM (Preserved from original)
# ============================================================================

@dataclass
class SkillCheckResult:
    """Result of a skill check"""
    success: bool
    skill_used: PlayerSkill
    player_val: int
    threshold: float
    margin: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_used": self.skill_used.value,
            "player_val": self.player_val,
            "threshold": self.threshold,
            "margin": self.margin
        }


class SkillCheckSystem:
    """Handles skill checks based on player input"""
    
    LANGUAGE_ART_TO_SKILL = {
        LanguageArt.CHALLENGE: PlayerSkill.AUTHORITY,
        LanguageArt.DIPLOMATIC: PlayerSkill.DIPLOMACY,
        LanguageArt.EMPATHETIC: PlayerSkill.EMPATHY,
        LanguageArt.MANIPULATIVE: PlayerSkill.MANIPULATION,
        LanguageArt.NEUTRAL: None
    }

    SKILL_MODIFIERS = {
        PlayerSkill.AUTHORITY: [
            ('social.assertion', lambda npc, margin: npc.social.assertion * (1 - margin * 0.5))
        ],
        PlayerSkill.MANIPULATION: [
            ('cognitive.self_esteem', lambda npc, margin: npc.cognitive.self_esteem * (1 - margin * 0.5))
        ],
        PlayerSkill.DIPLOMACY: [
            ('cognitive.cog_flexibility', lambda npc, margin: min(1.0, npc.cognitive.cog_flexibility * (1 + margin * 0.5)))
        ],
        PlayerSkill.EMPATHY: [
            ('social.empathy', lambda npc, margin: min(1.0, npc.social.empathy * (1 + margin * 0.5)))
        ]
    }

    @staticmethod
    def calc_threshold(npc, skill: PlayerSkill) -> float:
        if skill == PlayerSkill.AUTHORITY:
            return 0.3 + (npc.social.assertion * 0.4)
        elif skill == PlayerSkill.MANIPULATION:
            return 0.2 + (npc.cognitive.self_esteem * 0.5)
        elif skill == PlayerSkill.EMPATHY:
            return 0.4 - (npc.social.empathy * 0.2)
        elif skill == PlayerSkill.DIPLOMACY:
            return 0.3 - (npc.cognitive.cog_flexibility * 0.3)
        return 0.5

    @staticmethod
    def perform_check(
        player_input: PlayerDialogueInput,
        player_skills: PlayerSkillSet,
        npc
    ) -> Optional[SkillCheckResult]:
        skill = SkillCheckSystem.LANGUAGE_ART_TO_SKILL.get(player_input.language_art)
        if skill is None:
            return None
        
        player_val = player_skills.get_skill(skill)
        threshold = SkillCheckSystem.calc_threshold(npc, skill)
        roll = random.uniform(-0.1, 0.1)
        eff_val = (player_val / 10.0) + roll
        success = eff_val >= threshold
        margin = eff_val - threshold

        return SkillCheckResult(
            success=success,
            skill_used=skill,
            player_val=player_val,
            threshold=threshold,
            margin=margin
        )

    @staticmethod
    def apply_modifiers(npc, check_result: SkillCheckResult):
        if not check_result.success:
            return
        
        modifiers = SkillCheckSystem.SKILL_MODIFIERS.get(check_result.skill_used, [])
        for attr_path, mod_func in modifiers:
            new_value = mod_func(npc, abs(check_result.margin))
            npc.apply_temp_mod(attr_path, new_value)


# ============================================================================
# COGNITIVE INTERPRETATION (Stage III)
# ============================================================================

@dataclass
class ThoughtReaction:
    """NPC's internal subjective thought (not spoken)"""
    internal_thought: str  # What NPC thinks privately
    cognitive_state: Dict[str, float]  # Updated cognitive attributes
    emotional_valence: float  # -1 (negative) to 1 (positive)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'internal_thought': self.internal_thought,
            'cognitive_state': self.cognitive_state,
            'emotional_valence': self.emotional_valence
        }


class CognitiveInterpreter:
    """Processes input through NPC's cognitive model"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """Initialize cognitive interpreter with LLM connection"""
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
    
    def interpret(self, player_input: PlayerDialogueInput, npc) -> ThoughtReaction:
        """
        Generate subjective thought using LLM based on cognitive distortions
        """
        # Generate internal thought via LLM
        internal_thought = self._generate_subjective_thought(player_input, npc)
        
        # Calculate emotional valence from tone analysis
        emotional_valence = self._calculate_emotional_valence(player_input, npc)
        
        cognitive_state = {
            'self_esteem': npc.cognitive.self_esteem,
            'locus_of_control': npc.cognitive.locus_of_control,
            'cog_flexibility': npc.cognitive.cog_flexibility
        }
        
        return ThoughtReaction(
            internal_thought=internal_thought,
            cognitive_state=cognitive_state,
            emotional_valence=emotional_valence
        )
    
    def _generate_subjective_thought(self, player_input: PlayerDialogueInput, npc) -> str:
        """Generate NPC's private interpretation of player's words using LLM"""
        
        prompt = self._build_thought_prompt(player_input, npc)
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 30  # Keep thoughts brief
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                thought = result.get("response", "").strip()
                # Truncate to 75 chars max
                if len(thought) > 75:
                    thought = thought[:72] + "..."
                return thought if thought else "I need to think about this..."
            else:
                return "I need to process what they said..."
        
        except Exception as e:
            print(f"[Cognitive Interpreter Error: {str(e)}]")
            return "What are they really saying...?"
    
    def _build_thought_prompt(self, player_input: PlayerDialogueInput, npc) -> str:
        """Build prompt for generating subjective thought"""
        
        prompt_parts = []
        prompt_parts.append("Generate ONLY the NPC's private internal thought (max 75 characters). This is what they THINK, not what they SAY.MAKE IT FIRST PERSON, FOCAL ON THEIR IMMEDIATE EMOTIONAL REACTION.\n")
        
        prompt_parts.append(f"NPC Cognitive State:")
        prompt_parts.append(f"- Self-Esteem: {npc.cognitive.self_esteem:.2f} (low=insecure, high=confident)")
        prompt_parts.append(f"- Locus of Control: {npc.cognitive.locus_of_control:.2f} (low=blames others, high=self-responsible)")
        prompt_parts.append(f"- Cognitive Flexibility: {npc.cognitive.cog_flexibility:.2f} (low=rigid, high=open-minded)")
        
        prompt_parts.append(f"\nPlayer said: \"{player_input.choice_text}\"")
        prompt_parts.append(f"Rhetoric style: {player_input.language_art.value}")
        
        # Cognitive distortion hints
        if npc.cognitive.self_esteem < 0.4:
            prompt_parts.append("\nNPC has LOW self-esteem: likely to interpret negatively, feel threatened or inadequate")
        if npc.cognitive.locus_of_control < 0.5:
            prompt_parts.append("NPC has EXTERNAL locus: likely to blame others, see player as controlling")
        if npc.cognitive.cog_flexibility < 0.4:
            prompt_parts.append("NPC is RIGID: likely to resist change, see challenge as attack")
        
        prompt_parts.append("\nGenerate NPC's private thought (under 75 chars):")
        
        return "\n".join(prompt_parts)
    
    def _calculate_emotional_valence(self, player_input: PlayerDialogueInput, npc) -> float:
        """Calculate emotional reaction based on cognitive state and input tones"""
        valence = 0.0
        
        # Low self-esteem reacts negatively to authority/manipulation
        if npc.cognitive.self_esteem < 0.4:
            valence -= (player_input.authority_tone * 0.3)
            valence -= (player_input.manipulation_tone * 0.5)
        
        # External locus attributes hostility to others
        if npc.cognitive.locus_of_control < 0.5:
            valence -= (player_input.authority_tone * 0.4)
        
        # High flexibility responds positively to diplomacy
        if npc.cognitive.cog_flexibility > 0.6:
            valence += (player_input.diplomacy_tone * 0.4)
            valence += (player_input.empathy_tone * 0.3)
        
        # Rigid thinking resists persuasion
        if npc.cognitive.cog_flexibility < 0.4:
            valence -= (player_input.diplomacy_tone * 0.2)
        
        return max(-1.0, min(1.0, valence))


# ============================================================================
# SOCIALISATION FILTER (Stage IV - Behavioural Intention)
# ============================================================================

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


# ============================================================================
# INTERACTION OUTCOME (Stage V - Micro Outcomes)
# ============================================================================

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


# ============================================================================
# TERMINAL OUTCOME (Stage VI - End State)
# ============================================================================

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


# ============================================================================
# OUTCOME INDEX
# ============================================================================

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


# ============================================================================
# OLLAMA INTEGRATION (Preserved)
# ============================================================================

class OllamaResponseGenerator:
    """Generates NPC dialogue responses using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
    
    def generate_response(
        self,
        npc,
        thought_reaction: ThoughtReaction,
        behavioural_intention: BehaviouralIntention,
        interaction_outcome: InteractionOutcome,
        conversation_history: List[str] = None
    ) -> str:
        """Generate NPC response using Ollama with full pipeline context"""
        
        prompt = self._build_prompt(
            npc, thought_reaction, behavioural_intention, 
            interaction_outcome, conversation_history
        )
        
        try:
            print(f"  → Connecting to Ollama at {self.base_url}...")
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_predict": 150
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated = result.get("response", "").strip()
                if not generated:
                    return interaction_outcome.get_response(thought_reaction.emotional_valence)
                return generated
            else:
                return interaction_outcome.get_response(thought_reaction.emotional_valence)
        
        except Exception as e:
            print(f"[Ollama Error: {str(e)}]")
            return interaction_outcome.get_response(thought_reaction.emotional_valence)
    
    def _build_prompt(
        self,
        npc,
        thought_reaction: ThoughtReaction,
        behavioural_intention: BehaviouralIntention,
        interaction_outcome: InteractionOutcome,
        conversation_history: List[str] = None
    ) -> str:
        """Build prompt with pipeline context"""
        
        prompt_parts = []
        prompt_parts.append("You are generating dialogue for an NPC. Respond only as the NPC.\n")
        
        prompt_parts.append(f"## NPC: {npc.name}")
        prompt_parts.append(f"Faction: {npc.social.faction}")
        prompt_parts.append(f"Dominant Ideology: {npc.social.get_dominant_ideology()}")
        
        prompt_parts.append(f"\n## INTERNAL STATE")
        prompt_parts.append(f"Private Thought: \"{thought_reaction.internal_thought}\"")
        prompt_parts.append(f"Intended Behavior: {behavioural_intention.intention_type}")
        prompt_parts.append(f"Confrontation Level: {behavioural_intention.confrontation_level:.2f}")
        
        prompt_parts.append(f"\n## RESPONSE GUIDANCE")
        prompt_parts.append(f"Negative variant: \"{interaction_outcome.min_response}\"")
        prompt_parts.append(f"Positive variant: \"{interaction_outcome.max_response}\"")
        prompt_parts.append(f"\nGenerate response as {npc.name} based on the above context:")
        
        return "\n".join(prompt_parts)


# ============================================================================
# DIALOGUE PROCESSOR (Refactored Pipeline)
# ============================================================================

class DialogueProcessor:
    """
    Main processor implementing Purpose-Output Model:
    Purpose → Input → Cognitive → Social → Interaction → Terminal
    """
    
    def __init__(
        self, 
        npc, 
        player_skills: PlayerSkillSet,
        npc_intent: NPCIntent,
        outcome_index: OutcomeIndex,
        conversation_id: str,
        use_ollama: bool = True,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b"
    ):
        self.npc = npc
        self.player_skills = player_skills
        self.npc_intent = npc_intent
        self.outcome_index = outcome_index
        
        # Conversation containment
        self.conversation = ConversationModel(
            conversation_id=conversation_id,
            stage="opening",
            topic=npc_intent.immediate_intention
        )
        
        # Ollama integration
        self.use_ollama = use_ollama
        if use_ollama:
            self.ollama = OllamaResponseGenerator(ollama_url, ollama_model)
            self.cognitive_interpreter = CognitiveInterpreter(ollama_url, ollama_model)
        else:
            self.ollama = None
            self.cognitive_interpreter = None
    
    def process_dialogue(
        self, 
        player_input: PlayerDialogueInput,
        generate_with_ollama: bool = True
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Purpose → Input → Cognitive → Social → Interaction → Terminal
        """
        
        # Stage I: Purpose (already set in __init__ via npc_intent)
        
        # Stage II: Input / Rhetoric Parsing (already done via player_input)
        
        # Skill Check (auxiliary)
        skill_check = SkillCheckSystem.perform_check(
            player_input, self.player_skills, self.npc
        )
        if skill_check and skill_check.success:
            SkillCheckSystem.apply_modifiers(self.npc, skill_check)
        
        # Stage III: Cognitive Interpretation
        if self.cognitive_interpreter:
            thought_reaction = self.cognitive_interpreter.interpret(player_input, self.npc)
        else:
            # Fallback if Ollama not available
            thought_reaction = ThoughtReaction(
                internal_thought="What are they really saying...?",
                cognitive_state={
                    'self_esteem': self.npc.cognitive.self_esteem,
                    'locus_of_control': self.npc.cognitive.locus_of_control,
                    'cog_flexibility': self.npc.cognitive.cog_flexibility
                },
                emotional_valence=0.0
            )
        
        # Stage IV: Socialisation Filter
        behavioural_intention = SocialisationFilter.filter(
            thought_reaction, player_input, self.npc
        )
        
        # Stage V: Interaction Outcome
        interaction_outcome = self.outcome_index.get_interaction_outcome(behavioural_intention)
        
        # Apply interaction outcome effects
        if interaction_outcome:
            # Apply stance deltas
            for attr_path, delta in interaction_outcome.stance_delta.items():
                current = self.npc.get_attribute(attr_path)
                new_val = max(0.0, min(1.0, current + delta))
                self.npc.apply_temp_mod(attr_path, new_val)
            
            # Apply relation delta
            self.npc.world.update_relation(interaction_outcome.relation_delta)
            
            # Shift intention if needed
            if interaction_outcome.intention_shift:
                self.npc_intent.shift_intention(interaction_outcome.intention_shift)
        
        # Generate NPC response
        if generate_with_ollama and self.use_ollama and self.ollama and interaction_outcome:
            npc_response = self.ollama.generate_response(
                self.npc,
                thought_reaction,
                behavioural_intention,
                interaction_outcome,
                self.conversation.history
            )
        elif interaction_outcome:
            npc_response = interaction_outcome.get_response(thought_reaction.emotional_valence)
        else:
            npc_response = "..."
        
        # Add to conversation history
        self.conversation.add_exchange(player_input.choice_text, npc_response)
        
        # Stage VI: Check Terminal Outcomes
        terminal_outcome = self.outcome_index.check_terminal_outcomes(self.npc, self.conversation)
        
        # Build response context
        response_context = {
            'conversation_id': self.conversation.conversation_id,
            'turn': self.conversation.turn_count,
            'npc_intent': self.npc_intent.to_dict(),
            'skill_check': skill_check.to_dict() if skill_check else None,
            'thought_reaction': thought_reaction.to_dict(),
            'behavioural_intention': behavioural_intention.to_dict(),
            'interaction_outcome': interaction_outcome.to_dict() if interaction_outcome else None,
            'npc_response': npc_response,
            'terminal_outcome': terminal_outcome.to_dict() if terminal_outcome else None,
            'conversation_complete': terminal_outcome is not None
        }
        
        return response_context
    
    def end_conversation(self):
        """Reset temporary modifiers after conversation ends"""
        self.npc.reset_temp_mods()
        self.conversation.history.clear()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import sys
    from PNE_Models import NPCFactory
    
    # Create NPC
    moses = NPCFactory.create_morisson_moses()
    
    # Define NPC Intent (Purpose Layer)
    npc_intent = NPCIntent(
        baseline_belief="The Insurgency must be protected at all costs",
        long_term_desire="Secure the future of the Insurgency",
        immediate_intention="Test Player's Loyalty",
        stakes="Trust and alliance with player"
    )
    
    # Define Outcome Index
    interaction_outcomes = [
        InteractionOutcome(
            outcome_id="challenge_back",
            stance_delta={'social.assertion': 0.1},
            relation_delta=-0.1,
            intention_shift="Resist Player",
            min_response="You think you can intimidate me? Think again.",
            max_response="I respect your boldness, but I won't be pushed around.",
            scripted=False
        ),
        InteractionOutcome(
            outcome_id="seek_connection",
            stance_delta={'social.empathy': 0.1},
            relation_delta=0.2,
            intention_shift="Evaluate Player",
            min_response="I hear what you're saying...",
            max_response="You make a compelling point. I'm listening.",
            scripted=False
        )
    ]
    
    terminal_outcomes = [
        TerminalOutcome(
            terminal_id=TerminalOutcomeType.SUCCEED,
            condition=lambda npc, conv: npc.world.player_relation > 0.7,
            result="Moses trusts the player and opens the door",
            final_dialogue="Alright. You've proven yourself. Come in."
        ),
        TerminalOutcome(
            terminal_id=TerminalOutcomeType.FAIL,
            condition=lambda npc, conv: npc.world.player_relation < 0.3,
            result="Moses refuses entry",
            final_dialogue="I don't trust you. Leave."
        )
    ]
    
    outcome_index = OutcomeIndex(
        choice_id="test_loyalty",
        interaction_outcomes=interaction_outcomes,
        terminal_outcomes=terminal_outcomes
    )
    
    # Create player skills
    player_skills = PlayerSkillSet(authority=2, manipulation=10, empathy=2, diplomacy=2)
    
    # Initialize processor
    processor = DialogueProcessor(
        npc=moses,
        player_skills=player_skills,
        npc_intent=npc_intent,
        outcome_index=outcome_index,
        conversation_id="conv_001",
        use_ollama=True
    )
    
    # Test dialogue
    print("=" * 70)
    print("REFACTORED PIPELINE TEST")
    print("=" * 70)
    
    player_choice = PlayerDialogueInput(
        choice_text="Listen, I'm trying to help. The land is fucked because no one listened.",
        language_art=LanguageArt.EMPATHETIC,
        empathy_tone=0.8,
        manipulation_tone=0.3
    )
    
    context = processor.process_dialogue(player_choice, generate_with_ollama=True)
    
    print(f"\n[Turn {context['turn']}]")
    print(f"Player: {player_choice.choice_text}")
    print(f"\n[Internal Thought]: {context['thought_reaction']['internal_thought']}")
    print(f"[Intention]: {context['behavioural_intention']['intention_type']}")
    print(f"\nMoses: {context['npc_response']}")
