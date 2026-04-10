// PNEClient.cs
// MonoBehaviour that manages the full PNE API lifecycle:
//   - REST call to create a session (UnityWebRequest + coroutine)
//   - WebSocket connection for streaming turns (NativeWebSocket)
//   - C# events dispatched on the Unity main thread
//
// Requires:
//   NativeWebSocket    — Package Manager → Add from git URL:
//                        https://github.com/endel/NativeWebSocket.git#upm
//   Newtonsoft Json    — Package Manager → com.unity.nuget.newtonsoft-json
//
// Drop onto a GameObject in your scene. Wire up events in another script or
// use PNEDialogueUI.cs for a ready-made UI controller.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using NativeWebSocket;
using Newtonsoft.Json;
using PNE;

public class PNEClient : MonoBehaviour
{
    // ── Inspector fields ──────────────────────────────────────────────────────

    [Header("Server")]
    [Tooltip("Base URL of the PNE API server (no trailing slash).")]
    public string apiBaseUrl = "http://localhost:8000";

    [Header("Session")]
    public List<string> npcPaths = new List<string> { "npcs/troy.json" };
    public string scenarioPath = "scenarios/dgn.json";
    public string difficulty = "STANDARD";
    public bool useOllama = true;

    [Header("Debug")]
    [Tooltip("Save NPC JSON state to disk when the session ends. Uncheck to keep JSON files unchanged during testing.")]
    public bool updateJsons = true;

    [Header("Player Skills (0–10)")]
    public int authority    = 5;
    public int diplomacy    = 5;
    public int empathy      = 5;
    public int manipulation = 5;

    // ── Events ────────────────────────────────────────────────────────────────

    /// <summary>Fired once the session is created and opening choices are ready.</summary>
    public event Action<SessionData> OnSessionReady;

    /// <summary>Fired immediately when the player picks a choice, before Ollama starts streaming.
    /// Use this to display the player's line in a conversation log.</summary>
    public event Action<PlayerChoiceMessage> OnPlayerChoice;

    /// <summary>Fired for each Ollama streaming token. Append to your dialogue text.</summary>
    public event Action<string, string> OnToken;          // (npcName, token)

    /// <summary>Fired after each NPC's full BDI cycle completes.</summary>
    public event Action<TurnResultMessage> OnTurnResult;

    /// <summary>Fired when the server sends fresh choices for the next player turn.</summary>
    public event Action<ChoicesMessage> OnChoicesUpdated;

    /// <summary>Fired when the conversation reaches a terminal outcome.</summary>
    public event Action<TerminalMessage> OnTerminal;

    /// <summary>Fired on any server-side or connection error.</summary>
    public event Action<string> OnError;

    // ── State ─────────────────────────────────────────────────────────────────

    public string SessionId { get; private set; }
    public bool   IsConnected => _ws != null && _ws.State == WebSocketState.Open;
    public bool   IsComplete  { get; private set; }

    private WebSocket _ws;

    // ── Public API ────────────────────────────────────────────────────────────

    /// <summary>
    /// Create a session on the server and open the WebSocket.
    /// Fires OnSessionReady when complete.
    /// </summary>
    public void StartSession()
    {
        StartCoroutine(CreateSessionCoroutine());
    }

    /// <summary>
    /// Send a player choice over the WebSocket (1-based index from ChoiceItem.Index).
    /// </summary>
    public void SendChoice(int choiceIndex)
    {
        if (!IsConnected)
        {
            Debug.LogError("[PNEClient] WebSocket not connected. Call StartSession first.");
            return;
        }
        if (IsComplete)
        {
            Debug.LogWarning("[PNEClient] Conversation is already complete.");
            return;
        }

        var payload = new SendChoiceRequest { ChoiceIndex = choiceIndex };
        string json = JsonConvert.SerializeObject(payload);
        _ws.SendText(json);
    }

    /// <summary>
    /// Gracefully close the WebSocket and DELETE the session on the server.
    /// </summary>
    public void EndSession()
    {
        if (!string.IsNullOrEmpty(SessionId))
        {
            if (updateJsons)
                StartCoroutine(SaveSessionCoroutine());
            StartCoroutine(DeleteSessionCoroutine());
        }
        _ws?.Close();
        _ws = null;
        SessionId = null;
        IsComplete = false;
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    private void Update()
    {
        // NativeWebSocket requires this to dispatch callbacks on the main thread.
#if !UNITY_WEBGL || UNITY_EDITOR
        _ws?.DispatchMessageQueue();
#endif
    }

    private void OnDestroy()
    {
        EndSession();
    }

    // ── Session creation (HTTP) ───────────────────────────────────────────────

    private IEnumerator CreateSessionCoroutine()
    {
        var request = new CreateSessionRequest
        {
            NpcPaths      = npcPaths,
            ScenarioPath  = scenarioPath,
            Difficulty    = difficulty,
            UseOllama     = useOllama,
            PlayerSkills  = new PlayerSkills
            {
                Authority    = authority,
                Diplomacy    = diplomacy,
                Empathy      = empathy,
                Manipulation = manipulation,
            },
        };

        string json  = JsonConvert.SerializeObject(request);
        byte[] body  = Encoding.UTF8.GetBytes(json);

        using var uwr = new UnityWebRequest(apiBaseUrl + "/sessions", "POST");
        uwr.uploadHandler   = new UploadHandlerRaw(body);
        uwr.downloadHandler = new DownloadHandlerBuffer();
        uwr.SetRequestHeader("Content-Type", "application/json");

        yield return uwr.SendWebRequest();

        if (uwr.result != UnityWebRequest.Result.Success)
        {
            OnError?.Invoke($"Session creation failed: {uwr.error} (HTTP {uwr.responseCode})");
            yield break;
        }

        SessionData data;
        try
        {
            data = JsonConvert.DeserializeObject<SessionData>(uwr.downloadHandler.text);
        }
        catch (Exception e)
        {
            OnError?.Invoke($"Failed to parse session response: {e.Message}");
            yield break;
        }

        SessionId = data.SessionId;
        OnSessionReady?.Invoke(data);

        yield return ConnectWebSocketCoroutine();
    }

    // ── WebSocket ─────────────────────────────────────────────────────────────

    private IEnumerator ConnectWebSocketCoroutine()
    {
        string wsUrl = apiBaseUrl
            .Replace("https://", "wss://")
            .Replace("http://",  "ws://");
        wsUrl += $"/sessions/{SessionId}/play";

        _ws = new WebSocket(wsUrl);

        _ws.OnOpen    += ()           => Debug.Log("[PNEClient] WebSocket connected.");
        _ws.OnClose   += (code)       => Debug.Log($"[PNEClient] WebSocket closed ({code}).");
        _ws.OnError   += (err)        => OnError?.Invoke($"WebSocket error: {err}");
        _ws.OnMessage += HandleWsMessage;

        yield return _ws.Connect();
    }

    private void HandleWsMessage(byte[] bytes)
    {
        string raw = Encoding.UTF8.GetString(bytes);

        WsMessage base_;
        try { base_ = JsonConvert.DeserializeObject<WsMessage>(raw); }
        catch { OnError?.Invoke("Failed to parse WebSocket message."); return; }

        switch (base_.Type)
        {
            case "player_choice":
                var pc = JsonConvert.DeserializeObject<PlayerChoiceMessage>(raw);
                OnPlayerChoice?.Invoke(pc);
                break;

            case "token":
                var tok = JsonConvert.DeserializeObject<TokenMessage>(raw);
                OnToken?.Invoke(tok.Npc, tok.Token);
                break;

            case "turn_result":
                var tr = JsonConvert.DeserializeObject<TurnResultMessage>(raw);
                OnTurnResult?.Invoke(tr);
                break;

            case "choices":
                var ch = JsonConvert.DeserializeObject<ChoicesMessage>(raw);
                OnChoicesUpdated?.Invoke(ch);
                break;

            case "terminal":
                var term = JsonConvert.DeserializeObject<TerminalMessage>(raw);
                IsComplete = true;
                OnTerminal?.Invoke(term);
                break;

            case "error":
                var err = JsonConvert.DeserializeObject<ErrorMessage>(raw);
                OnError?.Invoke(err.Message);
                break;

            default:
                Debug.LogWarning($"[PNEClient] Unknown message type: {base_.Type}");
                break;
        }
    }

    // ── Session cleanup (HTTP) ────────────────────────────────────────────────

    private IEnumerator SaveSessionCoroutine()
    {
        using var uwr = new UnityWebRequest($"{apiBaseUrl}/sessions/{SessionId}/save", "POST");
        uwr.downloadHandler = new DownloadHandlerBuffer();
        yield return uwr.SendWebRequest();
        // Fire and forget — ignore result
    }

    private IEnumerator DeleteSessionCoroutine()
    {
        using var uwr = UnityWebRequest.Delete($"{apiBaseUrl}/sessions/{SessionId}");
        yield return uwr.SendWebRequest();
        // Fire and forget — ignore result
    }
}
