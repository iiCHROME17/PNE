"""
Psychological Narrative Engine - Dialogue Processor
Name: processor.py
Author: Jerome Bawa 

Implements Purpose-Output Model with Conversation Containment,
Interaction Outcomes, and Terminal Outcomes
"""

from typing import Dict, Any
from .conversation import ConversationModel
from .intent import NPCIntent
from .player_input import PlayerDialogueInput, PlayerSkillSet
from .skill_check import SkillCheckSystem
from .cognitive import CognitiveInterpreter, ThoughtReaction
from .desire import DesireFormation, DesireState
from .social import SocialisationFilter
from .outcomes import OutcomeIndex
from .ollama_integration import OllamaResponseGenerator


class DialogueProcessor:
    """
    Main processor implementing Purpose-Output Model with BDI architecture:
    Purpose → Input → COGNITIVE (Belief) → DESIRE (Want) → SOCIAL (Intention) → Output
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
        Complete BDI pipeline:
        Purpose → Input → COGNITIVE (Belief) → DESIRE (Want) → SOCIAL (Intention) → Interaction → Terminal
        """
        
        # ═══════════════════════════════════════════════════════════
        # STAGE I: Purpose (already set in __init__ via npc_intent)
        # ═══════════════════════════════════════════════════════════
        
        # ═══════════════════════════════════════════════════════════
        # STAGE II: Input / Rhetoric Parsing (already done via player_input)
        # ═══════════════════════════════════════════════════════════
        
        # Skill Check (auxiliary)
        skill_check = SkillCheckSystem.perform_check(
            player_input, self.player_skills, self.npc
        )
        if skill_check and skill_check.success:
            SkillCheckSystem.apply_modifiers(self.npc, skill_check)
        
        # ═══════════════════════════════════════════════════════════
        # STAGE III: COGNITIVE INTERPRETATION → BELIEF
        # ═══════════════════════════════════════════════════════════
        if self.cognitive_interpreter:
            thought_reaction = self.cognitive_interpreter.interpret(player_input, self.npc)
        else:
            # Fallback if Ollama not available
            thought_reaction = ThoughtReaction(
                internal_thought="What are they really saying...?",
                subjective_belief="Their intentions are unclear",
                cognitive_state={
                    'self_esteem': self.npc.cognitive.self_esteem,
                    'locus_of_control': self.npc.cognitive.locus_of_control,
                    'cog_flexibility': self.npc.cognitive.cog_flexibility
                },
                emotional_valence=0.0
            )
        
        # ═══════════════════════════════════════════════════════════
        # STAGE IV: DESIRE FORMATION → WANT
        # ═══════════════════════════════════════════════════════════
        desire_state = DesireFormation.form_desire(
            thought_reaction,
            player_input,
            self.npc,
            self.npc_intent
        )
        
        # ═══════════════════════════════════════════════════════════
        # STAGE V: SOCIALISATION FILTER → INTENTION
        # ═══════════════════════════════════════════════════════════
        behavioural_intention = SocialisationFilter.filter(
            thought_reaction,
            desire_state,
            player_input,
            self.npc
        )
        
        # ═══════════════════════════════════════════════════════════
        # STAGE VI: INTERACTION OUTCOME
        # ═══════════════════════════════════════════════════════════
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
        
        # ═══════════════════════════════════════════════════════════
        # STAGE VII: CHECK TERMINAL OUTCOMES
        # ═══════════════════════════════════════════════════════════
        terminal_outcome = self.outcome_index.check_terminal_outcomes(self.npc, self.conversation)
        
        # Build response context
        response_context = {
            'conversation_id': self.conversation.conversation_id,
            'turn': self.conversation.turn_count,
            'npc_intent': self.npc_intent.to_dict(),
            'skill_check': skill_check.to_dict() if skill_check else None,
            'thought_reaction': thought_reaction.to_dict(),
            'desire_state': desire_state.to_dict(),  # NEW
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