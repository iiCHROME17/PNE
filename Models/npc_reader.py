#!/usr/bin/env python3
"""
CLI tool to inspect a single NPC JSON definition.

Usage:
    python npc_reader.py npcs/morisson_moses.json
"""

import argparse
import os
import sys
from typing import Any

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import NPCModel from existing models (module is Models/PNE_Models.py)
from Models.PNE_Models import NPCModel


def _print_header(title: str):
    print(f"\n=== {title} ===")


def _safe_get(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely walk attributes using dot-notation, returning default on failure.
    Example: _safe_get(npc, "social.wildcard")
    """
    try:
        parts = path.split(".")
        cur = obj
        for p in parts:
            cur = getattr(cur, p)
        return cur
    except Exception:
        return default


def describe_npc(npc: NPCModel):
    print(f"\nNPC: {npc.name} (Age: {npc.age})")

    # Cognitive
    _print_header("Cognitive")
    print(f"  Self-esteem:       {npc.cognitive.self_esteem:.2f}")
    print(f"  Locus of control:  {npc.cognitive.locus_of_control:.2f}")
    print(f"  Cog. flexibility:  {npc.cognitive.cog_flexibility:.2f}")

    # Social
    _print_header("Social / Personality")
    print(f"  Faction:           {_safe_get(npc, 'social.faction', 'N/A')}")
    print(f"  Position:          {_safe_get(npc, 'social.social_position').value}")
    print(f"  Wildcard:          {_safe_get(npc, 'social.wildcard', 'None')}")
    print(f"  Assertion:         {npc.social.assertion:.2f}")
    print(f"  Conformity/Indep.: {npc.social.conf_indep:.2f}")
    print(f"  Empathy:           {npc.social.empathy:.2f}")

    dominant_ideology = npc.social.get_dominant_ideology()
    print(f"  Dominant ideology: {dominant_ideology or 'N/A'}")
    if npc.social.ideology:
        print("  Ideology weights:")
        for k, v in sorted(npc.social.ideology.items(), key=lambda kv: -kv[1]):
            print(f"    - {k}: {v:.2f}")

    # World / Relationship
    _print_header("World / Relationship")
    print(f"  Player relation:   {npc.world.player_relation:.2f}")
    print(f"  Faction ref:       {npc.world.faction_ref or 'N/A'}")
    print(f"  World history ref: {npc.world.world_history_ref or 'N/A'}")

    if npc.world.known_events:
        print("  Known events:")
        for ev in npc.world.known_events:
            print(f"    - {ev}")

    if npc.world.personal_history:
        _print_header("Personal History")
        print(npc.world.personal_history)

    if npc.world.player_history:
        _print_header("Player History")
        print(npc.world.player_history)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="View a single NPC JSON definition."
    )
    parser.add_argument(
        "npc_json",
        help="Path to NPC JSON file (e.g. npcs/morisson_moses.json)",
    )
    args = parser.parse_args(argv)

    npc_path = args.npc_json
    if not os.path.exists(npc_path):
        print(f"Error: file not found: {npc_path}", file=sys.stderr)
        return 1

    try:
        npc = NPCModel.from_json(npc_path)
    except Exception as e:
        print(f"Error: failed to load NPC from '{npc_path}': {e}", file=sys.stderr)
        return 1

    describe_npc(npc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
