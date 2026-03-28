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
