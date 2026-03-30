# Chapter 1: Introduction

## Abstract

Non-player character (NPC) dialogue in video games has long been constrained by the branching conversation tree — a paradigm that prioritises authored consistency at the cost of psychological depth and adaptive agency. This dissertation presents the Psychological Narrative Engine (PNE), a middleware dialogue system that replaces scripted branching with a staged Belief-Desire-Intention (BDI) processing pipeline, enabling NPC responses to emerge from a structured model of internal cognitive and social state. The system grounds NPC cognition in a three-layer personality representation and a template-matched thought library, then delegates surface text generation to a locally-deployable large language model (LLM) via the Ollama runtime. The central question investigated is whether psychological realism and narrative coherence can be achieved simultaneously with genuine player agency — and whether separating cognitive reasoning from language generation provides a viable architectural basis for doing so.

---

## 1.1 Introduction

The dialogue tree has defined NPC interaction in commercial video games for three decades. From the conversation wheel of *Fallout 4* (Bethesda Game Studios, 2015) to the episodic choice structures of *The Walking Dead* (Telltale Games, 2012), the dominant model has remained the same: a developer authors every possible exchange in advance, a player selects from a fixed set of options, and the system traverses a predetermined graph. This produces narratively consistent experiences, but carries a fundamental structural limitation — one that scales poorly and resolves nothing about the psychological nature of the characters it represents. NPCs in these systems do not hold beliefs or form intentions; they evaluate conditions and return pre-written strings. The apparent depth of a well-written branching tree is purely a product of human authorship, not of any computational model of mind.

The question this project addresses begins with *Disco Elysium* (ZA/UM, 2019), which produced a quality of emergent narrative experience the dialogue-tree model cannot replicate. That emergence, however, is directed inward — towards the player character's internalised skills manifesting as competing voices. This raises a distinct question: is it possible to locate the same quality of psychological emergence on the *NPC* side? Can an NPC hold an internal model of the world, form goals in response to what a player says, and select behaviour that expresses that internal state — not because an author scripted it, but because a cognitive process produced it?

This dissertation argues that such a system is now architecturally feasible. The PNE models each NPC through a three-layer personality structure — cognitive, social, and world knowledge — and processes each player turn through a staged BDI pipeline: belief updating, desire formation, social intention selection, and outcome application. The cognitive reasoning stage operates without LLM involvement, drawing from a library of 810 template-matched thought patterns to produce deterministic, author-controllable NPC cognition. The LLM's role is narrowly scoped to surface text generation, constrained by a closed vocabulary of canonical behavioural intentions. The separation of *what the NPC thinks* from *how the NPC speaks* is the central architectural claim.

The PNE is deployed as a FastAPI server exposing a REST and WebSocket API, enabling integration with Unity, Godot, and Unreal Engine without platform coupling. A two-dice skill-check mechanism governs whether player choices succeed, with outcome probability computed from player skill, NPC personality, relational state, and difficulty. A judgement-score-driven finite state machine (FSM) aggregates outcomes across turns into a stable 0–100 scalar that drives narrative routing independently of LLM output.

---

## 1.2 Motivation

### 1.2.1 The Research Problem

The core tension this project investigates is the trade-off between narrative coherence, psychological realism, and player agency in NPC dialogue systems. These properties have historically been treated as in conflict: systems that prioritise coherence rely on tight authorial control, which limits emergence; systems that allow emergence tend to sacrifice coherence; and systems that maximise player agency often reduce NPC behaviour to reactive outputs with no internal model.

The research question is: *to what extent can a BDI cognitive architecture, instantiated over a structured NPC personality model and constrained LLM text generation, produce NPC dialogue that is simultaneously psychologically grounded, narratively coherent, and genuinely responsive to player agency?*

The availability of locally-deployable large language models through Ollama has made this feasible outside cloud infrastructure. Reasoning and text generation can now be decoupled, with the reasoning layer operating deterministically under developer control, and the generation layer producing natural language conditioned on that reasoning. The PNE is designed to occupy this space.

### 1.2.2 Commercial and Economic Context

The PNE is architecturally accessible to developers of any size — from solo indie studios to mid-scale teams — because it functions as a self-contained middleware service with no cloud dependency and no per-request licensing cost. Models capable of producing game-quality dialogue — such as Llama 3 or Mistral at 7B–13B parameters — require 4–6 GB of VRAM. This makes the system unsuitable for integrated graphics or mobile, but does not restrict it to large-scale productions.

The target use case is exemplified by games such as *Stardew Valley* (ConcernedApe, 2016): titles where NPC depth is central but production scale is small. Authoring fully adaptive dialogue for a cast of named villagers is prohibitive for a solo developer; under the PNE model, the developer authors personality configurations and scenario graphs, and the system generates the dialogue. This positions the PNE as infrastructure that makes psychologically realistic NPC conversation feasible for developers who currently cannot afford the authorial investment.

---

## 1.3 Dissertation Outline

Chapter 2 addresses social, legal, and ethical considerations. Chapter 3 reviews the literature across cognitive psychology, social psychology, BDI architectures, and interactive narrative. Chapter 4 describes the methodology, system design, and data collection approach. Chapter 5 presents results. Chapter 6 discusses findings. Chapter 7 concludes with a reflection on contributions, limitations, and future directions.
