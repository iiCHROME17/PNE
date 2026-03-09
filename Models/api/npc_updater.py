"""
NPC JSON persistence layer.

Writes updated NPC state back to the original .json files after a conversation ends,
preserving changes to player_relation, cognitive/social attributes, and appending a
summary of the terminal outcome to player_history.

Called automatically by ws_handler when all NPCs reach a terminal outcome.
Also exposed via POST /sessions/{id}/save for manual / graceful-quit scenarios.
"""

import json
import os
from datetime import date
from typing import Any, Dict, List, Optional


def save_npc(
    npc_id: str,
    npc: Any,                              # NPCModel instance
    file_path: str,
    terminal_outcome: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Serialise the current NPC state and write it back to its source JSON file.

    Parameters
    ----------
    npc_id          : internal ID (used for logging)
    npc             : live NPCModel — all attribute changes (relation, stance_delta) are in here
    file_path       : absolute path to the original NPC JSON file
    terminal_outcome: dict with terminal_id, result, final_dialogue (or None for mid-save)
    """
    if not file_path or not os.path.exists(os.path.dirname(file_path) or "."):
        print(f"[npc_updater] Skipping '{npc_id}' — file path invalid: {file_path}")
        return

    try:
        data: Dict[str, Any] = npc.to_dict()
    except Exception as exc:
        print(f"[npc_updater] Could not serialise NPC '{npc_id}': {exc}")
        return

    # Append terminal outcome to player_history
    if terminal_outcome:
        today = date.today().isoformat()
        tid   = terminal_outcome.get("terminal_id", "UNKNOWN").upper()
        result = terminal_outcome.get("result", "")
        note  = f"[{today}] {tid}: {result}"

        existing = data.get("world", {}).get("player_history", "")
        data.setdefault("world", {})["player_history"] = (
            (existing.strip() + "\n" + note).strip() if existing.strip() else note
        )

    try:
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"[npc_updater] Saved '{npc_id}' → {file_path}")
    except Exception as exc:
        print(f"[npc_updater] Failed to write '{npc_id}': {exc}")


def save_all(api_session: Any) -> List[str]:
    """
    Save every NPC in the session back to disk.

    Returns a list of npc_ids that were successfully written.
    """
    saved: List[str] = []
    for npc_id, state in api_session.conversation.npc_states.items():
        path = api_session.npc_file_paths.get(npc_id)
        if not path:
            print(f"[npc_updater] No file path registered for '{npc_id}' — skipping")
            continue
        save_npc(npc_id, state.npc, path, state.terminal_outcome)
        saved.append(npc_id)
    return saved
