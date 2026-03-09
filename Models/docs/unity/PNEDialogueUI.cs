// PNEDialogueUI.cs
// Dialogue UI controller with typewriter animation and two-phase interaction.
//
// ── Interaction flow ─────────────────────────────────────────────────────────
//   Choice clicked     → "You: ..." typewriters immediately (non-skippable)
//                         while Ollama processes in the background
//   NPC text arrives   → typewriters after player line finishes (skippable)
//   Text complete      → press E / Space / interactButton → hide text, show choices
//   Choice visible     → click a choice button            → send choice, restart cycle
//
// ── Scene setup ──────────────────────────────────────────────────────────────
//   • GameObject with PNEClient + PNEDialogueUI
//   • dialoguePanel  : parent GameObject for the text box (shown/hidden as a unit)
//   • dialogueText   : TMP_Text inside dialoguePanel
//   • choicesContainer : parent Transform for choice buttons
//       → Set its Layout Group to HorizontalLayoutGroup (not Vertical)
//       → Recommended: add ContentSizeFitter + child-force-expand width = false
//   • choiceButtonPrefab : Button prefab with a TMP_Text child named "Label"
//   • interactButton : optional on-screen "Press E / Skip" button
//
// Requires: TextMeshPro, Input System package

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.InputSystem;
using TMPro;
using PNE;

public class PNEDialogueUI : MonoBehaviour
{
    // ── Inspector wiring ──────────────────────────────────────────────────────

    [Header("Components")]
    [SerializeField] private PNEClient client;

    [Header("UI Elements")]
    [SerializeField] private GameObject  dialoguePanel;      // shown during text, hidden during choices
    [SerializeField] private TMP_Text    dialogueText;
    [SerializeField] private TMP_Text    npcNameLabel;        // optional
    [SerializeField] private TMP_Text    judgementLabel;      // optional — "Judgement: 62/100"
    [SerializeField] private TMP_Text    outcomeLabel;        // shown on terminal
    [SerializeField] private Transform   choicesContainer;    // HorizontalLayoutGroup recommended
    [SerializeField] private Button      choiceButtonPrefab;  // prefab with TMP_Text child "Label"
    [SerializeField] private Button      interactButton;      // on-screen skip/continue hint button

    [Header("Typewriter Settings")]
    [SerializeField] private float  charsPerSecond        = 40f;   // NPC text speed
    [SerializeField] private float  playerCharsPerSecond  = 60f;   // player line speed (non-skippable)
    [SerializeField] private string skipHint              = "[ click to skip ]";
    [SerializeField] private string continueHint          = "[ press E to continue ]";

    // ── Internal state ────────────────────────────────────────────────────────

    // PlayerTyping = non-skippable player line playing while Ollama works in background
    private enum Phase { Idle, PlayerTyping, Typing, TextComplete, Choices }

    private Phase            _phase            = Phase.Idle;
    private Coroutine        _typingCoroutine;
    private string           _npcBuffer        = "";    // accumulates streaming tokens
    private string           _pendingNpcText;           // buffered if NPC arrives during PlayerTyping
    private List<ChoiceItem> _pendingChoices;           // stored until player advances past NPC text
    private readonly List<Button> _choiceButtons = new();

    // ── Unity lifecycle ───────────────────────────────────────────────────────

    private void Start()
    {
        if (client == null) client = GetComponent<PNEClient>();

        client.OnSessionReady   += HandleSessionReady;
        client.OnPlayerChoice   += HandlePlayerChoice;
        client.OnToken          += HandleToken;
        client.OnTurnResult     += HandleTurnResult;
        client.OnChoicesUpdated += HandleChoicesUpdated;
        client.OnTerminal       += HandleTerminal;
        client.OnError          += HandleError;

        SetDialoguePanelVisible(false);
        SetChoicesVisible(false);
        if (outcomeLabel)    outcomeLabel.text = "";
        if (interactButton)  interactButton.onClick.AddListener(OnInteractPressed);

        client.StartSession();
    }

    private void OnDestroy()
    {
        if (client == null) return;
        client.OnSessionReady   -= HandleSessionReady;
        client.OnPlayerChoice   -= HandlePlayerChoice;
        client.OnToken          -= HandleToken;
        client.OnTurnResult     -= HandleTurnResult;
        client.OnChoicesUpdated -= HandleChoicesUpdated;
        client.OnTerminal       -= HandleTerminal;
        client.OnError          -= HandleError;
    }

    private void Update()
    {
        var kb = Keyboard.current;
        if (kb != null && (kb.eKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame))
            OnInteractPressed();
    }

    // ── PNEClient event handlers ──────────────────────────────────────────────

    private void HandleSessionReady(SessionData data)
    {
        if (npcNameLabel != null && data.Npcs?.Count > 0)
            npcNameLabel.text = data.Npcs[0].Name;

        _pendingChoices = data.Choices;
        BeginTyping(data.Scenario.Opening);
    }

    private void HandlePlayerChoice(PlayerChoiceMessage msg)
    {
        // Fires immediately when SendChoice is called — before Ollama starts.
        // Typewrite the player's line to fill the processing gap visually.
        _pendingNpcText = null;
        BeginPlayerTyping($"<b>You:</b> {msg.Text}");
    }

    private void HandleToken(string npcName, string token)
    {
        // Buffer streaming tokens — displayed as a block after turn result arrives
        _npcBuffer += token;
    }

    private void HandleTurnResult(TurnResultMessage msg)
    {
        if (judgementLabel != null)
            judgementLabel.text = $"Judgement: {msg.Judgement}/100";

        Debug.Log($"[PNE] {msg.Npc} | Belief: {msg.Thought?.SubjectiveBelief} | " +
                  $"Intention: {msg.Intention?.IntentionType}");

        string npcText = $"<b>{msg.Npc}:</b> {_npcBuffer.Trim()}";
        _npcBuffer = "";

        if (_phase == Phase.PlayerTyping)
            _pendingNpcText = npcText;   // player line still playing — queue NPC text
        else
            BeginTyping(npcText);
    }

    private void HandleChoicesUpdated(ChoicesMessage msg)
    {
        // Store — shown after player presses interact past the NPC text
        _pendingChoices = msg.Choices;
    }

    private void HandleTerminal(TerminalMessage msg)
    {
        _pendingChoices = null;
        ClearChoices();
        SetChoicesVisible(false);

        BeginTyping($"<b>{msg.Npc}:</b> {msg.FinalDialogue}", onComplete: () =>
        {
            if (outcomeLabel != null)
                outcomeLabel.text = $"[{msg.TerminalId.ToUpper()}] {msg.Result}";
        });

        Debug.Log($"[PNE] Terminal: {msg.TerminalId} — {msg.Result}");
    }

    private void HandleError(string message)
    {
        Debug.LogError($"[PNEClient] {message}");
        if (dialogueText != null)
            dialogueText.text += $"\n<color=red>[Error: {message}]</color>";
    }

    // ── Interaction ───────────────────────────────────────────────────────────

    private void OnInteractPressed()
    {
        switch (_phase)
        {
            case Phase.Typing:
                SkipTyping();
                break;

            case Phase.TextComplete:
                if (_pendingChoices != null && _pendingChoices.Count > 0)
                {
                    SetDialoguePanelVisible(false);
                    SetInteractHint(false);
                    PopulateChoices(_pendingChoices);
                    _pendingChoices = null;
                    SetChoicesVisible(true);
                    _phase = Phase.Choices;
                }
                // PlayerTyping and Idle: not skippable / nothing to do
                break;
        }
    }

    // ── Typewriter — NPC / opening text (skippable) ───────────────────────────

    private void BeginTyping(string text, System.Action onComplete = null)
    {
        if (_typingCoroutine != null)
            StopCoroutine(_typingCoroutine);

        SetChoicesVisible(false);
        SetDialoguePanelVisible(true);
        Canvas.ForceUpdateCanvases();   // ensure panel renders immediately after SetActive

        dialogueText.text = text;
        dialogueText.ForceMeshUpdate();
        dialogueText.maxVisibleCharacters = 0;

        _phase = Phase.Typing;
        SetInteractHint(true, skipHint);
        _typingCoroutine = StartCoroutine(TypewriterRoutine(charsPerSecond, onComplete));
    }

    private void SkipTyping()
    {
        if (_typingCoroutine != null)
        {
            StopCoroutine(_typingCoroutine);
            _typingCoroutine = null;
        }
        dialogueText.maxVisibleCharacters = int.MaxValue;
        FinishTyping(onComplete: null);
    }

    private void FinishTyping(System.Action onComplete)
    {
        _typingCoroutine = null;
        _phase = Phase.TextComplete;
        onComplete?.Invoke();
        SetInteractHint(true, continueHint);
    }

    // ── Typewriter — player line (non-skippable, fills Ollama wait) ───────────

    private void BeginPlayerTyping(string text)
    {
        if (_typingCoroutine != null)
            StopCoroutine(_typingCoroutine);

        SetChoicesVisible(false);
        SetDialoguePanelVisible(true);
        Canvas.ForceUpdateCanvases();   // ensure panel renders immediately after SetActive

        dialogueText.text = text;
        dialogueText.ForceMeshUpdate();
        dialogueText.maxVisibleCharacters = 0;

        _phase = Phase.PlayerTyping;
        SetInteractHint(false);         // no skip hint — player line is non-skippable
        _typingCoroutine = StartCoroutine(TypewriterRoutine(playerCharsPerSecond, onComplete: null,
                                                            onFinish: FinishPlayerTyping));
    }

    private void FinishPlayerTyping()
    {
        _typingCoroutine = null;
        if (_pendingNpcText != null)
        {
            // NPC response already arrived while player line was animating — start it now
            string text = _pendingNpcText;
            _pendingNpcText = null;
            BeginTyping(text);
        }
        else
        {
            _phase = Phase.Idle;  // still waiting for Ollama
        }
    }

    // ── Shared coroutine ──────────────────────────────────────────────────────

    private IEnumerator TypewriterRoutine(float speed, System.Action onComplete,
                                          System.Action onFinish = null)
    {
        int total = dialogueText.textInfo.characterCount;
        float delay = 1f / Mathf.Max(1f, speed);

        for (int i = 0; i <= total; i++)
        {
            dialogueText.maxVisibleCharacters = i;
            yield return new WaitForSeconds(delay);
        }

        if (onFinish != null)
            onFinish();
        else
            FinishTyping(onComplete);
    }

    // ── Choices ───────────────────────────────────────────────────────────────

    private void PopulateChoices(List<ChoiceItem> choices)
    {
        ClearChoices();
        if (choices == null || choiceButtonPrefab == null || choicesContainer == null) return;

        foreach (var choice in choices)
        {
            var btn = Instantiate(choiceButtonPrefab, choicesContainer);
            _choiceButtons.Add(btn);

            var label = btn.GetComponentInChildren<TMP_Text>();
            if (label != null)
                label.text = $"{choice.Text}  <size=70%>({choice.SuccessPct}%)</size>";

            int idx = choice.Index;
            btn.onClick.AddListener(() => OnChoiceClicked(idx));
        }
    }

    private void OnChoiceClicked(int choiceIndex)
    {
        SetChoicesVisible(false);
        ClearChoices();
        _phase = Phase.Idle;
        client.SendChoice(choiceIndex);
    }

    private void ClearChoices()
    {
        foreach (var btn in _choiceButtons)
            if (btn != null) Destroy(btn.gameObject);
        _choiceButtons.Clear();
    }

    // ── UI visibility helpers ─────────────────────────────────────────────────

    private void SetDialoguePanelVisible(bool visible)
    {
        if (dialoguePanel != null)
            dialoguePanel.SetActive(visible);
        else if (dialogueText != null)
            dialogueText.gameObject.SetActive(visible);
    }

    private void SetChoicesVisible(bool visible)
    {
        if (choicesContainer != null)
            choicesContainer.gameObject.SetActive(visible);
    }

    private void SetInteractHint(bool visible, string label = null)
    {
        if (interactButton == null) return;
        interactButton.gameObject.SetActive(visible);
        if (label != null)
        {
            var tmp = interactButton.GetComponentInChildren<TMP_Text>();
            if (tmp != null) tmp.text = label;
        }
    }
}
