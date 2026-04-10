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
from fastapi.responses import HTMLResponse

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


# ── Dev Dashboard ──────────────────────────────────────────────────────────────

@app.get("/dev", response_class=HTMLResponse, include_in_schema=False)
def dev_dashboard():
    from config import OLLAMA_MODEL, OLLAMA_URL

    session_ids = store.list_ids()
    sessions_html = ""
    for sid in session_ids:
        s = store.get(sid)
        if not s:
            continue
        npcs = s.conversation.npc_states
        npc_rows = "".join(
            f"<tr><td>{nid}</td><td>{st.npc.name}</td>"
            f"<td>{st.judgement:.1f}</td>"
            f"<td>{'✓' if st.is_complete else '…'}</td>"
            f"<td>{st.turn_count}</td></tr>"
            for nid, st in npcs.items()
        )
        sessions_html += f"""
        <div class="card">
          <div class="card-header">
            <code>{sid}</code>
            <span class="badge">node: {s.node_id}</span>
          </div>
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Judgement</th><th>Done</th><th>Turns</th></tr></thead>
            <tbody>{npc_rows}</tbody>
          </table>
        </div>"""

    if not sessions_html:
        sessions_html = "<p class='muted'>No active sessions.</p>"

    npcs_dir = os.path.join(_BASE, "npcs")
    scenarios_dir = os.path.join(_BASE, "scenarios")
    npc_files = sorted(os.path.basename(f) for f in _glob.glob(os.path.join(npcs_dir, "*.json")))
    scenario_files = sorted(os.path.basename(f) for f in _glob.glob(os.path.join(scenarios_dir, "*.json")))

    npc_list = "".join(f"<li>{f}</li>" for f in npc_files) or "<li class='muted'>None found</li>"
    scenario_list = "".join(f"<li>{f}</li>" for f in scenario_files) or "<li class='muted'>None found</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PNE Dev Dashboard</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; }}
    h1 {{ color: #58a6ff; margin-bottom: 0.25rem; }}
    h2 {{ color: #8b949e; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em;
          margin: 1.5rem 0 0.5rem; }}
    .meta {{ color: #8b949e; font-size: 0.8rem; margin-bottom: 1.5rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center;
                    margin-bottom: 0.75rem; font-size: 0.8rem; }}
    .badge {{ background: #21262d; border: 1px solid #30363d; border-radius: 4px;
              padding: 2px 8px; font-size: 0.75rem; color: #8b949e; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
    th {{ color: #8b949e; text-align: left; padding: 4px 8px; border-bottom: 1px solid #30363d; }}
    td {{ padding: 4px 8px; }}
    tr:hover td {{ background: #21262d; }}
    ul {{ list-style: none; font-size: 0.82rem; }}
    li {{ padding: 3px 0; border-bottom: 1px solid #21262d; }}
    .config-row {{ display: flex; justify-content: space-between; font-size: 0.82rem;
                   padding: 4px 0; border-bottom: 1px solid #21262d; }}
    .config-row span:first-child {{ color: #8b949e; }}
    .config-row span:last-child {{ color: #79c0ff; }}
    .muted {{ color: #484f58; }}
    a {{ color: #58a6ff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .pill {{ display: inline-block; background: #1f6feb33; color: #58a6ff;
             border: 1px solid #1f6feb; border-radius: 12px; padding: 2px 10px;
             font-size: 0.75rem; margin-right: 0.5rem; }}
    footer {{ margin-top: 2rem; font-size: 0.75rem; color: #484f58; }}
    .toolbar {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
    .refresh-btn {{ background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
                    padding: 4px 14px; border-radius: 6px; cursor: pointer; font-family: monospace;
                    font-size: 0.8rem; }}
    .refresh-btn:hover {{ background: #30363d; }}
    .toggle-row {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: #8b949e; }}
    .toggle {{ position: relative; width: 36px; height: 20px; }}
    .toggle input {{ opacity: 0; width: 0; height: 0; }}
    .slider {{ position: absolute; inset: 0; background: #21262d; border: 1px solid #30363d;
               border-radius: 20px; cursor: pointer; transition: background 0.2s; }}
    .slider:before {{ content: ""; position: absolute; width: 14px; height: 14px; left: 2px; top: 2px;
                      background: #8b949e; border-radius: 50%; transition: transform 0.2s; }}
    input:checked + .slider {{ background: #1f6feb44; border-color: #1f6feb; }}
    input:checked + .slider:before {{ background: #58a6ff; transform: translateX(16px); }}
    .warn-banner {{ display: none; background: #3d1f00; border: 1px solid #f0883e55;
                    color: #f0883e; border-radius: 6px; padding: 6px 12px; font-size: 0.78rem; }}
  </style>
  <script>
    const STORAGE_KEY = 'pne_manual_refresh';
    let autoTimer = null;

    function isManual() {{
      const v = localStorage.getItem(STORAGE_KEY);
      return v === null ? true : v === 'true';  // default ON
    }}

    function applyState(manual) {{
      localStorage.setItem(STORAGE_KEY, manual);
      document.getElementById('toggle-input').checked = manual;
      document.getElementById('warn-banner').style.display = manual ? 'none' : 'block';
      document.getElementById('status-text').textContent =
        manual ? 'Manual refresh' : 'Auto-refresh (5s)';
      if (autoTimer) {{ clearInterval(autoTimer); autoTimer = null; }}
      if (!manual) {{ autoTimer = setInterval(() => location.reload(), 5000); }}
    }}

    function onToggle(checked) {{
      if (!checked) {{
        if (!confirm('Disable manual refresh?\\n\\nAuto-refresh will poll the server every 5 seconds.\\nDo NOT use this during demos — it will flood the server log.')) {{
          document.getElementById('toggle-input').checked = true;
          return;
        }}
      }}
      applyState(checked);
    }}

    window.addEventListener('DOMContentLoaded', () => applyState(isManual()));
  </script>
</head>
<body>
  <h1>PNE Dev Dashboard</h1>
  <div class="toolbar">
    <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
    <div class="toggle-row">
      <label class="toggle">
        <input type="checkbox" id="toggle-input" onchange="onToggle(this.checked)">
        <span class="slider"></span>
      </label>
      <span id="status-text">Manual refresh</span>
    </div>
    <span style="color:#484f58;font-size:0.75rem">
      &nbsp;|&nbsp; <a href="/docs">Swagger UI</a> &nbsp;|&nbsp; <a href="/redoc">ReDoc</a>
    </span>
  </div>
  <div class="warn-banner" id="warn-banner">
    Auto-refresh is ON — server log will be noisy. Do not use this during demos.
  </div>

  <h2>Config</h2>
  <div class="card" style="max-width:420px">
    <div class="config-row"><span>Ollama model</span><span>{OLLAMA_MODEL}</span></div>
    <div class="config-row"><span>Ollama URL</span><span>{OLLAMA_URL}</span></div>
    <div class="config-row"><span>Active sessions</span><span>{len(session_ids)}</span></div>
  </div>

  <h2>Active Sessions</h2>
  {sessions_html}

  <h2>Assets</h2>
  <div class="grid">
    <div class="card">
      <div class="card-header">NPCs <span class="badge">{len(npc_files)}</span></div>
      <ul>{npc_list}</ul>
    </div>
    <div class="card">
      <div class="card-header">Scenarios <span class="badge">{len(scenario_files)}</span></div>
      <ul>{scenario_list}</ul>
    </div>
  </div>

  <h2>Endpoints</h2>
  <div class="card" style="font-size:0.8rem; line-height:1.8">
    <span class="pill">GET</span> /npcs &nbsp; <span class="pill">GET</span> /scenarios<br>
    <span class="pill">POST</span> /sessions &nbsp;
    <span class="pill">GET</span> /sessions/{{id}} &nbsp;
    <span class="pill">GET</span> /sessions/{{id}}/choices &nbsp;
    <span class="pill">GET</span> /sessions/{{id}}/history<br>
    <span class="pill">POST</span> /sessions/{{id}}/save &nbsp;
    <span class="pill">DELETE</span> /sessions/{{id}}<br>
    <span class="pill">WS</span> /sessions/{{id}}/play
  </div>

  <footer>PNE API v1.0.0 &nbsp;·&nbsp; {len(session_ids)} session(s) in memory</footer>
</body>
</html>"""
    return HTMLResponse(content=html)


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
