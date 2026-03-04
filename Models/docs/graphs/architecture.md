# Psychological Narrative Engine — Architecture Reference

> Render with the VS Code Mermaid Preview extension or paste into [mermaid.live](https://mermaid.live).

---

## 1. Per-Turn Data Flow

How a single player choice flows through the system to produce an NPC response and route to the next node.

```mermaid
flowchart TD
    A([Player selects choice]) --> B[NarrativeEngine.apply_choice]

    subgraph FILTER ["Choice Gating (engine.py)"]
        B --> C[ChoiceFilter\nSkill reqs · relation gates · prerequisites]
        C --> D[DialogueMomentumFilter\nOptional coherence check]
    end

    subgraph DICE ["Dice System (skill_check.py)"]
        D --> E[SkillCheckSystem.roll_dice\nWeighted d6 player vs d6 NPC]
        E --> E1{player_die ≥ npc_die?}
        E1 -- YES --> E2[check_success = True\njudgement += delta_success × risk]
        E1 -- NO  --> E3[check_success = False\njudgement += delta_fail × risk]
    end

    subgraph BDI ["BDI Pipeline (processor.py)"]
        E2 & E3 --> F[CognitiveInterpreter.interpret\nOllama: qwen2.5:3b\n→ ThoughtReaction\n  · subjective_belief\n  · emotional_valence]
        F --> G[DesireFormation.form_desire\nPattern match on belief text + NPC stats\n→ DesireState\n  · immediate_desire\n  · desire_type\n  · intensity]
        G --> H[SocialisationFilter.filter\nScore INTENTION_REGISTRY templates\n→ BehaviouralIntention\n  · intention_type\n  · confrontation_level\n  · wildcard_triggered]
        H --> I[Select InteractionOutcome\nSuccess path or Failure path]
        I --> J[Apply effects to NPCModel\nstance_delta · relation_delta\nintention_shift]
    end

    subgraph RESPONSE ["Response Generation (ollama_integration.py)"]
        J --> K[OllamaResponseGenerator\n.generate_response_with_direction\nOllama: llama3\nPrompt sections:\n  IDENTITY · WORLD CONTEXT\n  BDI STATE · ACTING NOTES\n  RESPONSE RANGE · HISTORY\n  SCENE DIRECTION · DICE CONTEXT]
        K --> L([NPC dialogue line ≤ 40 words])
    end

    subgraph FSM ["FSM Routing (transition_resolver.py)"]
        L --> M[TransitionResolver.resolve\nEvaluate: judgement · turn_count\n· intention_shift]
        M --> N{Terminal node?}
        N -- YES --> O[generate_terminal\nFinal NPC line\nOutcome: SUCCEED / FAIL / NEGOTIATE]
        N -- NO  --> P([Next scenario node])
    end
```

---

## 2. Entity Relationship

Data structures and how they relate to each other.

```mermaid
erDiagram
    NarrativeEngine ||--o{ ConversationSession : manages
    NarrativeEngine ||--o{ NPCModel : "loads (npcs/)"
    NarrativeEngine ||--o{ Scenario : "loads (scenarios/)"

    ConversationSession ||--o{ NPCConversationState : contains
    ConversationSession ||--|| Scenario : uses

    NPCConversationState ||--|| NPCModel : "represents"
    NPCConversationState ||--|| DialogueProcessor : "owns BDI pipeline"
    NPCConversationState {
        str  npc_id
        str  current_node
        int  judgement
        bool is_complete
        bool recovery_mode
        set  failed_choices
    }

    DialogueProcessor ||--|| ConversationModel : tracks
    DialogueProcessor ||--|| NPCIntent : "has baseline purpose"
    DialogueProcessor ||--|| OutcomeIndex : "resolves outcomes"
    DialogueProcessor ||--|| OllamaResponseGenerator : "generates dialogue"
    DialogueProcessor ||--|| CognitiveInterpreter : interprets

    ConversationModel {
        str  conversation_id
        str  stage
        int  turn_count
        list history
    }

    NPCModel ||--|| CognitiveLayer : "personality core"
    NPCModel ||--|| SocialLayer : "social behaviour"
    NPCModel ||--|| WorldLayer : "world knowledge"

    CognitiveLayer {
        float self_esteem
        float locus_of_control
        float cog_flexibility
    }
    SocialLayer {
        float assertion
        float conf_indep
        float empathy
        str   faction
        str   wildcard
    }
    WorldLayer {
        str   personal_history
        float player_relation
        list  known_events
        list  known_figures
    }

    Scenario ||--o{ ScenarioNode : "node graph"
    ScenarioNode ||--o{ Choice : "player options"
    ScenarioNode ||--o{ Transition : "routing rules"
    ScenarioNode {
        str  id
        str  npc_mood
        str  npc_dialogue_prompt
        bool terminal
        str  terminal_id
        str  default_transition
    }

    Choice ||--o{ InteractionOutcome : "success path"
    Choice ||--|{ InteractionOutcome : "failure path"
    Choice ||--o{ RecoveryChoice : "retry options"
    Choice {
        str   choice_id
        str   text
        str   language_art
        float authority_tone
        float empathy_tone
        float diplomacy_tone
        float manipulation_tone
        int   judgement_delta_success
        int   judgement_delta_fail
    }

    InteractionOutcome {
        str   outcome_id
        dict  stance_delta
        float relation_delta
        str   intention_shift
        str   min_response
        str   max_response
        bool  scripted
    }

    Transition {
        str condition
        str target
    }

    DiceCheckResult {
        bool        success
        int         player_die
        int         npc_die
        PlayerSkill skill_used
        float       player_bias
        float       npc_bias
    }

    ThoughtReaction {
        str   subjective_belief
        str   internal_thought
        float emotional_valence
        dict  cognitive_state
    }

    DesireState {
        str   immediate_desire
        str   desire_type
        float intensity
    }

    BehaviouralIntention {
        str   intention_type
        float confrontation_level
        str   emotional_expression
        bool  wildcard_triggered
    }
```

---

## 3. Module Map

Package layout with each module's responsibility.

```mermaid
graph LR
    subgraph PNE ["pne/ — Core BDI Library"]
        direction TB
        E[enums.py\nLanguageArt · PlayerSkill\nDifficulty · TerminalOutcomeType]
        I[intent.py\nNPCIntent\nbaseline_belief · long_term_desire\nimmediate_intention · stakes]
        PI[player_input.py\nPlayerDialogueInput\nPlayerSkillSet]
        CV[conversation.py\nConversationModel\nturn tracking · history log]
        CG[cognitive.py\nCognitiveInterpreter\nThoughtReaction\nOllama call 1]
        DS[desire.py\nDesireFormation\nDesireState]
        SO[social.py\nSocialisationFilter\nBehaviouralIntention]
        IR[intention_registry.py\n19 canonical templates\nclosed intention vocabulary]
        SK[skill_check.py\nSkillCheckSystem\nweighted d6 · probability]
        OC[outcomes.py\nInteractionOutcome\nTerminalOutcome · OutcomeIndex]
        OL[ollama_integration.py\nOllamaResponseGenerator\nOllama call 2]
        PR[processor.py\nDialogueProcessor\nBDI orchestrator]
    end

    subgraph NE ["narrative_engine/ — Session Orchestrator"]
        direction TB
        ENG[engine.py\nNarrativeEngine\nsession controller · difficulty]
        SES[session.py\nConversationSession\nNPCConversationState]
        SL[scenario_loader.py\nScenarioLoader\nJSON → Scenario dict]
        TR[transition_resolver.py\nTransitionResolver\nFSM routing via judgement]
        CF[choice_filter.py\nChoiceFilter\nhard gates · recovery mode]
        DC[dialogue_coherence.py\nDialogueMomentumFilter\noptional coherence check]
    end

    subgraph DATA ["Data Files"]
        NPC[npcs/*.json\nNPC definitions\ncognitive · social · world]
        SCN[scenarios/*.json\nScenario graphs\nnodes · choices · transitions]
        WLD[data/world.json\nWorld context\nfactions · events · locations]
    end

    CLI([cli.py\nCLI entry point\n--difficulty flag]) --> ENG
    NPC --> ENG
    SCN --> SL --> ENG
    WLD --> NPC

    ENG --> SES
    ENG --> CF
    ENG --> DC
    ENG --> SK
    ENG --> TR
    ENG --> PR

    PR --> CG
    PR --> DS
    PR --> SO
    PR --> OC
    PR --> OL

    SO --> IR
    CG --> CV
```

---

## 4. Key Attribute Reference

| Layer | Fields | Scale |
|-------|--------|-------|
| Cognitive | `self_esteem`, `locus_of_control`, `cog_flexibility` | 0.0 – 1.0 |
| Social | `assertion`, `conf_indep`, `empathy` | 0.0 – 1.0 |
| World | `player_relation` | 0.0 (distrust) – 1.0 (trust) |
| Dice bias | `(skill / 10) + relation_bias + difficulty_adj` | 0.0 – 1.0 |
| FSM | `judgement` | 0 (fail) – 100 (succeed) |
| Difficulty adj | SIMPLE `+0.15` · STANDARD `0.00` · STRICT `−0.15` | additive bias |
| Emotional valence | negative ← −1.0 … +1.0 → positive | per-turn reaction |
| Confrontation | passive ← 0.0 … 1.0 → aggressive | `assertion × 0.7 + conf_indep × 0.3` |

---

## 5. Dice Probability Formula

```
player_bias  = clamp(player_skill / 10  +  relation_bias  +  difficulty_adj,  0, 1)
npc_bias     = calc_threshold(npc, skill)   ← derived from NPC attributes

P(face k) ∝ exp(bias × k)   for k = 1 … 6   (weighted d6)

success      = player_die >= npc_die
```

`relation_bias` = `(player_relation − 0.5) × 2 × (RELATION_CAP / 100)` where `RELATION_CAP = 10`
