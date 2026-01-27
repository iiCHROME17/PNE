"""
Psychological Narrative Engine - Multi-NPC Conversation Engine
name: narrative_engine.py
Author: Jerome Bawa (original), refactor by AI assistant

Fallout-style psychological narrative engine where:
- Player choices are visible and structured (node/choice tree)
- NPC responses are generated via the BDI+LLM pipeline in pne/
- Scenarios are NPC-agnostic; NPC individuality is injected at runtime
- Multiple NPCs can participate independently in the same scenario
"""

from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, field

from pne import (
    DialogueProcessor,
    NPCIntent,
    OutcomeIndex,
    InteractionOutcome,
    TerminalOutcome,
    TerminalOutcomeType,
    PlayerDialogueInput,
    PlayerSkillSet,
    LanguageArt,
    ConversationModel,
)
from PNE_Models import NPCModel


# ============================================================================
# SCENARIO LOADER (NPC-agnostic)
# ============================================================================


class ScenarioLoader:
    """Loads generic, NPC-independent scenario JSON."""

    @staticmethod
    def load_scenario(filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_node(scenario: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        for node in scenario.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    @staticmethod
    def parse_npc_intent(data: Dict[str, Any]) -> NPCIntent:
        """Scenario-defined high-level intent, injected per NPC at runtime."""
        return NPCIntent(
            baseline_belief=data.get("baseline_belief", ""),
            long_term_desire=data.get("long_term_desire", ""),
            immediate_intention=data.get("immediate_intention", ""),
            stakes=data.get("stakes", ""),
        )

    @staticmethod
    def parse_player_input(choice_data: Dict[str, Any]) -> PlayerDialogueInput:
        """Convert a choice JSON blob into structured player input."""
        return PlayerDialogueInput(
            choice_text=choice_data["text"],
            language_art=LanguageArt(choice_data.get("language_art", "neutral")),
            authority_tone=choice_data.get("authority_tone", 0.5),
            diplomacy_tone=choice_data.get("diplomacy_tone", 0.5),
            empathy_tone=choice_data.get("empathy_tone", 0.5),
            manipulation_tone=choice_data.get("manipulation_tone", 0.5),
            ideology_alignment=choice_data.get("ideology_alignment"),
            contextual_references=choice_data.get("contextual_references", []),
        )

    @staticmethod
    def parse_outcome_index(choice_data: Dict[str, Any]) -> OutcomeIndex:
        """
        Build an OutcomeIndex from choice metadata.

        This is NPC-agnostic: it defines *potential* micro- and terminal outcomes.
        The DialogueProcessor + NPC state decide which ones actually trigger.
        """
        interaction_outcomes: List[InteractionOutcome] = []
        for outcome_data in choice_data.get("interaction_outcomes", []):
            interaction_outcomes.append(
                InteractionOutcome(
                    outcome_id=outcome_data["outcome_id"],
                    stance_delta=outcome_data.get("stance_delta", {}),
                    relation_delta=outcome_data.get("relation_delta", 0.0),
                    intention_shift=outcome_data.get("intention_shift"),
                    min_response=outcome_data["min_response"],
                    max_response=outcome_data["max_response"],
                    scripted=outcome_data.get("scripted", False),
                )
            )

        terminal_outcomes: List[TerminalOutcome] = []
        for terminal_data in choice_data.get("terminal_outcomes", []):
            condition_str = terminal_data.get("condition", "lambda npc, conv: False")
            # Trusted scenario authoring; this is intentionally flexible.
            condition_func = eval(condition_str)  # noqa: S307

            terminal_outcomes.append(
                TerminalOutcome(
                    terminal_id=TerminalOutcomeType(terminal_data["terminal_id"]),
                    condition=condition_func,
                    result=terminal_data["result"],
                    final_dialogue=terminal_data["final_dialogue"],
                )
            )

        return OutcomeIndex(
            choice_id=choice_data["choice_id"],
            interaction_outcomes=interaction_outcomes,
            terminal_outcomes=terminal_outcomes,
        )


# ============================================================================
# PER-NPC CONVERSATION STATE
# ============================================================================


@dataclass
class NPCConversationState:
    """
    Per-NPC conversation state inside a shared scenario.

    Each NPC has:
    - its own DialogueProcessor (with its own ConversationModel)
    - its own current node
    - its own emotional / BDI trajectory and terminal outcome
    """

    npc_id: str
    npc: NPCModel
    processor: DialogueProcessor
    scenario_id: str
    current_node: str = "start"
    is_complete: bool = False
    terminal_outcome: Optional[Dict[str, Any]] = None

    # Fallout-style visible log for this NPC
    history: List[Dict[str, Any]] = field(default_factory=list)
    choices_made: List[str] = field(default_factory=list)

    def conversation_model(self) -> ConversationModel:
        return self.processor.conversation

    @property
    def turn_count(self) -> int:
        return self.processor.conversation.turn_count

    def add_exchange(
        self,
        speaker: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry: Dict[str, Any] = {
            "turn": self.turn_count,
            "speaker": speaker,
            "text": text,
        }
        if metadata:
            entry["metadata"] = metadata
        self.history.append(entry)


# ============================================================================
# MULTI-NPC SESSION CONTAINER
# ============================================================================


@dataclass
class ConversationSession:
    """
    A running conversation session for a single scenario and one or more NPCs.

    - Scenario is NPC-agnostic.
    - Each NPC has its own BDI/LLM pipeline and memory.
    - Player choices are shared; outcomes are evaluated per-NPC.
    """

    scenario_id: str
    scenario: Dict[str, Any]
    npc_states: Dict[str, NPCConversationState]  # npc_id -> state

    # Global visible choice history (independent of NPC internals)
    player_choice_log: List[Dict[str, Any]] = field(default_factory=list)

    def active_npcs(self) -> List[NPCConversationState]:
        return [s for s in self.npc_states.values() if not s.is_complete]


# ============================================================================
# NARRATIVE ENGINE (MODULAR, MULTI-NPC)
# ============================================================================


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

    # ------------------------------------------------------------------
    # Loading NPCs & Scenarios
    # ------------------------------------------------------------------

    def load_npc(self, filepath: str, npc_id: Optional[str] = None) -> str:
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

    # ------------------------------------------------------------------
    # Session Initialisation
    # ------------------------------------------------------------------

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
        session = ConversationSession(scenario_id=scenario_id, scenario=scenario, npc_states=npc_states)
        self.sessions[session_id] = session

        self._display_opening(session)
        return session

    @staticmethod
    def _make_session_id(npc_ids: List[str], scenario_id: str) -> str:
        npc_part = ",".join(sorted(npc_ids))
        return f"{scenario_id}|{npc_part}"

    def _display_opening(self, session: ConversationSession) -> None:
        scenario = session.scenario
        opening = scenario.get("opening", "Conversation begins...")

        print(f"\n{'=' * 70}")
        print(f"CONVERSATION: {scenario.get('title', 'Untitled')}")
        print(f"NPCs: {', '.join(s.npc.name for s in session.npc_states.values())}")
        print(f"{'=' * 70}\n")
        print(f"Narrator: {opening}\n")

        for state in session.npc_states.values():
            state.add_exchange("Narrator", opening)

    # ------------------------------------------------------------------
    # Turn Helpers
    # ------------------------------------------------------------------

    def get_node(self, session: ConversationSession, node_id: str) -> Optional[Dict[str, Any]]:
        return ScenarioLoader.get_node(session.scenario, node_id)

    def get_available_choices(self, session: ConversationSession, node_id: str) -> List[Dict[str, Any]]:
        node = self.get_node(session, node_id)
        if not node:
            return []

        choices = node.get("choices", [])
        visible_choices: List[Dict[str, Any]] = []
        for idx, choice in enumerate(choices, start=1):
            visible_choices.append(
                {
                    "index": idx,
                    "choice_id": choice["choice_id"],
                    "text": choice["text"],
                    "raw": choice,
                }
            )
        return visible_choices

    # ------------------------------------------------------------------
    # Core Turn Step: apply one player choice across NPCs
    # ------------------------------------------------------------------

    def apply_choice(
        self,
        session: ConversationSession,
        node_id: str,
        choice_index: int,
    ) -> Dict[str, Any]:
        """
        Apply a single player choice (by index) to all active NPCs.
        Returns npc_id -> response context from DialogueProcessor.
        """
        node = self.get_node(session, node_id)
        if not node:
            raise ValueError(f"Node '{node_id}' not found in scenario '{session.scenario_id}'")

        choices = node.get("choices", [])
        if not (1 <= choice_index <= len(choices)):
            raise ValueError(f"Invalid choice index {choice_index} for node '{node_id}'")

        choice_data = choices[choice_index - 1]

        # Fallout-style visible player choice list
        print("Available choices:")
        for idx, c in enumerate(choices, start=1):
            marker = ">>" if idx == choice_index else "  "
            print(f"{marker} [{idx}] {c['text']}")

        player_input = ScenarioLoader.parse_player_input(choice_data)
        session.player_choice_log.append(
            {
                "node_id": node_id,
                "choice_id": choice_data["choice_id"],
                "text": player_input.choice_text,
            }
        )

        responses: Dict[str, Any] = {}
        outcome_index = ScenarioLoader.parse_outcome_index(choice_data)

        for state in session.active_npcs():
            print(f"\nPlayer → {state.npc.name}: {player_input.choice_text}")
            state.add_exchange("Player", player_input.choice_text)
            state.choices_made.append(choice_data["choice_id"])

            state.processor.outcome_index = outcome_index

            context = state.processor.process_dialogue(
                player_input,
                generate_with_ollama=self.use_ollama,
            )

            thought = context["thought_reaction"]
            desire = context["desire_state"]
            intention = context["behavioural_intention"]
            npc_response = context["npc_response"]

            print(f"\n[{state.npc.name} | Internal Thought]: {thought['internal_thought']}")
            print(
                f"[{state.npc.name} | Desire]: "
                f"{desire['immediate_desire']} "
                f"(type={desire['desire_type']}, intensity={desire['intensity']:.2f})"
            )
            print(f"[{state.npc.name} | Intention]: {intention['intention_type']}")
            print(f"\n{state.npc.name}: {npc_response}\n")

            state.add_exchange(
                state.npc.name,
                npc_response,
                metadata={
                    "thought": thought,
                    "desire": desire,
                    "intention": intention,
                    "interaction_outcome": context.get("interaction_outcome"),
                    "terminal_outcome": context.get("terminal_outcome"),
                },
            )

            if context["conversation_complete"] and context["terminal_outcome"]:
                terminal = context["terminal_outcome"]
                state.is_complete = True
                state.terminal_outcome = terminal

                print(f"\n{'=' * 70}")
                print(f"TERMINAL OUTCOME for {state.npc.name}: {terminal['terminal_id'].upper()}")
                print(f"Result: {terminal['result']}")
                print(f"{state.npc.name}: {terminal['final_dialogue']}")
                print(f"{'=' * 70}\n")

                state.processor.end_conversation()

            state.current_node = choice_data.get("next_node", "end")
            responses[state.npc_id] = context

        return responses

    # ------------------------------------------------------------------
    # Session Termination & Export
    # ------------------------------------------------------------------

    def is_session_complete(self, session: ConversationSession) -> bool:
        """Session ends when all NPCs are complete or at node 'end'."""
        if not session.active_npcs():
            return True
        return all(s.current_node == "end" for s in session.active_npcs())

    def export_session_log(self, session: ConversationSession, filepath: str) -> None:
        """
        Export a rich, per-NPC log backed by each NPC's ConversationModel.
        """
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

        print(f"\n✓ Conversation session log exported to {filepath}")


# ============================================================================
# SIMPLE CLI (single-NPC for quick testing)
# ============================================================================


def main() -> None:
    """
    Minimal CLI entry-point.

    Usage:
        python narrative_engine.py <npc_file.json> <scenario_file.json> [--no-ollama]
    """
    import sys

    print("=" * 70)
    print("PSYCHOLOGICAL NARRATIVE ENGINE - MULTI-NPC CONVERSATION SIMULATOR")
    print("=" * 70)

    if len(sys.argv) < 3:
        print("\nUsage: python narrative_engine.py <npc_file.json> <scenario_file.json> [--no-ollama]")
        print("\nExample:")
        print("  python narrative_engine.py morisson_moses.json door_guard_scenario.json")
        print("\nOptional flags:")
        print("  --no-ollama : Disable Ollama integration (use fallback responses)")
        return

    # All args except last and flags are NPC files; last non-flag is scenario
    raw_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(raw_args) < 2:
        print("Error: need at least one NPC file and one scenario file.")
        return

    *npc_files, scenario_file = raw_args
    use_ollama = "--no-ollama" not in sys.argv

    try:
        engine = NarrativeEngine(use_ollama=use_ollama)

        npc_ids: List[str] = []
        for npc_path in npc_files:
            npc_ids.append(engine.load_npc(npc_path))

        scenario_id = engine.load_scenario(scenario_file)

        player_skills = PlayerSkillSet(
            authority=5,
            diplomacy=5,
            empathy=5,
            manipulation=5,
        )

        session = engine.start_session(npc_ids, scenario_id, player_skills)

        current_node = "start"
        while not engine.is_session_complete(session) and current_node != "end":
            choices = engine.get_available_choices(session, current_node)
            if not choices:
                print("\n[No available choices; conversation ends.]")
                break

            print("\nAvailable choices:")
            for c in choices:
                print(f"  [{c['index']}] {c['text']}")

            try:
                user_input = input("\nYour choice (number or 'quit'): ").strip()
                if user_input.lower() in {"q", "quit", "exit"}:
                    print("\nConversation ended by player.")
                    break

                choice_num = int(user_input)
                engine.apply_choice(session, current_node, choice_num)
                # All NPCs share the same scenario graph node id
                current_node = choices[choice_num - 1]["raw"].get("next_node", "end")

            except (ValueError, IndexError):
                print("Please enter a valid choice number.")
                continue
            except KeyboardInterrupt:
                print("\n\nConversation interrupted.")
                break

        # Export log if requested
        export = input("\nExport conversation log? (y/n): ").strip().lower()
        if export == "y":
            log_file = input("Enter filename (e.g., conversation_log.json): ").strip()
            engine.export_session_log(session, log_file)

    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

