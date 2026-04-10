# PNE — Changelog

Project history for the Psychological Narrative Engine, from first prototype to the current API-ready system.

---

## 10 April 2026 — Dissertation graph tables added

**What changed**

- **`run_engine.sh` fixed** — the launch script was pointing to the non-existent `narrative_engine.py`; corrected to `NE.py`.
- **`config.py` centralised model setting** — confirmed `OLLAMA_MODEL` is set to `qwen2.5:3b` and sourced by `ollama_integration.py` across the entire system.
- **Dissertation graph tables created** — three new reference tables added to `Dissertation/Literature Material/Drafts/Graphs/`:
  - `5.1.1.md` — pipeline stage overview table (7 stages, purpose and output for each).
  - `5.1.4 Table.md` — NPC data structure table using Amourie Othella as the worked example, covering metadata, cognitive attributes, social attributes, ideology, wildcard, faction, social position, world context, known events, and known figures.
  - `5.2.2.md` — scenario routing log table for the `door_guard_night` test, tracing turn-by-turn node traversal, player choices, NPC intent, and outcome deltas.

---

## 12 March 2026 — Codebase documentation pass (uncommitted)

**What changed**

- **Comprehensive docstrings added** — every public class and method across the core modules (`engine.py`, `dialogue_coherence.py`, `skill_check.py`, `processor.py`, `desire.py`, `player_input.py`, `intention_registry.py`, `social.py`, `schema.py`) now has full docstrings: module-level summaries, attribute tables, argument/return descriptions, and cross-references to related classes.
- **Module headers rewritten** — the top-of-file blurbs for `engine.py`, `dialogue_coherence.py`, and `skill_check.py` were replaced with structured overviews explaining each module's role in the pipeline, what classes it exports, and how they interact.
- **`schema.py` contracts documented** — every Pydantic model (`CreateSessionRequest`, `ChoiceItem`, `ChoicesResponse`, `SaveResponse`) now documents each field's purpose, valid values, and which API endpoint uses it.
- **`SkillCheckSystem` constants documented** — `DIFFICULTY_ADJ`, `LANGUAGE_ART_TO_SKILL`, and `SKILL_MODIFIERS` class-level tables have explanatory comments; `DiceCheckResult` and `SkillCheckResult` field comments standardised to en-dash ranges.
- **Pipeline Design PDF updated** — the architecture diagram was revised to reflect the current REST API layer and BDI pipeline structure.

---

## 9 March 2026 — Midterm Demo Version

**What changed**

- **Full REST API layer** — a new `Models/api/` package introduces a FastAPI server (`main.py`) with HTTP and WebSocket endpoints, a session store (`session_store.py`), Pydantic schemas (`schema.py`), WebSocket handler (`ws_handler.py`), and an NPC state updater (`npc_updater.py`). The engine is now accessible over a network, not just from the CLI.
- **Cognitive thought matcher** — `pne/cognitive_thought_matcher.py` and an accompanying `cognitive_thoughts.json` library (810 thought templates) were added. The cognitive interpreter now scores player input against a rich library of named thought patterns rather than generating free-form reactions, making NPC cognition more predictable and author-controllable.
- **`cognitive.py` and `desire.py` major rewrites** — both modules were substantially revised to integrate the thought matcher and support the extended data flowing through the API layer.
- **Ollama integration expanded** — `pne/ollama_integration.py` grew significantly to handle the richer prompt structures and session context introduced by the API.
- **Unity client library** — three C# files (`PNEClient.cs`, `PNEDialogueUI.cs`, `PNETypes.cs`) and a full Unity user guide (HTML + Markdown) were added under `docs/unity/`, giving Unity developers a drop-in integration layer.
- **Godot client script** — `docs/api_client_godot.gd` provides the equivalent integration for Godot 4 projects.
- **Install scripts** — `install.bat` and `install.sh` added at the repo root, along with a top-level `requirements.txt`, so the engine can be set up in one command on Windows or Unix.
- **Troy NPC overhaul** — `npcs/troy.json` was significantly revised with updated BDI attributes and scenario hooks.

---

## 4 March 2026 — Difficulty system, failed-choice pruning, architecture graphs

**What changed**

- **Difficulty levels** — the engine now accepts a `SIMPLE`, `STANDARD`, or `STRICT` setting when it starts. Simple tilts the dice in the player's favour by +15%; Strict does the opposite. This is applied on top of the existing relationship bonus so the two effects stack naturally.
- **Failed choices are removed** — if a player already attempted a choice and failed both the main roll *and* the recovery roll, that option is hidden from the list going forward. No more picking the same dead-end repeatedly.
- **Architecture documentation** — a new `docs/graphs/architecture.md` file captures the full system as Mermaid flowcharts: the per-turn data flow, the judgement state machine, and the recovery loop. Renderable in VS Code or at mermaid.live.
- **Test conversation logs saved** — several successful conversations (Troy, Krakk, Amourie Othella, Morisson Moses) were saved as `.json` snapshots for reference and regression testing.
- **Scenario tweak** — the `dgn.json` scenario's default fallback transition was removed (set to null) so the FSM no longer silently routes to `negotiate` when no condition matched; it stays on the current node instead.

---

## 3 March 2026 (evening) — Judgement tracker replaces raw relation as the FSM driver

**What changed**

- **Judgement score introduced** — every NPC now tracks a `judgement` value (0–100, starting at 50). Dice outcomes shift it up or down each turn, scaled by a risk multiplier when the pre-roll odds were against the player. This single number now drives all terminal routing rather than the raw `player_relation` float.
- **FSM conditions updated** — scenario transition conditions can now test `judgement` directly (e.g. `judgement <= 25` → fail route, `judgement >= 75` → succeed route). The old `player_relation` condition still works for backward compatibility.
- **`NE.py` entry point created** — a clean top-level script so the engine can be launched from anywhere with `python NE.py npcs/troy.json scenarios/dgn.json`. The old monolithic `narrative_engine.py` file was removed and replaced by the package structure it had been refactored into.
- **`DiceCheckResult` exported** — the dice result dataclass (player die, NPC die, success flag, biases) is now part of the public `pne` package API, ready for the game-engine integration layer.

---

## 3 March 2026 (afternoon) — Finite State Machine routing, Ollama scene direction, NPC Creator re-added

**What changed**

- **Proper FSM transitions** — scenario nodes can now define conditions, intention-keyword gates, and relation thresholds to route to the next node. The engine picks the first matching transition; unmatched turns stay on the current node. Before this, all routing was done by a simple turn counter.
- **Intention matching** — the `intention_shift` value declared in a choice's outcomes (e.g. "Propose Alliance") is extracted at the scenario level and fed directly into the FSM, so authors have reliable hooks to trigger story branches without depending on what the LLM decides to say.
- **Ollama gets scene direction** — instead of asking Ollama to generate a response from scratch, the engine now passes the node's `npc_dialogue_prompt` as a "scene direction" alongside the BDI state. The NPC stays in character and on-topic, and the terminal response is generated from the terminal node's own prompt rather than reusing whatever the last turn said.
- **Recovery mode added** — when a player fails a dice roll, a set of recovery choices is queued. On the next `get_available_choices()` call, those recovery choices are served instead of the node's normal list. The player gets one chance to claw back before the conversation moves on. If they fail the recovery too, that choice is permanently locked out.
- **`success_pct` on every choice** — before the player picks anything, each option now carries an estimated probability of success (0–100) based on their skill, the NPC's resistance, and the current relationship. The calculation is done analytically (not by rolling) so it's fast and accurate.
- **NPC Creator HTML tool** — the browser-based character creator was re-added alongside the updated engine code.

---

## 3 March 2026 (morning) — Pre-FSM snapshot

A checkpoint commit taken before the FSM rewrite began. Notable for:

- Scenario JSON restructured so each node directly references which NPCs are active (instead of the engine guessing).
- Several multi-turn test conversations recorded (Amourie Othella, Morisson Moses) that informed the FSM design.

---

## 2 March 2026 — Intention matching foundation, world context fixes

**What changed**

- **Intention registry** — a library of named intention templates (e.g. "Carefully Question Motives", "Propose Alliance") was added. The socialisation layer now scores player-NPC interaction against these templates rather than generating free-form text, making the BDI pipeline more predictable and author-controllable.
- **World context added to NPC prompts** — NPCs now receive a snapshot of the world context (factions, locations, history) when generating their responses. They previously only had their own personal history and the conversation so far.
- **Shell launcher** — `PNE.sh` added for convenience; sets sensible defaults and handles the working-directory issue so the pne package is always importable.

---

## 5 February 2026 — Package restructure, scenario format overhaul

**What changed**

- **`narrative_engine` is now a package** — the single `narrative_engine.py` file was split into a proper Python package with separate modules: `engine.py` (orchestrator), `session.py` (conversation state), `cli.py` (terminal interface), `scenario_loader.py`, `transition_resolver.py`, `choice_filter.py`, `dialogue_coherence.py`. Old prototype files moved to `depricated/`.
- **Scenario JSON restructured** — nodes now explicitly reference which NPC is active, making multi-NPC scenarios easier to define. Old scenario files that relied on the implicit single-NPC assumption were updated.
- **Auto-generated HTML docs** — `pdoc` was used to generate browsable API docs for the `pne` and `narrative_engine` packages, now living in `docs/`.

---

## 1 February 2026 — Outcome-matching transition model

**What changed**

- The narrative engine's transition logic was rewritten to use **outcome matching** — instead of checking dialogue content (which depends on what the LLM said), transitions now trigger on the `interaction_outcome` chosen by the BDI pipeline. This is far more reliable because it's deterministic.
- A full test conversation with Krakk was saved to confirm the new routing worked end-to-end.

---

## 27 January 2026 — Narrative construction phase begins

The focus shifted from the BDI pipeline itself to **how conversations unfold over multiple turns**. Work began on:

- Multi-NPC support within a single scenario.
- Node/choice tree structure for the scenario JSON.
- The `narrative_engine.py` file grew significantly to manage conversation state and history per NPC.

---

## 16 January 2026 — LLM switch, wildcard → prompt-modifier rename, structural refactor

**What changed**

- **Switched from `qwen2.5:3b` to `phi3:mini`** as the default local model. (Later commits switched back to qwen after quality comparison.)
- **Wildcards renamed to Prompt-Modifiers** — the system that injects special Ollama sampling parameters (temperature, penalty, token limits) for rare emotional states is now called "Prompt-Modifiers" to be clearer about what it does. The underlying behaviour is unchanged.
- Major `PNE_Models.py` refactor: cleaned up the data model classes and added external config file loading for wildcard/modifier definitions.

---

## 4 December 2025 — Narrative Simulator template complete

The first version of `narrative_engine.py` (at the time, a single flat file) was considered feature-complete as a template. The old `ConversationSimulator.py` was marked explicitly as a deprecated prototype.

Key capabilities at this point:
- Player choices loaded from a JSON scenario file.
- BDI pipeline runs per turn (Thought → Desire → Intention → Outcome).
- NPC response generated by Ollama.
- Terminal outcomes detected and reported.

---

## 3 December 2025 — Full pipeline wired up

The `pipeline.py` module was expanded into a complete BDI processing chain connecting all the individual components (cognitive interpreter, desire formation, socialisation filter, outcome selector). Conversation simulation end-to-end became possible for the first time.

---

## 22 November 2025 — Outcome model added, error fixed

- An `Outcome` type system was added to `pipeline.py` to represent what happens as a result of a choice (attribute changes, relation shifts, narrative transitions).
- A bug in the outcome model's data parsing was fixed the same day.

---

## 17 November 2025 — Ollama integration, first real tests

- **Ollama connected** — `qwen2.5:3b` running locally was wired into the pipeline to generate NPC dialogue. Before this, responses were scripted strings.
- First small-scale tests ran successfully. Noted at the time: the engine needed proper min/max outcome text to guide story coherence (later addressed by the `npc_dialogue_prompt` system).

---

## 16 November 2025 — Project started

Three commits on the same day established the foundation:

1. **Initial commit** — project created, basic structure in place.
2. **`PNE_Models.py` v1** — core data classes defined: `CognitivePersonalityModel`, `SocialPersonalityModel`, `WorldPerceptionModel`, `NPCModel`. These classes remain the backbone of the system today.
3. **Pipeline and LLM import** — `pipeline.py` started; a local language model was imported for the first time.
