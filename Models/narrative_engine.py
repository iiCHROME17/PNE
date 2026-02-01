"""
Psychological Narrative Engine - Multi-NPC Conversation Engine
name: narrative_engine.py
Author: Jerome Bawa (original), refactor by AI assistant

Fallout-style psychological narrative engine where:
- Player choices are visible and structured (node/choice tree)
- NPC responses are generated via the BDI+LLM pipeline in pne/
- Scenarios are NPC-agnostic; NPC individuality is injected at runtime
- Multiple NPCs can participate independently in the same scenario
- Routing between nodes is DYNAMIC: driven by NPC BDI state + player_relation,
  not hardcoded next_node per choice.
"""

from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, field
import math

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

        NPC-agnostic: defines *potential* micro- and terminal outcomes.
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

        # Terminal outcomes are now resolved at the NODE level via transitions,
        # not per-choice. Choices no longer carry terminal_outcomes.
        # This list will typically be empty.
        terminal_outcomes: List[TerminalOutcome] = []
        for terminal_data in choice_data.get("terminal_outcomes", []):
            condition_str = terminal_data.get("condition", "lambda npc, conv: False")
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
# TRANSITION RESOLVER (OUTCOME-BASED SIMILARITY MATCHING)
# ============================================================================


@dataclass
class OutcomeSignature:
    """Target outcome profile for a transition."""
    intention_keywords: List[str] = field(default_factory=list)  # ["Accept", "Ally", "Trust"]
    desire_types: List[str] = field(default_factory=list)        # ["approach", "cooperate"]
    stance_profile: Dict[str, float] = field(default_factory=dict)  # {"social.empathy": 0.1, "social.assertion": -0.05}
    relation_target: Optional[float] = None  # Ideal relation value (0.0-1.0)
    relation_tolerance: float = 0.2  # How far from target is acceptable
    min_desire_intensity: float = 0.0  # Minimum emotional intensity

    # Weights for scoring (should sum to 1.0)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "intention": 0.30,
        "desire": 0.25,
        "stance": 0.25,
        "relation": 0.20,
    })


class OutcomeMatchingResolver:
    """
    Routes to the next node based on similarity between actual outcome
    and target outcome signatures.
    """

    @staticmethod
    def resolve(
        transitions: List[Dict[str, Any]],
        context: Dict[str, Any],  # The full context from DialogueProcessor
        npc_state: "NPCConversationState",
    ) -> Optional[str]:
        """
        Score each transition by how well it matches the actual outcome.
        Returns the target node with highest confidence above threshold.
        """
        if not transitions:
            return None

        actual_outcome = context.get("interaction_outcome", {}) or {}
        desire_state = context.get("desire_state", {}) or {}
        intention = context.get("behavioural_intention", {}) or {}

        best_match: Optional[str] = None
        best_score: float = -1.0
        min_threshold: float = 0.5  # Default minimum match score

        for trans in transitions:
            signature_data = trans.get("outcome_match", {})
            if not signature_data:
                continue

            signature = OutcomeSignature(**signature_data)
            score = OutcomeMatchingResolver._calculate_score(
                signature=signature,
                actual_outcome=actual_outcome,
                desire_state=desire_state,
                intention=intention,
                npc_state=npc_state,
            )

            confidence_threshold = trans.get("min_confidence", min_threshold)

            if score >= confidence_threshold and score > best_score:
                best_score = score
                best_match = trans["target"]

        if best_match is not None:
            print(f"  [Transition] Matched with confidence {best_score:.2f} → {best_match}")

        return best_match

    @staticmethod
    def _calculate_score(
        signature: OutcomeSignature,
        actual_outcome: Dict[str, Any],
        desire_state: Dict[str, Any],
        intention: Dict[str, Any],
        npc_state: "NPCConversationState",
    ) -> float:
        """Calculate weighted similarity score (0.0 - 1.0)."""
        scores: Dict[str, float] = {}

        # 1. Intention Shift Matching (Keyword overlap on interaction outcome intention_shift OR behavioural intention)
        if signature.intention_keywords:
            actual_intention_text = (
                (actual_outcome.get("intention_shift") or "")
                + " "
                + (intention.get("intention_type") or "")
            ).lower()
            if actual_intention_text.strip():
                matches = sum(
                    1 for k in signature.intention_keywords if k.lower() in actual_intention_text
                )
                scores["intention"] = matches / len(signature.intention_keywords)

        # 2. Desire Type & Intensity Matching
        if signature.desire_types:
            actual_desire_type = desire_state.get("desire_type", "")
            type_match = 1.0 if actual_desire_type in signature.desire_types else 0.0

            intensity = float(desire_state.get("intensity", 0.5))
            if signature.min_desire_intensity > 0:
                intensity_match = (
                    1.0
                    if intensity >= signature.min_desire_intensity
                    else intensity / signature.min_desire_intensity
                )
            else:
                intensity_match = intensity  # normalized 0-1, as provided by the engine

            scores["desire"] = (type_match * 0.7) + (intensity_match * 0.3)

        # 3. Stance Delta Similarity (Cosine similarity on stance_delta)
        if signature.stance_profile:
            actual_stance = actual_outcome.get("stance_delta", {}) or {}
            scores["stance"] = OutcomeMatchingResolver._cosine_similarity(
                signature.stance_profile,
                actual_stance,
            )

        # 4. Relation Proximity (Gaussian falloff from target)
        if signature.relation_target is not None:
            current_relation = getattr(
                npc_state.processor.conversation, "player_relation", 0.5
            )
            distance = abs(current_relation - float(signature.relation_target))
            scores["relation"] = math.exp(
                -((distance ** 2) / (2 * (signature.relation_tolerance ** 2)))
            )

        total_weight = sum(signature.weights.get(k, 0.0) for k in scores.keys())
        if total_weight <= 0.0:
            return 0.0

        weighted_sum = sum(
            scores[k] * signature.weights.get(k, 0.0) for k in scores.keys()
        )
        return weighted_sum / total_weight

    @staticmethod
    def _cosine_similarity(dict1: Dict[str, float], dict2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two sparse vectors."""
        keys = set(dict1.keys()) | set(dict2.keys())
        if not keys:
            return 0.0

        dot = sum(dict1.get(k, 0.0) * dict2.get(k, 0.0) for k in keys)
        norm1 = math.sqrt(sum(v ** 2 for v in dict1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in dict2.values()))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot / (norm1 * norm2)


class TransitionResolver:
    """
    Minimal helper to keep terminal-node detection.
    Old eval-based condition logic has been removed in favor of
    OutcomeMatchingResolver above.
    """

    @staticmethod
    def is_terminal(node: Dict[str, Any]) -> bool:
        """A node is terminal if it has no choices and is explicitly marked."""
        return node.get("terminal", False)


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
    - Player choices are shared; routing is resolved per-NPC via TransitionResolver.
    """

    scenario_id: str
    scenario: Dict[str, Any]
    npc_states: Dict[str, NPCConversationState]  # npc_id -> state

    # Global visible choice history (independent of NPC internals)
    player_choice_log: List[Dict[str, Any]] = field(default_factory=list)

    def active_npcs(self) -> List[NPCConversationState]:
        return [s for s in self.npc_states.values() if not s.is_complete]


# ============================================================================
# NARRATIVE ENGINE (MODULAR, MULTI-NPC, DYNAMIC ROUTING)
# ============================================================================


class NarrativeEngine:
    """
    High-level orchestrator for Fallout-style conversations using pne's BDI engine.

    Key difference from the previous version:
    - Choices no longer have next_node.
    - After a choice is processed, each NPC's state is evaluated against
      the CURRENT node's transitions to determine where that NPC goes next.
    - Different NPCs can end up on different nodes after the same player choice.
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
             using outcome similarity matching
          4. Route NPC to the resolved target node (or default)
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

            # Extract actual outcome for relation updates
            actual_outcome = context.get("interaction_outcome", {}) or {}
            delta = float(actual_outcome.get("relation_delta", 0.0))
            # Initialize player_relation if missing
            current_rel = getattr(state.processor.conversation, "player_relation", 0.5)
            state.processor.conversation.player_relation = current_rel + delta

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
                    "interaction_outcome": actual_outcome,
                },
            )

            # --- NEW: Outcome-based routing ---
            resolved_node = OutcomeMatchingResolver.resolve(
                transitions=transitions,
                context=context,
                npc_state=state,
            )

            if resolved_node:
                target_node = self.get_node(session, resolved_node)

                # Terminal node reached
                if target_node and TransitionResolver.is_terminal(target_node):
                    terminal_id = target_node.get("terminal_id", "unknown")
                    terminal_result = target_node.get("terminal_result", "")
                    terminal_dialogue = npc_response  # could be regenerated with a terminal prompt

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
                else:
                    # Non-terminal: advance normally
                    state.current_node = resolved_node
                    print(f"  [{state.npc.name}] → routed to node: {resolved_node}")
            else:
                # Fallback: if no outcome matched, check for default "stay" or drift to probing
                default_node = node.get("default_transition", "probing")
                if self.get_node(session, default_node):
                    state.current_node = default_node
                    print(
                        f"  [{state.npc.name}] → no outcome match, defaulting to: {default_node}"
                    )
                else:
                    print(
                        f"  [{state.npc.name}] → no outcome match and no default; staying on: {node_id}"
                    )

            responses[state.npc_id] = {
                "context": context,
                "resolved_node": state.current_node,
                # For now we don't expose raw confidence; add later if needed.
            }

        return responses

    # ------------------------------------------------------------------
    # Session Termination & Export
    # ------------------------------------------------------------------

    def is_session_complete(self, session: ConversationSession) -> bool:
        """Session ends when all NPCs are complete."""
        return len(session.active_npcs()) == 0

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
# SIMPLE CLI (multi-NPC aware)
# ============================================================================


def main() -> None:
    """
    Minimal CLI entry-point.

    Usage:
        python narrative_engine.py <npc_file1.json> [npc_file2.json ...] <scenario_file.json> [--no-ollama]

    NPCs can diverge to different nodes after the same player choice.
    The CLI tracks per-NPC current nodes and only shows choices for nodes
    that still have active NPCs on them.
    """
    import sys

    print("=" * 70)
    print("PSYCHOLOGICAL NARRATIVE ENGINE - MULTI-NPC CONVERSATION SIMULATOR")
    print("=" * 70)

    if len(sys.argv) < 3:
        print("\nUsage: python narrative_engine.py <npc1.json> [npc2.json ...] <scenario.json> [--no-ollama]")
        print("\nExample:")
        print("  python narrative_engine.py morisson_moses.json door_guard_scenario.json")
        print("  python narrative_engine.py moses.json taylor.json door_guard_scenario.json")
        print("\nOptional flags:")
        print("  --no-ollama : Disable Ollama integration (use fallback responses)")
        return

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

        # CLI loop: all active NPCs share choices from a common node.
        # If NPCs diverge, we pick the node of the first active NPC.
        # (For a richer multi-NPC UI, you'd want per-NPC choice prompts.)
        while not engine.is_session_complete(session):
            active = session.active_npcs()
            if not active:
                break

            # Use the first active NPC's current node as the shared choice node.
            # In practice, if NPCs diverge you'd want a more sophisticated UI.
            current_node = active[0].current_node
            choices = engine.get_available_choices(session, current_node)

            if not choices:
                print("\n[No available choices at this node; conversation ends.]")
                break

            print(f"\n--- Node: {current_node} ---")
            print("Available choices:")
            for c in choices:
                print(f"  [{c['index']}] {c['text']}")

            # Show which NPCs are active and where they are
            if len(active) > 1:
                print("\n  Active NPCs:")
                for s in active:
                    print(f"    {s.npc.name} → node: {s.current_node}")

            try:
                user_input = input("\nYour choice (number or 'quit'): ").strip()
                if user_input.lower() in {"q", "quit", "exit"}:
                    print("\nConversation ended by player.")
                    break

                choice_num = int(user_input)
                engine.apply_choice(session, current_node, choice_num)

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