## PNE API Client — Godot 4 example
##
## Drop this script on a Node, set api_base_url to point at your server,
## then call start_session() and connect to the signals to drive the UI.
##
## Usage:
##   var pne = $PNEClient
##   pne.start_session(["npcs/troy.json"], "scenarios/dgn.json")
##
## Signals:
##   session_ready(session_id, opening, choices)
##   token_received(npc_name, token)
##   turn_result(npc_name, data)
##   choices_updated(node_id, choices)
##   terminal_reached(npc_name, terminal_id, result, final_dialogue)
##   error(message)

extends Node

signal session_ready(session_id: String, opening: String, choices: Array)
signal token_received(npc_name: String, token: String)
signal turn_result(npc_name: String, data: Dictionary)
signal choices_updated(node_id: String, choices: Array)
signal terminal_reached(npc_name: String, terminal_id: String, result: String, final_dialogue: String)
signal error(message: String)

@export var api_base_url: String = "http://localhost:8000"

var _session_id: String = ""
var _ws := WebSocketPeer.new()
var _ws_connected := false


# ── Session creation (HTTP) ────────────────────────────────────────────────────

func start_session(
	npc_paths: Array,
	scenario_path: String,
	difficulty: String = "STANDARD",
	player_skills: Dictionary = {"authority": 5, "diplomacy": 5, "empathy": 5, "manipulation": 5},
	use_ollama: bool = true
) -> void:
	var body := JSON.stringify({
		"npc_paths": npc_paths,
		"scenario_path": scenario_path,
		"difficulty": difficulty,
		"player_skills": player_skills,
		"use_ollama": use_ollama,
	})

	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(
		func(result, code, _headers, body_bytes):
			http.queue_free()
			if result != HTTPRequest.RESULT_SUCCESS or code != 200:
				error.emit("Failed to create session (HTTP %d)" % code)
				return
			var data: Dictionary = JSON.parse_string(body_bytes.get_string_from_utf8())
			_session_id = data.get("session_id", "")
			var opening: String = data.get("scenario", {}).get("opening", "")
			var choices: Array = data.get("choices", [])
			session_ready.emit(_session_id, opening, choices)
			_connect_ws()
	)
	http.request(
		api_base_url + "/sessions",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		body
	)


# ── WebSocket connection ───────────────────────────────────────────────────────

func _connect_ws() -> void:
	var ws_url := api_base_url.replace("http://", "ws://").replace("https://", "wss://")
	ws_url += "/sessions/%s/play" % _session_id
	_ws.connect_to_url(ws_url)
	_ws_connected = false


func _process(_delta: float) -> void:
	if _session_id.is_empty():
		return

	_ws.poll()
	var state := _ws.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN and not _ws_connected:
		_ws_connected = true

	if state == WebSocketPeer.STATE_OPEN:
		while _ws.get_available_packet_count() > 0:
			var msg: String = _ws.get_packet().get_string_from_utf8()
			_handle_ws_message(msg)

	elif state == WebSocketPeer.STATE_CLOSED and _ws_connected:
		_ws_connected = false


func _handle_ws_message(raw: String) -> void:
	var data: Dictionary = JSON.parse_string(raw)
	if data == null:
		return

	match data.get("type", ""):
		"token":
			token_received.emit(data.get("npc", ""), data.get("token", ""))

		"turn_result":
			turn_result.emit(data.get("npc", ""), data)

		"choices":
			choices_updated.emit(data.get("node_id", ""), data.get("choices", []))

		"terminal":
			terminal_reached.emit(
				data.get("npc", ""),
				data.get("terminal_id", ""),
				data.get("result", ""),
				data.get("final_dialogue", ""),
			)

		"error":
			error.emit(data.get("message", "unknown error"))


# ── Send a player choice ───────────────────────────────────────────────────────

func send_choice(choice_index: int) -> void:
	if not _ws_connected:
		push_error("PNEClient: WebSocket not connected")
		return
	var msg := JSON.stringify({"choice_index": choice_index})
	_ws.send_text(msg)


# ── Optional: fetch choices without playing a turn ────────────────────────────

func get_choices(callback: Callable) -> void:
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(
		func(result, code, _headers, body_bytes):
			http.queue_free()
			if result != HTTPRequest.RESULT_SUCCESS or code != 200:
				return
			var data: Dictionary = JSON.parse_string(body_bytes.get_string_from_utf8())
			callback.call(data)
	)
	http.request(api_base_url + "/sessions/%s/choices" % _session_id)


# ── Cleanup ───────────────────────────────────────────────────────────────────

func end_session() -> void:
	if _session_id.is_empty():
		return
	_ws.close()
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(func(_r, _c, _h, _b): http.queue_free())
	http.request(
		api_base_url + "/sessions/%s" % _session_id,
		[],
		HTTPClient.METHOD_DELETE
	)
	_session_id = ""
