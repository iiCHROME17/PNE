# THE PSYCHOLOGICAL NARRATIVE ENGINE (PNE)

## Abstract

Non-player character (NPC) dialogue in video games has historically been limited by branching conversation trees, a system that prioritises authored consistency at the cost of depth, immersion and agency. This project presents the Psychological Narrative Engine (PNE), a dialogue system that replaces scripted branching with a Belief-Desire-Intention (BDI) processing pipeline, enabling NPC responses to be emergent via models of internal cognition and social identity rather than from pre-authored text.

The system bases NPC cognition on a three-layer personality model and thought library, then outsources the text generation to a local large language model (LLM) via Ollama. The remainder of the system includes a gamified skill check, a judgement-score finite state machine and game engine agnostic REST and WebSocket API.

The central question investigated is whether psychological realism and narrative coherence in NPC interaction can be achieved simultaneously with player agency. Evaluation is conducted through structured conversation log analysis and internal state inspection across representative test scenarios. The system targets players running mid-to-high end consumer hardware, a constraint imposed by the memory requirements of local LLM models at scale.

---

![PNE Pipeline](Dissertation/Materials/PNE%20Pipeline.png)
