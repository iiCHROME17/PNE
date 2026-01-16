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
from .social import SocialisationFilter
from .outcomes import OutcomeIndex
from .ollama_integration import OllamaResponseGenerator


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
    sys.path.append('..')  # Allow imports from parent directory
    
    from PNE_Models import NPCFactory
    from .enums import LanguageArt, TerminalOutcomeType
    from .intent import NPCIntent
    from .player_input import PlayerDialogueInput, PlayerSkillSet
    from .outcomes import InteractionOutcome, TerminalOutcome, OutcomeIndex
    
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