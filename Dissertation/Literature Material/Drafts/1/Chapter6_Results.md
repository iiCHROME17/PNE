# Chapter 6: Results

---

## 6.1 Overview

This chapter presents the results of structured test conversations conducted against three NPCs in the `door_guard_night` scenario: Krystian 'Krakk' Klikowicz, Morisson Moses, and Troy. Each NPC carries a distinct psychological profile — different cognitive dimensions, social parameters, ideological alignments, and in two cases, wildcard modifiers. Testing across three profiles establishes whether the pipeline produces meaningfully different internal states in response to the same player inputs, and whether those differences are directly traceable to NPC personality parameters rather than to LLM variation.

Each NPC's full JSON profile is presented first, followed by a turn-by-turn BDI breakdown sourced from the conversation logs. A fourth test set — two comparative runs against Troy using contrasting player skill builds — is presented in Section 6.4, targeting the specific question of whether player stat distributions alone produce divergent outcomes against an identical NPC in identical conditions.

Full turn-by-turn BDI breakdowns for all three NPCs are recorded in Tables 6.1.1 (Krakk), 6.1.2 (Morisson Moses), and 6.1.3 (Troy).

---

## 6.2 NPC Profiles

### 6.2.1 Krystian 'Krakk' Klikowicz

**Table 6.2.1 — NPC JSON Profile: Krystian 'Krakk' Klikowicz**

| Block | Field | Value |
|---|---|---|
| **Metadata** | Name | Krystian 'Krakk' Klikowicz |
| | Age | 28 |
| | Faction | Runners |
| | Social Position | Boss |
| **Cognitive** | `self_esteem` | 0.5 |
| | `locus_of_control` | 0.8 |
| | `cog_flexibility` | 0.4 |
| **Social** | `assertion` | 0.3 |
| | `conf_indep` | 0.9 |
| | `empathy` | 0.8 |
| | `ideology` | Libertarianism 0.9, Individualism 0.1 |
| | `wildcard` | Inferiority |
| **World** | `player_relation` (start) | 0.5 |
| | `known_events` | hop_removal, dysphoria_expansion, runner_coordination |
| | `known_figures` | Amourie Othella, Morisson Moses, Jean Pope Chautlier |

Krakk's profile encodes a character who probes rather than confronts. His low assertion (`0.3`) and high empathy (`0.8`) make him receptive to sincere, well-framed approaches; his very high `conf_indep` (`0.9`) means he operates on personal judgement almost exclusively and is resistant to ideological pressure from outside his own framework. His strong Libertarian ideology (`0.9`) makes him especially responsive to appeals that frame the player's offer in terms of autonomy, utility, and freedom of movement. The `Inferiority` wildcard introduces a hard override under pressure — if the player's authority tone exceeds a defined threshold, Krakk's deep need to prove his worth can suppress the normal intention flow — though this did not fire during the test run presented here.

---

### 6.2.2 Morisson Moses

**Table 6.2.2 — NPC JSON Profile: Morisson Moses**

| Block | Field | Value |
|---|---|---|
| **Metadata** | Name | Morisson Moses |
| | Age | 35 |
| | Faction | Insurgency |
| | Social Position | Boss |
| **Cognitive** | `self_esteem` | 0.8 |
| | `locus_of_control` | 0.475 |
| | `cog_flexibility` | 0.3 |
| **Social** | `assertion` | 1.0 |
| | `conf_indep` | 0.7 |
| | `empathy` | 0.45 |
| | `ideology` | Utilitarianism 0.8, Authoritarianism 0.2 |
| | `wildcard` | Martyr |
| **World** | `player_relation` (start) | 0.5 |
| | `known_events` | moses_defection, hop_removal, dysphoria_expansion, romancian_takeover, commonman_formed |
| | `known_figures` | Jean Pope Chautlier, Amourie Othella, Krystian Krakk |

Moses is the most confrontational NPC in the test corpus. His maximum assertion (`1.0`), high self-esteem (`0.8`), and low cognitive flexibility (`0.3`) produce a resistance profile that makes him exceptionally difficult to reach through authority-based approaches. His near-balanced locus of control (`0.475`) reflects his worldview: outcomes are shaped by both individual action and systemic forces, which grounds his Utilitarian ideology — decisions must serve the Insurgency's collective survival, not personal sentiment. The `Martyr` wildcard is the most extreme in the current NPC set: under ideological pressure, it can hard-select `Defend Cause Passionately` at near-maximum confrontation, temporarily overriding the standard desire-to-intention flow. This fired twice during the test run.

---

### 6.2.3 Troy

**Table 6.2.3 — NPC JSON Profile: Troy**

| Block | Field | Value |
|---|---|---|
| **Metadata** | Name | Troy |
| | Age | 25 |
| | Faction | Insurgency |
| | Social Position | Vice |
| **Cognitive** | `self_esteem` | 0.2 |
| | `locus_of_control` | 0.85 |
| | `cog_flexibility` | 0.1 |
| **Social** | `assertion` | 0.8 |
| | `conf_indep` | 0.1 |
| | `empathy` | 0.5 |
| | `ideology` | *(none)* |
| | `wildcard` | *(none)* |
| **World** | `player_relation` (start) | 0.5 |
| | `known_events` | moses_defection |
| | `known_figures` | Morisson Moses |

Troy is the simplest psychological profile in the test corpus, and in some ways the most demanding to navigate. His very low self-esteem (`0.2`) makes him reactive to perceived disrespect; his very low cognitive flexibility (`0.1`) means that once he forms an initial read on the player, it reinforces itself rather than updating. His strong assertion (`0.8`) produces mid-to-high confrontation levels under pressure. Crucially, he carries no ideology dictionary and no wildcard — his behaviour is driven entirely by the base BDI pipeline with no override pathway. His very low `conf_indep` (`0.1`) reflects his defining characteristic: he is devoutly loyal to Moses and the Insurgency, meaning appeals to shared cause are among the few routes that consistently move him.

---

## 6.3 Cross-NPC Response to the Same Player Input

The most direct evidence that the pipeline responds to NPC personality — rather than producing uniform outputs — comes from comparing how Troy and Morisson Moses processed the identical opening choice: `open_authority` (*"I don't need to justify myself to a door guard. We're fighting the same war. Open the door."*).

Both NPCs received the same player text. Both produced negative emotional valence (`−0.45`). Beyond that, their pipeline states diverged substantially across every subsequent layer.

**Table 6.3.1 — Pipeline State Comparison: Troy vs Morisson Moses, `open_authority`**

| Layer | Troy | Morisson Moses |
|---|---|---|
| Bias Type | `black_white_thinking` | `ideological_filter` |
| Internal Thought | "There's no middle ground here. Never was." | "They're framing this wrong. The whole premise is off." |
| Subjective Belief | "I need to know which side of this they're on before I say another word." | "The way they're framing this tells me they haven't fully reckoned with what this costs." |
| Desire Type | `dominance` | `protection` |
| Desire Intensity | 0.90 | 0.75 |
| Intention Type | Challenge Back | Defend Cause Passionately |
| Confrontation Level | 0.654 | **0.978** |
| Wildcard Triggered | No | **Yes (Martyr)** |
| Relation Delta | −0.15 | −0.15 |
| NPC Response | *"You picked the wrong side, and you know it. Move."* | *"You've got more questions than answers, pal. Move it or lose your balls."* |

Troy's low cognitive flexibility (`0.1`) and binary worldview produced a `black_white_thinking` bias — the authority challenge was processed as a loyalty binary, generating a `dominance` desire and a mid-range confrontation level of `0.654`. His response was blunt but contained.

Moses processed the same input through an `ideological_filter` bias — his entrenched Utilitarian worldview and maximum assertion caused him to evaluate the challenge not as a loyalty test but as evidence of ideological misalignment. His `Martyr` wildcard fired, bypassing the normal intention scoring and hard-selecting `Defend Cause Passionately` at `0.978` confrontation. His response was significantly more explosive.

The divergence is entirely attributable to their personality parameters. The pipeline processed the same input text and produced different bias categories, different desire states, different intention types, radically different confrontation levels, and qualitatively different spoken outputs. Neither response was authored directly — both emerged from the NPCs' respective psychological configurations.

Krakk did not receive `open_authority` in his test run; he received `open_diplomacy` instead. The resulting pipeline state is shown in Table 6.1.1 and discussed in 6.4.1 below. The contrast between Krakk's `+0.45` positive valence on a diplomatic opener and Troy and Moses's `−0.45` negative valence on the authority opener further illustrates how the same scenario produces fundamentally different conversational trajectories depending on both NPC profile and player approach.

---

## 6.4 Individual NPC Conversation Logs

### 6.4.1 Krakk Klikowicz — 2-Turn SUCCEED

**[Table 6.1.1 — Full BDI Breakdown: Krakk Klikowicz]**

Krakk reached the terminal `SUCCEED` condition in two turns — the shortest run of the three. The diplomatic opening (`open_diplomacy`) triggered `confirmation_bias`, the cognitive layer reading his own values into the player's framing: *"Their values and mine are close enough to matter."* His emotional valence was `+0.45`, producing an `information-seeking` desire at intensity `0.6` and a `Neutral Evaluation` intention at confrontation `0.5`. His `cog_flexibility` shifted upward by `+0.05` following the outcome, reflecting a slight increase in openness as the conversation proceeded constructively. The relation delta was `+0.10`.

The `concrete_value` choice on turn 2 met the terminal condition before a second NPC response was generated. Final `player_relation`: `0.75`. The `Inferiority` wildcard did not fire — the diplomatic approach never triggered the authority tone threshold that activates it, meaning Krakk's behaviour throughout followed the normal BDI flow without override. This run demonstrates the pipeline's behaviour for a high-empathy, high-independence NPC approached through ideologically aligned framing.

---

### 6.4.2 Morisson Moses — 4-Turn SUCCEED

**[Table 6.1.2 — Full BDI Breakdown: Morisson Moses]**

Moses required four turns to reach `SUCCEED`, the joint-longest run. The `Martyr` wildcard fired on turns 1 and 3 — both on choices carrying adversarial or ideologically challenging framing (`open_authority` on turn 1, `mutual_challenge` on turn 3). Both wildcard-triggered turns selected `Defend Cause Passionately` at `0.978` confrontation with `explosive` emotional expression, producing the highest confrontation values in the entire test corpus.

Turn 2 (`authority_soften`) produced a meaningful pipeline shift. The player's admission of pushing too hard triggered `ideological_filter` bias again, but this time with positive valence (`+0.45`), shifting Moses's desire from `protection` to `information-seeking` at lower intensity (`0.55`). The wildcard did not fire on this turn — the softened framing did not meet the ideological pressure threshold. The intention dropped to `Challenge to Reveal Truth` at confrontation `0.9`, and the relation recovered by `+0.08`. The only personality attribute shift across Moses's run occurred here: `cog_flexibility +0.03`, a small but observable crack in his rigidity.

Turn 3 (`mutual_challenge`) re-triggered the wildcard, but the accumulated positive relation meant the terminal condition was close. Turn 4 (`concrete_value`) met it. Moses's final `player_relation` of `0.68` — the lowest SUCCEED score across all runs — reflects the accumulated cost of opening with an authority challenge against the system's most confrontational NPC. The score represents a grudging, transactional success rather than a cooperative one, which is consistent with Moses's profile and his final dialogue: *"You showed potential with your offers, now deliver on them or step back."*

---

### 6.4.3 Troy — 4-Turn SUCCEED

**[Table 6.1.3 — Full BDI Breakdown: Troy]**

Troy's run produced the highest final `player_relation` of the three primary tests (`1.0`) despite opening with the same authority challenge as Moses. The difference lies in what followed. Troy's `black_white_thinking` bias on turn 1 produced a `dominance` desire — he categorised the player as potentially adversarial — but the recovery turn (`authority_soften`) triggered `confirmation_bias` rather than continued hostility. His subjective belief shifted to *"They're framing this through the same lens I use"*, indicating that the acknowledgement of overreach was processed through his loyalty framework as evidence of ideological alignment rather than weakness. The desire shifted from `dominance` to `information-seeking` and the relation recovered by `+0.08`.

Turn 3 (`concrete_value`) produced the same `confirmation_bias` and sustained the positive trajectory with a further `+0.15` relation delta. Troy's `cog_flexibility` did not change significantly across any turn, consistent with his base value of `0.1` — his rigid thinking reinforced each new positive reading rather than creating nuance. Turn 4 (`mutual_challenge`) triggered the terminal condition. His final dialogue — *"You have shown initiative; let's see what you can do next."* — reflects a character who has made a binary decision in the player's favour, fully consistent with his psychological profile.

The contrast between Troy's `1.0` final relation and Moses's `0.68` is notable given that both ran four turns and both opened with the same authority challenge. The difference is attributable to their respective personality parameters: Troy's low `conf_indep` (`0.1`) made him susceptible to the shared-cause framing of the middle turns in a way that Moses — with his higher independent judgement and ideological rigidity — was not.

---

## 6.5 Comparative Run: Player Build vs. Same NPC

To isolate the effect of player skill distribution on pipeline output, the `door_guard_night` scenario was run twice against Troy using contrasting `PlayerSkillSet` configurations under matched choice conditions.

**[Figure 6.4.1 — Player skill build configurations: Run A (Empathy) and Run B (Assertion)]**

**Run A — Empathy Build** (`authority: 2, diplomacy: 5, empathy: 9, manipulation: 2`):
The empathy-weighted skill set biased the player's dice toward empathetic choices. The `open_empathy` opener (*"I've seen what this regime does to people..."*) triggered `ideological_filter` bias with positive valence (`+0.45`), producing `information-seeking` desire at intensity `0.65` and a `Neutral Evaluation` intention. Troy's internal thought: *"Finally — someone who understands what we're actually up against."* The `concrete_value` follow-up met the terminal condition. Terminal: **SUCCEED**. Final `player_relation`: `1.0`.

**Run B — Assertion Build** (`authority: 9, diplomacy: 5, empathy: 2, manipulation: 2`):
The authority-weighted build biased the dice toward commanding choices. The `open_authority` opener triggered `black_white_thinking` bias with negative valence (`−0.45`), producing `dominance` desire at intensity `0.90` and `Challenge Back` intention at confrontation `0.515`. The recovery attempt (`authority_soften`) was processed through `confirmation_bias` but produced a `backpedal_rejected` outcome (`relation_delta: −0.05`) — Troy's rigid cognitive model had already categorised the player negatively, and the backpedal was read as confirmation of tactical calculation rather than genuine recalibration. Terminal: **FAIL**. Final `player_relation`: `0.75`.

**Table 6.5.1 — Comparative Run Summary: Troy Empathy Build vs Assertion Build**

| | Run A (Empathy) | Run B (Assertion) |
|---|---|---|
| Player skill profile | authority: 2, empathy: 9 | authority: 9, empathy: 2 |
| Opening choice | `open_empathy` | `open_authority` |
| Turn 1 bias type | `ideological_filter` | `black_white_thinking` |
| Turn 1 internal thought | "Finally — someone who understands what we're actually up against." | "There's no middle ground here. Never was." |
| Turn 1 desire type | information-seeking | dominance |
| Turn 1 desire intensity | 0.65 | 0.90 |
| Turn 1 emotional valence | +0.45 | −0.45 |
| Turn 1 relation delta | +0.15 | −0.15 |
| Turns to terminal | 2 | 3 |
| Terminal outcome | **SUCCEED** | **FAIL** |
| Final `player_relation` | 1.0 | 0.75 |

The same NPC, the same scenario, and largely the same choice pool produced divergent pipeline states and opposite terminal outcomes. The mechanism is the `PlayerSkillSet`: the dice bias determined which choices succeeded at the skill check level, which shaped the player input signals reaching the cognitive layer, which cascaded through the belief-keyword matching in the desire layer and the confrontation scoring in the intention layer, through to the judgement score threshold that triggered the terminal routing. The divergence is structural and traceable at every pipeline stage — it is not a product of LLM variation, since the determining logic (cognitive through intention layers) operates entirely deterministically.

---

## 6.6 Terminal Outcome Summary

**Table 6.6.1 — Terminal Outcome Summary Across All Test Runs**

| NPC | Approach | Turns | Wildcard Fires | Final Relation | Terminal |
|---|---|---|---|---|---|
| Krakk Klikowicz | Diplomatic | 2 | 0 | 0.75 | SUCCEED |
| Morisson Moses | Authority → Recovery | 4 | 2 (Martyr) | 0.68 | SUCCEED |
| Troy (6.1 run) | Authority → Recovery | 4 | 0 | 1.0 | SUCCEED |
| Troy (Empathy build) | Empathetic | 2 | 0 | 1.0 | SUCCEED |
| Troy (Assertion build) | Authority | 3 | 0 | 0.75 | FAIL |

Across five test runs, the system produced four SUCCEED outcomes and one FAIL. The single FAIL is the most diagnostically valuable result in the corpus: it demonstrates that the terminal routing is not trivially permissive, and that approach against a psychologically resistant NPC carries genuine mechanical consequence. Moses's `0.68` final relation — the lowest SUCCEED score — further illustrates that the system distinguishes between clean successes and hard-won ones. The two-turn SUCCEED outcomes (Krakk and Troy empathy build) demonstrate the other end of the spectrum: an aligned approach against a receptive NPC profile can close a conversation efficiently, without requiring a long recovery arc.

The wildcard results are also informative in aggregate. Moses's `Martyr` wildcard fired twice in four turns, producing the pipeline's near-maximum confrontation level on both occasions. Krakk's `Inferiority` wildcard did not fire at all across his run. Troy carries no wildcard. This distribution reflects the design intention: wildcards are personality-extreme overrides that activate under specific conditions, not persistent modifiers that dominate every conversation. Their presence in the corpus — fired twice in one run, inactive in two others — is consistent with their intended role.

---
