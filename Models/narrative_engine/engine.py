"""
Narrative Engine Module

Core orchestrator for Fallout-style multi-NPC conversations using BDI psychology.

Key Features:
- NPC-agnostic scenario system: Same scenario works with any NPC
- Dynamic routing: Choices don't have hardcoded next_node; routing is determined
  by each NPC's internal state (beliefs, desires, intentions)
- Multi-NPC support: Multiple NPCs can participate in the same scenario,
  each with independent BDI processing and potentially different paths
- Ollama/LLM integration: Generates contextual NPC responses via language models

Key Components:
- NarrativeEngine: Main orchestrator class
"""

from typing import Dict, List, Optional, Any

from pne import DialogueProcessor, PlayerSkillSet, OutcomeIndex
from PNE_Models import NPCModel

from .session import ConversationSession, NPCConversationState
from .scenario_loader import ScenarioLoader
from .transition_resolver import TransitionResolver


class NarrativeEngine:
    """
    High-level orchestrator for Fallout-style conversations using pne's BDI engine.

    Key difference from traditional choice-based systems:
    - Choices no longer have next_node hardcoded
    - After a choice is processed, each NPC's state is evaluated against
      the CURRENT node's transitions to determine where that NPC goes next
    - Different NPCs can end up on different nodes after the same player choice

    Workflow:
    1. Load NPCs (personality, beliefs, world state)
    2. Load scenario (nodes, choices, transitions - NPC-agnostic)
    3. Start session (inject NPCs into scenario)
    4. Process player choices:
       - Parse choice into PlayerDialogueInput
       - Run through each NPC's DialogueProcessor (BDI + LLM)
       - Evaluate transitions against each NPC's updated state
       - Route each NPC to appropriate next node
    5. Export rich conversation logs

    Attributes:
        use_ollama: Whether to use Ollama for LLM generation
        ollama_url: URL for Ollama API endpoint
        scenarios: Dict of loaded scenarios (scenario_id -> scenario data)
        npcs: Dict of loaded NPCs (npc_id -> NPCModel)
        sessions: Dict of active conversation sessions (session_id -> ConversationSession)
    """

    def __init__(self, use_ollama: bool = True, ollama_url: str = "http://localhost:11434"):
        """
        Initialize the narrative engine.

        Args:
            use_ollama: Whether to use Ollama for LLM-based response generation
            ollama_url: URL of the Ollama API endpoint
        """
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url

        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.npcs: Dict[str, NPCModel] = {}
        self.sessions: Dict[str, ConversationSession] = {}

    @staticmethod
    def _format_with_npc(text: str, npc_name: str) -> str:
        """
        Replace simple parsewords in scenario text.

        Currently supported:
          {{NPC_NAME}} -> concrete NPC model name (e.g. 'Moses', 'Taylor')

        Args:
            text: Text containing parsewords
            npc_name: Name of the NPC to substitute

        Returns:
            Text with parsewords replaced by actual NPC data
        """
        return text.replace("{{NPC_NAME}}", npc_name)

    # ------------------------------------------------------------------
    # Loading NPCs & Scenarios
    # ------------------------------------------------------------------

    def load_npc(self, filepath: str, npc_id: Optional[str] = None) -> str:
        """
        Load an NPC from a JSON file.

        Args:
            filepath: Path to the NPC JSON file
            npc_id: Optional custom ID for the NPC (defaults to lowercase name)

        Returns:
            The NPC ID that was assigned

        Raises:
            FileNotFoundError: If the NPC file doesn't exist
        """
        npc = NPCModel.from_json(filepath)
        npc_id = npc_id or npc.name.lower().replace(" ", "_")
        self.npcs[npc_id] = npc
        print(f"✓ Loaded NPC: {npc.name} (ID: {npc_id})")
        return npc_id

    def load_scenario(self, filepath: str, scenario_id: Optional[str] = None) -> str:
        """
        Load a scenario from a JSON file.

        Args:
            filepath: Path to the scenario JSON file
            scenario_id: Optional custom ID (defaults to scenario's "id" field)

        Returns:
            The scenario ID that was assigned

        Raises:
            FileNotFoundError: If the scenario file doesn't exist
        """
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
        """
        Start a new conversation session with one or more NPCs.

        Creates a DialogueProcessor for each NPC, injecting their personality
        into the NPC-agnostic scenario structure.

        Args:
            npc_ids: List of NPC IDs to participate in this conversation
            scenario_id: ID of the scenario to use
            player_skills: Optional player skill set (defaults to 5 in all skills)

        Returns:
            ConversationSession object for the active conversation

        Raises:
            ValueError: If scenario_id or any npc_id is not loaded
        """
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not loaded")
        for npc_id in npc_ids:
            if npc_id not in self.npcs:
                raise ValueError(f"NPC '{npc_id}' not loaded")

        scenario = self.scenarios[scenario_id]
        npc_intent = ScenarioLoader.parse_npc_intent(scenario.get("npc_intent", {}))
        npc_role = ScenarioLoader.parse_npc_role(scenario.get("npc_role", {}))

        # attach parsed npc_role onto the scenario object for later use
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
        session = ConversationSession(scenario_id=scenario_id, scenario=scenario, npc_states=npc_states)
        self.sessions[session_id] = session

        self._display_opening(session)
        return session

    @staticmethod
    def _make_session_id(npc_ids: List[str], scenario_id: str) -> str:
        """
        Generate a unique session ID from NPC IDs and scenario ID.

        Args:
            npc_ids: List of NPC IDs
            scenario_id: Scenario ID

        Returns:
            Unique session ID string
        """
        npc_part = ",".join(sorted(npc_ids))
        return f"{scenario_id}|{npc_part}"

    def _display_opening(self, session: ConversationSession) -> None:
        """
        Display the opening text for a conversation session.

        Prints scenario title, participating NPCs, and opening narrative.
        Logs the opening to each NPC's conversation history.

        Args:
            session: The conversation session to display opening for
        """
        scenario = session.scenario
        opening = scenario.get("opening", "Conversation begins...")
        npc_role = scenario.get("_npc_role_meta", {})
        role_name = npc_role.get("display_name", "NPC")

        print(f"\n{'=' * 70}")
        print(f"CONVERSATION: {scenario.get('title', 'Untitled')}")
        print(f"NPCs: {', '.join(s.npc.name for s in session.npc_states.values())}")
        print(f"{'=' * 70}\n")

        # Opening text is per-NPC and can use {{NPC_NAME}}
        # Print once, using the first NPC's name for substitution
        first_state = next(iter(session.npc_states.values()))
        opening_visible = self._format_with_npc(opening, first_state.npc.name)
        print(opening_visible + "\n")

        # Log opening per NPC (with their own name substituted)
        for state in session.npc_states.values():
            opening_for_npc = self._format_with_npc(opening, state.npc.name)
            state.add_exchange("Narrator", opening_for_npc)

    # ------------------------------------------------------------------
    # Turn Helpers
    # ------------------------------------------------------------------

    def get_node(self, session: ConversationSession, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node from the session's scenario.

        Args:
            session: Current conversation session
            node_id: ID of the node to retrieve

        Returns:
            Node dict if found, None otherwise
        """
        return ScenarioLoader.get_node(session.scenario, node_id)

    def get_available_choices(self, session: ConversationSession, node_id: str) -> List[Dict[str, Any]]:
        """
        Get all available player choices at a given node.

        Args:
            session: Current conversation session
            node_id: ID of the node to get choices from

        Returns:
            List of choice dicts with index, choice_id, text, and raw data
        """
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
    # Core Turn Step: apply one player choice, then resolve per-NPC routing
    # ------------------------------------------------------------------

    def apply_choice(
        self,
        session: ConversationSession,
        node_id: str,
        choice_index: int,
    ) -> Dict[str, Any]:
        """
        Apply a single player choice (by index) to all active NPCs.

        Flow per NPC:
          1. Parse choice → PlayerDialogueInput
          2. Run through DialogueProcessor (BDI + LLM)
          3. Evaluate current node's transitions against updated NPC state
          4. Route NPC to the resolved target node (or stay if no match)

        This is where the dynamic routing happens: same choice, potentially
        different outcomes for each NPC based on their internal state.

        Args:
            session: Current conversation session
            node_id: ID of the current node
            choice_index: Index of the player's choice (1-based)

        Returns:
            Dict mapping npc_id to {context, resolved_node}

        Raises:
            ValueError: If node_id is invalid or choice_index is out of range
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
        transitions = node.get("transitions", [])

        for state in session.active_npcs():
            print(f"\nPlayer → {state.npc.name}: {player_input.choice_text}")
            state.add_exchange("Player", player_input.choice_text)
            state.choices_made.append(choice_data["choice_id"])

            # --- Step 1-2: Process dialogue through BDI pipeline ---
            state.processor.outcome_index = outcome_index
            context = state.processor.process_dialogue(
                player_input,
                generate_with_ollama=self.use_ollama,
            )

            thought = context["thought_reaction"]
            desire = context["desire_state"]
            intention = context["behavioural_intention"]
            npc_response = context["npc_response"]

            # If npc_response comes from scenario prompts containing parsewords,
            # run it through the formatter for this NPC.
            npc_response = self._format_with_npc(npc_response, state.npc.name)

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
                },
            )

            # --- Step 3: Resolve transitions against this NPC's live state ---
            resolved_node = TransitionResolver.resolve(transitions, state)

            if resolved_node:
                target_node = self.get_node(session, resolved_node)

                # --- Step 4a: Terminal node reached ---
                if target_node and TransitionResolver.is_terminal(target_node):
                    terminal_id = target_node.get("terminal_id", "unknown")
                    terminal_result = target_node.get("terminal_result", "")
                    # Terminal dialogue is generated by the NPC via its prompt,
                    # not hardcoded. Use npc_dialogue_prompt as the LLM's guide.
                    terminal_dialogue = npc_response  # already formatted above

                    state.is_complete = True
                    state.terminal_outcome = {
                        "terminal_id": terminal_id,
                        "result": terminal_result,
                        "final_dialogue": terminal_dialogue,
                    }
                    state.current_node = resolved_node

                    print(f"\n{'=' * 70}")
                    print(f"TERMINAL OUTCOME for {state.npc.name}: {terminal_id.upper()}")
                    print(f"Result: {terminal_result}")
                    print(f"{state.npc.name}: {terminal_dialogue}")
                    print(f"{'=' * 70}\n")

                    state.processor.end_conversation()

                # --- Step 4b: Non-terminal node; advance normally ---
                else:
                    state.current_node = resolved_node
                    print(f"  [{state.npc.name}] → routed to node: {resolved_node}")
            else:
                # No transition matched. Stay on current node if it has choices,
                # or fall through to 'probing' as a default continuation.
                default_node = "probing"
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

    # ------------------------------------------------------------------
    # Session Termination & Export
    # ------------------------------------------------------------------

    def is_session_complete(self, session: ConversationSession) -> bool:
        """
        Check if the conversation session is complete.

        Session ends when all NPCs have reached terminal states.

        Args:
            session: The conversation session to check

        Returns:
            True if all NPCs are complete, False otherwise
        """
        return len(session.active_npcs()) == 0

    def export_session_log(self, session: ConversationSession, filepath: str) -> None:
        """
        Export a rich, per-NPC log backed by each NPC's ConversationModel.

        The exported JSON contains:
        - Scenario metadata
        - Player choice log
        - Per-NPC data:
          - Full conversation model (BDI state trajectory)
          - Choices made by player
          - Visible conversation history
          - Terminal outcome
          - Final NPC state

        Args:
            session: The conversation session to export
            filepath: Path to write the JSON log file
        """
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

        print(f"\n✓ Conversation session log exported to {filepath}")