#!/usr/bin/env python3
"""
Prompt Checker / Prompt Debugger

Usage:
    python prompt_debugger.py npcs/morisson_moses.json scenarios/door_guard.json

This runs a single turn of the BDI pipeline (for one NPC and one scenario node),
then prints the EXACT prompt that would be sent to Ollama, without actually
calling Ollama.
"""

import argparse
import os
import sys
from typing import Any, Dict, List

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core models / engine
from Models.PNE_Models import NPCModel  # type: ignore
from pne import (
    PlayerSkillSet,
    PlayerDialogueInput,
)
# These imports will now correctly find the narrative_engine/ package
from narrative_engine import NarrativeEngine, ScenarioLoader  # type: ignore
from narrative_engine.session import NPCConversationState  # type: ignore
from pne.ollama_integration import OllamaResponseGenerator  # type: ignore


def _pick_index(items: List[Dict[str, Any]], label: str) -> int:
    """Simple CLI index picker (1-based)."""
    print(f"\nSelect {label}:")
    for idx, item in enumerate(items, start=1):
        print(f"  [{idx}] {item.get('text', item.get('id', 'unknown'))}")
    while True:
        choice = input(f"\n{label} number: ").strip()
        try:
            val = int(choice)
            if 1 <= val <= len(items):
                return val - 1
        except ValueError:
            pass
        print("Enter a valid number.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Prompt checker for PNE Ollama integration."
    )
    parser.add_argument("npc_json", help="Path to NPC JSON file")
    parser.add_argument("scenario_json", help="Path to scenario JSON file")
    args = parser.parse_args(argv)

    npc_path = args.npc_json
    scen_path = args.scenario_json

    if not os.path.exists(npc_path):
        print(f"NPC file not found: {npc_path}", file=sys.stderr)
        return 1
    if not os.path.exists(scen_path):
        print(f"Scenario file not found: {scen_path}", file=sys.stderr)
        return 1

    # Load NPC and scenario
    npc = NPCModel.from_json(npc_path)
    scenario = ScenarioLoader.load_scenario(scen_path)

    # Build a minimal NarrativeEngine-like context (single NPC)
    player_skills = PlayerSkillSet(authority=5, diplomacy=5, empathy=5, manipulation=5)

    # Use the real NarrativeEngine - MUST register NPC first
    engine = NarrativeEngine(use_ollama=False)
    
    # Register NPC with engine (this was missing!)
    npc_id = engine.load_npc(npc_path)

    # Choose node
    nodes = scenario.get("nodes", [])
    if not nodes:
        print("Scenario has no nodes.", file=sys.stderr)
        return 1

    node_idx = _pick_index(nodes, "node")
    node = nodes[node_idx]
    node_id = node.get("id", f"node_{node_idx}")
    print(f"\nSelected node: {node_id}")

    choices = node.get("choices", [])
    if not choices:
        print("Selected node has no choices.", file=sys.stderr)
        return 1

    choice_idx = _pick_index(choices, "choice")
    choice_data = choices[choice_idx]
    print(f"\nSelected choice_id: {choice_data.get('choice_id')}")

    # Build PlayerDialogueInput and OutcomeIndex
    player_input: PlayerDialogueInput = ScenarioLoader.parse_player_input(choice_data)
    from pne.outcomes import OutcomeIndex  # local import to avoid circulars
    outcome_index: OutcomeIndex = ScenarioLoader.parse_outcome_index(choice_data)

    # Build a temporary DialogueProcessor via NarrativeEngine logic
    scenario_id = engine.load_scenario(scen_path)
    session = engine.start_session(
        npc_ids=[npc_id],  # Use the registered npc_id
        scenario_id=scenario_id,
        player_skills=player_skills,
    )
    state: NPCConversationState = list(session.npc_states.values())[0]
    state.processor.outcome_index = outcome_index

    # Run BDI pipeline up to interaction_outcome, but DO NOT call Ollama
    ctx = state.processor.process_dialogue(
        player_input,
        generate_with_ollama=False,  # use min/max interpolation, we ignore the string
    )

    thought_reaction = ctx["thought_reaction"]
    desire_state = ctx["desire_state"]
    behavioural_intention = ctx["behavioural_intention"]
    interaction_outcome = ctx["interaction_outcome"]

    print("\n=== BDI SNAPSHOT ===")
    print(f"Belief:   {thought_reaction['subjective_belief']}")
    print(f"Desire:   {desire_state['immediate_desire']} "
          f"(type={desire_state['desire_type']}, intensity={desire_state['intensity']:.2f})")
    print(f"Intention:{behavioural_intention['intention_type']} "
          f"(conf={behavioural_intention['confrontation_level']:.2f}, "
          f"expr={behavioural_intention['emotional_expression']})")

    # Rebuild proper ThoughtReaction/BehaviouralIntention objects for prompt builder
    from pne.cognitive import ThoughtReaction as TR  # type: ignore
    from pne.social import BehaviouralIntention as BI  # type: ignore
    from pne.outcomes import InteractionOutcome as IO  # type: ignore

    tr_obj = TR(
        internal_thought=thought_reaction["internal_thought"],
        subjective_belief=thought_reaction["subjective_belief"],
        cognitive_state=thought_reaction["cognitive_state"],
        emotional_valence=thought_reaction["emotional_valence"],
    )
    bi_obj = BI(
        intention_type=behavioural_intention["intention_type"],
        confrontation_level=behavioural_intention["confrontation_level"],
        emotional_expression=behavioural_intention["emotional_expression"],
        wildcard_triggered=behavioural_intention.get("wildcard_triggered", False),
    )
    io_obj = IO(
        outcome_id=interaction_outcome["outcome_id"],
        stance_delta=interaction_outcome["stance_delta"],
        relation_delta=interaction_outcome["relation_delta"],
        intention_shift=interaction_outcome["intention_shift"],
        min_response=interaction_outcome["min_response"],
        max_response=interaction_outcome["max_response"],
        scripted=interaction_outcome.get("scripted", False),
    )

    # Build the prompt using the same generator, but without HTTP call.
    gen = OllamaResponseGenerator()
    prompt = gen._build_prompt(  # type: ignore[attr-defined]
        npc=npc,
        thought_reaction=tr_obj,
        behavioural_intention=bi_obj,
        interaction_outcome=io_obj,
        conversation_history=state.processor.conversation.history,
    )

    print("\n\n=== OLLAMA PROMPT ===\n")
    print(prompt)
    print("\n=== END PROMPT ===")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
