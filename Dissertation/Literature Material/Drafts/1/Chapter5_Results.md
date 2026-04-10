# Chapter 5: Results and Discussion

---

## 5.1 Model Design

### 5.1.1 Overview of the Final Pipeline

The Psychological Narrative Engine (PNE) processes each player turn through a deterministic, layered pipeline before a single word of NPC dialogue is generated. At a high level, the sequence is as follows: the player selects a dialogue choice; a two-dice skill check resolves whether the communicative act succeeds or fails; the result is passed through four sequential BDI stages — cognitive interpretation, desire formation, socialisation, and outcome selection — each of which produces a structured internal state; that final state, including a closed behavioural intention and emotional valence value, is passed to a locally-hosted large language model (Ollama, `qwen2.5:3b`) which generates the NPC's spoken response; and a terminal outcome check determines whether the conversation ends or advances to the next node.

[**FIGURE: Simplified pipeline diagram — player input → skill check → cognitive layer → desire layer → socialisation/intention layer → outcome layer → LLM output → terminal check**]

This sequence is orchestrated by the `DialogueProcessor` class (`processor.py`), which maintains per-NPC state across turns and exposes a single `process_dialogue()` method as the public-facing interface. The clean separation of concerns — each layer receiving a structured input and producing a structured output — was a deliberate design choice to enable independent testing and iteration of each component without destabilising the pipeline as a whole.

### 5.1.2 Core vs. Supporting Components

Not all components carry equal weight in the dissertation's central argument. The core components are those without which the PNE's claim to psychologically-grounded NPC behaviour cannot be sustained:

- **Player Input and Skill Check** (`player_input.py`, `skill_check.py`) — the entry point into the pipeline, establishing the rhetorical register and the stochastic success of each player turn.
- **Cognitive Layer / CognitiveThoughtMatcher** (`cognitive_thought_matcher.py`, `cognitive_thoughts.json`) — the deterministic replacement for LLM-based thought generation; the component most directly responsible for the system's interpretability.
- **Desire Layer** (`desire.py`) — the belief-to-motivation translation layer grounded in social psychology literature.
- **Socialisation / Intention Layer** (`social.py`, `intention_registry.py`) — the closed vocabulary of behavioural intentions that constrains LLM output and makes FSM routing deterministic.
- **Outcome Layer** (`outcomes.py`) — the system's consequence mechanism, including the two-tier interaction/terminal architecture.
- **Ollama LLM Output** — the surface text generation component, narrowly scoped by the structured context injected from all prior stages.

Supporting components that enhance usability but are not central to the theoretical argument include the FastAPI REST and WebSocket API layer (`api/`), the HTML-based character creator (`character_creator.html`), and the interactive dashboard. These exist to make the system deployable and accessible rather than to advance the cognitive modelling claims.

### 5.1.3 Key Design Decisions

**Language: Python and JSON**

The choice of Python as the primary implementation language reflected a pragmatic design priority: the most significant technical challenge in this project was the BDI pipeline logic and its interaction with the LLM runtime, not the language itself. Python offered the fastest iteration cycle for a solo developer and native support for JSON serialisation, which was critical given that NPC profiles, scenario definitions, cognitive thought templates, and output logs are all JSON-structured. Crucially, JSON's language-agnosticism was a deliberate cross-platform decision. Unity (C#), Godot (GDScript), and Unreal Engine (C++) all provide native JSON parsing libraries, which means any game engine can consume or produce NPC profile data and session logs without format translation. This portability was a primary motivation for structuring all persistent data as JSON rather than a database schema or binary format.

**Local LLM via Ollama: `qwen2.5:3b`**

The decision to route all language generation through a locally-hosted model rather than a cloud API was motivated by two concerns: latency and player privacy. A cloud API call introduces network round-trip time on every NPC response, which is incompatible with the real-time expectations of interactive dialogue. More substantively, routing player dialogue choices through a third-party service creates an unnecessary data dependency that would complicate the engine's deployment in commercial contexts. Ollama allows the LLM to run as a local process with no external traffic.

The specific model, `qwen2.5:3b`, was selected after testing on the development hardware — an NVIDIA GTX 1650 Super with 4 GB VRAM. This constraint is not merely anecdotal: the 1650 Super represents a realistic minimum for a budget-conscious gamer PC, and the model's 3 billion parameter count fits within 4 GB VRAM at 4-bit quantisation while still producing grammatically coherent English with reasonable adherence to prompt constraints. The choice represents a deliberate trade-off: the system targets hardware that a wide range of players already own, accepting some quality ceiling on dialogue generation in exchange for accessibility.

**BDI Architecture**

The Belief-Desire-Intention formalism was selected over alternative agent architectures (reactive, utility-based, GOAP) for its alignment with the cognitive science literature the system draws on directly. The B-D-I sequence maps cleanly onto the psychological models grounding each layer: Ellis's (1962) A-B-C model for the belief update, Maslow and Cialdini for desire formation, and Goffman's (1959) face management theory for intention selection. This is not incidental — the architecture's correspondence to the literature is what makes the system's outputs theoretically interpretable rather than merely empirically observed.

### 5.1.4 NPC Data Structure

Each NPC is represented as a JSON object with three top-level sections: `cognitive`, `social`, and `world`. The cognitive block encodes three continuous personality dimensions — `self_esteem`, `locus_of_control`, and `cog_flexibility`, each normalised to [0.0, 1.0] — which govern the cognitive layer's emotional valence computation and thought-template scoring. The social block encodes five interpersonal dimensions — `assertion`, `conf_indep`, `empathy`, an `ideology` dictionary, and an optional `wildcard` trait — which govern the intention layer's template selection and the skill check's NPC resistance threshold. The world block contains narrative context: `personal_history`, `player_relation`, faction membership, and references to known world events and figures.

[**FIGURE: Example NPC JSON — Amourie Othella (amourie_othella.json), showing all three blocks with annotated field descriptions**]

Troy's profile (`troy.json`) illustrates how the parameter space encodes a distinct psychological archetype. With `self_esteem: 0.2`, `locus_of_control: 0.85` (strongly external), and `cog_flexibility: 0.1` (highly rigid), Troy's cognitive block encodes a profile associated with hostile attribution bias and resistance to persuasive framing — consistent with his characterisation as a devoutly loyal, suspicious Insurgency operative. His social block (`assertion: 0.8`, `empathy: 0.5`, no wildcard) predicts behavioural intentions in the mid-high confrontation range, which can be observed directly in pipeline outputs when Troy is tested.

This structure was designed to be both machine-readable by the pipeline and human-readable by a narrative designer. A writer creating an NPC does not need to understand the pipeline's internal mechanics — they need only understand that higher assertion makes an NPC more confrontational, higher empathy makes them more responsive to sincerity, and the wildcard field unlocks extreme behavioural archetypes. The full character creator tool (`character_creator.html`) provides a form-based interface for authoring profiles without editing JSON directly.

---

## 5.2 Interpretability

### 5.2.1 How Psychological State Influences LLM Output

The PNE does not allow the LLM to operate as a free-form text generator. The output of every prior pipeline stage is injected into the LLM prompt as structured scene direction, constraining what the NPC says without dictating verbatim text. Concretely, the prompt provided to Ollama includes: the NPC's `internal_thought` and `subjective_belief` from the cognitive layer (what the NPC privately thinks and interprets), the `immediate_desire` and `desire_type` from the desire layer (what the NPC wants), the `intention_type` and `emotional_expression` from the intention layer (how the NPC intends to communicate), the selected `min_response` and `max_response` anchors from the interaction outcome (the stylistic extremes between which the response should fall), and the `emotional_valence` value (whether the NPC's current affect is positive or negative).

The result is a prompt that does not ask the LLM to generate freely from the player's input. It asks the LLM to give voice to a character whose full internal state has already been computed deterministically. The LLM's contribution is surface variation — phrasing, rhythm, and register — constrained by a precise psychological context it did not produce.

This architecture is the system's answer to the reliability problem that afflicts unconstrained LLM dialogue. When the model hallucinates or drifts, it does so within a constrained envelope; when it adheres to the prompt, the result is a response that is simultaneously legible as an expression of the NPC's internal state and non-repetitive in surface form.

### 5.2.2 End-to-End Scenario: Amourie Othella, Door Guard Scenario

The following walk-through traces a single four-turn conversation between the player and Amourie Othella (`door_guard_scenario`, log: `new_amourie_door.json`). Amourie's profile encodes high self-esteem (`0.9`), strongly internal locus of control (`0.2`), moderate cognitive flexibility (`0.8`), moderate assertion and empathy, a Communitarian ideology, and the `Napoleon` wildcard. Her starting `player_relation` is `0.5`.

**Turn 1 — Authority Challenge**

The player selects: *"I don't need to prove anything to you. I've fought for survival just like you have. Open the door."*

This choice carries the `CHALLENGE` language art, triggering the `authority` skill dimension in the dice check. The skill check resolves against Amourie's resistance threshold, which is elevated by her high assertion (`0.3 + 0.8 × 0.4 = 0.62`). The check fails; the authority tone is high but so is her resistance.

The cognitive layer matches this input against the thought-template library. The high authority tone and the NPC's moderate cognitive flexibility score a template in the `cynical_realism` bias category. The `internal_thought` output is: *"Maybe their words are genuine, but I can't fully trust them."* The `subjective_belief` is: *"They claim empathy but might be using me."* The `emotional_valence` computation reflects the authority tone applied to a high-self-esteem, internal-locus NPC: rather than suppression, it produces moderate negative affect (`-0.26`), signalling perceived challenge rather than threat.

The desire layer evaluates the subjective belief for keyword patterns. The belief text contains the keyword `using` (proximate to the `manipulative` pattern), triggering a `protection` desire with elevated intensity (`0.8`). However, Amourie's `Napoleon` wildcard is checked: the wildcard does not fire here because the player's authority tone, while high, does not yet meet the wildcard override threshold. The desire resolves as `information-seeking` at intensity `0.8`.

The intention layer selects `Carefully Question Motives` — a medium-confrontation template (`confrontation_level: 0.46`) consistent with the `information-seeking` desire and Amourie's personality profile. The confrontation value is computed by clamping Amourie's natural confrontation tendency to the template's valid range and nudging upward by a proportion of the desire intensity.

The outcome layer applies a `relation_delta` of `-0.2`, dropping the relation from `0.5` to `0.3`. The LLM is given the state summary including `min_response: "You think you can intimidate ME? Wrong move."` and `max_response: "Bold. I respect that. But respect isn't enough."` With negative emotional valence, the output tends toward the min anchor. The generated response is: *"Bold. I respect that. But respect isn't enough."*

**Turn 2 — Personal Sacrifice**

The player switches register: *"I've already lost everything. My family, my home. I have nothing left but the will to fight."*

This choice carries the `EMPATHETIC` language art and high `empathy_tone`. The cognitive layer matches a template closer to `empathy_resonance`. The `internal_thought` is: *"These words cut deep, real or not?"*; the `subjective_belief` is: *"Player seems genuinely broken and seeking support."* The valence shifts to `+0.27`.

The desire layer finds the keyword `genuine` in the belief text (sincerity pattern), triggering an `affiliation` desire. Amourie's empathy score of `0.75` does not suppress this pattern. The desire resolves as `information-seeking` at moderate intensity (`0.4`), reflecting the guarded quality of a character who is moved but not yet convinced.

The intention layer selects `Neutral Response` with confrontation at `0.6` — higher than turn 1's value despite the more empathetic player choice, because the desire intensity is lower and Amourie's base confrontation tendency (derived from her assertion and conf_indep) clamps the value upward. The outcome applies `relation_delta: +0.25`, recovering the relation from `0.3` to `0.55`. The LLM generates: *"Then you understand. That loss... that rage... use it well."*

**Turns 3–4 and Terminal Outcome**

Subsequent turns accumulate positive relation deltas as the player reaffirms commitment and accepts Amourie's terms. By turn 4, `player_relation` has reached `0.95` and the judgement score has accumulated sufficient positive weight. The terminal outcome check evaluates the condition `player_relation >= 0.9 and judgement_score >= 65`, which passes. The conversation ends with the terminal outcome `SUCCEED`, and the scenario FSM routes to the `succeed` node.

[**FIGURE: Routing log from new_amourie_door.json showing relation deltas across four turns and final terminal outcome state**]

### 5.2.3 Comparative Output Analysis

[**PLACEHOLDER — will be populated with side-by-side runs showing different player stat distributions producing divergent pipeline states and outputs. Author to provide test logs.**]

The qualitative prediction is clear from the architecture: a player with high `authority` skill and low `empathy` skill will produce systematically different pipeline states — different thought templates, different desire types, different intention selections, different relation deltas — from a player whose stats invert those values, even if both players select identical choice text. The mechanism for this difference is the `PlayerSkillSet`, which biases the player's dice roll, and the `language_art` classification, which determines which NPC resistance formula is applied and which tone signals populate the cognitive layer inputs.

---

## 5.3 Optimisation

### 5.3.1 Architectural Evolution: From Prototype to Current System

The most significant architectural change between the initial prototype and the current system was the removal of the second Ollama call in the cognitive layer and its replacement with the deterministic `CognitiveThoughtMatcher`. In the prototype, every pipeline invocation made two LLM calls: one to generate the NPC's `internal_thought` and `subjective_belief`, and one to generate the final spoken response. Output logs from this phase recorded generation times of approximately 4–8 seconds per turn in cognitive processing alone — before the second call for dialogue generation. In a game context where player-facing response time directly determines the quality of the experience, this latency was prohibitive.

The `CognitiveThoughtMatcher`, introduced on 9 March 2026, replaced the first LLM call entirely. The matcher operates against a library of 810 pre-authored thought-pattern templates (`cognitive_thoughts.json`), each carrying a `bias_type`, variant text strings, and a `match_weights` dictionary. Template selection is a weighted scoring algorithm that executes in sub-millisecond time. The practical result was a reduction in cognitive processing from 4–8 seconds to effectively zero, with no material reduction in the qualitative coherence of thought outputs as assessed by log inspection.

A second major revision was the introduction of the `INTENTION_REGISTRY` to replace free-form intention generation. The prototype's socialisation layer returned unstructured intention strings that were passed directly to the scenario FSM as transition conditions. Because the LLM producing these strings was non-deterministic, the FSM could not reliably match them against scenario-defined transition keywords, causing routing failures that were observable as unexpected conversation terminations or node repetitions in the output logs. Replacing this with a closed canonical vocabulary of registered intention types made every FSM transition deterministic: the scenario FSM always receives one of a finite set of known strings, and transition routing is guaranteed to match.

The terminal outcome architecture was a third structural revision, introduced in response to narrative incoherence observed in early test logs. The prototype's single-outcome system allowed conversations to end at any turn, producing abrupt terminations with no narrative arc. The two-tier system (interaction outcomes + terminal outcomes) separates per-turn consequences from full-conversation consequences, and the judgement score — a 0–100 integer that aggregates dice outcomes across turns — provides a more robust routing signal than the raw `player_relation` float, which proved too volatile under small per-turn deltas.

[**FIGURE: CHANGELOG timeline or annotated version history showing the three major revision points**]

### 5.3.2 Parameter Tuning

The numerical parameters governing the pipeline — difficulty modifiers, skill check thresholds, NPC resistance formula weights, cognitive-to-desire bias intensity boosts, confrontation level clamping values — were tuned iteratively through a cycle of test run → log inspection → value adjustment. The primary evaluation criterion was qualitative: did the output log reflect intuitively plausible NPC behaviour for the given personality profile and player input?

The difficulty modifier values (`SIMPLE: +0.15`, `STANDARD: 0.0`, `STRICT: -0.15`) were established through test runs at each difficulty tier against multiple NPC profiles, calibrating the values to produce success rates that felt appropriately challenging at standard difficulty without making success trivially easy at simple difficulty or statistically impossible at strict difficulty. Similarly, the NPC resistance formula constants (e.g. `0.3 + assertion × 0.4` for authority challenges) were tuned to ensure that a maximally assertive NPC (assertion = 1.0) produces a resistance of 0.7 — difficult but not unbeatable — while a minimally assertive NPC produces a resistance of 0.3, still non-trivial.

The `BIAS_TO_DESIRE_MODIFIER` intensity boost values (e.g. `hostile_attribution: +0.2`, `empathy_resonance: +0.25`) were calibrated to ensure that cognitive bias reliably shifts the desire state's downstream consequences without overwhelming the keyword-pattern logic. Too large a boost would effectively bypass the pattern matching; too small would render the bias modifier invisible in the output. Claude was employed as a diagnostic tool throughout this process: output logs were provided with a description of the expected behaviour, and discrepancies between expected and observed NPC state transitions were used to identify which parameter was out of range. Manual investigation followed any case where AI-assisted diagnosis was inconclusive.

### 5.3.3 Limitations

**The Ollama Bottleneck**

The LLM integration remains the system's primary limitation, and it is also the system's most distinctive feature — the component that gives NPCs their linguistic expressiveness. The `qwen2.5:3b` model, operating within a 4 GB VRAM budget, produces response generation times that are acceptable at low concurrency but would degrade significantly in a live game scenario with multiple simultaneous NPC conversations. More substantially, the model does not reliably adhere to prompt constraints across all inputs. In cases where the prompt's emotional context is complex or the `min_response`/`max_response` anchors are stylistically distant from the model's training distribution, the response can drift: the model may produce a response that is grammatically coherent but tonally inconsistent with the specified behavioural intention, or may append a meta-commentary on its own output, as observed in several turns of the `new_amourie_door.json` log.

This is a known limitation of small-scale quantised models: the instruction-following capability of `qwen2.5:3b` is materially weaker than that of larger models such as `qwen2.5:7b` or `qwen2.5:14b`, which would require 8 GB and 16 GB VRAM respectively. The system's design deliberately anticipates this: because the pipeline generates a complete, structured context before the LLM is called, a player on more capable hardware who switches to a larger model will receive the same deterministic pipeline behaviour with qualitatively better surface text, without any modification to the engine. This hardware-scalability is a design property, not an accident.

**Audience Constraint**

A corollary of the VRAM requirement is that the system in its current form is best suited to the mid-to-high end of the consumer PC market. Players on laptops with integrated graphics or older discrete GPUs below the 4 GB VRAM threshold cannot run the system in a playable configuration on a capable model. This constrains the potential audience in a way that distinguishes the PNE from cloud-API-based dialogue systems, which impose no local hardware requirement. The trade-off is an intentional one — player privacy and offline operation are preserved — but it represents a genuine restriction on accessibility.

**Prompt Adherence and Hallucination**

Beyond latency, the quality ceiling for `qwen2.5:3b` in creative dialogue tasks is lower than current state-of-the-art models. The model occasionally hallucinates character context not present in the prompt, produces responses that address the LLM's role rather than the NPC's, or generates text that is tonally flat relative to the emotional valence specified. These failures are observable in the test logs and are qualitatively distinguishable from failures in the deterministic pipeline stages. Importantly, because the pipeline operates independently of LLM output quality, the NPC's internal state is always correctly computed even when the surface text is weak — which means that upgrading the model improves output quality without requiring any changes to the pipeline logic.

**Scenario Scope**

The test corpus is limited to a small number of handcrafted scenarios centred on the `door_guard` interaction type. The system has not been evaluated against scenarios with more than four turns per conversation node, scenarios with multiple concurrent NPC participants, or scenarios that require the engine to handle adversarial or incoherent player input. These represent gaps in validation coverage rather than design failures, but they qualify the confidence with which the system's behaviour can be generalised beyond the evaluated scenarios.

---
