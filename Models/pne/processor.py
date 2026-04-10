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
from config import OLLAMA_MODEL, OLLAMA_URL


class DialogueProcessor:
    """Per-NPC BDI pipeline executor for a single conversation.

    Orchestrates the full **Purpose → Input → Belief → Want → Intention → Output**
    cycle on every player turn.  One ``DialogueProcessor`` is created per NPC per
    session and lives inside an ``NPCConversationState``.

    Pipeline stages (executed by ``process_dialogue``)
    --------------------------------------------------
    I.   **Purpose** — set at construction via ``npc_intent``; the NPC's goals
         remain constant across turns (though ``intention_shift`` can update them).
    II.  **Input / Rhetoric Parsing** — the ``PlayerDialogueInput`` arrives
         pre-built from the scenario JSON; no parsing happens here.
    III. **Cognitive Interpretation → Belief** — ``CognitiveInterpreter.interpret``
         produces a ``ThoughtReaction`` describing the NPC's internal reading of
         the player's words.  Falls back to a neutral default if Ollama is off.
    IV.  **Desire Formation → Want** — ``DesireFormation.form_desire`` converts
         the belief into a goal-oriented ``DesireState``.
    V.   **Socialisation Filter → Intention** — ``SocialisationFilter.filter``
         selects the best-matching ``BehaviouralIntention`` from ``INTENTION_REGISTRY``.
    VI.  **Interaction Outcome** — ``OutcomeIndex.get_interaction_outcome`` maps the
         intention to a scenario-defined outcome; applies stance and relation deltas.
    VII. **Terminal Check** — ``OutcomeIndex.check_terminal_outcomes`` tests whether
         the conversation has reached an ending condition.

    Attributes:
        npc: The ``NPCModel`` being processed; mutated in-place by outcome effects
            (temporary mods, relation updates).
        player_skills: Immutable skill set for the player; used in skill checks.
        npc_intent: Tracks the NPC's current goal; may shift via
            ``interaction_outcome.intention_shift``.
        outcome_index: Maps BDI intentions to interaction / terminal outcomes for
            the current choice.  Replaced each turn by the engine.
        conversation: Tracks conversation stage, turn count, and history.
        use_ollama: Whether LLM generation is enabled for this session.
        ollama: ``OllamaResponseGenerator`` instance, or ``None`` if disabled.
        cognitive_interpreter: ``CognitiveInterpreter`` instance, or ``None``
            if disabled.
    """

    def __init__(
        self,
        npc,
        player_skills: PlayerSkillSet,
        npc_intent: NPCIntent,
        outcome_index: OutcomeIndex,
        conversation_id: str,
        use_ollama: bool = True,
        ollama_url: str = OLLAMA_URL,
        ollama_model: str = OLLAMA_MODEL,
    ):
        """Initialise the processor and wire up its sub-components.

        Args:
            npc: The ``NPCModel`` for the NPC this processor manages.
            player_skills: The player's starting skill levels (0–10 each).
            npc_intent: The NPC's initial goal state.
            outcome_index: Starting ``OutcomeIndex`` for the first turn (replaced
                each turn by the engine before calling ``process_dialogue``).
            conversation_id: Unique identifier string for this conversation,
                used by ``ConversationModel`` for logging.
            use_ollama: Enable LLM-backed cognitive interpretation and response
                generation.  Set ``False`` for deterministic / offline operation.
            ollama_url: Base URL of the Ollama API server.
            ollama_model: Ollama model tag (e.g. ``"llama3.2:1b"``).
        """
        self.npc = npc
        self.player_skills = player_skills
        self.npc_intent = npc_intent
        self.outcome_index = outcome_index

        # Conversation containment — tracks stage, turn count, and history.
        self.conversation = ConversationModel(
            conversation_id=conversation_id,
            stage="opening",
            topic=npc_intent.immediate_intention,
        )

        # Ollama integration — both generators share the same connection config.
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
        generate_with_ollama: bool = True,
    ) -> Dict[str, Any]:
        """Run the full BDI pipeline for one player turn and return a rich context dict.

        This is the core method called by ``NarrativeEngine.apply_choice`` each turn.
        It executes all seven pipeline stages in sequence, applies outcome effects to
        the NPC, optionally generates an NPC text response, and bundles everything
        into a structured context dict for the engine layer.

        Note: The engine typically calls this with ``generate_with_ollama=False`` and
        then invokes ``ollama.generate_response_with_direction`` separately so it can
        inject the scene direction from the scenario node and the dice result.

        Args:
            player_input: The parsed player choice for this turn.
            generate_with_ollama: If ``True`` *and* Ollama is enabled, generate the
                NPC's text response inside this method.  If ``False``, the engine
                handles generation externally; ``npc_response`` in the returned dict
                will contain the interaction outcome's fallback text.

        Returns:
            A dict with the following keys:

            - ``conversation_id`` (str): Identifier of the ongoing conversation.
            - ``turn`` (int): Current turn count after this exchange.
            - ``npc_intent`` (dict): Serialised ``NPCIntent`` state.
            - ``skill_check`` (dict | None): Result of the legacy threshold check,
              or ``None`` for neutral choices.
            - ``thought_reaction`` (dict): NPC's internal belief from Stage III.
            - ``desire_state`` (dict): Goal-oriented desire from Stage IV.
            - ``behavioural_intention`` (dict): Chosen intention from Stage V.
            - ``interaction_outcome`` (dict | None): Matched outcome from Stage VI,
              or ``None`` if no outcome was found.
            - ``npc_response`` (str): Generated or fallback NPC dialogue text.
            - ``terminal_outcome`` (dict | None): Terminal result if the conversation
              has ended (Stage VII), otherwise ``None``.
            - ``conversation_complete`` (bool): ``True`` when a terminal outcome fired.
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
    
    def end_conversation(self) -> None:
        """Clean up NPC state after the conversation ends.

        Called by ``NarrativeEngine.apply_choice`` when a terminal node is
        reached.  Reverses any temporary attribute modifiers applied during
        the session (via ``apply_temp_mod``) and clears the conversation
        history to free memory.
        """
        self.npc.reset_temp_mods()
        self.conversation.history.clear()