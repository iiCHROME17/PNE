"""
WebSocket turn handler for the PNE API.

Bridges the synchronous NarrativeEngine with an async WebSocket connection,
streaming Ollama tokens to the client in real time.

Message flow (server → client):
  {"type": "player_choice", "choice_id": str, "text": str,
   "language_art": str}                                              -- immediately on choice receipt
  {"type": "token",       "npc": str, "token": str}                -- while Ollama streams
  {"type": "turn_result", "npc": str, "npc_id": str,
   "thought": {}, "desire": {}, "intention": {},
   "outcome": {}, "judgement": int, "npc_response": str,
   "dice": {"player_die": int, "npc_die": int, "success": bool,
            "skill": str, "success_pct": int,
            "risk_multiplier": float, "judgement_delta": int},
   "entered_recovery": bool}                                        -- after BDI cycle per NPC
  {"type": "choices",     "node_id": str, "in_recovery": bool,
   "choices": [...]}                                                -- next turn choices
  {"type": "terminal",    "npc": str, "terminal_id": str,
   "result": str, "final_dialogue": str}                           -- on terminal node
  {"type": "error",       "message": str}                          -- on failure
"""

import asyncio
from typing import Any


def _serialize_context_field(value: Any) -> Any:
    """Convert a BDI context value to a JSON-serialisable dict."""
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        return vars(value)
    except TypeError:
        return {}


def _choice_to_dict(c: dict) -> dict:
    return {
        "index": c["index"],
        "choice_id": c["choice_id"],
        "text": c["text"],
        "language_art": c["raw"].get("language_art", "neutral"),
        "success_pct": c.get("success_pct", 100),
    }


async def run_ws_turn(websocket, api_session, choice_index: int) -> None:
    """
    Execute one player turn, streaming Ollama tokens over the WebSocket.

    Parameters
    ----------
    websocket   : FastAPI WebSocket
    api_session : APISession from session_store
    choice_index: 1-based index matching the list returned by get_available_choices
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    # Sentinel object that signals the streaming thread is done
    _DONE = object()

    engine = api_session.engine
    session = api_session.conversation

    # -- Echo the player's choice immediately, before Ollama starts --
    choices_now = engine.get_available_choices(session, api_session.node_id)
    chosen = next((c for c in choices_now if c["index"] == choice_index), None)
    if chosen:
        await websocket.send_json({
            "type": "player_choice",
            "choice_id": chosen["choice_id"],
            "text": chosen["text"],
            "language_art": chosen["raw"].get("language_art", "neutral"),
        })

    def on_token(npc_name: str, token: str) -> None:
        """Called from the sync thread; routes tokens to the async queue."""
        loop.call_soon_threadsafe(queue.put_nowait, (npc_name, token))

    def run_sync():
        """Wraps apply_choice so we always push a sentinel when done."""
        try:
            return engine.apply_choice(
                session,
                api_session.node_id,
                choice_index,
                on_token=on_token,
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, _DONE)

    # Start the synchronous engine turn in a thread pool
    future = loop.run_in_executor(None, run_sync)

    # Stream tokens to the WebSocket while the thread runs
    while True:
        item = await queue.get()
        if item is _DONE:
            break
        npc_name, token = item
        await websocket.send_json({"type": "token", "npc": npc_name, "token": token})

    # Await the thread result
    try:
        responses = await future
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        return

    # Send per-NPC turn_result messages (enriched with dice + entered_recovery)
    for npc_id, npc_resp in responses.items():
        ctx = npc_resp.get("context", {})
        state = session.npc_states.get(npc_id)
        if not state:
            continue

        # Get the actual displayed response from history (post-Ollama)
        npc_response = ""
        for entry in reversed(state.history):
            if entry.get("speaker") == state.npc.name:
                npc_response = entry.get("text", "")
                break

        await websocket.send_json({
            "type": "turn_result",
            "npc": state.npc.name,
            "npc_id": npc_id,
            "thought": _serialize_context_field(ctx.get("thought_reaction")),
            "desire": _serialize_context_field(ctx.get("desire_state")),
            "intention": _serialize_context_field(ctx.get("behavioural_intention")),
            "outcome": _serialize_context_field(ctx.get("interaction_outcome")),
            "judgement": state.judgement,
            "npc_response": npc_response,
            "dice": npc_resp.get("dice"),
            "entered_recovery": npc_resp.get("entered_recovery", False),
        })

    # Check for terminals
    for npc_id, state in session.npc_states.items():
        if state.terminal_outcome:
            await websocket.send_json({
                "type": "terminal",
                "npc": state.npc.name,
                "npc_id": npc_id,
                **state.terminal_outcome,
            })

    # Auto-save NPC JSONs when the entire session reaches a terminal state
    if engine.is_session_complete(session):
        from .npc_updater import save_all
        save_all(api_session)

    # If any NPCs are still active, send choices for the next turn
    active = session.active_npcs()
    if active:
        primary = active[0]
        api_session.node_id = primary.current_node
        choices = engine.get_available_choices(session, api_session.node_id)
        await websocket.send_json({
            "type": "choices",
            "node_id": api_session.node_id,
            "in_recovery": any(s.recovery_mode for s in active),
            "choices": [_choice_to_dict(c) for c in choices],
        })
