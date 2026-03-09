# PNE API — Unity Integration Guide

## Overview

The Psychological Narrative Engine (PNE) runs as a local HTTP + WebSocket server. Unity connects to it for:

- **Session management** via REST (HTTP) — create sessions, list NPCs/scenarios
- **Turn gameplay** via WebSocket — send choices, receive streaming NPC dialogue and BDI state

A turn looks like this:

```
Unity                             PNE Server
  │── POST /sessions ──────────►  create session, load NPCs + scenario
  │◄── { session_id, choices } ─  initial choice list
  │
  │══ WS /sessions/{id}/play ══►  WebSocket connection open
  │── { "choice_index": 2 } ────►  player picks choice 2
  │◄── { "type": "token" } ─────  Ollama streams word by word (~2-10s)
  │◄── { "type": "token" } ─────
  │◄── { "type": "turn_result" }  BDI data (belief, desire, intention)
  │◄── { "type": "choices" } ───  next set of choices
  │        ... repeat per turn ...
  │◄── { "type": "terminal" } ──  conversation ends
```

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Unity 2021 LTS or later | Tested on 2021, 2022, 2023 |
| TextMeshPro | Already bundled with most Unity installs |
| Input System package | Required — `PNEDialogueUI` uses `UnityEngine.InputSystem` |
| PNE server running | See [Starting the Server](#starting-the-server) |
| Python 3.10+ on the server machine | Required to run the PNE server |

---

## Starting the Server

On the machine running the PNE (can be the same machine as Unity):

```bash
cd path/to/cs3ip/Models
pip install fastapi "uvicorn[standard]"

uvicorn api.main:app --host 0.0.0.0 --port 8000
```

To verify it's running, open `http://localhost:8000/docs` in a browser — you'll see the interactive API docs.

> **Tip:** Add `--reload` during development so the server restarts when Python files change.

---

## Unity Project Setup

### 1. Install required packages

Open **Window → Package Manager**.

**Install Input System:**
1. Click **+** → *Add package from registry*
2. Search for `Input System` and click **Install**
3. When prompted to switch the active Input Handling, click **Yes** — this sets Player Settings to "Input System Package (New)"

**Install NativeWebSocket:**
1. Click **+** → *Add package from git URL*
2. Paste: `https://github.com/endel/NativeWebSocket.git#upm`
3. Click **Add**

**Install Newtonsoft Json (JSON.NET):**
1. Click **+** → *Add package from git URL*
2. Paste: `com.unity.nuget.newtonsoft-json`
3. Click **Add**

> All three packages are required. **Input System** provides the keyboard handling in `PNEDialogueUI`. **NativeWebSocket** handles the WebSocket streaming (including WebGL). **Newtonsoft Json** parses the flexible API messages.

### 2. Copy the C# files into your project

Copy all three files from `Models/docs/unity/` into your Unity project's `Assets/` folder (any subfolder is fine):

```
Assets/
  PNE/
    PNETypes.cs        ← Data classes matching all API JSON shapes
    PNEClient.cs       ← MonoBehaviour — HTTP + WebSocket client
    PNEDialogueUI.cs   ← Example UI controller
```

### 3. Build Settings (WebGL only)

If targeting WebGL, no extra steps are needed — NativeWebSocket handles platform differences automatically.

For **Standalone** (Windows/Mac/Linux), everything works out of the box.

---

## Setting Up the Scene

### Minimal scene structure

```
Scene
├── PNEManager (GameObject)
│     ├── PNEClient       ← MonoBehaviour
│     └── PNEDialogueUI   ← MonoBehaviour
│
└── Canvas
      ├── DialoguePanel              ← shown during NPC text; hidden when choices appear
      │     ├── NpcNameLabel    (TMP_Text)
      │     ├── DialogueText    (TMP_Text)
      │     └── JudgementLabel  (TMP_Text, optional)
      ├── ChoicesPanel               ← hidden during NPC text; shown when player must choose
      │     └── ChoicesContainer  (Horizontal Layout Group)
      ├── InteractButton  (Button + TMP_Text)  ← "[ click to skip ]" / "[ press E ]" hint
      ├── OutcomeLabel  (TMP_Text)
      └── ChoiceButtonPrefab  (Button + TMP_Text child named "Label")
```

> **ChoicesContainer layout** — add a `HorizontalLayoutGroup` component (not Vertical).
> Set *Child Force Expand Width* → off, *Spacing* → 12. Add a `ContentSizeFitter`
> with *Horizontal Fit: Preferred Size* so buttons don't stretch across the full width.

### Configuring PNEClient in the Inspector

| Field | Example | Description |
|-------|---------|-------------|
| Api Base Url | `http://localhost:8000` | Change to server IP for networked play |
| Npc Paths | `npcs/troy.json` | Relative to the `Models/` directory on the server |
| Scenario Path | `scenarios/dgn.json` | Same — relative to `Models/` |
| Difficulty | `STANDARD` | `SIMPLE`, `STANDARD`, or `STRICT` |
| Use Ollama | ✓ | Uncheck for scripted responses only (faster, deterministic) |
| Authority / Diplomacy / Empathy / Manipulation | 0–10 | Player skill values |

### Configuring PNEDialogueUI in the Inspector

Drag the scene objects into the serialized fields:

| Field | Assign | Notes |
|-------|--------|-------|
| Client | `PNEManager` GameObject | |
| Dialogue Panel | The `DialoguePanel` GameObject | Whole panel — shown/hidden as a unit |
| Dialogue Text | `TMP_Text` inside `DialoguePanel` | Typewriter animates this |
| Npc Name Label | Optional name display | |
| Judgement Label | Optional `TMP_Text` | Shows `"Judgement: 62/100"` |
| Outcome Label | `TMP_Text` shown on terminal | |
| Choices Container | Parent `Transform` for buttons | Must use `HorizontalLayoutGroup` |
| Choice Button Prefab | Button with `TMP_Text` child `"Label"` | |
| Interact Button | Optional on-screen hint button | Label auto-updates to skip/continue text |
| Chars Per Second | `40` | Typewriter speed (characters per second) |
| Skip Hint | `[ click to skip ]` | Button label while animating |
| Continue Hint | `[ press E to continue ]` | Button label when text is complete |

**Interaction flow** — the UI has four phases:

| Phase | E / Space / Interact button does |
|-------|----------------------------------|
| Typing | Skip → reveal full text instantly |
| Text Complete | Advance → hide text box, show choices |
| Choices | Nothing (click a choice button to continue) |
| Idle | Nothing (waiting for Ollama) |

Press **Play** — the opening text typewriters in; press E or Space to advance.

---

## PNEClient Reference

### Events

Subscribe to these in `Awake` or `Start` on any script:

```csharp
var pne = GetComponent<PNEClient>();

pne.OnSessionReady   += data  => Debug.Log(data.Scenario.Opening);
pne.OnPlayerChoice   += msg   => AppendConvoLine("You", msg.Text);
pne.OnToken          += (npc, token) => dialogueText.text += token;
pne.OnTurnResult     += msg   => Debug.Log(msg.Thought.SubjectiveBelief);
pne.OnChoicesUpdated += msg   => RebuildChoiceButtons(msg.Choices);
pne.OnTerminal       += msg   => ShowOutcome(msg.TerminalId, msg.Result);
pne.OnError          += err   => Debug.LogError(err);
```

### Methods

```csharp
pne.StartSession();          // Creates session and opens WebSocket
pne.SendChoice(int index);   // 1-based index from ChoiceItem.Index
pne.EndSession();            // Closes WS and deletes session from server
```

### Properties

```csharp
pne.SessionId    // string — UUID of the active session
pne.IsConnected  // bool   — WebSocket is open
pne.IsComplete   // bool   — terminal outcome reached
```

---

## WebSocket Message Reference

Every message from the server has a `"type"` field. `PNEClient` deserialises these automatically and fires the matching event.

### `"player_choice"` → `OnPlayerChoice(PlayerChoiceMessage)`

Sent immediately when the player's choice is received — before any Ollama tokens arrive. Use this to show the player's line in a conversation log right away.

```json
{
  "type": "player_choice",
  "choice_id": "open_empathy",
  "text": "I've seen what this regime does to families.",
  "language_art": "empathetic"
}
```

**UI pattern:** append this as the player's line in a chat-style log. Disable choice buttons here — re-enable in `OnChoicesUpdated`.

### `"token"` → `OnToken(npcName, token)`

One chunk of Ollama's streaming output.

```json
{ "type": "token", "npc": "Troy", "token": "I " }
{ "type": "token", "npc": "Troy", "token": "don't " }
{ "type": "token", "npc": "Troy", "token": "trust you." }
```

**UI pattern (PNEDialogueUI):** tokens are buffered silently in `_npcBuffer`. When `OnTurnResult` fires, the complete response is typewriter-animated via `maxVisibleCharacters`. This avoids partial-word flicker and lets the player skip or wait at their own pace.

**Custom pattern (streaming directly):** if you prefer live streaming instead, append each token directly:
```csharp
pne.OnToken += (npc, token) => dialogueText.text += token;
```

### `"turn_result"` → `OnTurnResult(TurnResultMessage)`

Sent after all Ollama tokens for a turn have been streamed. Contains the full BDI state.

```json
{
  "type": "turn_result",
  "npc": "Troy",
  "npc_id": "troy",
  "thought": { "subjective_belief": "This person is testing me.", "emotional_valence": -0.45 },
  "desire":  { "desire_type": "information-seeking", "intensity": 0.72 },
  "intention": { "intention_type": "Evaluate Sincerity", "confrontation_level": 0.6 },
  "judgement": 42,
  "npc_response": "I don't trust you.",
  "dice": {
    "player_die": 3, "npc_die": 5, "success": false,
    "skill": "empathy", "success_pct": 45,
    "risk_multiplier": 1.11, "judgement_delta": -6
  },
  "entered_recovery": true
}
```

**UI pattern:** update a judgement bar with `judgement` (0–100). For arcade mode, show `dice.player_die`/`npc_die` as animated dice faces, `dice.judgement_delta` as a ±N overlay, and activate a recovery indicator when `entered_recovery` is `true`.

### `"choices"` → `OnChoicesUpdated(ChoicesMessage)`

The next set of available player choices. Rebuild your choice buttons.

```json
{
  "type": "choices",
  "node_id": "challenge",
  "in_recovery": false,
  "choices": [
    { "index": 1, "choice_id": "press_harder", "text": "I have proof.",
      "language_art": "challenge", "success_pct": 58 },
    { "index": 2, "choice_id": "back_off",     "text": "Fair enough.",
      "language_art": "diplomatic", "success_pct": 71 }
  ]
}
```

**UI pattern:** destroy old buttons, spawn one button per choice with text + success %.

> **`in_recovery`** — when `true`, the player is in a recovery sub-turn after a failed dice check. Show a "recovery" indicator in the UI.

### `"terminal"` → `OnTerminal(TerminalMessage)`

Conversation over. Show the outcome and disable choices.

```json
{
  "type": "terminal",
  "npc": "Troy",
  "terminal_id": "SUCCEED",
  "result": "Troy steps aside and lets you through.",
  "final_dialogue": "...don't make me regret this."
}
```

**`terminal_id` values:** `SUCCEED`, `FAIL`, `NEGOTIATE`, `DELAY`, `ESCALATE`

### `"error"` → `OnError(message)`

Something went wrong. Log it and optionally show the player a retry option.

---

## REST Endpoint Reference

These are available for non-turn operations (listing files, checking state, etc.).

| Method | URL | Notes |
|--------|-----|-------|
| `GET` | `/npcs` | List all `.json` files in `Models/npcs/` |
| `GET` | `/scenarios` | List all `.json` files in `Models/scenarios/` |
| `POST` | `/sessions` | Create session — see `CreateSessionRequest` |
| `GET` | `/sessions/{id}` | Snapshot of current session state |
| `GET` | `/sessions/{id}/choices` | Current choices without playing a turn |
| `GET` | `/sessions/{id}/history` | Full conversation transcript (all history entries per NPC) |
| `POST` | `/sessions/{id}/save` | Persist NPC state to their source JSON files now (returns `{"saved":[…]}`) |
| `DELETE` | `/sessions/{id}` | Clean up server-side session |

Calling these from Unity is done with `UnityWebRequest` coroutines — see the pattern used in `PNEClient.cs` for reference.

---

## Player Skills & Difficulty

### Skills (0–10)

| Skill | Language art | Effect |
|-------|-------------|--------|
| Authority | `challenge` | NPCs with high assertion resist more |
| Diplomacy | `diplomatic` | Broadest applicability |
| Empathy | `empathetic` | More effective on NPCs with high empathy |
| Manipulation | `manipulative` | Risky — higher reward/penalty swings |

### Difficulty

| Value | Effect |
|-------|--------|
| `SIMPLE` | Player die gets +0.15 bias — easier dice rolls |
| `STANDARD` | No bias adjustment |
| `STRICT` | Player die gets −0.15 bias — harder dice rolls |

### `success_pct` on choices

Each choice carries a `success_pct` (0–100) so you can show the player their odds. This accounts for their relevant skill vs the NPC's resistance plus the current `player_relation` (which increases as the NPC warms up).

---

## Common UI Patterns

### Typewriter with scroll view

`PNEDialogueUI` uses `TMP_Text.maxVisibleCharacters` for the typewriter effect — this respects all TMP rich text tags (`<b>`, `<color>`, `<size>`) without string-slicing issues.

To pair with a **ScrollRect**, force the canvas after each typewriter tick:

```csharp
// In a custom TypewriterRoutine override:
dialogueText.maxVisibleCharacters = i;
Canvas.ForceUpdateCanvases();
scrollRect.verticalNormalizedPosition = 0f;
yield return new WaitForSeconds(delay);
```

Set `ScrollRect → Content` to the `DialogueText` panel with a `Content Size Fitter` (Preferred Size, vertical).

### Emotion-based panel tinting

Use `emotional_valence` from `TurnResultMessage` to tint the dialogue panel:

```csharp
private void HandleTurnResult(TurnResultMessage msg)
{
    float v = msg.Thought?.EmotionalValence ?? 0f;
    // +1 = warm, -1 = cold
    dialoguePanel.color = Color.Lerp(hostileColor, friendlyColor, (v + 1f) / 2f);
}
```

### Judgement bar (progress bar)

```csharp
private void HandleTurnResult(TurnResultMessage msg)
{
    judgementBar.value = msg.Judgement / 100f;   // Slider or Image.fillAmount
}
```

---

## Tips & Gotchas

**NativeWebSocket callbacks are already on the main thread.**
`NativeWebSocket` uses `DispatchMessageQueue()` in `Update()` to marshal callbacks onto the main thread. You do *not* need `MainThreadDispatcher` or `lock` statements for the events fired by `PNEClient`.

**Ollama takes 2–10 seconds per turn.**
Disable choice buttons as soon as `SendChoice()` is called (done in `PNEDialogueUI`). Re-enable them in `OnChoicesUpdated`. Never call `SendChoice()` twice in the same turn.

**Server must be reachable by IP.**
On mobile or other devices, use the host machine's LAN IP (`192.168.x.x`) instead of `localhost`.

**Session cleanup.**
`PNEClient.OnDestroy()` calls `EndSession()` automatically, so sessions are cleaned up when the scene changes. For explicit control, call `client.EndSession()` yourself before loading a new scene.

**Multiple NPCs.**
When multiple NPCs are active, `OnToken` and `OnTurnResult` fire once per NPC per turn. Use `msg.Npc` or `msg.NpcId` to route to the correct UI element.

**No Ollama / offline mode.**
Set `Use Ollama = false` in the Inspector. The engine uses the scenario's scripted `min_response`/`max_response` text directly — fast and deterministic. Useful for testing UI without running Ollama.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Session creation failed (HTTP 0)` | Server not running, or wrong `apiBaseUrl` |
| `Session creation failed (HTTP 400)` | NPC/scenario path wrong; check paths are relative to `Models/` |
| WebSocket never connects | Firewall blocking port 8000; check `--host 0.0.0.0` on server |
| No tokens arrive but `turn_result` fires | `use_ollama = false` set, or Ollama not running (`localhost:11434`) |
| `NativeWebSocket` namespace missing | Package not installed — re-add the git URL in Package Manager |
| `Newtonsoft.Json` missing | Add `com.unity.nuget.newtonsoft-json` in Package Manager |
| `InvalidOperationException: You are trying to read Input using the UnityEngine.Input class` | Player Settings → Active Input Handling must be set to **Input System Package (New)** or **Both**. Install the Input System package if not present. |
| Choices appear during NPC text / text box and choices visible simultaneously | Assign `dialoguePanel` (the whole panel GameObject) rather than just `dialogueText` to the Dialogue Panel field |
