// PNETypes.cs
// Data classes that map to every JSON shape the PNE API sends or receives.
// Drop this file into any folder inside your Unity Assets/ directory.
//
// Requires: com.unity.nuget.newtonsoft-json  (Package Manager)

using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace PNE
{
    // ── Outgoing (Unity → Server) ─────────────────────────────────────────────

    [Serializable]
    public class CreateSessionRequest
    {
        [JsonProperty("npc_paths")]      public List<string> NpcPaths      { get; set; }
        [JsonProperty("scenario_path")]  public string ScenarioPath        { get; set; }
        [JsonProperty("difficulty")]     public string Difficulty           { get; set; } = "STANDARD";
        [JsonProperty("player_skills")]  public PlayerSkills PlayerSkills   { get; set; } = new PlayerSkills();
        [JsonProperty("use_ollama")]     public bool UseOllama              { get; set; } = true;
    }

    [Serializable]
    public class PlayerSkills
    {
        [JsonProperty("authority")]    public int Authority    { get; set; } = 5;
        [JsonProperty("diplomacy")]    public int Diplomacy    { get; set; } = 5;
        [JsonProperty("empathy")]      public int Empathy      { get; set; } = 5;
        [JsonProperty("manipulation")] public int Manipulation { get; set; } = 5;
    }

    [Serializable]
    public class SendChoiceRequest
    {
        [JsonProperty("choice_index")] public int ChoiceIndex { get; set; }
    }

    // ── REST responses ────────────────────────────────────────────────────────

    [Serializable]
    public class SessionData
    {
        [JsonProperty("session_id")] public string SessionId { get; set; }
        [JsonProperty("scenario")]   public ScenarioInfo Scenario { get; set; }
        [JsonProperty("npcs")]       public List<NpcInfo> Npcs { get; set; }
        [JsonProperty("node_id")]    public string NodeId { get; set; }
        [JsonProperty("choices")]    public List<ChoiceItem> Choices { get; set; }
    }

    [Serializable]
    public class ScenarioInfo
    {
        [JsonProperty("id")]      public string Id      { get; set; }
        [JsonProperty("title")]   public string Title   { get; set; }
        [JsonProperty("opening")] public string Opening { get; set; }
    }

    [Serializable]
    public class NpcInfo
    {
        [JsonProperty("npc_id")] public string NpcId { get; set; }
        [JsonProperty("name")]   public string Name  { get; set; }
    }

    [Serializable]
    public class ChoiceItem
    {
        [JsonProperty("index")]        public int    Index       { get; set; }
        [JsonProperty("choice_id")]    public string ChoiceId    { get; set; }
        [JsonProperty("text")]         public string Text        { get; set; }
        [JsonProperty("language_art")] public string LanguageArt { get; set; }
        [JsonProperty("success_pct")]  public int    SuccessPct  { get; set; }
    }

    [Serializable]
    public class ChoicesData
    {
        [JsonProperty("node_id")]    public string NodeId    { get; set; }
        [JsonProperty("in_recovery")] public bool  InRecovery { get; set; }
        [JsonProperty("choices")]    public List<ChoiceItem> Choices { get; set; }
    }

    [Serializable]
    public class SessionState
    {
        [JsonProperty("session_id")]        public string SessionId       { get; set; }
        [JsonProperty("node_id")]           public string NodeId          { get; set; }
        [JsonProperty("is_complete")]       public bool   IsComplete      { get; set; }
        [JsonProperty("player_choice_log")] public List<object> ChoiceLog { get; set; }
        [JsonProperty("npcs")]              public Dictionary<string, NpcState> Npcs { get; set; }
    }

    [Serializable]
    public class NpcState
    {
        [JsonProperty("name")]             public string Name           { get; set; }
        [JsonProperty("judgement")]        public int    Judgement      { get; set; }
        [JsonProperty("is_complete")]      public bool   IsComplete     { get; set; }
        [JsonProperty("turn_count")]       public int    TurnCount      { get; set; }
        [JsonProperty("terminal_outcome")] public TerminalOutcome TerminalOutcome { get; set; }
    }

    // ── WebSocket messages (Server → Unity) ───────────────────────────────────

    /// <summary>Base class — deserialise this first to read the "type" discriminator.</summary>
    [Serializable]
    public class WsMessage
    {
        [JsonProperty("type")] public string Type { get; set; }
    }

    /// <summary>type = "token"  — one chunk of Ollama streaming output.</summary>
    [Serializable]
    public class TokenMessage : WsMessage
    {
        [JsonProperty("npc")]   public string Npc   { get; set; }
        [JsonProperty("token")] public string Token { get; set; }
    }

    /// <summary>type = "player_choice"  — echoes the player's selection before Ollama streams.</summary>
    [Serializable]
    public class PlayerChoiceMessage : WsMessage
    {
        [JsonProperty("choice_id")]    public string ChoiceId    { get; set; }
        [JsonProperty("text")]         public string Text        { get; set; }
        [JsonProperty("language_art")] public string LanguageArt { get; set; }
    }

    /// <summary>type = "turn_result"  — full BDI result after a turn completes.</summary>
    [Serializable]
    public class TurnResultMessage : WsMessage
    {
        [JsonProperty("npc")]              public string      Npc             { get; set; }
        [JsonProperty("npc_id")]           public string      NpcId           { get; set; }
        [JsonProperty("thought")]          public ThoughtData Thought         { get; set; }
        [JsonProperty("desire")]           public DesireData  Desire          { get; set; }
        [JsonProperty("intention")]        public IntentionData Intention     { get; set; }
        [JsonProperty("outcome")]          public Dictionary<string, object> Outcome { get; set; }
        [JsonProperty("judgement")]        public int         Judgement       { get; set; }
        [JsonProperty("npc_response")]     public string      NpcResponse     { get; set; }
        [JsonProperty("dice")]             public DiceData    Dice            { get; set; }
        [JsonProperty("entered_recovery")] public bool        EnteredRecovery { get; set; }
    }

    /// <summary>Dice roll data for a single turn (null when no skill check occurred).</summary>
    [Serializable]
    public class DiceData
    {
        [JsonProperty("player_die")]       public int?   PlayerDie       { get; set; }
        [JsonProperty("npc_die")]          public int?   NpcDie          { get; set; }
        [JsonProperty("success")]          public bool   Success         { get; set; }
        [JsonProperty("skill")]            public string Skill           { get; set; }
        [JsonProperty("success_pct")]      public int    SuccessPct      { get; set; }
        [JsonProperty("risk_multiplier")]  public float  RiskMultiplier  { get; set; }
        [JsonProperty("judgement_delta")]  public int    JudgementDelta  { get; set; }
    }

    /// <summary>type = "choices"  — available choices for the next turn.</summary>
    [Serializable]
    public class ChoicesMessage : WsMessage
    {
        [JsonProperty("node_id")]    public string NodeId    { get; set; }
        [JsonProperty("in_recovery")] public bool  InRecovery { get; set; }
        [JsonProperty("choices")]    public List<ChoiceItem> Choices { get; set; }
    }

    /// <summary>type = "terminal"  — conversation has reached a terminal outcome.</summary>
    [Serializable]
    public class TerminalMessage : WsMessage
    {
        [JsonProperty("npc")]            public string Npc           { get; set; }
        [JsonProperty("npc_id")]         public string NpcId         { get; set; }
        [JsonProperty("terminal_id")]    public string TerminalId    { get; set; }
        [JsonProperty("result")]         public string Result        { get; set; }
        [JsonProperty("final_dialogue")] public string FinalDialogue { get; set; }
    }

    /// <summary>type = "error"  — something went wrong server-side.</summary>
    [Serializable]
    public class ErrorMessage : WsMessage
    {
        [JsonProperty("message")] public string Message { get; set; }
    }

    /// <summary>Reused inside TerminalMessage and NpcState.</summary>
    [Serializable]
    public class TerminalOutcome
    {
        [JsonProperty("terminal_id")]    public string TerminalId    { get; set; }
        [JsonProperty("result")]         public string Result        { get; set; }
        [JsonProperty("final_dialogue")] public string FinalDialogue { get; set; }
    }

    // ── BDI sub-types ─────────────────────────────────────────────────────────

    [Serializable]
    public class ThoughtData
    {
        [JsonProperty("internal_thought")]  public string InternalThought  { get; set; }
        [JsonProperty("subjective_belief")] public string SubjectiveBelief { get; set; }
        [JsonProperty("emotional_valence")] public float  EmotionalValence { get; set; }
    }

    [Serializable]
    public class DesireData
    {
        [JsonProperty("immediate_desire")] public string ImmediateDesire { get; set; }
        [JsonProperty("desire_type")]      public string DesireType      { get; set; }
        [JsonProperty("intensity")]        public float  Intensity       { get; set; }
    }

    [Serializable]
    public class IntentionData
    {
        [JsonProperty("intention_type")]     public string IntentionType    { get; set; }
        [JsonProperty("confrontation_level")] public float ConfrontationLevel { get; set; }
        [JsonProperty("emotional_expression")] public string EmotionalExpression { get; set; }
    }
}
