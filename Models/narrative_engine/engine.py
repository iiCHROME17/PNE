"""
Narrative Engine Module  (patched: coherent choice filtering)

KEY CHANGES vs original
-----------------------
* get_available_choices() now runs choices through ChoiceFilter + optional
  DialogueMomentumFilter before returning them to the CLI / caller.
* apply_choice() builds a full FilterContext and DialogueContext from live
  NPC state so filters have real data to work with.
* _build_filter_context() and _build_dialogue_context() are new helpers.

Everything else is identical to the original.
"""

from typing import Dict, List, Optional, Any

from pne import DialogueProcessor, PlayerSkillSet, OutcomeIndex
from PNE_Models import NPCModel

from .session import ConversationSession, NPCConversationState
from .scenario_loader import ScenarioLoader
from .transition_resolver import TransitionResolver
from .choice_filter import ChoiceFilter, FilterContext, ConversationStageDetector
from .dialogue_coherence import DialogueMomentumFilter, DialogueContext


class NarrativeEngine:
    """
    High-level orchestrator for Fallout-style conversations using pne's BDI engine.
    """

    def __init__(self, use_ollama: bool = True, ollama_url: str = "http://localhost:11434"):
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.npcs: Dict[str, NPCModel] = {}
        self.sessions: Dict[str, ConversationSession] = {}

    # ------------------------------------------------------------------ #
    # Static helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_with_npc(text: str, npc_name: str) -> str:
        return text.replace("{{NPC_NAME}}", npc_name)

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #

    def load_npc(self, filepath: str, npc_id: Optional[str] = None) -> str:
        """Load an NPC from JSON file."""
        npc = NPCModel.from_json(filepath)
        npc_id = npc_id or npc.name.lower().replace(" ", "_")
        self.npcs[npc_id] = npc
        print(f"✓ Loaded NPC: {npc.name} (ID: {npc_id})")
        return npc_id

    def load_scenario(self, filepath: str, scenario_id: Optional[str] = None) -> str:
        scenario = ScenarioLoader.load_scenario(filepath)
        scenario_id = scenario_id or scenario.get("id", "default_scenario")
        self.scenarios[scenario_id] = scenario
        print(f"✓ Loaded scenario: {scenario.get('title', scenario_id)} (ID: {scenario_id})")
        return scenario_id

    # ------------------------------------------------------------------ #
    # Session initialisation
    # ------------------------------------------------------------------ #

    def start_session(
        self,
        npc_ids: List[str],
        scenario_id: str,
        player_skills: Optional[PlayerSkillSet] = None,
    ) -> ConversationSession:
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not loaded")
        for npc_id in npc_ids:
            if npc_id not in self.npcs:
                raise ValueError(f"NPC '{npc_id}' not loaded")

        scenario = self.scenarios[scenario_id]
        npc_intent = ScenarioLoader.parse_npc_intent(scenario.get("npc_intent", {}))
        npc_role = ScenarioLoader.parse_npc_role(scenario.get("npc_role", {}))
        scenario["_npc_role_meta"] = npc_role

        if player_skills is None:
            player_skills = PlayerSkillSet(authority=5, diplomacy=5, empathy=5, manipulation=5)

        npc_states: Dict[str, NPCConversationState] = {}
        for npc_id in npc_ids:
            npc = self.npcs[npc_id]
            start_node = ScenarioLoader.get_node(scenario, "start")
            if not start_node or not start_node.get("choices"):
                outcome_index = OutcomeIndex(choice_id="empty", interaction_outcomes=[], terminal_outcomes=[])
            else:
                outcome_index = ScenarioLoader.parse_outcome_index(start_node["choices"][0])

            processor = DialogueProcessor(
                npc=npc,
                player_skills=player_skills,
                npc_intent=npc_intent,
                outcome_index=outcome_index,
                conversation_id=f"{scenario_id}:{npc_id}",
                use_ollama=self.use_ollama,
                ollama_url=self.ollama_url,
            )

            npc_states[npc_id] = NPCConversationState(
                npc_id=npc_id,
                npc=npc,
                processor=processor,
                scenario_id=scenario_id,
                current_node="start",
            )

        session_id = self._make_session_id(npc_ids, scenario_id)
        session = ConversationSession(
            scenario_id=scenario_id, scenario=scenario, npc_states=npc_states
        )
        self.sessions[session_id] = session
        self._display_opening(session)
        return session

    @staticmethod
    def _make_session_id(npc_ids: List[str], scenario_id: str) -> str:
        return f"{scenario_id}|{','.join(sorted(npc_ids))}"

    def _display_opening(self, session: ConversationSession) -> None:
        scenario = session.scenario
        opening = scenario.get("opening", "Conversation begins...")
        npc_role = scenario.get("_npc_role_meta", {})

        print(f"\n{'=' * 70}")
        print(f"CONVERSATION: {scenario.get('title', 'Untitled')}")
        print(f"NPCs: {', '.join(s.npc.name for s in session.npc_states.values())}")
        print(f"{'=' * 70}\n")

        first_state = next(iter(session.npc_states.values()))
        opening_visible = self._format_with_npc(opening, first_state.npc.name)
        print(opening_visible + "\n")

        for state in session.npc_states.values():
            opening_for_npc = self._format_with_npc(opening, state.npc.name)
            state.add_exchange("Narrator", opening_for_npc)

    # ------------------------------------------------------------------ #
    # Turn helpers
    # ------------------------------------------------------------------ #

    def get_node(self, session: ConversationSession, node_id: str) -> Optional[Dict[str, Any]]:
        return ScenarioLoader.get_node(session.scenario, node_id)

    def get_available_choices(
        self,
        session: ConversationSession,
        node_id: str,
        verbose_filter: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Returns filtered, coherence-checked choices for the given node.

        Filtering pipeline:
          1. ChoiceFilter  – hard gates (skill/relation/state/prerequisite)
          2. DialogueMomentumFilter – coherence scoring (responds to NPC momentum)
        """
        node = self.get_node(session, node_id)
        if not node:
            return []

        raw_choices = node.get("choices", [])
        if not raw_choices:
            return []

        # Use the first active NPC as the representative state for filtering.
        active = session.active_npcs()
        if not active:
            return self._index_choices(raw_choices)

        primary_state = active[0]
        npc = primary_state.npc

        # ── Build FilterContext ──────────────────────────────────────────
        filter_ctx = self._build_filter_context(primary_state, node_id)

        # ── Stage 1: hard gate filtering ────────────────────────────────
        filtered = ChoiceFilter.smart_fallback(raw_choices, filter_ctx)

        # ── Stage 2: coherence scoring ───────────────────────────────────
        scenario_config = session.scenario.get("conversation_config", {})
        if scenario_config.get("enable_coherence_filtering", True):
            dialogue_ctx = self._build_dialogue_context(primary_state, filter_ctx)
            filtered = self._apply_coherence_filter(filtered, dialogue_ctx, verbose_filter)

        return self._index_choices(filtered)

    @staticmethod
    def _index_choices(choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach 1-based index to each choice dict."""
        return [
            {"index": idx, "choice_id": c["choice_id"], "text": c["text"], "raw": c}
            for idx, c in enumerate(choices, start=1)
        ]

    # ------------------------------------------------------------------ #
    # Core turn step
    # ------------------------------------------------------------------ #

    def apply_choice(
        self,
        session: ConversationSession,
        node_id: str,
        choice_index: int,
    ) -> Dict[str, Any]:
        """
        Apply a single player choice (1-based index) to all active NPCs.
        """
        node = self.get_node(session, node_id)
        if not node:
            raise ValueError(f"Node '{node_id}' not found")

        # Resolve against *filtered* choices so indices stay consistent.
        visible_choices = self.get_available_choices(session, node_id)
        if not (1 <= choice_index <= len(visible_choices)):
            raise ValueError(
                f"Invalid choice index {choice_index} (only {len(visible_choices)} available)"
            )

        chosen = visible_choices[choice_index - 1]["raw"]
        choice_data = chosen

        # Fallout-style display
        print("Available choices:")
        for c in visible_choices:
            marker = ">>" if c["index"] == choice_index else "  "
            print(f"{marker} [{c['index']}] {c['text']}")

        player_input = ScenarioLoader.parse_player_input(choice_data)
        session.player_choice_log.append({
            "node_id": node_id,
            "choice_id": choice_data["choice_id"],
            "text": player_input.choice_text,
        })

        responses: Dict[str, Any] = {}
        outcome_index = ScenarioLoader.parse_outcome_index(choice_data)
        transitions = node.get("transitions", [])

        for state in session.active_npcs():
            print(f"\nPlayer → {state.npc.name}: {player_input.choice_text}")
            state.add_exchange("Player", player_input.choice_text)
            state.choices_made.append(choice_data["choice_id"])

            # ── BDI pipeline ─────────────────────────────────────────────
            state.processor.outcome_index = outcome_index
            context = state.processor.process_dialogue(
                player_input,
                generate_with_ollama=self.use_ollama,
            )

            thought = context["thought_reaction"]
            desire = context["desire_state"]
            intention = context["behavioural_intention"]
            npc_response = self._format_with_npc(context["npc_response"], state.npc.name)

            print(f"\n[{state.npc.name} | Belief]: {thought['subjective_belief']}")
            print(
                f"[{state.npc.name} | Desire]: "
                f"{desire['immediate_desire']} "
                f"(type={desire['desire_type']}, intensity={desire['intensity']:.2f})"
            )
            print(f"[{state.npc.name} | Intention]: {intention['intention_type']} "
                  f"(confrontation={intention['confrontation_level']:.2f})")
            print(f"\n{state.npc.name}: {npc_response}\n")

            state.add_exchange(
                state.npc.name,
                npc_response,
                metadata={
                    "thought": thought,
                    "desire": desire,
                    "intention": intention,
                    "interaction_outcome": context.get("interaction_outcome"),
                },
            )

            # ── Transition resolution ─────────────────────────────────────
            resolved_node = TransitionResolver.resolve(transitions, state)

            if resolved_node:
                target_node = self.get_node(session, resolved_node)

                if target_node and TransitionResolver.is_terminal(target_node):
                    terminal_id = target_node.get("terminal_id", "unknown")
                    terminal_result = target_node.get("terminal_result", "")

                    state.is_complete = True
                    state.terminal_outcome = {
                        "terminal_id": terminal_id,
                        "result": terminal_result,
                        "final_dialogue": npc_response,
                    }
                    state.current_node = resolved_node

                    print(f"\n{'=' * 70}")
                    print(f"TERMINAL OUTCOME for {state.npc.name}: {terminal_id.upper()}")
                    print(f"Result: {terminal_result}")
                    print(f"{state.npc.name}: {npc_response}")
                    print(f"{'=' * 70}\n")

                    state.processor.end_conversation()
                else:
                    state.current_node = resolved_node
                    print(f"  [{state.npc.name}] → routed to node: {resolved_node}")
            else:
                default_node = node.get("default_transition", "probing")
                if self.get_node(session, default_node):
                    state.current_node = default_node
                    print(f"  [{state.npc.name}] → no transition matched, defaulting to: {default_node}")
                else:
                    print(f"  [{state.npc.name}] → no transition matched, staying on: {node_id}")

            responses[state.npc_id] = {
                "context": context,
                "resolved_node": state.current_node,
            }

        return responses

    # ------------------------------------------------------------------ #
    # Session helpers
    # ------------------------------------------------------------------ #

    def is_session_complete(self, session: ConversationSession) -> bool:
        return len(session.active_npcs()) == 0

    def export_session_log(self, session: ConversationSession, filepath: str) -> None:
        import json

        data: Dict[str, Any] = {
            "scenario_id": session.scenario_id,
            "player_choice_log": session.player_choice_log,
            "npcs": {},
        }

        for npc_id, state in session.npc_states.items():
            conv_model = state.conversation_model()
            data["npcs"][npc_id] = {
                "name": state.npc.name,
                "conversation": conv_model.to_dict(),
                "choices_made": state.choices_made,
                "history": state.history,
                "terminal_outcome": state.terminal_outcome,
                "final_npc_state": state.npc.to_dict(),
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Session log exported to {filepath}")

    # ------------------------------------------------------------------ #
    # Private: filter context builders
    # ------------------------------------------------------------------ #

    def _build_filter_context(
        self,
        state: NPCConversationState,
        node_id: str,
    ) -> FilterContext:
        """Build a FilterContext from live NPC + session state."""
        npc = state.npc
        processor = state.processor

        player_skills_dict = {
            "authority": processor.player_skills.authority,
            "diplomacy": processor.player_skills.diplomacy,
            "empathy": processor.player_skills.empathy,
            "manipulation": processor.player_skills.manipulation,
        }

        # Grab last intention from history if available
        last_intention = None
        for entry in reversed(state.history):
            meta = entry.get("metadata")
            if meta and meta.get("intention"):
                last_intention = meta["intention"].get("intention_type")
                break

        # Last desire type
        last_desire_type = "information-seeking"
        for entry in reversed(state.history):
            meta = entry.get("metadata")
            if meta and meta.get("desire"):
                last_desire_type = meta["desire"].get("desire_type", last_desire_type)
                break

        # Emotional valence from last entry
        npc_emotional_valence = 0.0
        for entry in reversed(state.history):
            meta = entry.get("metadata")
            if meta and meta.get("thought"):
                npc_emotional_valence = meta["thought"].get("emotional_valence", 0.0)
                break

        # Conversation stage detection
        emotional_trajectory = []
        for entry in state.history:
            meta = entry.get("metadata")
            if meta and meta.get("thought"):
                emotional_trajectory.append(meta["thought"].get("emotional_valence", 0.0))

        stage = ConversationStageDetector.detect_stage(
            state.turn_count,
            npc.world.player_relation,
            emotional_trajectory,
        )

        return FilterContext(
            player_skills=player_skills_dict,
            player_relation=npc.world.player_relation,
            npc_self_esteem=npc.cognitive.self_esteem,
            npc_emotional_valence=npc_emotional_valence,
            npc_current_intention=last_intention or "",
            npc_current_desire_type=last_desire_type,
            choices_made=state.choices_made,
            turn_count=state.turn_count,
            last_intention_shift=last_intention,
            conversation_topic=node_id,
            conversation_stage=stage,
        )

    def _build_dialogue_context(
        self,
        state: NPCConversationState,
        filter_ctx: FilterContext,
    ) -> DialogueContext:
        """Build a DialogueContext for momentum-based coherence filtering."""
        # Pull the last NPC response text
        last_npc_response = None
        for entry in reversed(state.history):
            if entry.get("speaker") == state.npc.name:
                last_npc_response = entry.get("text")
                break

        # Pull npc_momentum_tags from last interaction_outcome intention_shift
        momentum_tags: List[str] = []
        for entry in reversed(state.history):
            meta = entry.get("metadata")
            if meta:
                outcome = meta.get("interaction_outcome")
                if outcome and outcome.get("intention_shift"):
                    shift = outcome["intention_shift"].lower()
                    # Infer momentum tag from shift text
                    if any(k in shift for k in ["test", "challenge", "prove"]):
                        momentum_tags.append("challenge_posed")
                    if any(k in shift for k in ["question", "evaluate"]):
                        momentum_tags.append("question_asked")
                    if any(k in shift for k in ["doubt", "skeptic", "suspicious"]):
                        momentum_tags.append("doubt_expressed")
                    if any(k in shift for k in ["accept", "ally", "trust", "trial"]):
                        momentum_tags.append("acceptance_signaled")
                    if any(k in shift for k in ["reject", "dismiss", "close"]):
                        momentum_tags.append("rejection_signaled")
                    if any(k in shift for k in ["demand", "ultimatum"]):
                        momentum_tags.append("demand_made")
                    break

        return DialogueContext(
            player_skills=filter_ctx.player_skills,
            player_relation=filter_ctx.player_relation,
            npc_self_esteem=filter_ctx.npc_self_esteem,
            npc_emotional_valence=filter_ctx.npc_emotional_valence,
            npc_current_intention=filter_ctx.npc_current_intention,
            npc_current_desire_type=filter_ctx.npc_current_desire_type,
            choices_made=filter_ctx.choices_made,
            turn_count=filter_ctx.turn_count,
            last_npc_response=last_npc_response,
            conversation_stage=filter_ctx.conversation_stage or "opening",
            npc_momentum_tags=momentum_tags,
        )

    @staticmethod
    def _apply_coherence_filter(
        choices: List[Dict[str, Any]],
        dialogue_ctx: DialogueContext,
        verbose: bool,
    ) -> List[Dict[str, Any]]:
        """
        Run DialogueMomentumFilter; fall back to original list if it removes everything.
        """
        coherent = DialogueMomentumFilter.filter_for_coherence(choices, dialogue_ctx, verbose)
        if not coherent:
            return choices  # Safety net
        return coherent