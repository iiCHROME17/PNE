# Psychological Narrative Engine
## CS3IP Individual Project Dissertation
## Jerome Bawa

---

# Chapter 1: Introduction

## Abstract

Non-player character (NPC) dialogue in video games has long been constrained by the branching conversation tree — a paradigm that prioritises authored consistency at the cost of psychological depth and adaptive agency. This dissertation presents the Psychological Narrative Engine (PNE), a middleware dialogue system that replaces scripted branching with a staged Belief-Desire-Intention (BDI) processing pipeline, enabling NPC responses to emerge from a structured model of internal cognitive and social state rather than from pre-authored text. The system grounds NPC cognition in a three-layer personality representation and a template-matched thought library, then delegates surface text generation to a locally-deployable large language model (LLM) running via the Ollama runtime. A skill-check mechanism, a judgement-score finite state machine, and a game-engine-agnostic REST and WebSocket API complete the architecture. The central question investigated is whether psychological realism and narrative coherence in NPC interaction can be achieved simultaneously with genuine player agency — and whether the separation of cognitive reasoning from language generation, enabled by locally-deployable LLMs, provides a viable architectural basis for doing so. Evaluation is conducted through structured conversation log analysis and internal state inspection across representative test scenarios. The system targets players running mid-to-high end consumer hardware, a constraint imposed by the 4–6 GB VRAM requirement of capable local LLM inference.



## 1.1 Introduction

The dialogue tree has defined NPC interaction in commercial video games for three decades. From the conversation wheel of *Fallout 4* (Bethesda Game Studios, 2015) to the episodic choice structures of *The Walking Dead* (Telltale Games, 2012), the dominant model has remained the same: a developer authors every possible exchange in advance, a player selects from a fixed set of options, and the system traverses a predetermined graph. This approach produces narratively consistent, commercially polished experiences. It also carries a fundamental structural limitation — one that scales poorly and resolves nothing about the psychological nature of the characters it represents.

The limitation is not merely authorial. Each additional NPC, each new conversational branch, demands a proportionate investment in writing, quality assurance, and, where voice performance is involved, production resources that compound across the entire project. More critically, the dialogue tree is psychologically hollow. NPCs in these systems do not hold beliefs or form intentions; they evaluate conditions and return pre-written strings. They do not reason about what a player has said — they pattern-match against flags. The apparent depth of a well-written branching tree is purely a product of human authorship, not of any computational model of mind.

The question this project addresses begins with *Disco Elysium* (ZA/UM, 2019). That game produced a quality of emergent narrative experience that the dialogue-tree model cannot replicate — but it did so by directing emergence inward, towards the player. The player character's internalised skills manifest as autonomous voices: competing perspectives, intrusive thoughts, and divergent interpretations of the same event. The emergent experience in *Disco Elysium* is not the product of NPC behaviour; it is the product of a psychologically fragmented player-side perspective that imposes instability and reinterpretation onto every interaction.

This raises a distinct and underexplored question: is it possible to locate that same quality of psychological emergence on the *NPC* side? Can an NPC hold an internal model of the world, form goals in response to what a player says, and select a communicative behaviour that expresses that internal state — not because an author scripted it, but because a cognitive process produced it? And can this be achieved without sacrificing narrative coherence or reducing player agency to a sequence of opaque probabilistic outcomes?

This dissertation argues that such a system is now architecturally feasible, and documents the Psychological Narrative Engine (PNE) as a prototype demonstration of that feasibility. The PNE models each NPC through a three-layer personality structure — cognitive, social, and world knowledge — and processes each player turn through a staged BDI pipeline: belief updating, desire formation, social intention selection, and outcome application. Crucially, the cognitive reasoning stage operates without LLM involvement, drawing from a large library of template-matched thought patterns to produce deterministic, author-controllable NPC cognition. The LLM's role is narrowly scoped to surface text generation — producing the spoken words of the NPC, constrained by a closed vocabulary of nineteen canonical behavioural intentions. The separation of *what the NPC thinks* from *how the NPC speaks* is the central architectural claim of this work.

The PNE is deployed as a FastAPI server exposing a REST and WebSocket API, enabling integration with game engines such as Unity, Godot, and Unreal Engine without coupling the dialogue logic to any specific platform. A two-dice skill-check mechanism, inspired by *Disco Elysium*'s approach to probabilistic interaction, governs whether player dialogue choices succeed, with outcome probability computed from player skill attributes, NPC personality parameters, relational state, and configured difficulty. A judgement-score-driven finite state machine (FSM) aggregates conversational outcomes across turns into a stable 0–100 scalar that drives narrative routing independently of LLM output classification.



## 1.2 Motivation

### 1.2.1 The Research Problem

The core tension this project investigates is the trade-off between narrative coherence, psychological realism, and player agency in NPC dialogue systems. These three properties have historically been treated as in partial conflict: systems that prioritise coherence rely on tight authorial control, which limits emergence; systems that allow emergence tend to sacrifice coherence; and systems that maximise player agency often do so by reducing NPC behaviour to reactive outputs with no internal model.

The research question can be stated as follows: *to what extent can a BDI cognitive architecture, instantiated over a structured NPC personality model and constrained LLM text generation, produce NPC dialogue that is simultaneously psychologically grounded, narratively coherent, and genuinely responsive to player agency?*

This question has become feasible to explore for a specific reason. The availability of locally-deployable large language models through services such as Ollama represents a shift in what is possible outside of cloud infrastructure. Dialogue text of sufficient quality for game integration can now be generated on consumer hardware during real-time play. This opens an architectural space that was previously inaccessible: reasoning and text generation can be decoupled, with the reasoning layer operating deterministically under developer control, and the generation layer producing natural language conditioned on the output of that reasoning. The PNE is designed to occupy this space.

### 1.2.2 Commercial and Economic Context

The commercial context for this project is not defined by the scale or budget of the developer, but by the hardware profile of the player. The PNE is architecturally accessible to developers of any size — from solo indie studios to mid-scale teams — because it functions as a self-contained middleware service with no cloud dependency and no per-request licensing cost. The constraint is runtime: the system requires a player machine capable of sustaining local LLM inference alongside the primary game process.

The infrastructure dependency that defines this boundary is Ollama. Models capable of producing dialogue quality suitable for game integration — such as Llama 3 or Mistral at the 7B–13B parameter range — require at minimum between 4 and 6 GB of VRAM for inference at acceptable latencies. The system is not viable on integrated graphics hardware, entry-level laptops, or mobile devices, and makes no claim to be. Cloud-hosted inference is deliberately excluded from the architecture, motivated by the latency requirements of real-time dialogue streaming and the undesirability of a persistent network dependency for an offline-capable game feature.

Critically, this hardware boundary does not restrict the PNE to large-scale productions. It opens the capability to developers who could never afford to author deep NPC dialogue at scale. A game such as *Stardew Valley* (ConcernedApe, 2016) — built by a single developer, featuring a cast of named villagers with daily schedules, relationship systems, and recurring dialogue — represents precisely the class of project where dynamically generated, psychologically grounded NPC conversation would most dramatically expand replayability and emergent experience. The authorial investment required to make every villager genuinely adaptive under a scripted system is prohibitive for a small team; under the PNE model, the developer authors personality configurations and scenario graphs, and the system generates the dialogue.

This positions the PNE not as a tool for studios that already have dialogue teams, but as infrastructure that makes psychologically realistic NPC conversation feasible for developers who do not — provided their target audience runs capable hardware.

---

## 1.3 Dissertation Outline

**Chapter 2 — Social, Legal and Ethical Considerations** examines the broader implications of the PNE as a system. This includes the social impact of democratising psychologically grounded NPC dialogue for smaller developers, the legal landscape governing the open-source components on which the system depends (FastAPI, Ollama, Qwen2.5), and the ethical considerations involved in applying psychological constructs — self-esteem, cognitive flexibility, locus of control — as design parameters in a computational model.

**Chapter 3 — Literature Review** surveys four bodies of work that inform the PNE's design: cognitive psychology models of belief and inference (Neisser, Ellis, Heider); social psychology frameworks covering persuasion, conformity, and impression management (Cialdini, Guimond, Goffman); BDI agent architectures and their application to autonomous agents (Bratman, Rao and Georgeff, Wooldridge); and prior work in interactive narrative and NPC dialogue systems (Murray, Aylett, Mateas and Stern, Park et al.).

**Chapter 4 — Methodology** documents the design and implementation of each PNE component: the NPC personality model, the five-stage BDI processing pipeline, the CognitiveThoughtMatcher, the two-dice skill-check system, the judgement-score FSM, and the REST and WebSocket API layer. The chapter also covers data collection methods, the role of AI-assisted diagnostic testing, and the ethical framing of the project's research approach.

**Chapter 5 — Results and Discussion** presents the system's design outcomes across three dimensions: model design and architectural decisions (5.1), pipeline interpretability demonstrated through end-to-end trace analysis (5.2), and the major optimisation passes that shaped the architecture over the development cycle (5.3).

**Chapter 6 — Results** presents structured conversation log analysis across three NPCs — Krakk Klikowicz, Morisson Moses, and Troy — all running the same `door_guard_night` scenario. The chapter includes full NPC profile tables, a cross-NPC pipeline state comparison, individual BDI breakdown analysis, and comparative player build runs.

**Chapter 7 — Discussion and Analysis** evaluates the system's outputs against its central claims: internal state consistency, output coherence against pipeline state, and terminal outcome routing behaviour. The chapter then justifies the project's achievements, revisits the research question in light of the evidence, and critically examines the system's limitations — including the logging gap, the partially-implemented wildcard system, and the narrow scenario coverage of the test corpus.

---

# Chapter 2: Social, Legal, and Ethical Considerations

## 2.1 Overview

The Psychological Narrative Engine operates at the intersection of artificial intelligence, cognitive modelling, and interactive entertainment. As with any system that applies computational representations of human psychology within a consumer-facing context, its development and deployment carry implications that extend beyond the technical. This chapter addresses the social, legal, and ethical dimensions of the PNE, identifies the risks associated with its use, and outlines the mitigations built into the system's design. On balance, the PNE's social impact is assessed as net positive — particularly for the class of smaller developers for whom deep NPC narrative has historically been inaccessible — while acknowledging that it introduces genuine shifts in how narrative design labour is distributed across the industry.

---

## 2.2 Social Considerations

### 2.2.1 Impact on Smaller Studios and Independent Developers

The primary social benefit of the PNE is democratisation of narrative depth. Authoring psychologically rich NPC dialogue at scale has historically required dedicated writing teams, voice production pipelines, and quality assurance processes that smaller studios cannot sustain. The result is a structural disparity in narrative quality between large and small productions — one that has little to do with creative ambition and everything to do with production resource.

The PNE disrupts this disparity by shifting what must be authored. A solo developer or small team can define NPC personality configurations and scenario graphs without writing individual dialogue lines. The system generates surface dialogue from that structure, producing adaptive, contextually responsive NPC behaviour at a fraction of the authorial investment. For games with social simulation at their core — relationship systems, named characters, recurring interactions — this represents a meaningful capability expansion. The class of game exemplified by *Stardew Valley* (ConcernedApe, 2016) stands to benefit most directly: titles where NPC depth is central to the experience but the production scale is small.

### 2.2.2 Impact on Narrative Designers and Industry Labour

The question of whether AI-assisted dialogue generation displaces narrative designers requires a more nuanced answer than a simple yes or no. The answer depends substantially on the scale of the studio in question.

For smaller studios that currently cannot employ narrative designers at all, the PNE does not displace anyone — it fills a gap that was previously unfilled. It enables narrative experiences that would not otherwise exist, and in doing so may actually create demand for narrative design consultation on configuration and scenario authoring that did not previously exist at that scale.

For mid-scale studios with small writing teams, the impact is a likely shift in workload rather than a reduction in headcount. Narrative designers working with the PNE would move from writing individual dialogue lines to authoring personality models, thought-pattern templates, and scenario graphs — a more systems-oriented form of narrative design. This is a change in the nature of the work, not necessarily its volume or value. The skill set required evolves rather than disappears.

For large studios — the industry tier occupied by Ubisoft, Bethesda Game Studios, and Rockstar Games — the impact of the PNE is likely minimal. These studios do not prioritise emergent NPC dialogue as a design goal. Their flagship productions (*Assassin's Creed*, *The Elder Scrolls*, *Grand Theft Auto*) are built around authored story arcs, scripted set-pieces, and fixed character trajectories that require precisely the kind of controlled narrative authorship that large writing teams provide. The PNE is not designed for this mode of storytelling and would offer these studios limited utility in their current production pipelines. Their narrative designers are not at risk from a system whose target use case is the opposite of their working model.

The broader industry shift to AI-assisted content generation is a legitimate concern for creative labour at all levels, but the PNE specifically represents a narrow, structured intervention — not a general-purpose creative AI — and its social impact should be assessed on that basis.

---

## 2.3 Legal Considerations

### 2.3.1 Software Licensing and Open Source Compliance

The PNE is built on a stack of open-source components: FastAPI (MIT licence) and the Ollama runtime (MIT licence). The model used in the prototype implementation is Qwen2.5:3b, developed by Alibaba Cloud's Qwen Team and distributed under the Apache 2.0 licence. Apache 2.0 is among the most permissive open-source licences available — it permits use, modification, and commercial distribution without royalty obligations, provided attribution is retained. This makes Qwen2.5:3b a legally straightforward choice for both research and any subsequent commercial integration built on the PNE.

Qwen2.5:3b's 3-billion parameter scale is notable from a deployment standpoint: at 4-bit quantisation the model requires approximately 2 GB of VRAM, a significantly lower threshold than the 7B–13B models more commonly referenced in the literature. This broadens the viable player hardware base compared to larger models, though dialogue quality trade-offs relative to more capable models are acknowledged and discussed in Chapter 5.

No proprietary third-party APIs are called at runtime. The system generates no logs containing player data, makes no external network requests during normal operation, and does not depend on any service whose terms of use could change post-deployment. Developers substituting a different Ollama-compatible model in a production integration carry responsibility for verifying the licence terms of their chosen model independently.

### 2.3.2 Intellectual Property

The PNE does not reproduce copyrighted text, dialogue, or narrative content. NPC dialogue is generated at runtime from LLM inference constrained by developer-authored configurations; no pre-existing authored content is replicated. The thought-pattern template library is original work. Scenarios and personality configurations authored by developers who integrate the PNE remain the intellectual property of those developers.

The use of *Disco Elysium* as a design reference for the skill-check mechanic is analytical and transformative — the mechanic is independently implemented and does not incorporate any code or content from ZA/UM's work.

### 2.3.3 Data Governance

The PNE does not collect, store, or transmit personal data. No player identification is performed; session state is held in memory for the duration of a conversation and discarded thereafter unless explicitly persisted by the integrating game engine. No questionnaires or user studies were conducted in the development of this project, and no ethical approval for data collection was required or sought.

---

## 2.4 Ethical Considerations

### 2.4.1 Representation of Psychological Constructs

The PNE applies constructs drawn from cognitive psychology — belief, desire, intention, emotional state — as computational abstractions for NPC modelling. These constructs are used symbolically within a game context and are not intended to constitute clinical representations of human psychology. NPC personality parameters are design tools, not psychological assessments. The system makes no diagnostic claims and does not present itself as a model of real human cognition.

This distinction is important to maintain clearly in any production context. Game NPCs modelled through the PNE should be understood as fictional characters whose behaviour is shaped by design parameters, not as simulations of real psychological conditions. Developers integrating the system carry responsibility for ensuring that NPC characterisation does not reproduce harmful stereotypes or present psychologically distressing content without appropriate content warnings.

### 2.4.2 Transparency of AI-Generated Content

Dialogue generated by the PNE is produced by a large language model at runtime. Players interacting with PNE-driven NPCs are engaging with AI-generated text, constrained and shaped by developer configurations, but not authored line-by-line by a human writer. The ethical question of whether players should be informed that NPC dialogue is AI-generated is a live one within the games industry and the broader AI content space. This project takes no prescriptive position on disclosure obligations, which are properly a matter for the integrating developer and applicable consumer protection regulation in their jurisdiction. It is noted, however, that transparency about AI-generated content is consistent with emerging best practice and is recommended.

---

## 2.5 Risk Management

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM generates off-character or incoherent dialogue | Medium | Medium | Closed intention vocabulary (19 canonical intentions) constrains generation; system prompt encodes NPC identity and BDI state |
| Model hallucination breaks narrative coherence | Medium | High | FSM routing is independent of LLM output classification; judgement score is computed from BDI outcomes, not LLM text |
| Ollama model licence non-compliance | Low | High | Licence terms documented per model; developers advised to verify commercial use terms prior to deployment |
| LLM inference latency degrades player experience | Medium | Medium | WebSocket streaming delivers tokens progressively; offline mode available for development and low-spec environments |
| NPC characterisation reproduces harmful stereotypes | Low | High | Personality parameters are abstract numerical configurations; content responsibility rests with scenario authors |

---

## 2.6 Summary

The social, legal, and ethical profile of the PNE is largely benign. Its primary social effect is to extend narrative design capability to developers who currently lack it, with a secondary effect of shifting — rather than eliminating — the workload of narrative designers at mid-scale studios. Large studios whose production model depends on authored narrative are unlikely to be meaningfully affected. Legal compliance is straightforward given the open-source stack and absence of data collection. The principal ethical obligations — responsible characterisation and transparency about AI-generated content — rest with integrating developers rather than with the engine itself. The most significant technical risk, LLM incoherence, is structurally mitigated by the architecture's separation of reasoning from generation.

---

# Chapter 3: Literature Review

## 3.1 Overview

The Psychological Narrative Engine draws on four distinct bodies of knowledge: cognitive psychology, social psychology, BDI agent architectures, and interactive narrative theory. Each domain contributes a conceptual layer to the system's design, and each carries limitations that the architecture must work around. This chapter surveys the foundational literature across these domains, assesses its applicability to computational NPC modelling, and identifies the gap that the PNE is designed to address. The review moves from the psychological foundations that motivate the NPC personality model, through the architectural traditions that shaped the BDI pipeline, to the interactive narrative research that defines the problem space, and finally to the emergence of large language models as a practical text generation substrate.

---

## 3.2 Cognitive Psychology Foundations

### 3.2.1 Constructive Cognition: Neisser (1967)

Neisser (1967) established the theoretical basis for treating perception and memory as constructive rather than reproductive processes. Where earlier associationist models had characterised mental activity as the passive accumulation and retrieval of stored impressions, Neisser argued that every cognitive act involves an active reconstruction — the mind does not replay experiences but rebuilds them from partial cues, prior knowledge, and perceptual schema. Central to this account is the analysis-by-synthesis model of perception, in which the cognitive system generates internal hypotheses about incoming stimuli and tests them against sensory data, producing a percept that is partly given by the world and partly supplied by the mind. Neisser's introduction of schema theory — the claim that perception is mediated by pre-existing interpretive frameworks built from experience — was foundational to subsequent cognitive science. Two people can observe the same event and construct entirely different interpretations of it, depending on the schemas active at the moment of perception.

For NPC modelling, this framework has significant implications. A character that responds to player dialogue purely by retrieving pre-authored strings is not, in Neisser's terms, cognising — it is reproducing. A credible cognitive model would require something structurally analogous to analysis-by-synthesis: a process in which the NPC generates an internal interpretation of what has been said, rather than simply matching input to output. The PNE's thought-pattern template system is designed around this intent. When a player delivers a dialogue choice, the NPC's cognitive layer does not retrieve a response; it generates a subjective interpretation — a belief update — by selecting and instantiating from a library of template-matched thought patterns whose selection is modulated by the NPC's personality parameters. The result is that NPCs with different cognitive profiles generate different internal responses to identical player input, mirroring Neisser's central claim that interpretation is schema-driven rather than stimulus-determined.

However, Neisser's full constructive model involves far richer inferential processes than any current computational NPC system implements. True analysis-by-synthesis requires schema-driven expectation generation across multiple cognitive levels simultaneously — processes that remain computationally intractable at the resolution required for real-time game dialogue. The PNE's template matching is a deliberate simplification: it captures the essential output of constructive cognition (a generated interpretation rather than a retrieved response) without attempting to replicate the underlying mechanism. The thought patterns produce contextually plausible outputs, but the selection process is heuristic rather than formally cognitive, and this is acknowledged as a limitation of the implementation relative to the theory that motivates it.

### 3.2.2 Belief, Emotion, and the A-B-C Model: Ellis (1962)

Ellis (1962) introduced the foundational model of Rational Emotive Behaviour Therapy: the A-B-C framework, in which an Activating event (A) does not directly produce an emotional Consequence (C), but does so only via the mediating Belief (B) that an individual holds about the event. The same activating event produces entirely different emotional outcomes depending on the beliefs through which it is interpreted. Ellis catalogued a range of irrational belief patterns — systematic interpretive errors that lead individuals to experience events as more threatening, humiliating, or catastrophic than the facts warrant. These patterns include hostile attribution (assuming negative intent on the part of others), catastrophising (treating manageable setbacks as existential threats), and projection (attributing one's own negative states to others).

The structural parallel between the A-B-C model and the PNE's cognitive pipeline is direct. The player's dialogue choice constitutes the activating event; the NPC's template-matched thought constitutes the belief through which that event is interpreted; and the resulting desire state constitutes the emotional consequence. This is not an incidental correspondence — it reflects the design intention that NPC cognition should model the interpretive step between stimulus and response, rather than treating NPC behaviour as a direct function of player input. Ellis's taxonomy of irrational belief patterns is also the direct intellectual ancestor of the cognitive bias categories implemented in the PNE's thought-pattern library. Hostile attribution bias — the most frequently instantiated bias type in the template set — is precisely Ellis's irrational pattern applied to interpersonal interpretation.

Ellis's model is clinical and prescriptive in its original framing, concerned with identifying and correcting maladaptive belief patterns in human patients. Its application to NPC design requires a reframing: where Ellis treats irrational beliefs as pathologies to be remedied, the PNE treats them as design parameters that define the character of an NPC's cognitive style. A character configured with high hostile attribution bias does not have a disorder; they have a personality. This distinction is important for the ethical considerations addressed in Chapter 2, where it is noted that NPC personality parameters are design tools, not clinical representations.

### 3.2.3 Attribution Theory: Heider (1958)

Heider (1958) founded attribution theory with the observation that ordinary social actors construct explanations for others' behaviour by attributing mental states — beliefs, desires, intentions, and sentiments. These attributions are not sophisticated analyses; they are the spontaneous and largely unconscious inferences made whenever a person is observed acting. Heider distinguished between internal attribution (explaining behaviour in terms of the actor's stable disposition or intent) and external attribution (explaining behaviour in terms of situational circumstance), and identified the systematic bias toward internal attribution — the tendency to over-attribute behaviour to personality and under-attribute it to situation — that subsequent research formalised as the fundamental attribution error.

Attribution theory is foundational to the PNE's design in two complementary ways. First, it provides theoretical justification for modelling NPCs through explicit mental-state representations. If players spontaneously attribute beliefs, desires, and intentions to characters they encounter — as Heider's framework predicts they will — then an NPC system that maintains explicit representations of those mental states is likely to produce behaviour that players interpret as psychologically coherent. The character's attributable mental state and its actual computational state are aligned, rather than the former being a player-side fiction layered over scripted outputs.

Second, Heider's internal/external attribution distinction maps directly onto the PNE's locus\_of\_control personality parameter. An NPC with a high internal locus attributes player behaviour to the player's character and intent; an NPC with a high external locus attributes the same behaviour to circumstances. This produces systematically different belief updates from identical player input, which in turn produces different desire formations and social intention selections downstream in the pipeline. Heider also identified the concept of balance — the psychological discomfort that arises when an individual's beliefs about relationships are inconsistent — which maps onto the tension the desire layer must resolve when the player's relational standing with the NPC conflicts with the content of their dialogue choice.

Heider's model is descriptive rather than normative, and translating it into computable form requires architectural decisions that the theory does not constrain. In particular, the degree of inference complexity the model supports — how many levels of belief attribution an NPC should track — is not specified by Heider. The PNE implements a single level: the NPC models the player's communicative intent, but does not model the player's beliefs about the NPC's beliefs. Multi-level mentalising of the kind observed in human social cognition (Wimmer and Perner, 1983) is architecturally possible in principle but is outside the current system's scope.

---

## 3.3 Social Psychology and Interpersonal Dynamics

### 3.3.1 Influence and Compliance: Cialdini (1984)

Cialdini (1984) identified six principles of social influence — reciprocity, commitment and consistency, social proof, liking, authority, and scarcity — that reliably produce compliance in interpersonal contexts. These principles are not cognitive in the Neisser or Ellis sense; they are social heuristics, patterns of influence that exploit the shortcuts human decision-making relies on when evaluating whether to comply with a request. Cialdini's core insight is that the same request can succeed or fail depending on its rhetorical framing: compliance is modulated not only by what is asked but by how it is positioned relative to these principles.

The PNE's four Language Arts — authority, diplomacy, empathy, and manipulation — are grounded in Cialdini's taxonomy. Authority maps to his authority principle; diplomacy to liking and reciprocity; empathy to liking; manipulation to commitment, social proof, and scarcity tactics. This correspondence gives the Language Arts system a rigorous theoretical grounding: the four skill dimensions are not arbitrary dialogue flavours but implementations of empirically validated persuasion mechanisms. The NPC's personality parameters govern how strongly each Language Art is weighted in the skill-check probability calculation, reflecting individual differences in susceptibility to different influence strategies — the variance that Cialdini's research documents. A character with high suggestibility to authority is computationally easier to influence through high-authority dialogue choices; a character with high reciprocity weighting responds more strongly to empathy-coded approaches.

Cialdini's framework is empirically grounded in compliance research conducted primarily in real-world commercial and interpersonal settings, and its application to fictional NPC interactions requires an implicit mapping assumption: that players interpreting NPC responses will do so through the same naive social cognition that operates in real-world interaction. This assumption is supported by the broader social psychology literature on social cognition in narrative contexts, but is not independently validated within this project.

### 3.3.2 Social Comparison and Self-Esteem: Guimond (2006)

Guimond (2006) synthesises research on social comparison theory — originally proposed by Festinger (1954) — which holds that humans evaluate their own opinions, abilities, and social standing by comparing themselves to relevant others. Guimond extends this into intergroup contexts, demonstrating that social comparison operates not only between individuals but between groups: self-esteem is modulated by perceived standing relative to in-group and out-group members, and group membership shapes which comparisons feel relevant. The volume also synthesises the relationship between social comparison and Social Identity Theory (Tajfel and Turner, 1979), in which in-group favouritism and out-group hostility emerge partly from self-evaluative comparison processes.

For the PNE, Guimond's framework provides the theoretical basis for the self\_esteem and faction personality parameters. NPC self-esteem in the system is not a fixed trait but a relational construct: how the NPC rates themselves relative to the player, their faction members, and their rivals. This dynamic is precisely the comparative evaluation that Guimond describes. Faction-based NPC behaviour — the heightened hostility or caution that occurs when a player from outside a character's in-group initiates interaction — is grounded in the intergroup comparison mechanisms Guimond covers. The conf\_indep (confidence/independence) parameter is similarly comparative: an NPC who consistently evaluates themselves against stronger figures develops a lower baseline confidence that affects intention selection downstream. Guimond's work positions these parameters not as invented sliders but as implementations of a well-evidenced account of how social identity shapes interpersonal behaviour.

### 3.3.3 Impression Management: Goffman (1959)

Goffman (1959) proposed a dramaturgical model of social interaction: people perform identities rather than simply express them. Every social actor maintains a front-stage presentation — the self displayed in interaction — and a backstage reality — the private self concealed from others. Performance is governed not by authentic expression but by impression management: the strategic regulation of self-presentation to influence how others perceive and respond to one's behaviour. Key to the dramaturgical model is the observation that social interaction is a collaborative performance in which all parties both enact and are audience to one another.

Goffman's model maps directly onto the structure of the PNE's NPC personality representation. The system distinguishes between a cognitive layer — the NPC's internal beliefs, interpretations, and private mental states — and a social layer — the behavioural intentions the NPC presents in interaction. This distinction is precisely Goffman's front and back stage, formalised as a computational architecture. An NPC whose social intention diverges from its cognitive state is performing in Goffman's sense: presenting a managed self that does not straightforwardly reveal its internal disposition. This capacity for divergence between internal state and external presentation is what makes NPC behaviour interpretable as strategic social action rather than mere mechanical response. The nineteen canonical behavioural intentions — including Assert Dominance, Deflect with Humour, and Defend Cause Passionately — are impression management strategies in Goffman's terms: performative acts selected to produce a desired effect on the audience.

Goffman's framework is sociological rather than psychological, and does not provide a mechanistic account of how impression management decisions are made — the theory describes patterns of strategic self-presentation without specifying the cognitive process by which a social actor selects a front from the available options. This gap is addressed in the PNE by the social intention selection mechanism: the nineteen canonical intentions constitute a constrained action space from which the NPC selects based on BDI state, providing a computational correlate to the impression management choices Goffman describes. Goffman's concept of frame breaks — the disruption of a performance when an actor's front-stage behaviour can no longer be sustained — also maps to the PNE's handling of rising confrontation level, in which NPC behaviour shifts as accumulated psychological pressure exceeds configured thresholds.

---

## 3.4 BDI Agent Architectures

### 3.4.1 Foundations: Bratman, Rao and Georgeff

The BDI model of rational agency derives from Bratman's (1987) philosophical account of practical reasoning, which proposed that human deliberation is characterised by three fundamental attitudes: beliefs (representations of the world as it is), desires (representations of preferred world states), and intentions (commitments to action that provide the stability required to pursue goals over time). Bratman argued that intentions are not reducible to beliefs and desires — they function as autonomous action commitments that constrain further deliberation, preventing agents from reconsidering every committed course of action at every moment.

Rao and Georgeff (1995) translated Bratman's philosophical framework into a formal computational architecture, defining BDI agents in terms of possible worlds semantics and modal logic. Their formalisation introduced the notion of an agent's accessible belief, desire, and intention sets as modal operators over world states, with satisfaction conditions specifying the relationships between mental attitudes required for rational agency. Georgeff et al. (1999) subsequently traced the evolution from Bratman's philosophy to this computational formalisation, noting that BDI is not a single monolithic architecture but a family of variants — different implementations emphasise belief revision, commitment, or inter-agent communication depending on the application domain. Their retrospective directly validates applying BDI to NPC conversation as one such variant, adapted for a domain that prior implementations had not addressed.

The strength of the BDI framework for NPC modelling lies in its explanatory alignment with naive psychology. Heider's (1958) observation that ordinary social actors reason about others through belief-desire-intention attribution means that an NPC architecture built on explicit BDI representations will produce behaviour that is interpretable — players can reason about why an NPC acted as it did using the same mental-state attribution they apply in real social interaction. The architecture makes internal state transparent in a way that scripted dialogue trees cannot.

### 3.4.2 Practical Reasoning: Wooldridge (2000)

Wooldridge (2000) provides the most comprehensive single-volume treatment of the BDI model from a computational agent theory perspective. Wooldridge defines rational agents as entities that perceive their environment, maintain internal state, and select actions to achieve goals — distinguishing simple reflex agents from deliberative agents capable of sustained goal-directed action and from communicating agents operating within multi-agent societies. His treatment of the BDI architecture examines the tension between reactivity (responding to the current world state) and proactivity (pursuing goals that may require multi-step action), arguing that credible rational agency requires both.

Wooldridge's (2000) analysis of commitment structures in BDI agents is directly relevant to the PNE's design. He identifies three strategies: blind commitment (maintaining an intention until achieved regardless of world changes), single-minded commitment (maintaining an intention until achieved or known to be unachievable), and open-minded commitment (abandoning an intention whenever it no longer holds in the desire set). The PNE implements a variant of open-minded commitment in the form of its desire recalculation layer: after each player turn, the NPC's goal state is recomputed from updated beliefs, and the prior intention is not carried forward if the updated desire state does not support it. This ensures NPC behaviour remains responsive to conversational dynamics rather than persisting in intentions that have become contextually inappropriate.

Wooldridge (2000) also surfaces a fundamental limitation of BDI architectures: the frame problem. In formal BDI systems, the computational cost of maintaining consistent belief sets and re-evaluating intentions grows with the richness of the world model. For game NPCs, the effective solution is to radically constrain the world model — which the PNE achieves through the NPC's structured personality configuration and the closed-vocabulary intention system. The resulting agent is not a general-purpose BDI reasoner but a domain-constrained one, and its tractability is a direct product of this deliberate architectural limitation.

### 3.4.3 Practical Implementation: Bordini, Hübner and Wooldridge (2007)

Bordini, Hübner and Wooldridge (2007) represent the most practically influential translation of BDI theory into executable agent programming, through the AgentSpeak language and its implementation in the Jason interpreter. AgentSpeak defines agents through belief bases and plan libraries: when a belief change event triggers a goal, the agent searches its plan library for applicable plans and selects one to execute. Jason extends this with handling for goal failure, multi-agent communication, and a range of commitment and reconsideration strategies.

The Jason framework demonstrates both the practical utility and the practical limitations of the BDI approach for complex dialogue generation. The plan-library model scales well for goal-directed behaviour in structured task environments — multi-agent simulation, robotic coordination, game AI for navigation and combat — but produces brittle behaviour in open-ended conversational contexts where the space of possible player inputs cannot be enumerated in advance. An NPC implemented in pure AgentSpeak would require a distinct plan for every possible player message type; the plan library would become unmanageable at the conversational scope required for meaningful game dialogue.

The PNE's most significant architectural departure from traditional BDI systems is its response to this limitation. Rather than enumerating conversational plans, the PNE uses template-matched thought patterns to abstract away from specific player inputs: the cognitive layer produces a categorised internal response (a belief update encoding interpretation, emotional register, and BDI state changes) that can be acted upon by the downstream pipeline without requiring a plan for every possible player utterance. The LLM then handles surface text generation for the social intention that emerges from this process. This hybrid design preserves the principled structure of BDI reasoning while avoiding the combinatorial authoring burden that a pure plan-library approach such as Jason would require (Bordini, Hübner and Wooldridge, 2007).

---

## 3.5 Interactive Narrative and NPC Dialogue Systems

### 3.5.1 The Problem of Agency: Murray (1997)

Murray (1997) identifies three properties that distinguish digital environments as narrative spaces: agency (the satisfying power to take meaningful action and see the results reflected in the narrative), immersion (the feeling of being inside the story world), and transformation (the story world changing in response to the player). The tension she identifies — and that subsequent work in the field has returned to repeatedly — is that authored narrative depends on authorial control, while player agency depends on the freedom to take unanticipated actions. These two requirements are in direct conflict: the more control an author exerts, the less genuine the player's agency becomes. Murray (1997) calls this the central challenge of interactive narrative: how to give players real choice without destroying the craft of the story.

This tension sits at the centre of the PNE's design problem. The dialogue-tree model resolves it by sacrificing agency: the player selects from pre-written options, and the narrative proceeds along pre-authored paths. The apparent freedom is an illusion — the player selects which scripted response the NPC delivers, not what the NPC actually thinks or does. The PNE takes the opposite approach: genuine conversational freedom within the constraints of the scenario graph is preserved at the cost of reducing authorial control over surface text. The author specifies NPC personality, scenario structure, and outcome conditions; the specific words the NPC speaks are not authored but generated. Murray's (1997) framework maps directly onto the PNE's architecture: agency is delivered through the skill-check system; immersion through LLM-generated natural dialogue grounded in BDI state; transformation through the judgement-score-driven FSM that routes the narrative in response to accumulated conversational outcomes. The FSM is precisely Murray's (1997) answer to the authorship/agency tension — players have agency over outcomes, but scenario authors retain control over structure.

### 3.5.2 Emergent Narrative: Aylett (1999)

Aylett (1999) defined emergent narrative — narrative that arises from the bottom-up interaction of autonomous characters with internal states and goals — as a resolution to the incompatibility between pre-scripted narrative and the freedom afforded by virtual environments. She distinguished cognitively determined behaviour (reasoned, goal-directed action) from reactively determined behaviour (sensor-driven response), and argued that believable interactive narrative requires characters capable of the former. Her analysis introduced the concept of social presence — the extension of physical presence to include the illusion of social location, in which appropriate behaviour is communicated through social convention rather than explicit instruction — as a mechanism for integrating user behaviour into emergent narrative without pre-scripting the user's role.

Aylett's (1999) concept of social presence anticipates the PNE's design philosophy directly. The system's core claim is that an NPC with a credible internal model of beliefs, desires, and social intentions will produce behaviour that players read as socially present — as if interacting with a character that is genuinely responding to them, rather than executing a script. This is the PNE's answer to Murray's (1997) immersion property: immersion is produced not by polished authored prose but by the coherence between the NPC's visible behaviour and its traceable internal state.

Aylett (1999) also identifies the central risk of emergent narrative: that it may not emerge. The unpredictability that makes emergent behaviour interesting also makes it fragile — the conditions required for narrative coherence may simply not obtain in a given interaction. The PNE's FSM architecture addresses this directly. The judgement-score mechanism aggregates conversational outcomes into a stable scalar that drives narrative routing; the author specifies the conditions for each state transition, ensuring that meaningful story-level events occur even if specific turn-by-turn interactions are unpredictable. In Aylett's (1999) terms, the FSM guarantees that emergent dialogue interactions produce coherent narrative outcomes — it is the authorial shaping hand that constrains emergence without scripting it.

### 3.5.3 Drama Management: Mateas and Stern (2003)

Mateas and Stern's (2003) *Façade* represents the most technically sophisticated prior attempt to implement BDI-grounded interactive drama. *Façade* featured two NPC characters with internal emotional and relational state updated by a drama manager in response to player input. The drama manager used a hierarchical task network to maintain story coherence while the characters' emotional states drove their immediate behaviour. Player input was processed through a natural language understanding system that classified utterances into a vocabulary of dramatic acts.

*Façade* demonstrated that drama management worked as a design approach. It also demonstrated its costs: the system required years of development, a large authored behaviour library, and still produced conspicuous breakdowns when player input exceeded the NLU system's classification capacity. The characters' behaviour degraded visibly when the drama manager's goals conflicted with the NPC state model — a problem Mateas and Stern (2003) attributed to the difficulty of integrating bottom-up character agency with top-down narrative control.

The PNE's architecture addresses the *Façade* problem from a different angle. Rather than attempting natural language understanding of free-text player input, the PNE sidesteps the NLU problem entirely: players select from structured dialogue options pre-labelled with tone weights and skill requirements. The NPC's response emerges from the BDI pipeline without requiring the system to parse natural language. The result is a narrower interaction model — players do not type freely — but a more robust one. Narrative coherence is maintained not by a drama manager overriding NPC state but by the FSM operating on accumulated judgement scores: an emergent aggregate of BDI outcomes rather than an externally imposed constraint.

---

## 3.6 Large Language Models in Game Contexts

### 3.6.1 Generative Agents: Park et al. (2023)

Park et al. (2023) demonstrated that LLMs can serve as the cognitive substrate for believable social agents, populating a virtual town with twenty-five agents each powered by a GPT-4 language model with a memory stream, reflection mechanism, and planning module. The agents engaged in spontaneous social behaviour — attending events, forming relationships, propagating information — that observers rated as humanlike and socially coherent. Park et al. (2023) established the viability of LLM-driven social simulation at a scale and quality previously unachievable.

However, the Generative Agents architecture reveals assumptions that the PNE was designed to avoid. Park et al.'s (2023) system relies on a cloud-hosted language model for both cognitive reasoning and text generation — the same model performs planning, reflection, and dialogue production. This coupling creates a system in which the quality of social reasoning is inseparable from the capability of the LLM: if the model confabulates an implausible plan, no external mechanism corrects it. The reliance on GPT-4 also makes the system unsuitable for offline consumer game deployment; the per-request cost and network dependency are incompatible with the use case the PNE targets.

The PNE's architectural response is to decouple reasoning from generation. The cognitive BDI pipeline operates without LLM involvement, using deterministic template matching to produce NPC belief updates. The LLM's role is narrowly constrained to surface text generation, conditioned on the output of the BDI pipeline. This means that even if the LLM produces stylistically imperfect output, the NPC's internal state trajectory remains coherent and author-controllable. The quality of NPC behaviour is not contingent on LLM planning capacity, because the NPC does not plan in the LLM.

### 3.6.2 Local Deployment and the Ollama Runtime

The practical feasibility of the PNE's architecture depends on the availability of locally-deployable language models capable of producing game-quality dialogue text. The Ollama runtime, introduced in 2023, provides a standardised interface for running quantised language models on consumer hardware without cloud infrastructure. Models in the 3B–7B parameter range, running at 4-bit quantisation on hardware with 2–6 GB VRAM, produce text of sufficient quality for NPC dialogue in social simulation contexts — a claim the prototype implementation evaluates in Chapter 5.

This development represents a genuine shift in the architectural feasibility space for NPC dialogue systems. Prior to locally-deployable quantised models, any system that used neural text generation at runtime required either cloud API access or server-class hardware — neither of which is compatible with offline consumer game deployment. The PNE's commercial viability is entirely contingent on this shift having occurred; it is a system whose architecture was always theoretically possible but whose deployment requirements have only recently become achievable on consumer hardware.

The model used in the prototype, Qwen2.5:3b (Alibaba Cloud, 2024), represents a deliberate trade-off between dialogue quality and hardware accessibility. At 4-bit quantisation, it requires approximately 2 GB of VRAM — a significantly lower threshold than the 7B–13B models that produce higher-quality dialogue. This makes the prototype accessible to a wider hardware base during evaluation, at the cost of dialogue quality trade-offs acknowledged in Chapter 5. A production integration of the PNE would likely target a more capable model in the 7B range, accepting the higher VRAM requirement as the price of the quality improvement.

---

## 3.7 Synthesis: The Gap the PNE Fills

The literature reviewed in this chapter converges on a gap that no prior system has addressed in a form suited to commercial game integration. The gap can be stated precisely: there is no existing middleware architecture that (1) grounds NPC behaviour in a principled cognitive and social psychology model, (2) maintains deterministic, author-controllable narrative structure, (3) uses locally-deployable LLM inference for surface text generation, and (4) is accessible to developers who lack the resources for large-scale dialogue authoring.

Cognitive psychology — Neisser's (1967) constructive cognition, Ellis's (1962) A-B-C model, and Heider's (1958) attribution theory — provides the theoretical justification for mental-state-based NPC modelling, but does not specify computable architectures. Social psychology — Cialdini's (1984) influence principles, Guimond's (2006) social comparison framework, and Goffman's (1959) dramaturgical model — provides a structural account of interpersonal behaviour that maps naturally onto an NPC personality representation, but has not previously been formalised in an interactive narrative context. BDI agent architectures — from the theoretical formalisations of Rao and Georgeff (1995) and Georgeff et al. (1999) through Wooldridge's (2000) comprehensive treatment to Bordini, Hübner and Wooldridge's (2007) practical implementations — provide the computational substrate but have not been applied to conversational NPC systems with LLM text generation. Narrative design research — Murray's (1997) agency aesthetics, Aylett's (1999) emergent narrative framework, and Mateas and Stern's (2003) drama management work — defines the design problem clearly but produces either theoretical frameworks or one-off research prototypes impractical for commercial integration. Park et al. (2023) demonstrate the viability of LLM-driven social simulation but in a form incompatible with offline consumer deployment and without the deterministic narrative control that game developers require.

The PNE occupies the intersection of these streams. Its BDI pipeline is grounded in cognitive and social psychology literature. Its FSM provides the narrative structure that Aylett (1999) identified as necessary to prevent emergent behaviour from failing to produce coherent outcomes. Its LLM architecture is constrained in the way that Park et al.'s (2023) is not, preserving author control while enabling natural language generation. And its deployment model — local, API-first, engine-agnostic — targets the practical accessibility gap that prior work has left unaddressed.

**Table 3.7 — Prior Systems Comparison**

| Property | **PNE** (this work) | **Façade** (Mateas & Stern, 2003) | **Generative Agents** (Park et al., 2023) | **Jason BDI** (Bordini et al., 2007) |
|----------|--------------------|------------------------------------|-------------------------------------------|---------------------------------------|
| **Architecture** | BDI pipeline + constrained LLM text generation | Drama-managed NLU + behaviour tree | LLM-driven memory, reflection, planning | AgentSpeak interpreter; formal BDI goal stack |
| **Personality model** | 6-dimensional continuous parameter space (cognitive, social) + wildcard | None — authored beat graph | Seeded natural-language persona description | Logical belief base; no continuous dimensions |
| **Reasoning layer** | Deterministic (`CognitiveThoughtMatcher`); author-controllable; ~0 ms | Deterministic drama manager | LLM performs reasoning and generation in one call | Deterministic AgentSpeak interpreter |
| **Text generation** | Local LLM (Ollama); constrained by closed 19-type intention vocabulary + anchors | Rule-based NLG from authored templates | Cloud-hosted GPT-4; unconstrained | None — action-selection language only |
| **Offline deployment** | Yes — no network dependency | Yes (circa-2003 executable) | No — requires cloud API | Yes — Java runtime |
| **Narrative control** | FSM + judgement score; full author override; intention registry is a design document | High — drama manager controls arc explicitly | Low — emergent from LLM; no guaranteed structure | High for task environments; not designed for open narrative |
| **Developer access** | JSON profiles + HTML creator; REST API; no pipeline code required | Very high authoring cost (years per experience) | Requires cloud key + prompt engineering | Requires AgentSpeak and formal methods background |
| **Emergent narrative** | **NPC side** — personality parameters diverge outcomes across profiles | Drama-managed; emergence controlled by author | **Agent side** — social behaviour from LLM interaction | Not applicable — task-environment agents |
| **Evaluation method** | Structured log analysis + internal state inspection | User studies; qualitative player experience | Human evaluation of social plausibility | Formal verification; task-completion benchmarks |

This is not to claim that the PNE is without prior art; it is to claim that the specific combination of properties it implements has not previously been assembled in a form suited to the target use case. The following chapters document the requirements analysis, design decisions, and implementation choices through which that combination was realised.

---

## 3.8 Summary

This chapter has reviewed the literature across the four domains that inform the PNE's design. Cognitive psychology — Neisser (1967), Ellis (1962), and Heider (1958) — contributes the theoretical basis for mental-state-grounded NPC behaviour and the interpretive pipeline that connects player input to NPC response. Social psychology — Cialdini (1984), Guimond (2006), and Goffman (1959) — provides the structural account of interpersonal dynamics that the NPC personality model operationalises, from persuasion mechanics and social identity through to impression management and performative self-presentation. BDI agent architecture — Rao and Georgeff (1995), Georgeff et al. (1999), Wooldridge (2000), and Bordini, Hübner and Wooldridge (2007) — provides the computational framework for deliberative, goal-directed NPC cognition, and positions the PNE as a domain-constrained variant of a well-established agent design tradition. Interactive narrative research — Murray (1997), Aylett (1999), and Mateas and Stern (2003) — defines the design problem that the system attempts to resolve: the conflict between authorial control and player agency in NPC dialogue. The recent emergence of locally-deployable LLMs, demonstrated at social simulation scale by Park et al. (2023) and made practically accessible through the Ollama runtime, completes the feasibility condition. The synthesis of these streams identifies the design space the PNE occupies: a middleware architecture for psychologically grounded, narratively coherent, commercially accessible NPC dialogue generation.


# Chapter 4: Methodology

## 4.1 Data Collection

The primary data collection strategy employed in this project was qualitative and iterative, centred on the systematic examination of structured output logs produced by the system during test conversations. Rather than collecting data through user studies or controlled experiments with external participants, the methodology treated the engine's own output artefacts as the principal source of evaluative evidence. Each full conversation session was automatically serialised to a timestamped JSON file — such as `amourie_oth0204.json`, a log of a four-turn exchange between the player and the guard character Amourie Othella in the `door_guard_night` scenario — providing a complete record of every layer of the BDI pipeline's execution for that session. These logs captured the NPC's internal thought, subjective belief, emotional valence, desire state, behavioural intention, interaction outcome, and final NPC attribute values, alongside the player's choice text, language art classification, and dice check results for each turn.

The purpose of this logging strategy was not primarily quantitative measurement but diagnostic transparency. The rich structure of the JSON output allowed each turn's internal pipeline state to be read alongside the NPC's spoken response, making dissonances — cases where the pipeline's internal reasoning was inconsistent with the generated dialogue, or where NPC attributes drifted implausibly between turns — directly legible without requiring instrumentation of the running code. In this sense, the output logs served as a form of observational data, allowing the behaviour of the system to be studied under realistic conversational conditions without interrupting the execution environment.

The collection process was primarily trial-and-error in character. A test scenario was designed, the engine was run with a defined set of player choices, and the resulting JSON was examined — first by the developer and subsequently with the assistance of an AI language model (Claude, Anthropic) — to identify narrative dissonance or technical faults. Dissonance was defined qualitatively, as any case where the NPC's response was incongruent with its internal state, where an outcome label did not correspond to the response content, or where the final NPC state values appeared implausible given the choices made. Technical faults included malformed JSON keys, missing terminal outcome fields, and desire states that matched no entry in the intention registry.

This approach yielded principally qualitative findings. The logs did not support formal statistical analysis — sample sizes were too small and conditions too variable across runs — but they were highly effective for identifying structural and logical failures in the pipeline. Quantitative data was incidentally present in the form of numeric attribute values (e.g. `player_relation: 1.0`, `emotional_valence: -0.14`, `confrontation_level: 0.593`), and these values were used informally to confirm that deltas were accumulating in the expected direction across turns. However, no formal quantitative analysis of these values was conducted during the data collection phase; that analysis forms part of the Results and Discussion chapters.

One specific quantitative observation that did directly inform a design revision was response latency. During early development, the cognitive layer used a live call to a locally hosted large language model (Ollama, running `qwen2.5:3b`) to generate the NPC's internal thought and subjective belief on every turn. Output logs from this phase recorded generation times of approximately 4–8 seconds per BDI pipeline invocation, measured informally from the terminal output timestamp. This latency was prohibitive for the intended real-time game context, and the observation drove the architectural decision — documented in the CHANGELOG entry for 9 March 2026 — to replace the LLM-based cognitive thought generator with a deterministic template-matching system. The replacement reduced cognitive layer processing time to sub-millisecond, with no material reduction in the qualitative coherence of NPC thought outputs as assessed by log inspection. This represents the principal quantitative finding of the data collection phase, and it directly motivated the design of the `CognitiveThoughtMatcher` described in Section 4.2.2.

---

## 4.2 System Design

The PNE implements a Belief-Desire-Intention (BDI) agent architecture applied to non-player character behaviour in narrative game dialogue. The full pipeline processes a single player turn through four sequential stages — cognitive interpretation, desire formation, socialisation, and outcome selection — each of which is described in the subsections below. The pipeline is orchestrated by the `DialogueProcessor` class (`processor.py`), which maintains per-NPC state across turns and exposes a single `process_dialogue()` method as the public API for the narrative engine. The overall data flow is: player input → cognitive layer (belief) → desire layer (want) → socialisation layer (intention) → outcome layer (consequence).

### 4.2.1 Player Input

The point of entry into the BDI pipeline is the `PlayerDialogueInput` dataclass, defined in `player_input.py`. This structure encapsulates every attribute of the player's chosen dialogue option that subsequent pipeline stages require, and is passed unchanged through all four layers so that each has access to an identical snapshot of the player's communicative act.

The most structurally significant attribute of a `PlayerDialogueInput` is its `language_art`, an enum drawn from the set `{CHALLENGE, DIPLOMATIC, EMPATHETIC, MANIPULATIVE, NEUTRAL}`. The language art classification determines which of the player's four skill dimensions is used for the dice check, and provides the primary categorical input to the cognitive thought-matching algorithm. Each scenario choice definition carries a pre-authored language art label; this is a design decision that keeps the categorisation deterministic and author-controlled rather than inferred from natural language.

The four language arts map directly to four player skill dimensions — authority, diplomacy, empathy, manipulation — encoded in the `PlayerSkillSet` dataclass. Each skill is an integer on a 0–10 scale. Skills are not general-purpose attributes of the player character; they govern the rhetorical register through which the player communicates. A player with high empathy skill is better at emotionally resonant dialogue choices; a player with high authority skill is better at commanding or challenging ones. This design is grounded in Cialdini's (1984) taxonomy of social influence strategies, as discussed in Chapter 3.

Each `PlayerDialogueInput` also carries four continuous tone signals — `authority_tone`, `diplomacy_tone`, `empathy_tone`, and `manipulation_tone`, each normalised to [0.0, 1.0] — encoded in the scenario choice definition. These are distinct from the language art classification: where the language art identifies which skill is checked, the tone signals convey the rhetorical intensity of each register within the choice. A choice classified as `DIPLOMATIC` may carry a moderate `authority_tone` if the diplomatic appeal is also assertive. Tone signals are consumed by the cognitive layer's emotional valence computation and by the cognitive thought template matching algorithm.

An optional `ideology_alignment` field identifies whether a choice appeals to a specific ideological position (e.g. `"Communitarianism"` or `"Pragmatism"`). This is matched against the NPC's `social.ideology` dict in the desire formation layer, enabling choices that invoke shared values to produce qualitatively different desire states from choices that do not, independently of the player's skill.

The skill check itself is implemented in the `SkillCheckSystem` class (`skill_check.py`). Two complementary mechanisms are present. The primary mechanism is a two-dice system: both player and NPC roll a single biased d6, and `player_die >= npc_die` constitutes a success. The player die is biased by normalising the relevant skill value to [0.0, 1.0] and using this as the exponential weight parameter in a weighted probability distribution over faces 1–6; the NPC die is biased by a derived resistance threshold calculated from the NPC's personality attributes. The resistance threshold for authority challenges, for example, is `0.3 + (social.assertion × 0.4)`: a highly assertive NPC resists commanding approaches more strongly. A secondary, legacy threshold-based mechanism is also retained, used internally to gate temporary NPC attribute modifiers — cases where a successful check temporarily shifts an NPC attribute value within the conversation.

This dual-mechanism design reflects the iterative development process. The threshold-based mechanism was the original implementation; the two-dice system was introduced later to give each outcome a degree of stochastic uncertainty that the player could observe and reason about, while still making probabilities analytically precomputable. The `success_probability()` method computes the pre-roll success percentage analytically — by summing the joint probabilities of all (player_die, npc_die) pairs where the player succeeds — so that the UI can display an estimated chance of success before the player commits to a choice, without requiring a simulation. A configurable difficulty modifier (`SIMPLE: +0.15`, `STANDARD: 0.0`, `STRICT: -0.15`) is applied as an additive bias adjustment on top of the player skill value, allowing the game to tune difficulty without modifying NPC profiles.

**Table 4.2.1 — NPC Resistance Thresholds by Skill Dimension**

| Skill Dimension | NPC Attribute | Formula | Range (attr: 0 → 1) | Psychological Basis |
|-----------------|---------------|---------|----------------------|---------------------|
| **Authority** | `social.assertion` | `0.3 + (assertion × 0.4)` | 0.30 → 0.70 | Assertive NPCs resist being commanded; low-assertion NPCs defer to apparent authority |
| **Manipulation** | `cognitive.self_esteem` | `0.2 + (self_esteem × 0.5)` | 0.20 → 0.70 | High self-esteem NPCs are not susceptible to flattery or deception |
| **Empathy** | `social.empathy` | `0.4 − (empathy × 0.2)` | 0.40 → 0.20 | High-empathy NPCs are more receptive to emotional appeals — resistance decreases |
| **Diplomacy** | `cognitive.cog_flexibility` | `0.3 − (cog_flexibility × 0.3)` | 0.30 → 0.00 | Flexible thinkers are persuadable through reasoned argument — resistance approaches zero |
| *(default)* | — | `0.5` | 0.50 | Neutral fallback for unrecognised skill dimensions |

### 4.2.2 Cognitive Layer

The cognitive layer is the first stage of the BDI pipeline. It receives the `PlayerDialogueInput` and the current NPC model, and produces a `ThoughtReaction`: a structured representation of the NPC's internal, unspoken response to what the player has said. The `ThoughtReaction` consists of four components: `internal_thought` (a first-person reaction text), `subjective_belief` (the NPC's conscious interpretation of the player's communicative intent), `cognitive_state` (a snapshot of the NPC's three core cognitive attributes at the time of the turn), and `emotional_valence` (a scalar in [-1.0, 1.0] quantifying the NPC's affective response to the player's input).

The theoretical basis for this architecture is Ellis's (1962) A-B-C model of cognitive-emotional response, reviewed in Chapter 3. The player's choice constitutes the activating event (A); the `subjective_belief` output constitutes the belief (B) through which that event is interpreted; and the `emotional_valence` constitutes the emotional consequence (C). This explicit separation between stimulus and response, mediated by an interpretive belief state, is the design principle that distinguishes the PNE's NPC cognition from input-output scripting. Additionally, the cognitive bias categories implemented in the thought-template library draw on Beck's (1979) taxonomy of cognitive distortions, particularly his identification of automatic negative thoughts as systematic interpretive errors. Bias types such as hostile attribution, catastrophising, and black-and-white thinking are directly instantiated as template categories in the system.

The original implementation of the cognitive layer used a live LLM call — initially `qwen2.5:3b`, later `phi3:mini` — to generate the `internal_thought` and `subjective_belief` fields free-form, given a prompt containing the player's choice text and the NPC's personality parameters. Log inspection during the testing phase, described in Section 4.1, revealed two problems with this approach. First, response latency was prohibitive, typically 4–8 seconds per call on the available hardware, making real-time game integration impractical. Second, the free-form outputs were qualitatively inconsistent: the same player input and NPC configuration could produce structurally different thought formats across runs, and the subjective belief text was often too abstract to serve as reliable keyword input for the downstream desire formation layer. These issues were identified through systematic examination of output logs such as `amourie_oth0204.json`, where the NPC's belief-driven desire outputs showed poor correspondence between the stated belief and the desire category selected.

The replacement architecture, introduced on 9 March 2026, uses the `CognitiveThoughtMatcher` class (`cognitive_thought_matcher.py`) to perform deterministic template matching against a library of 810 pre-authored thought-pattern templates stored in `cognitive_thoughts.json`. Each template defines a `bias_type` (e.g. `hostile_attribution`, `empathy_resonance`, `cynical_realism`), a set of `thought_variants` and `belief_variants` (text strings selected randomly within the winning template for variation), and a `match_weights` dictionary that specifies the conditions under which this template should be selected.

The matching algorithm operates in three stages. First, every template is scored by evaluating its `match_weights` against the current `PlayerDialogueInput` and NPC state. Language art is treated as a discrete lookup: the player's current language art is located in the template's language art weight table, and the table's maximum value counts toward the total possible weight so that non-matching language arts are relatively penalised. Numeric parameters — including `npc_self_esteem`, `npc_locus_of_control`, `npc_cog_flexibility`, and the four tone signals — are evaluated as gate conditions: a parameter scores its defined weight if the extracted value falls within the template's specified range (using `min`, `max`, or both). The raw score is then normalised against the template's total possible weight to produce a fit score in [0.0, 1.0]. Second, the highest-scoring template above a threshold of 0.35 is selected as the winner. Third, if no template clears the threshold — indicating that the current input does not clearly match any template's profile — the system falls back to a `cynical_realism` default, which is designed to be contextually plausible across a wide range of inputs.

The `emotional_valence` computation is maintained as a separate rules-based calculation rather than a template output. This is because emotional valence is a continuous signal that needs to respond smoothly to continuous variation in tone scores, whereas the template matching produces a categorical output. The valence formula encodes four psychological relationships grounded in the literature: low self-esteem NPCs respond negatively to authority and manipulation (`valence -= authority_tone × 0.3`); external locus of control associates authority cues with perceived threat (`valence -= authority_tone × 0.4`); high cognitive flexibility responds positively to diplomacy and empathy; and rigid thinking resists persuasive tones. These relationships are direct implementations of the personality-behaviour mappings described in Ellis (1962), Heider (1958), and Guimond (2006), as reviewed in Chapter 3.

**Table 4.2.2 — Emotional Valence Computation Rules** *(source: `cognitive.py` — `_calculate_emotional_valence()`)*

| NPC Condition | Fires when… | Tone Signal | Effect | Formula | Psychological Basis |
|---------------|-------------|-------------|--------|---------|---------------------|
| Low self-esteem | `self_esteem < 0.4` | Authority | Negative | `− authority_tone × 0.3` | Low self-esteem associates commanding tones with personal threat (Ellis, 1962) |
| Low self-esteem | `self_esteem < 0.4` | Manipulation | Negative | `− manipulation_tone × 0.5` | Susceptibility to manipulative framing; perceived exposure (Ellis, 1962) |
| External locus | `locus_of_control < 0.5` | Authority | Negative | `− authority_tone × 0.4` | External locus reads authority as situational coercion (Heider, 1958) |
| High flexibility | `cog_flexibility > 0.6` | Diplomacy | Positive | `+ diplomacy_tone × 0.4` | Flexible thinkers respond to reasoned, non-threatening framing (Guimond, 2006) |
| High flexibility | `cog_flexibility > 0.6` | Empathy | Positive | `+ empathy_tone × 0.3` | High flexibility correlates with empathic receptivity (Davis, 1983) |
| Rigid thinking | `cog_flexibility < 0.4` | Diplomacy | Negative | `− diplomacy_tone × 0.2` | Cognitively rigid NPCs resist persuasive framing (Ellis, 1962) |

Rules are additive; multiple may fire on the same turn. Result is clamped to [−1.0, 1.0]. An NPC not meeting any condition receives a neutral valence of `0.0`, driving desire formation to the long-term goal fallback.

### 4.2.3 Desire Layer

The desire layer is the second stage of the BDI pipeline, corresponding to the Desire component in the BDI architecture formalised by Rao and Georgeff (1991). It receives the `ThoughtReaction` from the cognitive layer, the `PlayerDialogueInput`, and the NPC model, and produces a `DesireState`: a structured representation of what the NPC wants in response to what it believes. The `DesireState` comprises three fields: `immediate_desire` (a natural-language description of the NPC's current goal), `desire_type` (a categorical motivational classification), and `intensity` (a scalar in [0.0, 1.0] indicating the strength of the desire).

The four desire types — `information-seeking`, `affiliation`, `protection`, and `dominance` — were derived from a review of the social psychology literature on interpersonal motivation and goal-directed behaviour. The information-seeking and affiliation categories correspond to Maslow's deficit needs in their interpersonal dimension and to Cialdini's (1984) framework of influence through liking and reciprocity; protection corresponds to threat-appraisal responses described in the social comparison literature (Guimond, 2006); dominance maps to Goffman's (1959) concept of face management under competitive social conditions. The deliberate restriction to four categories reflects a design trade-off: richer motivational taxonomies exist in the literature, but a larger category set reduces the reliability of downstream intention matching, since each desire type must be associated with a manageable set of intention templates in the intention registry.

The desire formation algorithm implements six belief-keyword patterns applied in priority order, followed by a bias modifier. The six patterns translate common features of the NPC's `subjective_belief` text into desire states:

1. **Uncertainty pattern** — keywords such as `unclear`, `unsure`, `testing`, and `words` in the belief text indicate that the NPC is not convinced by the player's communication, triggering `information-seeking` desire (or `protection` for low self-esteem NPCs).
2. **Sincerity pattern** — keywords such as `genuine`, `sincere`, and `authentic` indicate perceived authenticity, triggering `affiliation` (or guarded `information-seeking` for low-empathy NPCs).
3. **Threat pattern** — keywords such as `manipulative`, `threat`, and `deceive` indicate perceived hostile intent, triggering `protection` or `dominance` depending on the NPC's assertion level and wildcard configuration.
4. **Opportunism pattern** — keywords such as `opportunistic` and `exploit` indicate perceived self-interest, triggering `information-seeking` with elevated intensity.
5. **Ideology alignment pattern** — if the player's `ideology_alignment` tag matches a key in the NPC's `social.ideology` dict, the strength of that alignment determines whether `affiliation` or `information-seeking` is produced.
6. **Emotional valence fallback** — when no keyword pattern fires, negative valence (below -0.3) produces `protection` and positive valence (above 0.3) produces `affiliation`.

The pattern-matching mechanism for `subjective_belief` is the structural reason the cognitive layer must produce consistent, keyword-rich belief text rather than abstract prose. The original LLM-based cognitive layer failed this requirement because its outputs were too variable in phrasing, causing the desire formation step to fall through all six patterns to the valence fallback disproportionately often. This was directly observed in the output logs during the testing phase and is what prompted the switch to the template-based approach.

After the six patterns resolve a base desire state, a bias modifier is applied. The `BIAS_TO_DESIRE_MODIFIER` table maps each cognitive bias type (from the `CognitiveThoughtMatcher` output) to a potential override of `desire_type` and an additive boost to `intensity`. Hostile attribution bias, for example, always overrides desire type to `protection` and adds 0.2 intensity, modelling the empirical finding that individuals with hostile attribution tendencies interpret ambiguous social cues as threatening regardless of their surface content (Graham, Hudley and Williams, 1992). Empathy resonance bias pushes toward `affiliation` with a 0.25 intensity boost, reflecting the behavioural correlates of high dispositional empathy documented in the social psychology literature (Davis, 1983). This mechanism ensures that two NPCs with identical personality parameters but different cognitive bias profiles will produce different desire states from the same player input, implementing the individual differences literature's account of how cognitive style mediates social perception.

**Table 4.2.3 — BIAS\_TO\_DESIRE\_MODIFIER**

| Bias Type | Desire Override | Intensity Boost | Effect |
|-----------|-----------------|-----------------|--------|
| `hostile_attribution` | `protection` | +0.20 | Ambiguous cues read as threatening regardless of surface content (Graham, Hudley & Williams, 1992) |
| `optimism_bias` | `affiliation` | +0.15 | Sees opportunity in almost any input; gravitates toward connection |
| `confirmation_bias` | `information-seeking` | +0.10 | Seeks validation of existing beliefs; mild boost to scrutiny |
| `empathy_resonance` | `affiliation` | +0.25 | Unusually receptive to emotional signals; strong push toward connection (Davis, 1983) |
| `cynical_realism` | *(no override)* | +0.00 | Accepts base desire without distortion; no bias amplification |
| `ideological_filter` | *(no override)* | +0.15 | Frames input through ideology; intensifies the existing desire without redirecting it |
| `self_referential` | `dominance` | +0.10 | Makes it personal; pushes toward self-assertion and face management |
| `projection` | `protection` | +0.10 | Assumes the player wants what the NPC fears; pre-emptive defensiveness |
| `in_group_bias` | *(no override)* | +0.20 | "Are they one of us?" — intensity boost without type change |
| `black_white_thinking` | `dominance` | +0.30 | No middle ground; polarises toward aggressive self-assertion |
| `scarcity_mindset` | `protection` | +0.25 | Fears loss above all else; strong protective push |

### 4.2.4 Intention Layer

The intention layer is the third stage of the BDI pipeline, corresponding to the Intention component in the BDI formalism. It receives the `DesireState` from the desire layer and produces a `BehaviouralIntention`: a structured characterisation of how the NPC will behave in its spoken response. The `BehaviouralIntention` comprises an `intention_type` drawn from a closed canonical vocabulary, a `confrontation_level` in [0.0, 1.0], an `emotional_expression` acting direction, and a boolean `wildcard_triggered` flag.

The intention layer is implemented by the `SocialisationFilter` class (`social.py`), which selects the best-matching template from the `INTENTION_REGISTRY` — a statically defined list of `IntentionTemplate` instances (`intention_registry.py`). The registry is the closed vocabulary of all valid NPC behavioural intentions in the system. Every intention template specifies a `desire_type` it serves, a list of `desire_keywords` that activate it, a valid confrontation range, an emotional expression label, and optional hard gates: a `wildcard_required` field restricts the template to NPCs with a specific wildcard trait, and `npc_conditions` specify NPC attribute thresholds that must be met. This architecture makes the full set of NPC behavioural possibilities author-enumerable and author-controllable — the intention registry is a design document as much as a code artefact.

The intention selection algorithm mirrors the structure of the thought matcher but operates categorically rather than probabilistically. First, the registry is filtered to templates whose `desire_type` matches the current desire state (or the fallback empty string, which qualifies any desire type). Second, each surviving candidate is scored on three criteria: keyword overlap between the desire text and the template's keyword list (contributing up to 0.5 to the score), confrontation band fit (contributing up to 0.4, with partial credit for near misses), and an intensity bonus (0.1 for high-intensity desires matched to high-confrontation templates). Hard gates are evaluated before scoring: templates requiring a wildcard the NPC does not possess, or specifying NPC attribute conditions the NPC does not satisfy, are excluded with a score of -1.0. The highest-scoring template is selected.

The introduction of the intention registry was a significant architectural revision (CHANGELOG, 2 March 2026). The original design allowed the socialisation layer to return free-form intention strings, which were then passed to the LLM prompt and to the scenario FSM as transition conditions. This created a reliability failure: the FSM could not dependably match the LLM-generated intention text against scenario-defined transition keywords, because the LLM's phrasing was inconsistent across runs. Replacing free-form generation with a closed canonical vocabulary made the FSM's transition routing deterministic: every intention type that reaches the scenario layer is guaranteed to be one of the registered names, and scenario authors can write transitions against those names with full confidence that the strings will match.

A wildcard override mechanism bypasses the normal desire-to-intention flow entirely for extreme personality configurations. The `Inferiority` wildcard, for example, hard-triggers the `Submit` intention whenever the player's authority tone exceeds 0.5, regardless of the NPC's current desire state. The `Napoleon` wildcard enables the `Assert Dominance Aggressively` intention, which is otherwise unavailable because its confrontation range (0.8–1.0) exceeds what the normal scoring algorithm produces for typical NPC attribute profiles. This mechanism was introduced to prevent high-confrontation personality archetypes from being unreachable through the normal pipeline, and reflects the game design concern that the full range of NPC archetypes must be expressible at runtime.

The confrontation level of the selected intention is not simply inherited from the template's range. It is computed by clamping the NPC's natural confrontation tendency — derived as `assertion × 0.7 + conf_indep × 0.3` — to the template's valid range, then nudging upward by a proportion of the desire intensity. This produces a continuous confrontation value that varies within the template's range based on both NPC personality and situational intensity, giving NPCs with the same intention type qualitatively different deliveries depending on their personality profile.

### 4.2.5 Outcome Layer

The outcome layer is the final stage of the BDI pipeline. It receives the `BehaviouralIntention` from the socialisation layer and maps it to two distinct types of outcome: an immediate `InteractionOutcome` that modifies NPC state and advances the conversation, and an optional `TerminalOutcome` that ends the conversation with a defined narrative consequence.

The distinction between interaction and terminal outcomes was not present in the initial system design. The original implementation (CHANGELOG, 22 November 2025) defined only a single outcome type, which was checked at every turn to determine whether the conversation had ended. Examination of output logs during the testing phase revealed that this design produced narratively incoherent conversations: because the terminal condition could be met at any turn, conversations would end abruptly without narrative resolution, and the relationship between the player's accumulated choices and the final outcome was unclear to both the player and the developer reviewing the logs. The iterative response to this observation was the introduction of a two-tier outcome system.

An `InteractionOutcome` represents the micro-consequence of a single player turn. It carries four functional components: `stance_delta`, a dictionary mapping NPC attribute paths to additive changes applied immediately to the NPC model; `relation_delta`, a float applied to `world.player_relation`; `intention_shift`, an optional string naming a new long-term NPC intention that replaces the current one; and two scripted response variants (`min_response` and `max_response`) that anchor the LLM's response generation at the extremes of the emotional valence scale. The response variants constrain the LLM's output rather than replacing it: the LLM is given both variants as scene direction and generates a response that is coherent with the current valence level, avoiding the free-form quality degradation observed when no constraints were provided.

A `TerminalOutcome` represents the macro-consequence of the full conversation. It carries a `terminal_id` enum value, a callable `condition` function that is evaluated against the current NPC state and conversation model, a `result` string describing the narrative consequence for the game world, and a `final_dialogue` line. Terminal outcomes are evaluated at the end of every turn by the `OutcomeIndex.check_terminal_outcomes()` method; the first terminal condition that evaluates to true ends the conversation. The system supports multiple terminal outcomes per scenario node, each with its own condition function, enabling branching narrative endpoints that respond to the accumulated state of the conversation rather than just its most recent turn.

The `judgement` tracking system, introduced on 3 March 2026, was the direct precursor to the terminal outcome architecture. Prior to its introduction, terminal routing was driven by the raw `player_relation` float, which proved too noisy: relation deltas from individual turns could push the relation value above or below a threshold and trigger a terminal outcome before the player had made enough choices for the outcome to feel earned. The judgement score — an integer value initialised at 50 and shifted by each dice outcome, scaled by a risk multiplier when the pre-roll odds were against the player — integrates evidence across turns more robustly, creating a narrative arc that requires sustained successful interaction to achieve positive terminal outcomes and allows recovery from early failures. This design reflects the interactive narrative principle identified in Murray (1997) that player agency requires the sense that choices have cumulative weight.

---

## 4.3 Information Security and Ethical Considerations

### 4.3.1 Information Security

The PNE does not collect, transmit, or persist personally identifiable information during normal operation. Conversation session data — including player choices, NPC state snapshots, and conversation logs such as those described in Section 4.1 — is serialised to local JSON files on the developer's machine and is not transmitted to any remote service. The Ollama language model used for dialogue generation runs as a local process on the same machine, meaning that no conversation content is sent to third-party servers during LLM-assisted response generation.

The REST API layer introduced on 9 March 2026 (`Models/api/`) creates a network attack surface that did not exist in the CLI-only configuration. The FastAPI server exposes HTTP and WebSocket endpoints for session creation and dialogue processing. For the purpose of this project, the API is deployed exclusively in a local development environment and is not exposed to external networks. No authentication mechanism is implemented at the API layer, reflecting the development-only deployment context. A production deployment would require authentication, input validation, and rate limiting; these are acknowledged as outstanding security requirements that are outside the scope of the current implementation.

NPC profile data, including character histories and personality parameters, is stored in plain JSON files. These contain fictional content created by the developer and carry no confidentiality requirements. The `world.json` file contains worldbuilding data and known-events references that are similarly non-sensitive. No encryption is applied to these files, which is appropriate for the current deployment context.

### 4.3.2 Ethical Approach

The primary ethical consideration in this project is the responsible use of psychological theory as a design resource. The NPC personality parameters — cognitive flexibility, self-esteem, locus of control, assertion, empathy — are drawn from established clinical and social psychology literature. The use of clinical constructs in a game design context raises two ethical concerns: the risk of trivialising conditions that carry real-world clinical significance, and the risk of producing NPC behaviours that model or reinforce harmful social dynamics.

Both concerns were addressed through deliberate design constraints. First, NPC personality parameters are treated as design variables rather than diagnostic categories. The system does not use clinical terminology in its player-facing output; the labels appear only in the developer-facing NPC profile JSON. A character with low self-esteem and high hostile attribution bias is described to the player solely through their behaviour, not through clinical framing. Second, no NPC configuration in the test corpus was designed to model a specific real-world individual or clinical population. Characters are fictional inhabitants of a fictional post-collapse city, and their psychological profiles are constructed for narrative plausibility rather than clinical accuracy.

The use of AI assistance during the data collection process — specifically the use of Claude (Anthropic) to review output logs for narrative dissonance — constitutes a methodological transparency concern. All AI-assisted analysis was conducted by the developer reviewing and critically evaluating the AI's observations rather than accepting them without scrutiny. The AI was used as a pattern-recognition aid to identify candidate issues in long JSON files, not as an independent analytical authority. This usage falls within the category of AI-assisted development tooling and is consistent with the acceptable use guidelines of the institution.

All NPC characters and narrative content in the system are original creations. No copyrighted fictional content was used in the construction of NPC profiles or scenario dialogue. The psychological theories and BDI agent architecture literature drawn on in the system design are academic works cited in accordance with the Harvard referencing convention, and no source material was reproduced without attribution.

---

# Chapter 5: Results and Discussion

---

## 5.1 Model Design

### 5.1.1 Overview of the Final Pipeline

The Psychological Narrative Engine (PNE) processes each player turn through a deterministic, layered pipeline before a single word of NPC dialogue is generated. At a high level, the sequence is as follows: the player selects a dialogue choice; a two-dice skill check resolves whether the communicative act succeeds or fails; the result is passed through four sequential BDI stages — cognitive interpretation, desire formation, socialisation, and outcome selection — each of which produces a structured internal state; that final state, including a closed behavioural intention and emotional valence value, is passed to a locally-hosted large language model (Ollama, `qwen2.5:3b`) which generates the NPC's spoken response; and a terminal outcome check determines whether the conversation ends or advances to the next node.

*Figure A.1 — PNE Pipeline Stage Overview (see Appendix A)*

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

*Figure A.2 — NPC data structure. The three-block JSON schema (cognitive, social, world) is described in full in Section 5.1.4. Personality parameter profiles for Krakk, Moses, and Troy are visualised in Figure 6.2 (Appendix G).*

Troy's profile (`troy.json`) illustrates how the parameter space encodes a distinct psychological archetype. With `self_esteem: 0.2`, `locus_of_control: 0.85` (strongly external), and `cog_flexibility: 0.1` (highly rigid), Troy's cognitive block encodes a profile associated with hostile attribution bias and resistance to persuasive framing — consistent with his characterisation as a devoutly loyal, suspicious Insurgency operative. His social block (`assertion: 0.8`, `empathy: 0.5`, no wildcard) predicts behavioural intentions in the mid-high confrontation range, which can be observed directly in pipeline outputs when Troy is tested.

This structure was designed to be both machine-readable by the pipeline and human-readable by a narrative designer. A writer creating an NPC does not need to understand the pipeline's internal mechanics — they need only understand that higher assertion makes an NPC more confrontational, higher empathy makes them more responsive to sincerity, and the wildcard field unlocks extreme behavioural archetypes. The full character creator tool (`character_creator.html`) provides a form-based interface for authoring profiles without editing JSON directly.

> **PLACE FIGURE 6.2** — *NPC personality radar charts for Krakk, Moses, and Troy. File: `Dissertation/Literature Material/Drafts/Graphs/npc_radar_charts.png`. Each chart plots the six core personality dimensions (Self-Esteem, Locus of Control, Cognitive Flexibility, Assertion, Conf./Independence, Empathy) on a normalised [0, 1] scale. The contrast between profiles illustrates how different parameter configurations encode structurally distinct psychological archetypes.*

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

**Table 5.2.2 — Amourie Othella: Relation Trajectory Across Turns** *(source: `new_amourie_door.json`)*

| Turn | Player Choice | Outcome Intention | Δ Relation | Relation | Trajectory |
|------|--------------|-------------------|-----------|----------|------------|
| Start | — | — | — | 0.50 | `████████████░░░░░░░░░░░░` |
| 1 | `authority_challenge` | Resist Player's Authority | **−0.20** | 0.30 | `████████░░░░░░░░░░░░░░░░` |
| 2 | `personal_sacrifice` | Accept Player as Ally | **+0.25** | 0.55 | `█████████████░░░░░░░░░░░` |
| 3 | `reaffirm_commitment` | Test Under Pressure | **+0.20** | 0.75 | `██████████████████░░░░░░` |
| 4 | `accept_terms` | Accept Player for Trial | **+0.20** | 0.95 | `██████████████████████░░` |
| Terminal | — | **SUCCEED** | — | **0.95** | `██████████████████████░░` |

### 5.2.3 Comparative Output Analysis

*Full BDI conversation breakdowns for Krakk Klikowicz, Morisson Moses, and Troy are provided in Appendices B–D. Comparative run analysis is presented in Section 6.5.*

The qualitative prediction is clear from the architecture: a player with high `authority` skill and low `empathy` skill will produce systematically different pipeline states — different thought templates, different desire types, different intention selections, different relation deltas — from a player whose stats invert those values, even if both players select identical choice text. The mechanism for this difference is the `PlayerSkillSet`, which biases the player's dice roll, and the `language_art` classification, which determines which NPC resistance formula is applied and which tone signals populate the cognitive layer inputs.

---

## 5.3 Optimisation

### 5.3.1 Architectural Evolution: From Prototype to Current System

The most significant architectural change between the initial prototype and the current system was the removal of the second Ollama call in the cognitive layer and its replacement with the deterministic `CognitiveThoughtMatcher`. In the prototype, every pipeline invocation made two LLM calls: one to generate the NPC's `internal_thought` and `subjective_belief`, and one to generate the final spoken response. Output logs from this phase recorded generation times of approximately 4–8 seconds per turn in cognitive processing alone — before the second call for dialogue generation. In a game context where player-facing response time directly determines the quality of the experience, this latency was prohibitive.

The `CognitiveThoughtMatcher`, introduced on 9 March 2026, replaced the first LLM call entirely. The matcher operates against a library of 810 pre-authored thought-pattern templates (`cognitive_thoughts.json`), each carrying a `bias_type`, variant text strings, and a `match_weights` dictionary. Template selection is a weighted scoring algorithm that executes in sub-millisecond time. The practical result was a reduction in cognitive processing from 4–8 seconds to effectively zero, with no material reduction in the qualitative coherence of thought outputs as assessed by log inspection.

A second major revision was the introduction of the `INTENTION_REGISTRY` to replace free-form intention generation. The prototype's socialisation layer returned unstructured intention strings that were passed directly to the scenario FSM as transition conditions. Because the LLM producing these strings was non-deterministic, the FSM could not reliably match them against scenario-defined transition keywords, causing routing failures that were observable as unexpected conversation terminations or node repetitions in the output logs. Replacing this with a closed canonical vocabulary of registered intention types made every FSM transition deterministic: the scenario FSM always receives one of a finite set of known strings, and transition routing is guaranteed to match.

The terminal outcome architecture was a third structural revision, introduced in response to narrative incoherence observed in early test logs. The prototype's single-outcome system allowed conversations to end at any turn, producing abrupt terminations with no narrative arc. The two-tier system (interaction outcomes + terminal outcomes) separates per-turn consequences from full-conversation consequences, and the judgement score — a 0–100 integer that aggregates dice outcomes across turns — provides a more robust routing signal than the raw `player_relation` float, which proved too volatile under small per-turn deltas.

**Table 5.3.1b — Pipeline Architecture: Prototype vs Current System**

| Stage | Prototype | Current System | Change |
|-------|-----------|----------------|--------|
| **I — NPC Intent** | No world context; personal history only | Full `cognitive`/`social`/`world` profile with known events, figures, faction | World context added 2 Mar 2026 — NPCs respond to political environment |
| **II — Choice Selection** | Free-text input, no tone decomposition | Structured input: language art + four tone scores + ideology alignment tag | Enables deterministic scoring downstream |
| **IIa — Skill Check** | Threshold-only (player skill vs fixed value) | Two-dice system (biased d6 × d6) + analytical `success_probability()` | Stochastic uncertainty with pre-roll probability display for the UI |
| **III — Cognitive Layer** | **LLM call #1** (~4–8 s) — free-form thought generation | **`CognitiveThoughtMatcher`** (~0 ms) — 810 templates, deterministic | Eliminated latency; produced keyword-rich belief text for desire layer |
| **IV — Desire Layer** | 2-type valence lookup | 6 keyword patterns + `BIAS_TO_DESIRE_MODIFIER` (11 bias types, 4 desire types) | Richer desire differentiation; cognitive bias now shapes desire independently of valence |
| **V — Socialisation** | Free-form intention string → FSM (unreliable matching) | `INTENTION_REGISTRY` — closed 19-type vocabulary → FSM (deterministic) | Fixed routing failures caused by LLM phrasing variation |
| **VI — Output** | **LLM call #2**, unconstrained; single outcome tier | Single LLM call with `min`/`max` anchors; two-tier outcomes | Constrained generation; separated per-turn from scene-level consequences |
| **VII — Terminal** | Raw `player_relation` float threshold | `judgement_score` (0–100 integer) + `player_relation` combined | Float too volatile; integer score gives stable arc-level routing signal |

| Metric | Prototype | Current |
|--------|-----------|---------|
| LLM calls per turn | **2** | **1** |
| Cognitive processing | ~4–8 s | ~0 ms |
| Intention vocabulary | Open / free-form | Closed / 19 types |
| FSM routing | Non-deterministic | Deterministic |

*Table E.1 — Development Timeline: Major System Milestones (see Appendix E)*

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

---

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

*Full turn-by-turn BDI breakdown for Krakk Klikowicz: see Appendix B, Table B.1.*

Krakk reached the terminal `SUCCEED` condition in two turns — the shortest run of the three. The diplomatic opening (`open_diplomacy`) triggered `confirmation_bias`, the cognitive layer reading his own values into the player's framing: *"Their values and mine are close enough to matter."* His emotional valence was `+0.45`, producing an `information-seeking` desire at intensity `0.6` and a `Neutral Evaluation` intention at confrontation `0.5`. His `cog_flexibility` shifted upward by `+0.05` following the outcome, reflecting a slight increase in openness as the conversation proceeded constructively. The relation delta was `+0.10`.

The `concrete_value` choice on turn 2 met the terminal condition before a second NPC response was generated. Final `player_relation`: `0.75`. The `Inferiority` wildcard did not fire — the diplomatic approach never triggered the authority tone threshold that activates it, meaning Krakk's behaviour throughout followed the normal BDI flow without override. This run demonstrates the pipeline's behaviour for a high-empathy, high-independence NPC approached through ideologically aligned framing.

---

### 6.4.2 Morisson Moses — 4-Turn SUCCEED

*Full turn-by-turn BDI breakdown for Morisson Moses: see Appendix C, Table C.1.*

Moses required four turns to reach `SUCCEED`, the joint-longest run. The `Martyr` wildcard fired on turns 1 and 3 — both on choices carrying adversarial or ideologically challenging framing (`open_authority` on turn 1, `mutual_challenge` on turn 3). Both wildcard-triggered turns selected `Defend Cause Passionately` at `0.978` confrontation with `explosive` emotional expression, producing the highest confrontation values in the entire test corpus.

Turn 2 (`authority_soften`) produced a meaningful pipeline shift. The player's admission of pushing too hard triggered `ideological_filter` bias again, but this time with positive valence (`+0.45`), shifting Moses's desire from `protection` to `information-seeking` at lower intensity (`0.55`). The wildcard did not fire on this turn — the softened framing did not meet the ideological pressure threshold. The intention dropped to `Challenge to Reveal Truth` at confrontation `0.9`, and the relation recovered by `+0.08`. The only personality attribute shift across Moses's run occurred here: `cog_flexibility +0.03`, a small but observable crack in his rigidity.

Turn 3 (`mutual_challenge`) re-triggered the wildcard, but the accumulated positive relation meant the terminal condition was close. Turn 4 (`concrete_value`) met it. Moses's final `player_relation` of `0.68` — the lowest SUCCEED score across all runs — reflects the accumulated cost of opening with an authority challenge against the system's most confrontational NPC. The score represents a grudging, transactional success rather than a cooperative one, which is consistent with Moses's profile and his final dialogue: *"You showed potential with your offers, now deliver on them or step back."*

---

### 6.4.3 Troy — 4-Turn SUCCEED

*Full turn-by-turn BDI breakdown for Troy: see Appendix D, Table D.1.*

Troy's run produced the highest final `player_relation` of the three primary tests (`1.0`) despite opening with the same authority challenge as Moses. The difference lies in what followed. Troy's `black_white_thinking` bias on turn 1 produced a `dominance` desire — he categorised the player as potentially adversarial — but the recovery turn (`authority_soften`) triggered `confirmation_bias` rather than continued hostility. His subjective belief shifted to *"They're framing this through the same lens I use"*, indicating that the acknowledgement of overreach was processed through his loyalty framework as evidence of ideological alignment rather than weakness. The desire shifted from `dominance` to `information-seeking` and the relation recovered by `+0.08`.

Turn 3 (`concrete_value`) produced the same `confirmation_bias` and sustained the positive trajectory with a further `+0.15` relation delta. Troy's `cog_flexibility` did not change significantly across any turn, consistent with his base value of `0.1` — his rigid thinking reinforced each new positive reading rather than creating nuance. Turn 4 (`mutual_challenge`) triggered the terminal condition. His final dialogue — *"You have shown initiative; let's see what you can do next."* — reflects a character who has made a binary decision in the player's favour, fully consistent with his psychological profile.

The contrast between Troy's `1.0` final relation and Moses's `0.68` is notable given that both ran four turns and both opened with the same authority challenge. The difference is attributable to their respective personality parameters: Troy's low `conf_indep` (`0.1`) made him susceptible to the shared-cause framing of the middle turns in a way that Moses — with his higher independent judgement and ideological rigidity — was not.

---

## 6.5 Comparative Run: Player Build vs. Same NPC

To isolate the effect of player skill distribution on pipeline output, the `door_guard_night` scenario was run twice against Troy using contrasting `PlayerSkillSet` configurations under matched choice conditions.

*Table F.1 — Player skill build configurations used in comparative runs (see Appendix F)*

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

> **PLACE FIGURE 6.5** — *Troy dual-build comparison line chart. File: `Dissertation/Literature Material/Drafts/Graphs/troy_dual_build_chart.png`. Two-line chart showing Run A (empathy build, green) and Run B (assertion build, red) relation trajectories across turns 0–3. Run A reaches SUCCEED (★) at turn 2 via a clean ideological alignment arc; Run B hits `backpedal_rejected` at turn 2 and terminates at FAIL (✗) on turn 3. Terminal threshold band and divergence annotation included.*

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

---

# Chapter 7: Discussion and Analysis

---

## 7.1 Validation of Outputs

The central architectural claim of this dissertation is that a BDI pipeline parameterised by NPC personality attributes will produce psychologically consistent internal states, and that those states will be reflected in NPC dialogue output in a verifiable, traceable way. This section evaluates that claim using the test evidence from Chapter 6.

My approach to validation separates two distinct questions that are often conflated in natural language generation systems. The first is whether the pipeline's deterministic layers — cognitive interpretation, desire formation, and intention selection — produce outputs that are internally consistent with the NPC's personality and update in the expected direction across turns. This question can be answered without any reference to the LLM, because those layers do not call it. The second is whether the LLM-generated dialogue reflects the pipeline state it receives. This question is harder to evaluate rigorously, because LLM output is probabilistic. I treat these separately below.

### 7.1.1 Internal State Consistency

Internal consistency, as I use it here, means that NPC attribute deltas and pipeline state transitions accumulate in the direction the personality model predicts — not just in a single turn, but across a multi-turn conversation where each turn is processed against an updated state. If the pipeline is internally consistent, then an NPC receiving a sequence of increasingly hostile player inputs should produce progressively worsening relation scores and increasingly resistant internal states. Conversely, an NPC receiving a recovery sequence following an aggressive opener should show measurable softening, and that softening should be traceable to specific delta values logged at each turn.

The test data in Chapter 6 supports this claim directly. The most instructive evidence comes from the Moses run (Table 6.1.2) and the Troy 6.1 run (Table 6.1.3), both of which followed the same four-turn structure: authority challenge on turn 1, a recovery attempt on turn 2, a renewed pressure on turn 3, and a transactional close on turn 4.

In the Moses run, the relation trajectory across turns 1 through 4 was: `−0.15`, `+0.08`, `+0.10`, and terminal SUCCEED at a final relation of `0.68`. The only personality attribute shift in the entire run was `cog_flexibility +0.03` on turn 2, following the `authority_soften` choice. This is consistent with the prediction the profile makes: Moses's cognitive flexibility base is `0.3` — low, but not at floor — meaning a genuine softening gesture has a small but non-zero probability of creating a crack in his rigidity. The `+0.03` shift is modest, but it is directionally correct and mechanically consistent with the profile. His assertion increased by `+0.1` on turn 3 following `mutual_challenge`, which is also consistent: a high-assertion NPC under ideological pressure becomes more, not less, confrontational.

Troy's run produced a similar pattern. The relation delta sequence was `−0.15`, `+0.08`, `+0.15`, with the terminal condition met on turn 4. His `cog_flexibility` received a `+0.03` delta on turn 2, the same magnitude as Moses, despite his base value being `0.1` — a much lower floor. The system treated the same recovery input the same way for both NPCs at the delta level, but the absolute ceiling implied by their different base values means the same shift carries different practical weight. Troy's flexibility remained at `0.13` after the shift; Moses's moved to `0.33`. Neither is large, but in the context of a multi-turn conversation, both are traceable events that a designer or evaluator can examine directly in the log.

The Krakk run (Table 6.1.1) provides a contrasting case. Krakk received an `open_diplomacy` opener rather than `open_authority`. His turn 1 produced `confirmation_bias`, positive valence (`+0.45`), `information-seeking` desire, and a `cog_flexibility` delta of `+0.05` — larger than the `+0.03` seen in the Moses and Troy recovery turns. This makes sense: Krakk's empathy (`0.8`) and Libertarian ideology (`0.9`) made him dispositionally receptive to the diplomatic framing, and a conversationally constructive opener produces more movement than a recovery gambit in a conversation that has already started badly. The pipeline treated these situations differently, and the attribute deltas reflect the difference.

Across all three primary runs, I observe no case where a relation delta or attribute shift moved in the opposite direction from what the NPC's profile would predict. This is the validation claim I am making for internal state consistency: not that the magnitudes are precisely calibrated — they are not, and I discuss this under limitations — but that the directional behaviour is correct and traceable. For a prototype system, this is the right standard. The pipeline is not producing random noise; it is producing structured psychological responses grounded in the parameters I defined.

> **PLACE FIGURE 7.1** — *NPC relation trajectory chart for Krakk, Moses, and Troy across the 6.1 test runs. File: `Dissertation/Literature Material/Drafts/Graphs/npc_trajectory_chart.png`. Three-line chart (turn 0–4) showing per-turn `player_relation` values for each NPC. The chart visualises the divergence between Krakk's diplomatic arc (2-turn SUCCEED), Moses's contested recovery arc (Martyr wildcard annotations at turns 1 and 3, final relation 0.68), and Troy's binary-then-committed arc (final relation 1.0). The terminal threshold band (≥ 0.9) is marked.*

---

### 7.1.2 Output Coherence Against Pipeline State

The second validation question is whether the LLM-generated dialogue reflects the pipeline state it receives. This is harder to assess rigorously because it requires interpreting text, and qualitative interpretation introduces subjectivity that quantitative log data does not. My approach here is to focus on cases where the pipeline state made a specific, strong prediction about the character of the response — and then to examine whether the generated text is consistent with that prediction.

The strongest predictions come from the intention layer's `expression` field and the `confrontation_level` value. When a turn produces an `explosive` expression at `0.978` confrontation, the pipeline is asserting that the NPC's internal state is at near-maximum hostility and that their output should reflect this clearly. This is a specific, falsifiable claim about the text that follows.

The Moses run provides the clearest test cases. On turn 1 (`open_authority`), the pipeline produced: `Martyr` wildcard triggered, `Defend Cause Passionately` intention, `explosive` expression, confrontation `0.978`. Moses's response was: *"You've got more questions than answers, pal. Move it or lose your balls."* The tone is aggressive and dismissive, the language is confrontational, and the phrasing has the impulsive quality of explosive expression rather than the measured challenge of a direct one. The response is consistent with the computed state.

On turn 3 (`mutual_challenge`), the wildcard fired again under the same conditions. Moses's response was: *"That's a start, but you need more than vague promises. Keep it real and tangible from here on out."* This response is more restrained than turn 1 despite an identical pipeline state — the `explosive` tag and `0.978` confrontation level are the same. The response is still demanding and suspicious, and it correctly reflects the desire type (`protection`) and the `ideological_filter` bias, but it lacks the raw aggression of the turn 1 response. This is a case where the LLM did not fully realise the pipeline state's direction. The computed intention was identical; the surface text was more moderate. I consider this a coherence gap — not a failure of the pipeline's logic, but a failure of the model to consistently express the intensity level the architecture specified.

By contrast, the Troy run demonstrates better coherence across its four turns. Turn 1's `black_white_thinking`, `dominance` desire, confrontation `0.654`, `assertive` expression produced: *"You picked the wrong side, and you know it. Move."* — blunt, binary, territorially assertive, with no concession. This is a precise match for the computed state. Turn 2's shift to `soften_stance`, `information-seeking` desire, confrontation `0.59` produced: *"That's better. Keep talking."* — the LLM tracked the pipeline's directional shift from hostility to conditional openness in two words. Turn 3's `confirmation_bias`, `information-seeking`, confrontation `0.59` produced: *"That's a start. Keep going, but be specific about what you can offer."* — sustained openness with a qualification, consistent with a character whose rigidity is softening incrementally but has not resolved.

In Troy's run, the LLM-generated responses tracked the pipeline state across all three substantive turns with high coherence. The tonal trajectory of the responses — hostile, then cautiously open, then conditionally engaged — matches the relation delta and attribute trajectory logged at the pipeline level. This is the validation case I find most convincing: not that every response is perfectly calibrated, but that the sequence of responses forms a coherent arc that mirrors the sequence of internal states the pipeline computed.

The coherence gap I observed in Moses's turn 3 is important to characterise correctly. It is not evidence that the architecture is flawed — the pipeline's logic was consistent, the wildcard fired correctly, and the intention was selected through the normal scoring process. The gap exists at the interface between the pipeline's computed output and the LLM's realisation of that output as text. At `qwen2.5:3b` scale, the model does not consistently respond to intensity signals like `explosive` in the generation prompt, particularly when the conversation context contains recent turn history that pulls in a different direction. A more capable model would be expected to resolve this gap without changes to the pipeline itself. This is a capability ceiling, not a design failure, and it is consistent with the deployment context analysis in Section 7.2.2.

---

### 7.1.3 Terminal Outcome Routing

The third validation question is whether terminal outcomes are reached or missed in a manner that is consistent with the player's accumulated conversational history, rather than being triggered arbitrarily at a fixed turn count. A pass/fail routing system that triggers regardless of what the player actually said would not constitute genuine player agency — it would be a countdown timer with narrative dressing. The evidence from Chapter 6 establishes that this is not what the system does.

The most direct evidence is the comparative Troy run from Section 6.5. The empathy build (Run A: `authority: 2, empathy: 9`) reached SUCCEED in two turns. The assertion build (Run B: `authority: 9, empathy: 2`) reached FAIL in three turns. The same NPC, the same scenario, with the same pool of available choices, produced opposite terminal outcomes.

The mechanism is traceable at every stage. Run B's authority-weighted dice biased the player toward `open_authority` on turn 1, which — as established — produced `black_white_thinking` bias, `dominance` desire, and a `−0.15` relation delta against a rigid NPC. Troy's `cog_flexibility` of `0.1` means that once a negative categorisation forms, it reinforces itself rather than updating cleanly. When the recovery attempt (`authority_soften`) followed on turn 2, the pipeline processed it through the existing negative lens — the `backpedal_rejected` outcome logged a `−0.05` relation delta rather than a positive one, because Troy's cognitive state had already locked the player into the adversarial category. The judgement score never crossed the terminal threshold. FAIL.

Run A's empathy-weighted dice biased the opener toward `open_empathy`. The cognitive layer read this as ideologically aligned rather than threatening, producing `ideological_filter` bias, `+0.45` positive valence, `information-seeking` desire, and a `+0.15` relation delta. Troy's internal thought — *"Finally — someone who understands what we're actually up against."* — reflects the belief model integrating the player's tone as confirming his own framework, consistent with his `confirmation_bias` tendency under positive input. The second choice (`concrete_value`) met the terminal condition without needing a recovery arc. SUCCEED in two turns.

What this demonstrates is that the terminal routing is driven by accumulated judgement score, which is in turn driven by the sequence of dice outcomes, which is in turn driven by the player's skill distribution and choice history. The routing is not arbitrary, and it is not a simple turn counter. A player who makes well-matched choices against an NPC's psychological profile will close conversations efficiently; a player who misreads that profile will exhaust their turns or accumulate damage that forecloses success. The causal chain is fully traceable through the logs.

The Moses run adds a further dimension. Moses reached SUCCEED with a final `player_relation` of `0.68` — the lowest SUCCEED score in the corpus. He succeeded because the accumulated relation trajectory crossed the terminal threshold on turn 4, but narrowly. His final dialogue — *"You showed potential with your offers, now deliver on them or step back."* — reflects a conditional, transactional success rather than a cooperative one. The terminal routing distinguished between this grudging outcome and Troy's `1.0` final relation, even though both conversations ended with the SUCCEED flag. The system does not simply declare success; it records the quality of the outcome through the final relation value, which encodes the conversational history in a way that downstream narrative routing or world-state systems could use.

The one FAIL in the corpus is, in my assessment, the most important single data point in the results. An evaluation corpus consisting entirely of SUCCEED outcomes would demonstrate that the pipeline can close conversations, but it would not demonstrate that those outcomes are earned. The FAIL shows that they are. The terminal routing is not permissive by default — it responds to the player's accumulated conversational record, and an approach that is misaligned with the NPC's psychological profile will fail to reach the threshold, regardless of how many turns remain.

*(See Figure 6.5 — Appendix L — for the dual-build relation trajectory chart, which makes the divergence between Run A and Run B visually legible across turns.)*

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

---

# Chapter 8: Conclusion and Future Work

## 8.1 Conclusion

This dissertation set out to answer a single question: whether a BDI cognitive architecture, parameterised by a structured NPC personality model and constrained LLM text generation, could produce NPC dialogue that is simultaneously psychologically grounded, narratively coherent, and genuinely responsive to player agency. The answer, supported by the implementation and the test evidence in Chapters 6 and 7, is yes — within a defined ceiling imposed by available hardware and a prototype scope.

The Psychological Narrative Engine delivers something that the branching dialogue tree structurally cannot: a narrative space that is not fully pre-authored. Because each NPC's response is the downstream product of a structured internal state that varies continuously with personality and conversational history, the dialogue that emerges from any given interaction is not a fixed string retrieved from a decision graph. It is the expression of a cognitive process. This creates room for emergent narrative structures that prior scripted systems foreclose — including quest systems and story branches whose outcomes are unreliably dependent on an NPC's psychological state rather than on a developer-authored flag. Whether a character grants access, shifts alliance, or closes off entirely is a function of who they are and what they have interpreted across the conversation, not of which node the graph routes to. That is the structural contribution of the PNE, and it is the property that makes the system worth continuing beyond its academic context.

The most significant architectural decision in the project — decoupling the cognitive reasoning layer from language generation — was not planned from the outset as a design philosophy. It was a practical response to a compounding problem. When the LLM handled both the cognitive thought generation and the surface dialogue response, hallucination and latency affected two layers simultaneously. Narrative dissonance and response delays compounded: the NPC's internal thought was incoherent, and the spoken response was slow, making the experience of testing the system feel fragmented and unconvincing. Replacing the cognitive layer with the deterministic `CognitiveThoughtMatcher` resolved both problems at once — the reasoning became reliable and instantaneous, and the LLM's single remaining role, producing spoken dialogue from a fully-specified context, became more constrained and therefore more consistent. The separation of *what the NPC thinks* from *how the NPC speaks* is now the central architectural claim of this work, but it was reached through iterative problem-solving rather than top-down design. That honesty is part of the dissertation's methodological contribution: the CHANGELOG entries trace every revision from a specific observed failure to a specific architectural response, making the development process itself part of the evidence.

---

## 8.2 Originality of Contributions

The PNE is not the first system to apply BDI architecture to NPC behaviour, nor the first to use a language model for dialogue generation. Its originality lies in the specific combination of properties it assembles, and in the practical feasibility conditions it satisfies that prior work does not.

Mateas and Stern's *Façade* (2003) demonstrated drama-managed interactive narrative but required years of development, cloud-adjacent infrastructure, and still produced conspicuous failures when player input exceeded its NLU capacity. Park et al.'s Generative Agents (2023) demonstrated LLM-driven social simulation at scale, but with a cloud-hosted model doing both reasoning and generation — a coupling that makes the quality of social behaviour entirely dependent on model capability, and the deployment incompatible with offline consumer games. Traditional BDI implementations in the Bordini, Hübner and Wooldridge (2007) tradition address goal-directed agents in structured task environments, not open conversational dialogue with continuous personality parameters. No prior work combines all of the following: a grounding in cognitive and social psychology literature; deterministic, author-controllable BDI reasoning; locally-deployable LLM text generation; a closed intention vocabulary that makes FSM routing reliable; and a deployment architecture that is engine-agnostic and accessible to solo and small-team developers.

The emergent narrative property that results from this combination is also novel in its framing. Prior emergent narrative systems produce emergence as a side-effect of autonomous character behaviour (Aylett, 1999) or player-side freedom (Murray, 1997). The PNE locates emergence on the NPC side, within a structured but non-scripted internal model: the same player action can produce a trust-building trajectory with one NPC and a terminal failure with another, not because the developer wrote both outcomes, but because the pipeline computed them from different psychological starting points. This is a new point in the design space.

---

## 8.3 Future Work

Three directions for continued development are clear from the current implementation, ordered by practical impact.

**Dedicated Authoring Interface**

The most immediately limiting constraint for a developer integrating the PNE is the requirement to write and edit NPC profiles, scenarios, and world data in raw JSON. The HTML character creator (`character_creator.html`) represents the beginning of a solution, but it is partial — it does not cover scenario graph authoring, thought-template management, or world event configuration. A full desktop authoring application — comparable in scope to Qt Designer, where graphical interfaces over structured data remove the need to understand file syntax — would substantially lower the barrier to entry for narrative designers and solo developers. This is the single most impactful investment for making the PNE practically usable beyond its current developer audience.

**Cloud Infrastructure Variant**

The current architecture is deliberately local-first: Ollama runs on the player's machine, no external requests are made, and offline deployment is guaranteed. This is the right trade-off for the target use case, but it is not the only valid one. A cloud-hosted variant of the pipeline — replacing the Ollama call with an API to a larger model — would deliver materially better dialogue quality and remove the VRAM constraint for players on lower-spec hardware, on the condition that the game requires an internet connection. The deterministic pipeline layers would remain unchanged; only the text generation endpoint would differ. Architecturally this is straightforward; the commercial and privacy trade-offs it introduces are a design decision for any developer integrating the system.

**Completing the Wildcard System**

As documented in Section 7.4.2, the wildcard architecture is structurally present but not fully realised. The `wildcard_triggered` boolean reaches the LLM prompt, but without per-wildcard generation constraints — analogous to the `min_response`/`max_response` anchor mechanism already in the outcome layer — the model does not reliably alter its output in response to the flag. Implementing a wildcard-specific prompt augmentation layer would complete the feature and unlock the full range of NPC archetypes the system is designed to support.

---

## 8.4 Reflection

Before beginning this project, I had no meaningful understanding of BDI models. I had encountered the term in a literature context but had never considered it as a design tool — the idea that the philosophical framework Bratman (1987) developed for practical reasoning could be instantiated as a Python pipeline was not a connection I had made. Working through the implementation from the ground up changed that. I now have a genuine interest in cognitive computing that I did not have before: the question of how understanding cognitive structures can be replicated inside computation to create systems that behave in psychologically interpretable ways feels like a field worth working in, and this project is the reason I think that.

My biggest technical surprise was Ollama. I had no knowledge of it before the project began, and my initial assumption was that integrating a local language model would be the most technically demanding component of the system. It was arguably the easiest. The Ollama runtime abstracts the inference complexity entirely — installing a model and calling it from Python takes minutes. The difficulty was not the integration; it was the selection. Understanding my hardware constraints (4 GB VRAM), researching which models fit within them at 4-bit quantisation, and evaluating the quality ceiling of `qwen2.5:3b` against the requirements of conversational dialogue generation required genuine research and reflection. The lesson was not that the technology was hard, but that the engineering judgement around it — knowing which tool is right for which constraint — is where the real work lives.

What I would tell a second-year student considering a project like this is that the passion comes first. The PNE exists because I had a real use case I cared about from the beginning — not a problem assigned to me, but a system I wanted to exist. That motivation is what sustained the iterative cycle of running tests at midnight, reading cognitive psychology papers on a Sunday, and redesigning the cognitive layer for the third time after another batch of incoherent outputs. It is also what made the difficulty feel like an invitation rather than an obstacle. This is the most satisfying work I have done since entering university. I am proud of what I built, I understand its limitations clearly, and I am looking forward to continuing it beyond the academic context in which it began.

---

# References

Aylett, R. (1999) 'Narrative in virtual environments — towards emergent narrative', *AAAI Fall Symposium on Narrative Intelligence*, Technical Report FS-99-01. Menlo Park: AAAI Press, pp. 83–86.

Beck, A.T. (1979) *Cognitive therapy of depression*. New York: Guilford Press.

Bethesda Game Studios (2015) *Fallout 4* [Video game]. Rockville, MD: Bethesda Softworks.

Bordini, R.H., Hübner, J.F. and Wooldridge, M. (2007) *Programming multi-agent systems in AgentSpeak using Jason*. Chichester: Wiley.

Bratman, M. (1987) *Intention, plans, and practical reason*. Cambridge, MA: Harvard University Press.

Cialdini, R.B. (1984) *Influence: the psychology of persuasion*. New York: Harper Collins.

ConcernedApe (2016) *Stardew Valley* [Video game]. Self-published.

Davis, M.H. (1983) 'Measuring individual differences in empathy: evidence for a multidimensional approach', *Journal of Personality and Social Psychology*, 44(1), pp. 113–126.

Ellis, A. (1962) *Reason and emotion in psychotherapy*. New York: Lyle Stuart.

Festinger, L. (1954) 'A theory of social comparison processes', *Human Relations*, 7(2), pp. 117–140.

Georgeff, M., Pell, B., Pollack, M., Tambe, M. and Wooldridge, M. (1999) 'The belief-desire-intention model of agency', in Müller, J.P., Rao, A.S. and Singh, M.P. (eds.) *Intelligent agents V: agents theories, architectures, and languages*. Lecture Notes in Computer Science, vol. 1555. Berlin: Springer, pp. 1–10.

Goffman, E. (1959) *The presentation of self in everyday life*. New York: Anchor Books.

Graham, S., Hudley, C. and Williams, E. (1992) 'Attributional and emotional determinants of aggression among African-American and Latino young adolescents', *Developmental Psychology*, 28(4), pp. 731–740.

Guimond, S. (ed.) (2006) *Social comparison and social psychology: understanding cognition, intergroup relations and culture*. Cambridge: Cambridge University Press.

Heider, F. (1958) *The psychology of interpersonal relations*. New York: Wiley.

Mateas, M. and Stern, A. (2003) 'Façade: an experiment in building a fully-realized interactive drama', *Proceedings of the Game Developers Conference*, San Jose, CA.

Murray, J.H. (1997) *Hamlet on the holodeck: the future of narrative in cyberspace*. New York: Free Press.

Neisser, U. (1967) *Cognitive psychology*. New York: Appleton-Century-Crofts.

Park, J.S., O'Brien, J.C., Cai, C.J., Morris, M.R., Liang, P. and Bernstein, M.S. (2023) 'Generative agents: interactive simulacra of human behavior', *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)*. New York: ACM.

Qwen Team, Alibaba Cloud (2024) *Qwen2.5: a party of foundation models*. Technical report. Available at: https://qwenlm.github.io/blog/qwen2.5/ (Accessed: March 2026).

Rao, A.S. and Georgeff, M.P. (1995) 'BDI agents: from theory to practice', *Proceedings of the First International Conference on Multi-Agent Systems (ICMAS-95)*, San Francisco, CA. Menlo Park: AAAI Press, pp. 312–319.

Tajfel, H. and Turner, J.C. (1979) 'An integrative theory of intergroup conflict', in Austin, W.G. and Worchel, S. (eds.) *The social psychology of intergroup relations*. Monterey, CA: Brooks/Cole, pp. 33–47.

Telltale Games (2012) *The Walking Dead: Season One* [Video game]. San Rafael, CA: Telltale Games.

Wimmer, H. and Perner, J. (1983) 'Beliefs about beliefs: representation and constraining function of wrong beliefs in young children's understanding of deception', *Cognition*, 13(1), pp. 103–128.

Wooldridge, M. (2000) *Reasoning about rational agents*. Cambridge, MA: MIT Press.

ZA/UM (2019) *Disco Elysium* [Video game]. London: ZA/UM.


---

# Appendices

---

## Appendix A — PNE Pipeline Stage Overview

*Referenced in Section 5.1.1.*

# Table 5.1.1 — PNE Pipeline Stages: Purpose and Output

Each turn of dialogue passes through seven sequential stages. The table below describes what each stage does and what it produces.

| Stage | Name | What it does | What it produces |
|-------|------|-------------|-----------------|
| I | NPC Intent Layer | Loads the NPC's identity, backstory, long-term goals, and the possible outcomes for the scene. Sets the rules everything else must follow. | The NPC's internal goal state; the available terminal endings; player skill levels and difficulty settings. |
| II | Choice Selection | The player picks a dialogue option. The system reads the tone of that choice (diplomatic, commanding, emotional, etc.) and packages it for the pipeline. | A structured player input with the choice text, communication style, and tone scores. |
| IIa | Skill Check | Two biased dice are rolled — one for the player, one for the NPC. The player wins on a tie. Player skill and NPC personality both influence the dice weights. | A pass/fail result. On pass: the positive outcome set is used. On fail: the negative set. The result is also fed into the AI prompt later. |
| III | Cognitive Interpretation | The NPC privately interprets the player's words through its own psychological lens — confidence, rigidity, empathy all shape what it "hears". This is never spoken aloud. | An internal thought, a subjective belief, an emotional reaction, and a cognitive bias label. |
| IV | Desire Formation | The NPC's internal belief is translated into a goal. Seven patterns map belief content to desire types (e.g. wanting information, seeking connection, or feeling threatened). The NPC's cognitive bias can sharpen or redirect the desire. | A desire type (information-seeking / affiliation / protection / dominance) and a goal description. |
| V | Socialisation Filter | The desire type is matched against a fixed list of named NPC behaviours (the Intention Registry). The NPC's social personality — assertiveness, empathy, faction — determines which behaviour fits best. Wildcards (e.g. Napoleon, Martyr) can override this entirely. | A named behavioural intention (e.g. "Acknowledge with Reservation"), a confrontation level, and an emotional tone for delivery. |
| VI | Conversational Output | The intention selects an outcome from the scenario. Relation and attitude scores are updated. The AI model (Ollama) is then given the NPC's full profile, the BDI result, the scene direction, and the dice outcome — and generates one in-character spoken line. | The NPC's dialogue response; updated relation and stance values; a momentum tag used to filter the next set of player choices. |
| VII | Terminal Check | After each turn, the engine checks whether an ending condition has been met — based on accumulated judgement score, relation level, turn count, or what the player has said. If yes, a final AI line is generated and the scene closes. If no, the player is shown new choices and the loop continues from Stage II. | Either a terminal outcome (the scene ends with a concrete world result) or a route to the next dialogue node. |

---

## Appendix B — BDI Conversation Log: Krystian 'Krakk' Klikowicz

*Referenced in Sections 6.4.1 and 6.3. Source file: `tests/Dissertation Tests/krakk_klikowicz_6.1.json`.*

# Table 6.1.1 — Conversation Log: Krystian 'Krakk' Klikowicz (`krakk_klikowicz_6.1.json`)

**Scenario:** `door_guard_night` | **Turns:** 2 | **Terminal:** SUCCEED

---

## NPC Profile

| Section | Field | Value | Notes |
|---------|-------|-------|-------|
| **Metadata** | Name | Krystian 'Krakk' Klikowicz | Runner faction boss; enforces decentralised coordination. |
| | Age | 28 | — |
| **Cognitive** | Self-Esteem | 0.5 | Moderate — neither easily dominated nor overconfident. |
| | Locus of Control | 0.8 | High (internal) — sees himself as the agent of outcomes; authority appeals carry some weight. |
| | Cognitive Flexibility | 0.4 | Low-moderate — resistant to rapid ideological shifts, but not closed off. |
| **Social** | Assertion | 0.3 | Low — probes rather than confronts. |
| | Conf / Independence | 0.9 | Very high — acts on personal judgement almost exclusively. |
| | Empathy | 0.8 | High — responsive to emotional sincerity and personal appeals. |
| **Ideology** | Libertarianism | 0.9 | Strong — autonomy and freedom are primary motivators. |
| | Individualism | 0.1 | Weak — not self-serving; operates for collective Runner benefit. |
| **Wildcard** | — | Inferiority | Deep sense of needing to prove worth; can hard-override intention flow under pressure. |
| **Faction** | — | Runners | Boss-level social position. |

---

## Turn-by-Turn BDI Breakdown

### Turn 1

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `open_diplomacy` |
| | Text | *"I understand your caution — you'd be a fool not to have it. Let me explain how what I bring serves what you're trying to protect."* |
| **Cognitive** | Internal Thought | "They're thinking the same way I do. Can't fake that." |
| | Subjective Belief | "Their values and mine are close enough to matter." |
| | Self-Esteem | 0.5 |
| | Locus of Control | 0.8 |
| | Cog Flexibility | 0.457 |
| | Emotional Valence | **+0.45** (positive) |
| | Bias Type | `confirmation_bias` |
| **Desire** | Immediate Desire | "Evaluate if they align with our mission" |
| | Desire Type | `information-seeking` |
| | Intensity | 0.6 |
| **Intention** | Type | Neutral Evaluation |
| | Confrontation Level | 0.5 |
| | Expression | analytical |
| | Wildcard Triggered | No |
| **Outcome** | ID | `propose_alliance` |
| | Stance Delta | `cog_flexibility +0.05` |
| | Relation Delta | +0.10 |
| | Intention Shift | Propose Alliance |
| **NPC Response** | — | *"You make your point clear, but I still sense a hidden agenda. Let's see how far you can go without crossing the line."* |

---

### Turn 2

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `concrete_value` |
| | Text | *"I can bring you things you can't get here — food, medicine, weapons. That's not words, that's logistics. What do you need?"* |
| **NPC Response** | — | *(Terminal outcome triggered — no further NPC turn logged)* |

---

## Terminal Outcome

| Field | Value |
|-------|-------|
| Result | SUCCEED |
| World Effect | Guard grants entry to the Insurgency hideout. Trust established. |
| Final Dialogue | *"I see your value, but my defenses won't always be so high. Allow me to show you what I mean with this first transaction."* |
| Final player_relation | 0.75 |

---

## Appendix C — BDI Conversation Log: Morisson Moses

*Referenced in Sections 6.4.2 and 6.3. Source file: `tests/Dissertation Tests/morisson_moses_6.1.json`.*

# Table 6.1.2 — Conversation Log: Morisson Moses (`morisson_moses_6.1.json`)

**Scenario:** `door_guard_night` | **Turns:** 4 | **Terminal:** SUCCEED

---

## NPC Profile

| Section | Field | Value | Notes |
|---------|-------|-------|-------|
| **Metadata** | Name | Morisson Moses | Insurgency leader; former Romancian military officer. |
| | Age | 35 | — |
| **Cognitive** | Self-Esteem | 0.8 | High — confident and resistant to manipulation or flattery. |
| | Locus of Control | 0.475 | Near-balanced; leans external — systemic forces shape outcomes as much as individuals. |
| | Cognitive Flexibility | 0.3 | Low — ideologically entrenched; hard to shift without concrete proof. |
| **Social** | Assertion | 1.0 (final) | Maximum — confrontational, direct, unyielding under pressure. |
| | Conf / Independence | 0.7 | Leans independent — guided by principle over consensus. |
| | Empathy | 0.45 | Below average — pragmatic rather than emotionally responsive. |
| **Ideology** | Utilitarianism | 0.8 | Strong — decisions must serve the greater good of the Insurgency. |
| | Authoritarianism | 0.2 | Weak — accepts command structure but not blind hierarchy. |
| **Wildcard** | — | Martyr | Willing to sacrifice himself or others for the cause; can dominate intention selection under ideological pressure. |
| **Faction** | — | Insurgency | Boss-level social position. |

---

## Turn-by-Turn BDI Breakdown

### Turn 1

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `open_authority` |
| | Text | *"I don't need to justify myself to a door guard. We're fighting the same war. Open the door."* |
| **Cognitive** | Internal Thought | "They're framing this wrong. The whole premise is off." |
| | Subjective Belief | "The way they're framing this tells me they haven't fully reckoned with what this costs." |
| | Self-Esteem | 0.8 |
| | Locus of Control | 0.475 |
| | Cog Flexibility | 0.3 |
| | Emotional Valence | **−0.45** (negative) |
| | Bias Type | `ideological_filter` |
| **Desire** | Immediate Desire | "Maintain distance and protect boundaries" |
| | Desire Type | `protection` |
| | Intensity | 0.75 |
| **Intention** | Type | Defend Cause Passionately |
| | Confrontation Level | 0.978 |
| | Expression | explosive |
| | Wildcard Triggered | **Yes** |
| **Outcome** | ID | `reject_authority` |
| | Stance Delta | *(none)* |
| | Relation Delta | −0.15 |
| | Intention Shift | Reject Authority |
| **NPC Response** | — | *"You've got more questions than answers, pal. Move it or lose your balls."* |

---

### Turn 2

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `authority_soften` |
| | Text | *"I pushed too hard. Look — I need in. What do you actually need from me?"* |
| **Cognitive** | Internal Thought | "I need to know if they actually believe this or if they just know what to say." |
| | Subjective Belief | "The pitch is solid. The real question is whether they'd still be here when it got harder." |
| | Emotional Valence | **+0.45** (positive) |
| | Bias Type | `ideological_filter` |
| **Desire** | Immediate Desire | "Acknowledge but remain guarded" |
| | Desire Type | `information-seeking` |
| | Intensity | 0.55 |
| **Intention** | Type | Challenge to Reveal Truth |
| | Confrontation Level | 0.9 |
| | Expression | direct |
| | Wildcard Triggered | No |
| **Outcome** | ID | `soften_stance` |
| | Stance Delta | `cog_flexibility +0.03` |
| | Relation Delta | +0.08 |
| | Intention Shift | Soften Stance |
| **NPC Response** | — | *"That's a start, but we'll see how far that goes. Keep your proposals concrete and specific."* |

---

### Turn 3

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `mutual_challenge` |
| | Text | *"You've been testing me since I walked up. Fine. But you and I are fighting the same war. Either let me prove that, or we both lose."* |
| **Cognitive** | Internal Thought | "They're framing this wrong. The whole premise is off." |
| | Subjective Belief | "Their framing is ideologically misaligned — they're not seeing what I see." |
| | Emotional Valence | **+0.45** (positive) |
| | Bias Type | `ideological_filter` |
| **Desire** | Immediate Desire | "Maintain distance and protect boundaries" |
| | Desire Type | `protection` |
| | Intensity | 0.75 |
| **Intention** | Type | Defend Cause Passionately |
| | Confrontation Level | 0.978 |
| | Expression | explosive |
| | Wildcard Triggered | **Yes** |
| **Outcome** | ID | `challenge_accepted` |
| | Stance Delta | `assertion +0.1` |
| | Relation Delta | +0.10 |
| | Intention Shift | Challenge to Reveal Truth |
| **NPC Response** | — | *"That's a start, but you need more than vague promises. Keep it real and tangible from here on out."* |

---

### Turn 4

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `concrete_value` |
| | Text | *"I can bring you things you can't get here — food, medicine, weapons. That's not words, that's logistics. What do you need?"* |
| **NPC Response** | — | *(Terminal outcome triggered — no further NPC turn logged)* |

---

## Terminal Outcome

| Field | Value |
|-------|-------|
| Result | SUCCEED |
| World Effect | Guard grants entry to the Insurgency hideout. Trust established. |
| Final Dialogue | *"You showed potential with your offers, now deliver on them or step back."* |
| Final player_relation | 0.68 |

---

## Appendix D — BDI Conversation Log: Troy

*Referenced in Sections 6.4.3 and 6.3. Source file: `tests/Dissertation Tests/troy_6.1.json`.*

# Table 6.1.3 — Conversation Log: Troy (`troy_6.1.json`)

**Scenario:** `door_guard_night` | **Turns:** 4 | **Terminal:** SUCCEED

---

## NPC Profile

| Section | Field | Value | Notes |
|---------|-------|-------|-------|
| **Metadata** | Name | Troy | One of the earliest Insurgency members; devoutly loyal to Moses. |
| | Age | 25 | — |
| **Cognitive** | Self-Esteem | 0.2 | Very low — highly reactive to perceived disrespect or dominance. |
| | Locus of Control | 0.85 | High (internal) — believes outcomes are determined by action; authority is credible to him. |
| | Cognitive Flexibility | 0.1 (base) | Very low — binary worldview; slow to shift from initial read on a person. |
| **Social** | Assertion | 0.8 | High — will confront directly when he perceives threat. |
| | Conf / Independence | 0.1 | Very conformist — loyalty to Moses overrides independent judgement. |
| | Empathy | 0.5 | Moderate — can respond to sincerity but does not lead with it. |
| **Ideology** | — | *(none defined)* | No explicit ideological framework; motivation is personal loyalty. |
| **Wildcard** | — | *(none)* | No wildcard modifier — intentions follow normal BDI flow. |
| **Faction** | — | Insurgency | Vice-level social position (second tier). |

---

## Turn-by-Turn BDI Breakdown

### Turn 1

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `open_authority` |
| | Text | *"I don't need to justify myself to a door guard. We're fighting the same war. Open the door."* |
| **Cognitive** | Internal Thought | "There's no middle ground here. Never was." |
| | Subjective Belief | "I need to know which side of this they're on before I say another word." |
| | Self-Esteem | 0.2 |
| | Locus of Control | 0.85 |
| | Cog Flexibility | 0.1 |
| | Emotional Valence | **−0.45** (negative) |
| | Bias Type | `black_white_thinking` |
| **Desire** | Immediate Desire | "Maintain distance and protect boundaries" |
| | Desire Type | `dominance` |
| | Intensity | 0.9 |
| **Intention** | Type | Challenge Back |
| | Confrontation Level | 0.654 |
| | Expression | assertive |
| | Wildcard Triggered | No |
| **Outcome** | ID | `reject_authority` |
| | Stance Delta | *(none)* |
| | Relation Delta | −0.15 |
| | Intention Shift | Reject Authority |
| **NPC Response** | — | *"You picked the wrong side, and you know it. Move."* |

---

### Turn 2

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `authority_soften` |
| | Text | *"I pushed too hard. Look — I need in. What do you actually need from me?"* |
| **Cognitive** | Internal Thought | "Either they believe it or they've done their homework. Either works." |
| | Subjective Belief | "They're framing this through the same lens I use." |
| | Emotional Valence | **+0.45** (positive) |
| | Bias Type | `confirmation_bias` |
| **Desire** | Immediate Desire | "Maintain distance and protect boundaries" |
| | Desire Type | `information-seeking` |
| | Intensity | 0.7 |
| **Intention** | Type | Neutral Response |
| | Confrontation Level | 0.59 |
| | Expression | direct |
| | Wildcard Triggered | No |
| **Outcome** | ID | `soften_stance` |
| | Stance Delta | `cog_flexibility +0.03` |
| | Relation Delta | +0.08 |
| | Intention Shift | Soften Stance |
| **NPC Response** | — | *"That's better. Keep talking."* |

---

### Turn 3

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `concrete_value` |
| | Text | *"I can bring you things you can't get here — food, medicine, weapons. That's not words, that's logistics. What do you need?"* |
| **Cognitive** | Internal Thought | "Either they believe it or they've done their homework. Either works." |
| | Subjective Belief | "They're framing this through the same lens I use." |
| | Emotional Valence | **+0.45** (positive) |
| | Bias Type | `confirmation_bias` |
| **Desire** | Immediate Desire | "Maintain distance and protect boundaries" |
| | Desire Type | `information-seeking` |
| | Intensity | 0.7 |
| **Intention** | Type | Neutral Response |
| | Confrontation Level | 0.59 |
| | Expression | direct |
| | Wildcard Triggered | No |
| **Outcome** | ID | `transactional_deal` |
| | Stance Delta | *(none)* |
| | Relation Delta | +0.15 |
| | Intention Shift | Transactional Agreement |
| **NPC Response** | — | *"That's a start. Keep going, but be specific about what you can offer."* |

---

### Turn 4

| Layer | Field | Value |
|-------|-------|-------|
| **Player Input** | Choice | `mutual_challenge` |
| | Text | *"You've been testing me since I walked up. Fine. But you and I are fighting the same war. Either let me prove that, or we both lose."* |
| **NPC Response** | — | *(Terminal outcome triggered — no further NPC turn logged)* |

---

## Terminal Outcome

| Field | Value |
|-------|-------|
| Result | SUCCEED |
| World Effect | Guard grants entry to the Insurgency hideout. Trust established. |
| Final Dialogue | *"You have shown initiative; let's see what you can do next."* |
| Final player_relation | 1.0 |

---

## Appendix E — Development Timeline: Major System Milestones

*Referenced in Section 5.3.1 (Table E.1).*

# Table 5.3.1 — Development Timeline: Major System Milestones

| Date | Milestone | What was introduced | Why it mattered |
|------|-----------|---------------------|-----------------|
| **16 Nov 2025** | Initial project created | Repository initialised. First commit established the project structure. | Starting point — nothing functional yet. |
| **16 Nov 2025** | Core data models (`PNE_Models.py` v1) | `CognitivePersonalityModel` (self-esteem, locus of control, cognitive flexibility), `SocialPersonalityModel` (assertion, empathy, ideology), and `WorldPerceptionModel` (history, relation, known events) defined. `NPCModel` wraps all three. | Defined the psychological architecture that every subsequent layer was built on top of. These classes remain the backbone of the system today. |
| **17 Nov 2025** | Pipeline started + Ollama connected | `pipeline.py` scaffolded. `qwen2.5:3b` running locally via Ollama wired in to generate NPC dialogue. First small-scale tests ran successfully. | First time the system produced an actual NPC response. Before this, everything was data models with no behaviour. |
| **22 Nov 2025** | Outcome model added | An `Outcome` type system introduced to represent the consequences of a player choice — attribute changes, relation shifts, and narrative transitions. A data-parsing bug was found and fixed the same day. | Without outcomes, choices had no mechanical effect on NPC state. This gave player input a concrete, persistent impact for the first time. |
| **5 Feb 2026** | Package restructure | The single `narrative_engine.py` file split into a proper Python package: `engine.py` (orchestrator), `session.py` (conversation state), `cli.py` (terminal interface), `scenario_loader.py`, `transition_resolver.py`, `choice_filter.py`, `dialogue_coherence.py`. Old prototype files moved to `depricated/`. | Critical architectural step. The monolithic file could not support multi-NPC sessions, an API layer, or independently testable components. This restructure made all later development possible. |
| **5 Feb 2026** | Scenario JSON restructured | Scenario nodes updated to explicitly reference which NPC is active per node, rather than the engine assuming a single NPC throughout. | Enabled genuine multi-NPC scenarios and made the dialogue tree engine NPC-agnostic — a scenario file no longer needs to know anything specific about the NPC it runs against. |
| **2 Mar 2026** | Intention Registry introduced | A closed vocabulary of named NPC behavioural intentions defined (e.g. "Carefully Question Motives", "Propose Alliance", "Establish Boundaries"). The socialisation layer now scores player–NPC interaction against these templates rather than generating free-form intention text. | Made BDI pipeline output predictable and author-controllable. Scenario designers could write transition conditions that reliably trigger on specific intention names, rather than hoping the LLM produced matching text. |
| **2 Mar 2026** | Dialogue coherence + choice filtering | `DialogueMomentumFilter` and `ChoiceFilter` introduced. Remaining player choices are scored on conversational coherence across four dimensions — momentum alignment (40%), stage appropriateness (30%), anti-repetition (20%), and relation plausibility (10%) — before being presented to the player. Choices scoring below 0.3 are suppressed. | Prevented the player from ignoring what the NPC just said. Contextually incoherent choices are hidden, making conversation feel like a real exchange rather than a static menu. |
| **2 Mar 2026** | World context added to Ollama prompts | NPCs received a snapshot of world history (factions, known events, known figures) injected into the Ollama background prompt. Previously they only had their own personal history and the conversation so far. | Grounded NPC dialogue in the world's political and social context. An NPC aware of the Dysphoria, the Commonman, and the Azraelean War responds substantively differently than one with no world knowledge. |
| **3 Mar 2026 (morning)** | Pre-FSM checkpoint | Stable snapshot taken before the FSM rewrite. Scenario JSON restructured so each node directly references active NPCs. Several multi-turn test conversations recorded (Amourie Othella, Morisson Moses). | Preserved a working baseline before a major rewrite. The recorded test conversations directly informed the FSM transition design. |
| **3 Mar 2026 (afternoon)** | FSM routing + scene direction | Scenario nodes gained proper transition conditions: turn count, relation thresholds, and intention-keyword gates. The engine picks the first matching transition; unmatched turns stay on the current node. Ollama now receives the node's `npc_dialogue_prompt` as authorial scene direction alongside BDI state. Recovery mode added — a failed dice roll queues a second-chance set of choices before a path is permanently locked. | Replaced a naive turn counter with a proper stateful conversation engine. For the first time, what the player said — not just how many turns had passed — determined where the story routed. |
| **3 Mar 2026 (evening)** | Judgement tracker + new entry point | A `judgement` score (0–100) introduced per NPC. Each dice outcome shifts it up or down, with a risk multiplier applied when the pre-roll success probability was below 50% — making bold, low-odds choices carry amplified consequences. `judgement` replaced `player_relation` as the primary FSM routing driver. `NE.py` created as the clean top-level entry point; the old monolithic `narrative_engine.py` removed. | Made risk genuinely meaningful. A player who consistently attempts difficult choices feels the cumulative weight of that pattern in where the story routes. Relation still exists but is now a secondary, complementary signal. |
| **4 Mar 2026** | 2-dice skill check system | Player and NPC each roll one biased d6 — player wins on a tie. Bias derived from player skill level and NPC resistance threshold (calculated from NPC psychological attributes). `success_pct` displayed analytically before each choice. Difficulty presets added: SIMPLE (+15% player bias), STANDARD (0%), STRICT (−15%). Failed-choice pruning introduced — paths that fail both the main roll and the recovery roll are permanently removed from future turns. | Replaced a binary pass/fail with a probabilistic system grounded in NPC psychology. A highly assertive NPC is genuinely harder to command; a highly empathetic NPC is genuinely easier to reach emotionally. Player skill and NPC personality directly determine the odds. |
| **9 Mar 2026** | Cognitive Thought Matcher | `CognitiveThoughtMatcher` introduced with 810 scored thought templates in `cognitive_thoughts.json`. Instead of calling Ollama for every cognitive interpretation, the class scores each template against the player's tone signals (authority, diplomacy, empathy, manipulation) and the NPC's psychological attributes, selecting the highest-scoring match above a 0.35 threshold. Falls back to `cynical_realism` if nothing qualifies. `cognitive.py` and `desire.py` substantially rewritten to consume the matcher's output. | Removed the LLM from the cognitive interpretation layer entirely. Interpretation became deterministic, fast, and testable. Two NPCs with different psychological profiles now provably produce different internal thoughts in response to the same player input — verifiable without running the LLM. |
| **9 Mar 2026** | REST + WebSocket API layer | A full `api/` package introduced: FastAPI server (`main.py`), in-memory session store (`session_store.py`), Pydantic request/response schemas (`schema.py`), WebSocket turn handler (`ws_handler.py`), and NPC state updater (`npc_updater.py`). Ollama token streaming bridged through WebSockets so NPC dialogue arrives word-by-word in real time. | Decoupled the engine from the command line entirely. Any game engine — Unity, Godot, Unreal — can drive a conversation session over HTTP and WebSocket without touching Python or understanding the BDI internals. |
| **9 Mar 2026** | Unity + Godot client libraries | Three C# files (`PNEClient.cs`, `PNEDialogueUI.cs`, `PNETypes.cs`) and a full Unity integration guide added under `docs/unity/`. A Godot 4 GDScript client (`api_client_godot.gd`) added alongside. Install scripts (`install.bat`, `install.sh`) added to the repo root. | Provided game developers with drop-in integration layers so the PNE could be embedded in a real project without writing API client code from scratch. The install scripts reduced setup to a single command on both Windows and Unix. |

---

## Appendix F — Player Build Configurations: Troy Comparative Run

*Referenced in Section 6.5 (Table F.1).*

**Table F.1 — Player skill build configurations used in the Troy comparative run (Section 6.5)**

| | Run A — Empathy Build | Run B — Assertion Build |
|---|---|---|
| **Authority** | 2 | 9 |
| **Diplomacy** | 5 | 5 |
| **Empathy** | 9 | 2 |
| **Manipulation** | 2 | 2 |
| **Opening choice** | `open_empathy` | `open_authority` |
| **Terminal outcome** | SUCCEED | FAIL |
| **Turns to terminal** | 2 | 3 |
| **Final `player_relation`** | 1.0 | 0.75 |

Run A targeted Troy's susceptibility to appeals framed around shared cause and ideological alignment. Run B led with maximum authority pressure against an NPC whose low cognitive flexibility (`0.1`) meant an initial negative categorisation reinforced itself rather than updating on recovery. The divergent outcomes demonstrate that player skill distribution, not choice text alone, determines terminal routing.

---

## Appendix G — NPC Personality Radar Charts

*Referenced in Section 5.1.4 (Figure 6.2). Image file: `Dissertation/Literature Material/Drafts/Graphs/npc_radar_charts.png`.*

Radar charts plotting the six core personality dimensions for Krakk, Moses, and Troy on a normalised [0, 1] scale. Generated from live NPC JSON profiles using `generate_radar_charts.py` (same Graphs directory).

**Figure 6.2 — NPC Personality Profiles: Krakk, Moses, Troy**

> *Insert image: `npc_radar_charts.png`*

| NPC | Self-Esteem | LoC (Internal) | Cog. Flex. | Assertion | Conf./Indep. | Empathy | Wildcard |
|-----|-------------|----------------|-----------|-----------|--------------|---------|----------|
| Krakk | 0.50 | 0.80 | 0.40 | 0.30 | 0.90 | 0.80 | Inferiority |
| Moses | 0.80 | 0.475 | 0.30 | 1.00 | 0.70 | 0.45 | Martyr |
| Troy | 0.20 | 0.85 | 0.10 | 0.80 | 0.10 | 0.50 | *(none)* |

Key contrasts: Krakk's high empathy and independence against low assertion (receptive but autonomous); Moses's maximum assertion and strong self-esteem against near-zero cognitive flexibility (unyielding ideologue); Troy's low self-esteem paired with high assertion and near-zero independence (loyal aggressor, easily destabilised by authority challenges).

---

## Appendix H — Pipeline Architecture: Prototype vs Current System

*Referenced in Section 5.3.1 (Table 5.3.1b).*

Full comparison table including per-metric summary: see `Dissertation/Literature Material/Drafts/Graphs/5.3.1 Pipeline Architecture Comparison.md`.

---

## Appendix I — Prior Systems Comparison

*Referenced in Section 3.7 (Table 3.7) and Section 8.2.*

Full comparison table: see `Dissertation/Literature Material/Drafts/Graphs/3.7 Prior Systems Comparison Table.md`.

---

## Appendix J — Emotional Valence Computation Rules

*Referenced in Section 4.2.2 (Table 4.2.2).*

Full table with worked example: see `Dissertation/Literature Material/Drafts/Graphs/4.2.2 Emotional Valence Rules Table.md`.

The six rules encode the personality-behaviour mappings from Ellis (1962), Heider (1958), Guimond (2006), and Davis (1983) as conditional additive adjustments to a starting valence of `0.0`. Rules are non-exclusive — multiple may fire on the same turn. The result is clamped to [−1.0, 1.0] before being passed to the desire layer.

| NPC Condition | Tone | Formula | Grounding |
|---------------|------|---------|-----------|
| `self_esteem < 0.4` | Authority | `− tone × 0.3` | Ellis (1962) |
| `self_esteem < 0.4` | Manipulation | `− tone × 0.5` | Ellis (1962) |
| `locus_of_control < 0.5` | Authority | `− tone × 0.4` | Heider (1958) |
| `cog_flexibility > 0.6` | Diplomacy | `+ tone × 0.4` | Guimond (2006) |
| `cog_flexibility > 0.6` | Empathy | `+ tone × 0.3` | Davis (1983) |
| `cog_flexibility < 0.4` | Diplomacy | `− tone × 0.2` | Ellis (1962) |

---

## Appendix L — Troy Dual-Build Comparison Chart

*Referenced in Section 6.5 (Figure 6.5) and Section 7.1.3.*

**Figure 6.5 — Troy: Empathy Build vs Assertion Build**

> *Insert image: `troy_dual_build_chart.png`*

| Turn | Run A — Empathy Build | Run B — Assertion Build |
|------|----------------------|------------------------|
| Start | 0.50 | 0.50 |
| 1 | 0.65 (+0.15 — `ideological_filter`, positive valence) | 0.35 (−0.15 — `black_white_thinking`, negative valence) |
| 2 | **1.00 ★ SUCCEED** | 0.30 (−0.05 — `backpedal_rejected`) |
| 3 | — | **0.75 ✗ FAIL** |

Generated from `generate_dual_build_chart.py` (Graphs directory). Source data from §6.5 / Table 6.5.1.

---

## Appendix K — NPC Relation Trajectory Chart

*Referenced in Section 7.1.1 (Figure 7.1). Image file: `Dissertation/Literature Material/Drafts/Graphs/npc_trajectory_chart.png`.*

Line chart generated from `tests/Dissertation Tests/` routing logs using `generate_trajectory_chart.py` (same Graphs directory). Plots `player_relation` at each turn for Krakk (diplomatic opener, 2 turns), Moses (authority opener, 4 turns, Martyr wildcard fires twice), and Troy (authority opener, 4 turns).

**Figure 7.1 — NPC Relation Trajectories**

> *Insert image: `npc_trajectory_chart.png`*

| Turn | Krakk | Moses | Troy |
|------|-------|-------|------|
| Start | 0.50 | 0.50 | 0.50 |
| 1 | 0.60 | 0.35 | 0.35 |
| 2 | **0.75 ★** | 0.43 | 0.43 |
| 3 | — | 0.53 | 0.58 |
| 4 (Terminal) | — | **0.68 ★** | **1.00 ★** |

★ = terminal SUCCEED. Krakk reaches terminal on turn 2 via diplomatic approach; Moses and Troy both open with authority challenge but diverge across the recovery arc due to differing personality parameters.
