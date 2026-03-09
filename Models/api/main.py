"""
PNE REST + WebSocket API
========================

Start the server:
    cd Models
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

REST endpoints:
    GET  /npcs                       → list available NPC JSON files
    GET  /scenarios                  → list available scenario JSON files
    POST /sessions                   → create a session, get session_id + opening choices
    GET  /sessions/{id}              → session state snapshot
    GET  /sessions/{id}/choices      → current available choices
    GET  /sessions/{id}/history      → full conversation transcript
    POST /sessions/{id}/save         → persist NPC JSONs to disk now
    DELETE /sessions/{id}            → clean up session

WebSocket:
    WS /sessions/{id}/play
        Client sends: {"choice_index": <int>}   (1-based)
        Server sends: token / turn_result / choices / terminal / error messages
"""

import glob as _glob
import os
import sys

# Ensure Models/ is importable (works whether run from Models/ or its parent)
_MODELS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MODELS_DIR not in sys.path:
    sys.path.insert(0, _MODELS_DIR)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .schema import CreateSessionRequest, ChoicesResponse, ChoiceItem, SaveResponse
from .session_store import store
from .ws_handler import run_ws_turn

app = FastAPI(
    title="Psychological Narrative Engine API",
    description="REST + WebSocket API for driving PNE conversations from Godot / Unity / UE.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_BASE = _MODELS_DIR  # Models/ directory — all paths are resolved relative to this


# ── Helpers ────────────────────────────────────────────────────────────────────

def _choices_payload(choices: list) -> list:
    return [
        {
            "index": c["index"],
            "choice_id": c["choice_id"],
            "text": c["text"],
            "language_art": c["raw"].get("language_art", "neutral"),
            "success_pct": c.get("success_pct", 100),
        }
        for c in choices
    ]


# ── Discovery ──────────────────────────────────────────────────────────────────

@app.get("/npcs", summary="List available NPC files")
def list_npcs():
    npcs_dir = os.path.join(_BASE, "npcs")
    files = _glob.glob(os.path.join(npcs_dir, "*.json"))
    return {"npcs": sorted(os.path.relpath(f, _BASE) for f in files)}


@app.get("/scenarios", summary="List available scenario files")
def list_scenarios():
    scenarios_dir = os.path.join(_BASE, "scenarios")
    files = _glob.glob(os.path.join(scenarios_dir, "*.json"))
    return {"scenarios": sorted(os.path.relpath(f, _BASE) for f in files)}


# ── Session management ─────────────────────────────────────────────────────────

@app.post("/sessions", summary="Create a new conversation session")
def create_session(req: CreateSessionRequest):
    from narrative_engine.engine import NarrativeEngine
    from pne import PlayerSkillSet, Difficulty

    try:
        difficulty = Difficulty[req.difficulty.upper()]
    except KeyError:
        raise HTTPException(400, f"Unknown difficulty '{req.difficulty}'. Valid: SIMPLE, STANDARD, STRICT")

    engine = NarrativeEngine(use_ollama=req.use_ollama, ollama_model=req.ollama_model, difficulty=difficulty)

    # Load NPCs
    npc_ids = []
    npc_file_map: dict = {}  # npc_id → absolute path (for persistence)
    for path in req.npc_paths:
        full = os.path.join(_BASE, path)
        if not os.path.exists(full):
            raise HTTPException(400, f"NPC file not found: {path}")
        try:
            npc_id = engine.load_npc(full)
            npc_ids.append(npc_id)
            npc_file_map[npc_id] = full
        except Exception as exc:
            raise HTTPException(400, f"Failed to load NPC '{path}': {exc}")

    # Load scenario
    scenario_full = os.path.join(_BASE, req.scenario_path)
    if not os.path.exists(scenario_full):
        raise HTTPException(400, f"Scenario file not found: {req.scenario_path}")
    try:
        scenario_id = engine.load_scenario(scenario_full)
    except Exception as exc:
        raise HTTPException(400, f"Failed to load scenario: {exc}")

    # Start session
    try:
        skills = req.player_skills
        player_skills = PlayerSkillSet(
            authority=skills.get("authority", 5),
            diplomacy=skills.get("diplomacy", 5),
            empathy=skills.get("empathy", 5),
            manipulation=skills.get("manipulation", 5),
        )
        conversation = engine.start_session(npc_ids, scenario_id, player_skills)
    except Exception as exc:
        raise HTTPException(500, f"Failed to start session: {exc}")

    api_session = store.create(engine, conversation)
    api_session.npc_file_paths = npc_file_map

    choices = engine.get_available_choices(conversation, "start")

    return {
        "session_id": api_session.session_id,
        "scenario": {
            "id": scenario_id,
            "title": conversation.scenario.get("title", ""),
            "opening": conversation.scenario.get("opening", ""),
        },
        "npcs": [
            {"npc_id": nid, "name": state.npc.name}
            for nid, state in conversation.npc_states.items()
        ],
        "node_id": "start",
        "choices": _choices_payload(choices),
    }


@app.get("/sessions/{session_id}", summary="Get session state snapshot")
def get_session(session_id: str):
    api_session = store.get(session_id)
    if not api_session:
        raise HTTPException(404, "Session not found")

    session = api_session.conversation
    return {
        "session_id": session_id,
        "node_id": api_session.node_id,
        "is_complete": api_session.engine.is_session_complete(session),
        "npcs": {
            npc_id: {
                "name": state.npc.name,
                "judgement": state.judgement,
                "is_complete": state.is_complete,
                "turn_count": state.turn_count,
                "terminal_outcome": state.terminal_outcome,
            }
            for npc_id, state in session.npc_states.items()
        },
        "player_choice_log": session.player_choice_log,
    }


@app.get("/sessions/{session_id}/choices", response_model=ChoicesResponse)
def get_choices(session_id: str):
    api_session = store.get(session_id)
    if not api_session:
        raise HTTPException(404, "Session not found")

    session = api_session.conversation
    engine = api_session.engine
    choices = engine.get_available_choices(session, api_session.node_id)
    active = session.active_npcs()

    return {
        "node_id": api_session.node_id,
        "in_recovery": any(s.recovery_mode for s in active),
        "choices": [
            ChoiceItem(
                index=c["index"],
                choice_id=c["choice_id"],
                text=c["text"],
                language_art=c["raw"].get("language_art", "neutral"),
                success_pct=c.get("success_pct", 100),
            )
            for c in choices
        ],
    }


@app.get("/sessions/{session_id}/history", summary="Get full conversation transcript")
def get_history(session_id: str):
    api_session = store.get(session_id)
    if not api_session:
        raise HTTPException(404, "Session not found")

    session = api_session.conversation
    history = {}
    for npc_id, state in session.npc_states.items():
        history[npc_id] = {
            "npc_name": state.npc.name,
            "entries": state.history,
        }
    return {"session_id": session_id, "history": history}


@app.post("/sessions/{session_id}/save", response_model=SaveResponse,
          summary="Persist NPC state to disk immediately")
def save_session(session_id: str):
    api_session = store.get(session_id)
    if not api_session:
        raise HTTPException(404, "Session not found")

    from .npc_updater import save_all
    saved = save_all(api_session)
    return {"saved": saved}


@app.delete("/sessions/{session_id}", summary="Delete a session")
def delete_session(session_id: str):
    if not store.delete(session_id):
        raise HTTPException(404, "Session not found")
    return {"deleted": session_id}


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/sessions/{session_id}/play")
async def ws_play(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming a conversation turn.

    Client sends: {"choice_index": <1-based int>}
    Server streams: token / turn_result / choices / terminal / error messages
    """
    api_session = store.get(session_id)
    if not api_session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            choice_index = data.get("choice_index")
            if choice_index is None:
                await websocket.send_json({"type": "error", "message": "Missing 'choice_index'"})
                continue

            await run_ws_turn(websocket, api_session, int(choice_index))

            if api_session.engine.is_session_complete(api_session.conversation):
                break

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
