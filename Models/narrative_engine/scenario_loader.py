"""
Scenario Loader Module

Handles loading and parsing of NPC-agnostic scenario JSON files.
Scenarios define the conversation structure (nodes, choices, transitions)
independently of specific NPC personalities.

Key Components:
- ScenarioLoader: Main class for loading and parsing scenario files
- JSON parsing utilities for intents, roles, player inputs, and outcomes
"""

from typing import Dict, List, Optional, Any
import json

from pne import (
    NPCIntent,
    OutcomeIndex,
    InteractionOutcome,
    TerminalOutcome,
    TerminalOutcomeType,
    PlayerDialogueInput,
    LanguageArt,
)


class ScenarioLoader:
    """
    Loads generic, NPC-independent scenario JSON.

    Scenarios define the conversation flow without being tied to specific NPCs.
    NPC personality and state are injected at runtime during session creation.

    Methods:
        load_scenario: Load scenario from JSON file
        get_node: Retrieve a specific node by ID
        parse_npc_intent: Parse high-level NPC intent for the scenario
        parse_npc_role: Parse NPC role metadata (display name, etc.)
        parse_player_input: Convert choice JSON to PlayerDialogueInput
        parse_outcome_index: Build OutcomeIndex from choice metadata
    """

    @staticmethod
    def load_scenario(filepath: str) -> Dict[str, Any]:
        """
        Load a scenario from a JSON file.

        Args:
            filepath: Path to the scenario JSON file

        Returns:
            Dict containing the complete scenario data structure

        Raises:
            FileNotFoundError: If the scenario file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_node(scenario: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific node from the scenario by its ID.

        Args:
            scenario: The loaded scenario dictionary
            node_id: The unique identifier for the node to retrieve

        Returns:
            Dict containing the node data, or None if not found
        """
        for node in scenario.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    @staticmethod
    def parse_npc_intent(data: Dict[str, Any]) -> NPCIntent:
        """
        Parse scenario-defined high-level intent for NPCs.

        This intent is NPC-agnostic and gets combined with each NPC's
        individual personality during runtime.

        Args:
            data: Dict containing intent fields (baseline_belief, long_term_desire, etc.)

        Returns:
            NPCIntent object with the parsed intent data
        """
        return NPCIntent(
            baseline_belief=data.get("baseline_belief", ""),
            long_term_desire=data.get("long_term_desire", ""),
            immediate_intention=data.get("immediate_intention", ""),
            stakes=data.get("stakes", ""),
        )

    @staticmethod
    def parse_npc_role(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse lightweight role metadata for how the NPC is presented.

        This is NPC-agnostic; it just names the 'role' (e.g., 'Door Guard')
        without tying it to a specific NPC's personality.

        Args:
            data: Dict containing role information

        Returns:
            Dict with role metadata (display_name, etc.)
        """
        return {
            "display_name": data.get("display_name", "NPC"),
        }

    @staticmethod
    def parse_player_input(choice_data: Dict[str, Any]) -> PlayerDialogueInput:
        """
        Convert a choice JSON blob into structured player input.

        Parses all the linguistic and tonal components of a player choice,
        including language art, authority/diplomacy/empathy/manipulation tones,
        and contextual references.

        Args:
            choice_data: Dict containing choice text and metadata

        Returns:
            PlayerDialogueInput object ready for processing by DialogueProcessor
        """
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
    def parse_outcome_index(
        choice_data: Dict[str, Any],
        outcome_key: str = "interaction_outcomes",
    ) -> OutcomeIndex:
        """
        Build an OutcomeIndex from choice metadata.

        NPC-agnostic: defines *potential* micro- and terminal outcomes.
        The DialogueProcessor + NPC state decide which ones actually trigger.

        Terminal outcomes are now resolved at the NODE level via transitions,
        not per-choice. The terminal_outcomes list in choices is typically empty.

        Args:
            choice_data: Dict containing choice outcomes metadata
            outcome_key: Key to read outcomes from — "interaction_outcomes" (default)
                         or "failure_outcomes" for dice-check failure branches.

        Returns:
            OutcomeIndex with all potential interaction and terminal outcomes
        """
        interaction_outcomes: List[InteractionOutcome] = []
        for outcome_data in choice_data.get(outcome_key, []):
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
        # not per-choice. This list will typically be empty.
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