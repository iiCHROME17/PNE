# Chapter 7: Discussion and Analysis

---

## 7.1 Validation of Outputs

> **[AUTHOR NOTE — COMPLETE AFTER PROGRAM ACCESS]**
> This section requires live access to the PNE to generate controlled test runs for validation. The following sub-sections are structural placeholders. Content to be written after Chapter 6 (Results) is complete.
>
> Minimum required to fill this section:
> - At least two runs of the same scenario with different player skill distributions, showing divergent pipeline states (thought templates, desire types, intention selections, relation deltas)
> - One run demonstrating a wildcard trigger vs. the same NPC without the wildcard firing
> - One run demonstrating a terminal outcome condition being met vs. narrowly missed
> - Cross-reference specific figures and log excerpts from Chapter 6
>
> Key argument to make here: the pipeline's deterministic layers (cognitive → desire → intention) can be validated independently of LLM output quality. Internal state consistency is separable from surface text quality.

### 7.1.1 Internal State Consistency

[PLACEHOLDER — demonstrate that NPC attribute deltas accumulate in the expected direction across turns, using log data from Chapter 6]

### 7.1.2 Output Coherence Against Pipeline State

[PLACEHOLDER — demonstrate correspondence between computed intention type / emotional valence and the character of the LLM-generated response. Note cases where the LLM drifts from the pipeline's direction and discuss what this reveals about the model's limitations vs. the architecture's soundness]

### 7.1.3 Terminal Outcome Routing

[PLACEHOLDER — demonstrate that terminal outcome conditions are reached or missed in a manner consistent with the player's accumulated choice history, not arbitrarily]

---

## 7.2 Justification of Achievements

### 7.2.1 The System as a Functional Prototype

With the engine, I did not set out to build an entire dialogue engine for a commercial title; I set out to demonstrate that a BDI cognitive architecture alongside a structured NPC personality model and constrained LLM text generation, constitutes a viable architectural basis for psychologically grounded NPC dialogue for narratives. By that standard, I consider the project a success.

What I delivered is a functional prototype of a considerably more ambitious system — one that processes player input through four psychologically-grounded pipeline stages, produces a fully articulated internal NPC state on every turn, constrains a locally-hosted LLM to give voice to that state, and routes narrative outcomes through a judgement-score finite state machine. I built this as a single developer, within an academic project timeline, while simultaneously learning the Ollama runtime and learning to implement a REST and WebSocket API. I ensured that the system functions coherently end-to-end and it will reach terminal outcomes. This I am incredibly proud of.

The more honest measure of the project's achievement is not whether it is production-ready, but whether it is worth continuing. For me, the answer is a definitely. I believe the PNE has genuine value beyond its academic context and would warrant further development as a standalone middleware product. The architecture is sound, the data model is portable, and the core pipeline logic is fully separable from any specific game engine — qualities I designed for deliberately from the outset, this is because I always had a real use case in mind.

### 7.2.2 Deployment Context: Where the System Works

The clearest way I can articulate what the system achieves is to be specific about where it works and where it does not.

The PNE is best suited to games where dialogue is narratively light — where conversation contributes personality and texture without carrying the weight of a complex authored story. *Stardew Valley* (ConcernedApe, 2016) is the example I keep returning to. That game's dialogue is deliberately simple: villagers respond to the player's gift choices and seasonal events with short, characterful exchanges that communicate personality and relationship state without elaborate narrative consequence. The gameplay loop is agricultural and social simulation; the narrative is ambient. An engine like the PNE would transform those exchanges substantially — giving villagers a structured internal model of their relationship with the player, producing responses that reflect accumulated social history, and allowing the same player action to land differently depending on the NPC's psychological profile. The dialogue quality ceiling of `qwen2.5:3b` is not a disqualifying limitation in that context; short, characterful exchanges are precisely what smaller quantised models handle most reliably.

The system is not suited, in its current form, to games where dialogue is narratively critical — where NPC responses must carry precise emotional weight, maintain multi-session continuity, and sustain the coherence of a complex authored story. *Fallout 4* (Bethesda Game Studios, 2015) represents this class. The companion characters in that title require nuanced contextual memory, tonal precision across emotionally loaded scenes, and consistent personality expression across dozens of hours of play. The `qwen2.5:3b` model cannot reliably sustain this quality level, and the PNE's current scenario graph architecture does not model long-term narrative continuity at the required depth. I do not consider this a failure of the architecture's design principles — it is a scope boundary defined by hardware constraints and a single-developer timeline, and it is one I am transparent about.

The distinction between these two contexts is, for me, the most useful thing my evaluation can establish. The question is not about "does it work?" but moreso where.

---

## 7.3 Research Question Revisited

The central question I posed in Chapter 1 was: *to what extent can a BDI cognitive architecture, instantiated over a structured NPC personality model and constrained LLM text generation, produce NPC dialogue that is simultaneously psychologically grounded, narratively coherent, and genuinely responsive to player agency?*

My answer, supported by the implementation and test evidence, is: *yes, within a defined ceiling.*

The pipeline demonstrably produces psychologically grounded NPC behaviour. The cognitive layer translates player input through a personality-parameterised belief model; the desire layer maps those beliefs to motivational states grounded in the social psychology literature; the intention layer selects a behavioural response from a closed, author-controllable vocabulary. At no stage does an NPC simply return a pre-authored string (unless Ollama fails) or pattern-match against a flag. Every response is the downstream product of a structured internal state that varies continuously with NPC personality and player choice history. This is the central architectural claim of my dissertation, and the output logs provide direct evidence that the pipeline operates as described.

Player agency is preserved in a meaningful sense. The system does not route players toward predetermined outcomes — the judgement score integrates evidence across turns, terminal conditions respond to accumulated conversational state, and the two-dice skill check introduces genuine uncertainty without removing player influence. A player who consistently selects empathetic choices against a high-empathy NPC will produce systematically different pipeline states, and thus systematically different outcomes, from a player who challenges the same NPC with authority-based approaches throughout. The relationship between player behaviour and narrative consequence is legible and mechanically grounded.

The honest limit is narrative coherence, and it is a limit imposed not by the architecture but by the surface text layer. The LLM's adherence to prompt constraints is imperfect at the `qwen2.5:3b` scale. Responses occasionally drift from the specified emotional register, turn into meta-commentary, or fail to reflect the nuance of the computed internal state. In these cases, the pipeline's carefully computed context is not fully realised in the spoken text. This is important to distinguish: this is a model capability ceiling, not a pipeline failure. The failure is in transcription rather than cognition. Upgrading the model on capable hardware resolves this ceiling without too much modification to the engine.

---

## 7.4 Critique

### 7.4.1 The Logging Gap

The most significant methodological limitation of my project is the disparity between the volume of testing I conducted and the volume of test evidence I preserved. I ran the system through a large number of conversational scenarios across the development cycle, producing a continuous stream of pipeline output that informed every major architectural revision documented in Chapter 5. The majority of this output was observed in the terminal and discarded. The test logs that were serialised to JSON — the files that form the primary evidential basis of Chapters 4 and 6 — represent a small fraction of the total testing I actually did.

At the time, this felt acceptable. When I was running tests, my purpose was diagnostic — I was looking for failures, not building a record. It became a real problem when the evaluation phase required me to demonstrate differences in NPCs experiencing the same scenario. Scenarios that I had tested repeatedly and found to work reliably could not be shown retrospectively because I had not kept the logs. The result is that my written evaluation rests on a smaller evidential base than my development experience would actually support.

If I were to repeat this project, implementing a automatic logging protocol from the earliest prototype stage would be my single highest-priority methodological change. The current system it is optional per scenario. The optimal change would be that every test run should be serialised automatically and stored with a structured note of what I was testing and what I observed. That discipline would have transformed my validation section from a gap into one of the dissertation's strongest sections.

### 7.4.2 The Wildcard System

The wildcard architecture is the clearest example of a feature I partially built rather than either finishing or cleanly removing. As I designed it, the wildcard system was intended to introduce controlled psychological instability into NPC behaviour — temporary stat modifications triggered by specific player inputs, producing responses that deviated meaningfully from the NPC's baseline personality in ways that felt consistent with an extreme character trait rather than random noise. The `Napoleon` wildcard I assigned to Amourie Othella, for example, was intended to trigger an aggressive dominance response whenever the player's authority tone exceeded a defined threshold, temporarily overriding her normally measured interpersonal style.

In the current implementation, the wildcard flag propagates structurally through the pipeline: it is checked in the desire layer as a routing override condition, gates specific intention templates in the intention registry, and is passed to the LLM prompt via the `wildcard_triggered` boolean on the `BehaviouralIntention` output. The flag reaches the LLM. The problem is that the LLM's response to this signal is inconsistent — without a more tightly authored prompt constraint specific to each wildcard type, the model does not reliably alter its generation style in response to the flag alone.

The system is not broken. The wildcard check does not produce errors or corrupt pipeline state. It simply does not produce a qualitative behavioural shift I designed it to create. Removing it at the point where this became clear would have required refactoring the desire layer, the intention registry, and the NPC profile schemas — a scope of change I could not justify given the other architectural work still in progress. I made a pragmatic decision to retain the partially-implemented feature rather than remove it, acknowledging here that this is a gap between what I intended and what I delivered.

Completing the wildcard system is something I would prioritise in future development. The architecture  is already there; what is missing is a per-wildcard prompt augmentation layer that gives the LLM specific, stylistically distinct generation constraints when a wildcard is active — analogous to the `min_response`/`max_response` anchor mechanism I already use in the outcome layer.

### 7.4.3 Scenario Coverage

My test corpus is narrow by necessity. All of my documented test scenarios centre on the `door_guard` interaction type — an NPC blocking access to a location and evaluating the player's suitability for entry. This was a well-defined, high-stakes conversational context with clear success and failure conditions, which made it the right choice for iterative pipeline testing. But it does not represent the full range of conversational contexts the engine is designed to support.

What is notably absent from my test corpus: scenarios with more than four turns per conversation node; scenarios involving NPCs with wildcard traits that fire reliably under test conditions; scenarios that test the pipeline's robustness to incoherent or adversarial player input; and scenarios that place two or more NPCs with different psychological profiles in the same conversational context. I am not claiming the system fails these cases — I simply have not evaluated them. Establishing the engine's behaviour across a broader scenario taxonomy would be the natural first step in any continued development work beyond this project.

---
