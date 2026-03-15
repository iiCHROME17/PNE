# Final Pipeline Design

**Psychological Narrative Engine — complete architecture reference**

This document supersedes the Prototype Pipeline Design. It reflects the fully implemented system including the Desire Formation layer, Intention Registry, 2-dice skill-check system, Judgement scoring, Recovery Mode, two-stage Choice Filtering, Cognitive Thought Matcher, Ollama prompt architecture, and scenario-driven dialogue tree engine.

---

## Containment Models

### ConversationModel

Per-NPC dialogue session container. Tracks stage, topic, and turn count for the internal BDI pipeline.

| Attribute | Type | Description |
|---|---|---|
| conversation_id | str | Unique identifier for this dialogue session (scenario_id:npc_id). |
| stage | str | Current conversation phase: opening / development / crisis / resolution. |
| topic | str | Active subject — initialised from the NPC's immediate_intention. |
| turn_count | int | Number of completed player–NPC exchanges this session. |
| history | List[str] | Plain exchange log used by the BDI pipeline's internal Ollama calls. |

### NPCConversationState

Per-NPC runtime state held by the NarrativeEngine inside a ConversationSession. Carries all live data needed between turns.

| Attribute | Type | Description |
|---|---|---|
| npc_id | str | Registry key used to look up the NPCModel. |
| npc | NPCModel | The live NPC model — mutated by outcome effects each turn. |
| processor | DialogueProcessor | Per-NPC BDI pipeline executor. |
| scenario_id | str | The scenario this NPC belongs to. |
| current_node | str | Active dialogue-tree node ID (e.g. 'start', 'trust_check'). |
| judgement | int 0–100 | Accumulates judgement_delta values each turn. Drives transition conditions. |
| history | List[dict] | Full exchange log with per-turn BDI metadata (thought, desire, intention, outcome). |
| choices_made | List[str] | Ordered log of choice_ids — used for anti-repetition filtering. |
| recovery_mode | bool | True when awaiting a recovery choice after a failed skill check. |
| pending_recovery_choices | List[dict] | Recovery choices served instead of the node's normal choices. |
| pending_recovery_parent | Optional[str] | choice_id that triggered recovery — marked failed if recovery also fails. |
| failed_choices | Set[str] | Permanently exhausted choice paths (main + recovery both failed). |
| is_complete | bool | True once a terminal node has been reached. |
| terminal_outcome | Optional[dict] | terminal_id, result, and final_dialogue when conversation ends. |

---

## Conceptual Models

### Cognitive Model

| Attribute | Value | Explanation |
|---|---|---|
| Self-Esteem | 0–1 (Float) | NPC's internal sense of worth. High = confident decision-making; low = vulnerability to social influence and self-doubt. Also drives resistance threshold for Manipulation skill checks. |
| Locus of Control | 0–1 (Float) | Perceived control over outcomes. 0 = external (blames fate/others); 1 = internal (believes own actions determine results). Influences how the NPC interprets responsibility in dialogue. |
| Cognitive Flexibility | 0–1 (Float) | Ability to adapt beliefs when presented with new information. Low = rigid, dogmatic; high = adaptive, open to persuasion or compromise. Inversely drives the resistance threshold for Diplomacy checks. |

### Social Personality Model

| Attribute | Value | Explanation |
|---|---|---|
| Assertion | 0–1 (Float) | 0 = highly passive (easily persuaded); 1 = highly assertive (challenges player, sticks to opinion). Drives resistance threshold for Authority checks and NPC confrontation level. |
| Conformity/Independence | 0–1 (Float) | 0 = high conformity (follows group norms); 1 = high independence (acts autonomously). Used as a secondary input to NPC confrontation tendency (30% weight vs 70% for assertion). |
| Empathy | 0–1 (Float) | 0 = highly self-focused; 1 = highly empathetic. Governs responsiveness to emotional appeals and inversely drives resistance for Empathy checks. |
| Ideology | Dict[str,float] | Mapping of ideology keywords to alignment strength (0–1). Used in Desire Formation Pattern 5: strong alignment (>0.6) triggers affiliation desire. |
| Wildcard | str (Optional) | Psychological modifier representing a deep-seated complex (e.g. Martyr, Napoleon, Inferiority). Can hard-override the desire→intention flow and drive unique Ollama temperature settings. |
| Faction | str | Political or social affiliation (e.g. Insurgent Militia, Runner Network). Provides factional context to the Ollama identity prompt. |
| Social Position | Enum | Rank within faction: Boss / Vice / Higher / Member. Determines authority framing in the Ollama identity prompt. |

### World Perception Model

| Attribute | Value | Explanation |
|---|---|---|
| Personal History | str | Objective record of NPC-specific experiences — milestones, trauma, achievements. Injected verbatim into the Ollama BACKGROUND prompt section. |
| Player History | str | Record of observable prior player interactions with this NPC. Injected into the Ollama BACKGROUND prompt; interpreted through the NPC's cognitive model. |
| Player Relation | 0–1 (Float) | How much trust and respect exists between NPC and player. 0 = contempt, 0.5 = neutral, 1 = close alliance. Used as a dice bias (±RELATION_CAP 10%) and drives the Ollama disposition note. |
| Known Events | List[str] | World events the NPC is aware of. Formatted as human-readable text in the Ollama BACKGROUND prompt. |
| Known Figures | List[str] | Notable people the NPC knows of. Formatted in the Ollama BACKGROUND prompt alongside known events. |

---

## Player Model

### PlayerSkillSet

The player's four language-art proficiency levels on a 0–10 integer scale. Skill values directly set the player die-weight bias during the 2-dice check: skill 10 → heavily top-weighted d6; skill 0 → bottom-weighted.

| Skill | Scale | Language Art Mapped To |
|---|---|---|
| Authority | 0–10 int | CHALLENGE — commands, assertions, direct pressure. |
| Diplomacy | 0–10 int | DIPLOMATIC — reasoned argument, cooperative framing. |
| Empathy | 0–10 int | EMPATHETIC — emotional connection, personal appeal. |
| Manipulation | 0–10 int | MANIPULATIVE — misdirection, flattery, subtle persuasion. |

### PlayerDialogueInput

Structured representation of a single player choice. Created by ScenarioLoader.parse_player_input() and passed unchanged through the entire BDI pipeline each turn.

| Attribute | Type | Description |
|---|---|---|
| choice_text | str | Display text of the selected choice — logged verbatim. |
| language_art | LanguageArt | Rhetorical category (NEUTRAL / CHALLENGE / DIPLOMATIC / EMPATHETIC / MANIPULATIVE). Determines which skill is used for the dice check. |
| authority_tone | float 0–1 | Commanding quality of the line. Drives wildcard hard-overrides (e.g. Inferiority → Submit). |
| diplomacy_tone | float 0–1 | Perceived conciliatory or cooperative quality. |
| empathy_tone | float 0–1 | Perceived emotional understanding or vulnerability. |
| manipulation_tone | float 0–1 | Perceived persuasive or deceptive quality. |
| ideology_alignment | Optional[str] | Ideology keyword the choice appeals to — matched against npc.social.ideology in Desire Formation Pattern 5. |
| contextual_references | List[str] | World-state tags the choice references — available for cognitive template matching. |

---

## Skill Check System

Two complementary mechanisms coexist:

**2-Dice System (primary)** — used by the NarrativeEngine for the authoritative success/failure signal each turn.

**Threshold System (legacy)** — used internally by DialogueProcessor to gate temporary NPC attribute modifiers.

### 2-Dice Check

Player and NPC each roll one biased d6. player_die ≥ npc_die → SUCCESS (ties go to player). Bias is computed from skill level and NPC resistance threshold respectively using P(face k) ∝ exp(bias × k).

| Concept | Formula / Values | Description |
|---|---|---|
| player_bias | skill / 10 + bias_adj | Die-weight bias for the player roll. Clamped [0,1]. |
| npc_bias | calc_threshold(npc, skill) | NPC resistance — higher = harder for player to beat. |
| bias_adj | relation_bias + difficulty_adj | Additive modifier. relation_bias = (relation – 0.5) × 2 × (RELATION_CAP/100). RELATION_CAP = 10%. |
| Difficulty | SIMPLE +0.15 / STANDARD 0.0 / STRICT –0.15 | Global difficulty shifts player bias up or down. |
| success_pct | Σ P(p≥n) across all face pairs × 100 | Pre-roll display percentage computed analytically before the actual roll. |

### NPC Resistance Thresholds (calc_threshold)

| Skill | Threshold Formula | Psychological Rationale |
|---|---|---|
| AUTHORITY | 0.3 + (social.assertion × 0.4) | Assertive NPCs resist commands more. |
| MANIPULATION | 0.2 + (cognitive.self_esteem × 0.5) | Self-confident NPCs resist deceit. |
| EMPATHY | 0.4 – (social.empathy × 0.2) | Empathetic NPCs are receptive → lower threshold. |
| DIPLOMACY | 0.3 – (cognitive.cog_flexibility × 0.3) | Cognitively rigid NPCs resist reasoning → higher threshold. |

---

## Judgement System

Each turn's dice outcome feeds into a 0–100 Judgement score tracked per NPCConversationState. Transition conditions can gate on judgement thresholds to route dialogue flow.

| Concept | Description |
|---|---|
| judgement_delta_success | Positive or negative integer delta applied when the skill check succeeds. |
| judgement_delta_fail | Negative integer delta applied on failure. |
| Risk Multiplier | When success_pct < 50, delta is scaled by (50 / success_pct) — high-risk choices have amplified consequences. |
| Judgement range | Clamped 0–100. Used in transition conditions (e.g. 'judgement >= 60 → trust_node'). |

---

## Recovery Mode

When a skill check fails on a choice that defines recovery_choices, the engine enters recovery mode for that NPC. On the next turn it serves the recovery choices instead of the node's normal ones, giving the player a second attempt. If the recovery also fails, the parent choice_id is added to failed_choices and permanently removed from future turns.

---

## Choice Filtering Pipeline

Every turn, get_available_choices() runs choices through two sequential stages before presenting them to the player.

### Stage 1 — ChoiceFilter (Hard Gates)

Permanently removes choices that cannot legally be selected given current state. Uses smart_fallback: if all choices are filtered, the filter is relaxed to always return at least one option.

| Gate | Description |
|---|---|
| Skill threshold | Removes choices requiring a minimum skill level the player doesn't have. |
| Player relation | Removes choices gated on minimum trust (e.g. require_relation >= 0.6). |
| NPC state flags | Removes choices blocked by NPC flags (e.g. already_accepted, already_refused). |
| Prerequisites | Removes choices requiring prior choice_ids in choices_made. |
| allowed_after_intentions | Removes choices only valid after a specific NPC intention_shift has occurred. |
| failed_choices | Removes permanently exhausted choice paths. |

### Stage 2 — DialogueMomentumFilter (Coherence Scoring)

Scores remaining choices on conversational coherence. Choices scoring below 0.3 are removed. If all choices would be removed, the stage is skipped as a safety net.

| Dimension | Weight | Description |
|---|---|---|
| Momentum Alignment | 40% | Does this choice respond to what the NPC just communicated? Inferred from the last intention_shift text (e.g. challenge_posed, acceptance_signaled). |
| Stage Appropriateness | 30% | Is this choice appropriate for the current conversation stage (opening / development / crisis / resolution)? |
| Anti-Repetition | 20% | Penalise choices the player has used recently — light penalty after 1 use, heavy penalty after 2+ uses in last 3 turns. |
| Relation Plausibility | 10% | Some choices need minimum trust (vulnerable choices), others have synergy at higher relation. |

---

## Desire Formation Layer (NEW)

The Desire Formation layer sits between Cognitive Interpretation and the Socialisation Filter. It converts the NPC's subjective belief into a goal-oriented DesireState, giving the BDI pipeline a clean Belief → Want → Intention chain.

### DesireState

| Attribute | Type | Description |
|---|---|---|
| immediate_desire | str | Natural-language goal description (e.g. 'Test their commitment and sincerity'). |
| desire_type | str | Broad motivational category used to filter the Intention Registry: • information-seeking — probe, evaluate, test. • affiliation — connection, trust, cooperation. • protection — guard, withdraw, resist. • dominance — assert, challenge, control. |
| intensity | float 0–1 | Desire strength. Pushes the selected intention's confrontation level toward the upper end of its valid range. |

### Belief-Keyword Patterns (7, evaluated in priority order)

| Priority | Trigger | Base Desire |
|---|---|---|
| 1 | Uncertainty keywords (unclear, unsure, testing, cheap, words) | information-seeking or protection — branches on NPC self-esteem > 0.6. |
| 2 | Sincerity keywords (genuine, sincere, authentic, real, honest) | affiliation or guarded information-seeking — branches on NPC empathy > 0.5. |
| 3 | Threat keywords (manipulative, threat, challenging, attack, deceive) | protection or dominance — branches on Martyr wildcard and assertion > 0.7. |
| 4 | Opportunism keywords (opportunistic, using, exploit, advantage) | information-seeking — NPC suspects they are being used. |
| 5 | Ideology alignment (player_input.ideology_alignment in npc.social.ideology) | affiliation if alignment_strength > 0.6, else information-seeking. |
| 6 | Emotional valence defaults (valence < –0.3 or valence > 0.3) | protection (negative) or affiliation (positive). |
| 7 | Fallback — driven by npc_intent.long_term_desire keywords | information-seeking (protect/secure/power/control) or information-seeking (default). |

### Cognitive Bias Modifier (BIAS_TO_DESIRE_MODIFIER)

Applied after pattern selection. Can override desire_type and add to intensity (capped at 1.0). Ensures two NPCs with different cognitive biases react differently to the identical player choice.

| Bias Type | desire_type Override | Intensity Boost | Effect |
|---|---|---|---|
| hostile_attribution | protection | +0.20 | Always reads intent as threatening. |
| optimism_bias | affiliation | +0.15 | Sees opportunity in almost anything. |
| confirmation_bias | information-seeking | +0.10 | Wants validation of existing beliefs. |
| empathy_resonance | affiliation | +0.25 | Unusually receptive to emotional signals. |
| cynical_realism | (none) | +0.00 | Accepts base desire unchanged. |
| ideological_filter | (none) | +0.15 | Frames everything through ideology lens. |
| self_referential | dominance | +0.10 | Makes it personal — pushes self-assertion. |
| projection | protection | +0.10 | Assumes player wants what NPC fears. |
| in_group_bias | (none) | +0.20 | 'Are they one of us?' — intensity boost only. |
| black_white_thinking | dominance | +0.30 | No middle ground — strong dominance push. |
| scarcity_mindset | protection | +0.25 | Fears loss above all else. |

---

## Intention Registry (NEW)

A closed vocabulary of canonical NPC behavioural intentions. The SocialisationFilter selects from this list; TransitionResolver matches against these names in scenario transition rules. This guarantees that every intention produced by the BDI pipeline can be reliably routed by the scenario author.

### IntentionTemplate

| Attribute | Type | Description |
|---|---|---|
| name | str | Canonical name used in scenario transitions and Ollama prompts (e.g. 'Challenge to Reveal Truth'). |
| desire_type | str | Which desire category produces this intention. Empty string = fallback (matches any). |
| desire_keywords | List[str] | Keywords in the desire text that activate this template during scoring. |
| confrontation_min | float 0–1 | Lower bound of the valid confrontation range for this intention. |
| confrontation_max | float 0–1 | Upper bound. NPC's natural confrontation is clamped into [min, max] then nudged by intensity. |
| emotional_expression | str | Acting direction injected into the Ollama prompt (direct / measured / explosive / suppressed / etc.). |
| wildcard_required | Optional[str] | If set, NPC must have this wildcard trait for the template to be eligible. |
| npc_conditions | Dict | Additional NPC attribute gates, e.g. {'social.assertion': ('>', 0.7)}. |

### Selection Algorithm (SocialisationFilter)

1. **Wildcard hard-override** — some wildcard+player-tone combinations bypass the registry entirely (e.g. Inferiority wildcard + high authority_tone → Submit).
2. **Pre-filter** — keep only templates whose desire_type matches.
3. **Score each candidate** (0–1): keyword overlap (50%), confrontation band fit (40%), intensity bonus (10%), hard gates for wildcard_required and npc_conditions.
4. **Select highest-scoring template** and build BehaviouralIntention.
5. **Fallback** — 'Neutral Response' if nothing passes.

### Registry Summary

| Desire Type | Canonical Intention Names |
|---|---|
| information-seeking | Challenge to Reveal Truth · Carefully Question Motives · Neutral Evaluation · Accept Player for Trial |
| affiliation | Seek Connection · Cautious Openness · Explore Common Ground · Acknowledge with Reservation · Transactional Agreement |
| protection | Defend Cause Passionately (Martyr) · Establish Boundaries · Maintain Distance · De-escalate and Withdraw · Resist Player · Submit (Inferiority) |
| dominance | Assert Dominance Aggressively (Napoleon) · Challenge Back |
| (fallback) | Neutral Response |

---

## Outcome Models

### Interaction Outcome

The immediate conversational effect of the player's line. Not terminal — changes NPC stance, mood, relation, and intention.

| Attribute | Type | Purpose |
|---|---|---|
| outcome_id | str | Identifier for this micro-outcome. |
| stance_delta | dict | Adjusts NPC social + cognitive attributes based on rhetoric success. |
| relation_delta | float | Adjusts the NPC's feeling toward the player (positive or negative). |
| intention_shift | Optional[str] | Changes the NPC's underlying goal (e.g. 'resist' → 'evaluate'). Also drives momentum tag inference for coherence filtering. |
| min_response | str | Negative reaction calibration variant (used as Ollama fallback). |
| max_response | str | Positive reaction calibration variant (used as Ollama fallback). |
| skip_dice | bool | If true, no skill check is performed — choice always succeeds. |

### Terminal Outcome

The end-state of the interaction. Reached when TransitionResolver matches a terminal node based on judgement, relation, turn count, or intention.

| Attribute | Type | Description |
|---|---|---|
| terminal_id | str | Outcome label (SUCCEED / FAIL / NEGOTIATE / DELAY / ESCALATE — or custom). |
| terminal_result | str | What actually happens in the world (door opens, quest unlocks, fight begins, etc.). |
| npc_dialogue_prompt | str | Scene direction passed to Ollama to generate the NPC's final line. |
| conditions | dict | Evaluated by TransitionResolver: turn_count, judgement, intention_match, player_relation, choices_made. |

### Outcome Index

| Attribute | Type | Description |
|---|---|---|
| choice_id | str | The dialogue choice this index is built for. |
| interaction_outcomes | List[InteractionOutcome] | All short-term results available from this choice. |
| failure_outcomes | List[InteractionOutcome] | Outcome set used when the skill check fails. |
| terminal_outcomes | List[TerminalOutcome] | Possible end states evaluated after each exchange. |
| recovery_choices | List[dict] | Follow-up choices offered when the skill check fails (triggers Recovery Mode). |

---

## Cognitive Thought Matcher (NEW)

A template-based replacement for the LLM-based CognitiveInterpreter. Instead of calling Ollama for every cognitive interpretation, this class scores each template in cognitive_thoughts.json against the current player input and NPC state, then picks the highest-scoring winner above a 0.35 threshold.

### Matching Algorithm

1. Extract language_art and numeric NPC/player attributes.
2. For each template: accumulate score from match_weights entries.
   - language_art: discrete lookup (table max counts toward total possible).
   - numeric params: gate on min/max/range; award weight if in range.
3. Normalise score against total possible weight.
4. Select highest-normalised template above THRESHOLD (0.35).
5. Fallback to 'cynical_realism' template if nothing qualifies.
6. Pick a random variant from thought_variants and belief_variants.

### Supported Numeric Parameters in match_weights

| Parameter | Source |
|---|---|
| npc_self_esteem | npc.cognitive.self_esteem |
| npc_locus_of_control | npc.cognitive.locus_of_control |
| npc_cog_flexibility | npc.cognitive.cog_flexibility |
| authority_tone | player_input.authority_tone |
| diplomacy_tone | player_input.diplomacy_tone |
| empathy_tone | player_input.empathy_tone |
| manipulation_tone | player_input.manipulation_tone |
| player_relation | npc.world.player_relation |

---

## Ollama Prompt Architecture

The OllamaResponseGenerator builds a structured prompt from the full NPC model and current BDI state. Every section is guarded with try/except so the prompt degrades gracefully if any field is missing.

### Prompt Structure (generate_response_with_direction)

| Section | Content |
|---|---|
| IDENTITY | Name, age, faction, social position, dominant ideology, cognitive stats (self-esteem/locus/flexibility), social stats (assertion/conf.indep/empathy). |
| BACKGROUND | Personal history, player history, known events, known figures, disposition note (derived from player_relation float). |
| CURRENT STATE | BELIEF (subjective_belief from thought_reaction), INTENTION (intention_type), Stance (confrontation_note), emotional valence note. |
| SCENE DIRECTION | npc_dialogue_prompt from the current scenario node — authorial direction for this beat. |
| DICE CONTEXT | Overrides scene direction. Tells NPC whether the player's skill check SUCCEEDED or FAILED and shows the dice result. Ensures dialogue is grounded in the actual roll outcome. |
| RESPONSE RANGE | Calibration only — min_response and max_response from the interaction outcome. Not to be copied verbatim. |
| HISTORY | Last 6 exchanges from NPCConversationState.history (speaker + text). |
| INSTRUCTION | Generate ONE line as {name}. Stay in character. No action brackets. Under 40 words. |

### Generation Methods

| Method | Description |
|---|---|
| generate_response | Original method — uses BDI objects directly. Called by DialogueProcessor when generate_with_ollama=True. |
| generate_response_with_direction | Primary engine method — accepts BDI context dicts + scene direction from the scenario node. |
| generate_response_with_direction_streaming | Streaming version — yields token strings as Ollama produces them via iter_lines(). |
| generate_terminal | Generates the NPC's final line for a terminal node using a stripped-down prompt. |
| generate_terminal_streaming | Streaming version of generate_terminal. |

### Wildcard Temperature Offsets

Each NPC wildcard can define a wildcard_config with temperature overrides. These are applied on top of the base temperature (0.85) before each Ollama call, giving wildcard characters measurably more (or less) varied output.

---

## Scenario Engine (NarrativeEngine)

The NarrativeEngine is the top-level orchestrator. It manages loaded NPCs, scenarios, and active sessions, and is the only entry point for the CLI and REST API.

### Dialogue Tree

Scenarios are JSON files defining a tree of nodes. Each node has choices, transitions, a default_transition, and an npc_dialogue_prompt for scene direction. The engine is fully NPC-agnostic — scenarios do not reference specific NPCs.

| Node Field | Description |
|---|---|
| choices | List of player choice dicts (choice_id, text, language_art, outcome data, recovery_choices, judgement_delta_success/fail, skip_dice). |
| transitions | List of routing conditions evaluated by TransitionResolver after each turn. |
| default_transition | Node to route to if no transition condition matches. |
| npc_dialogue_prompt | Scene direction injected into the Ollama prompt for mid-turn responses. |
| terminal_id | Present on terminal nodes — marks the end state (SUCCEED/FAIL/etc.). |
| terminal_result | Human-readable outcome description shown at conversation end. |

### TransitionResolver Condition Types

| Condition | Evaluates |
|---|---|
| turn_count >= N | Number of completed turns in this session. |
| judgement >= N | NPC's accumulated judgement score. |
| judgement <= N | Low-judgement path (e.g. trust collapsed). |
| player_relation >= N | Current player_relation float. |
| intention_match: [...] | Whether the last BDI intention_type matches any name in the list. |
| choices_made includes X | Whether the player has previously selected a specific choice_id. |
| is_terminal: true | Marks the target node as a terminal — triggers terminal response flow. |

### ConversationStageDetector

Classifies the current conversation stage from turn count, player relation, and emotional trajectory (list of valence floats from history).

| Stage | Typical Characteristics |
|---|---|
| opening | First 2 turns or relation neutral — establishing tone. |
| development | Turns 3–6 — positions being tested and revealed. |
| crisis | High emotional volatility or very low relation — pressure point. |
| resolution | Late turns or converging intent — approaching terminal. |

---

## Design Explanation

NPC interactions in the final system emerge from the interplay of four core layers: the NPC's psychological models, the Desire Formation bridge, the Intention Registry, and the scenario engine that routes everything toward narrative outcomes. Together they ensure every exchange is grounded in character identity while progressing toward specific story goals.

At the highest level, the NPC Intent layer establishes baseline beliefs, long-term desires, and immediate intentions. This is the purpose-driven scaffold for the entire scene — it defines why the NPC is engaging the player at all, and which terminal outcomes are available. It does not produce dialogue; it sets the constraints that all subsequent reasoning must respect.

Once the player selects a choice, the system first runs a 2-dice skill check (player d6 vs NPC d6, both biased by skill level and resistance threshold). The result immediately determines the judgement delta and which outcome set is consulted, and is later injected into the Ollama prompt as an authoritative grounding signal. High-risk choices — those with success probability below 50% — have their judgement impact amplified by a risk multiplier, making bold attempts genuinely consequential.

The player's chosen rhetoric style is parsed into a PlayerDialogueInput and passed into the NPC's Cognitive Interpretation layer. Here the CognitiveThoughtMatcher scores template patterns against the player's tone signals and the NPC's psychological attributes to produce a ThoughtReaction: a subjective belief, an internal thought, and a cognitive bias type. This is not spoken — it is the NPC's private distortion of the objective input.

The ThoughtReaction feeds into the Desire Formation layer, which is new in the final system. Seven belief-keyword patterns determine a base desire type and immediate goal. The NPC's cognitive bias type then applies a modifier that can sharpen or redirect the desire — ensuring two NPCs with different psychological profiles respond differently to identical player choices.

With a desire established, the Socialisation Filter selects the best-matching BehaviouralIntention from the canonical Intention Registry. This registry defines a closed vocabulary of named intentions — ensuring consistent routing by the TransitionResolver and consistent tone direction in Ollama prompts. The selection algorithm scores templates on keyword overlap, confrontation band fit, and intensity, with wildcard traits capable of hard-overriding the normal desire logic entirely.

The resulting intention selects an Interaction Outcome from the scenario's outcome index. This produces relation and stance changes, and an intention_shift string that updates the NPC's goal and tags the conversation's momentum for the coherence filter. The Ollama prompt is then built from the full NPC model, BDI state, scene direction, and dice result — producing the NPC's spoken line.

Between turns, the two-stage choice filter prepares the next player options. ChoiceFilter hard-gates choices on skill levels, relation, prerequisites, and exhausted paths. DialogueMomentumFilter then scores remaining choices on conversational coherence — ensuring the player responds to what the NPC actually said rather than ignoring it. Failed choices can enter Recovery Mode, offering a follow-up attempt before the path is permanently closed.

The conversation ends when TransitionResolver routes to a terminal node — triggered by accumulated judgement, relation thresholds, intention alignment, or explicit choice prerequisites. A final Ollama call generates the NPC's closing line, and the terminal outcome determines the practical world result: a door opens, a quest unlocks, conflict begins, or the player is turned away.

---

## Pipeline Process (Purpose–Output Model)

### I. Purpose (NPC Intent Layer)

**Purpose:** Give the NPC its goal, identity, backstory, and stakes. This is the meta-BDI root: Beliefs, Desires, Intentions.

**Output:**
- Persistent internal Intention State (immediate_intention, long_term_desire).
- Scenario's terminal outcome set — the possible endings for this scene.
- Player skills and difficulty preset that will govern all dice checks.

### II. Input / Choice Selection

**Purpose:** Player selects a dialogue option from the filtered choice list. The choice is parsed into a PlayerDialogueInput with tone signals.

**Output:**
- PlayerDialogueInput: choice_text, language_art, tone floats, ideology_alignment.
- The rhetoric LanguageArt determines which PlayerSkill is checked in Stage IIa.

### IIa. Skill Check (2-Dice System)

**Purpose:** Player d6 and NPC d6 are rolled with skill-derived bias weights. player_die ≥ npc_die → SUCCESS. Ties go to player.

**Output:**
- DiceCheckResult: player_die, npc_die, success, player_bias, npc_bias.
- Judgement delta applied (risk-multiplied when success_pct < 50).
- Outcome set selected: interaction_outcomes on success, failure_outcomes on failure.
- Dice result stored — injected into Ollama prompt in Stage VI.

### III. Cognitive Interpretation (Belief)

**Purpose:** NPC distorts the input through its cognitive model using CognitiveThoughtMatcher. Templates are scored against player tones and NPC attributes. The winner produces the internal thought.

**Output:**
- ThoughtReaction: internal_thought (not spoken), subjective_belief, emotional_valence.
- bias_type (e.g. hostile_attribution, empathy_resonance) — feeds Desire Formation.

### IV. Desire Formation (Want) ← NEW

**Purpose:** Converts the NPC's belief into a goal-oriented desire using 7 belief-keyword patterns, then applies the cognitive bias modifier.

**Output:**
- DesireState: immediate_desire (natural language), desire_type, intensity.
- desire_type filters the Intention Registry in the next stage.
- intensity nudges the final confrontation level toward the template's upper band.

### V. Socialisation Filter (Intention)

**Purpose:** Selects the best-matching IntentionTemplate from the Intention Registry for the current desire type and NPC social profile.

**Output:**
- BehaviouralIntention: intention_type (canonical registry name), confrontation_level, emotional_expression, wildcard_triggered.
- intention_type is used verbatim in the Ollama prompt and in TransitionResolver routing.
- Wildcard hard-overrides bypass this stage entirely for matching NPC+player combinations.

### VI. Conversational Output (Interaction Outcome + Ollama)

**Purpose:** Produce the NPC's spoken line and update short-term state.

**Output:**
- Relation delta and stance deltas applied to the live NPCModel.
- intention_shift updates NPC intent and tags conversation momentum for coherence filtering.
- Ollama prompt built from NPC identity, BDI state, scene direction, and dice result.
- NPC dialogue generated — one grounded, in-character line under 40 words.

### VII. Terminal Check (Macro-Outcome)

**Purpose:** TransitionResolver evaluates all transition conditions against the current session state. Routes to a terminal node when conditions are met.

**Output:**
- If terminal: final Ollama line generated with terminal node's scene direction.
- terminal_outcome recorded: terminal_id, result, final_dialogue.
- Practical world result: door opens / quest unlocks / fight begins / player turned away.
- If not terminal: route to next node — return to Stage II for the next player turn.
