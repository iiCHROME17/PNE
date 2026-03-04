"""
Command-Line Interface Module

Provides a simple CLI for running multi-NPC conversations via the Narrative Engine.

Usage:
    python -m narrative_engine.cli <npc1.json> [npc2.json ...] <scenario.json> [--no-ollama]

Examples:
    # Single NPC conversation
    python -m narrative_engine.cli morisson_moses.json door_guard_scenario.json

    # Multi-NPC conversation
    python -m narrative_engine.cli moses.json taylor.json door_guard_scenario.json

    # Disable Ollama (use fallback responses)
    python -m narrative_engine.cli moses.json scenario.json --no-ollama

The CLI provides:
- Interactive choice selection
- Real-time display of NPC thoughts, desires, and intentions
- Per-NPC routing visualization
- Conversation log export on completion
"""

from typing import List
import sys

from pne import PlayerSkillSet, Difficulty
from .engine import NarrativeEngine


def main() -> None:
    """
    Minimal CLI entry-point for multi-NPC conversations.

    Parses command-line arguments, loads NPCs and scenario, and runs
    an interactive conversation loop.

    NPCs can diverge to different nodes after the same player choice.
    The CLI tracks per-NPC current nodes and only shows choices for nodes
    that still have active NPCs on them.

    Command-line args:
        npc_files: One or more NPC JSON files
        scenario_file: Scenario JSON file (last positional arg)
        --no-ollama: Optional flag to disable Ollama integration
    """
    print("=" * 70)
    print("PSYCHOLOGICAL NARRATIVE ENGINE - MULTI-NPC CONVERSATION SIMULATOR")
    print("=" * 70)

    if len(sys.argv) < 3:
        print("\nUsage: python -m narrative_engine.cli <npc1.json> [npc2.json ...] <scenario.json> [--no-ollama]")
        print("\nExample:")
        print("  python -m narrative_engine.cli morisson_moses.json door_guard_scenario.json")
        print("  python -m narrative_engine.cli moses.json taylor.json door_guard_scenario.json")
        print("\nOptional flags:")
        print("  --no-ollama              : Disable Ollama (use fallback responses)")
        print("  --difficulty=<level>     : simple | standard (default) | strict")
        return

    raw_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(raw_args) < 2:
        print("Error: need at least one NPC file and one scenario file.")
        return

    *npc_files, scenario_file = raw_args
    use_ollama = "--no-ollama" not in sys.argv

    # Parse --difficulty=<simple|standard|strict>  (default: standard)
    difficulty = Difficulty.STANDARD
    for arg in sys.argv[1:]:
        if arg.startswith("--difficulty="):
            level = arg.split("=", 1)[1].strip().upper()
            try:
                difficulty = Difficulty[level]
            except KeyError:
                print(f"Unknown difficulty '{level}'. Options: simple, standard, strict.")
                return

    try:
        engine = NarrativeEngine(use_ollama=use_ollama, difficulty=difficulty)
        print(f"Difficulty: {difficulty.value.upper()}")

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

            # Judgement bar
            j = active[0].judgement
            filled = j // 10
            bar = "▓" * filled + "░" * (10 - filled)
            print(f"\n  Judgement: [{bar}] {j}/100")

            if active[0].recovery_mode:
                print("  >> RECOVERY — choose your follow-up:")
            else:
                print(f"\n--- Node: {current_node} ---")

            print("Available choices:")
            for c in choices:
                print(f"  [{c['index']}] {c['text']} | ({c.get('success_pct', 100)}%)")

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