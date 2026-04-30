// PNEOutcomeHandler.cs
// Scene-level MonoBehaviour that starts a PNEEncounter and maps terminal
// outcome IDs to UnityEvents that can reference anything in the scene.
//
// Setup:
//   1. Add this component to any GameObject alongside PNEClient
//   2. Assign pneClient and an encounter asset
//   3. Add outcome bindings — key matches terminal_id from the server
//      e.g. "success" → ImageSwapper.Swap(1)
//           "failure" → ImageSwapper.Swap(2)
//   4. Tick Auto Start to begin on Play, or call Begin() from any script

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace PNE
{
    public class PNEOutcomeHandler : MonoBehaviour
    {
        [Header("PNE")]
        public PNEClient    pneClient;
        public PNEEncounter encounter;
        public bool         autoStart = true;

        [Header("Outcome Bindings")]
        [Tooltip("Key = terminal_id sent by the server (case-insensitive), e.g. 'success', 'failure'")]
        public List<OutcomeBinding> outcomes = new List<OutcomeBinding>();

        // ── Lifecycle ─────────────────────────────────────────────────────────

        void Start()
        {
            pneClient.OnTerminal += HandleTerminal;
            if (autoStart) Begin();
        }

        void OnDestroy() => pneClient.OnTerminal -= HandleTerminal;

        // ── Public API ────────────────────────────────────────────────────────

        public void Begin()
        {
            if (encounter != null) pneClient.StartEncounter(encounter);
            else                   pneClient.StartSession();
        }

        // ── Internal ──────────────────────────────────────────────────────────

        void HandleTerminal(TerminalMessage term)
        {
            foreach (var binding in outcomes)
            {
                if (string.Equals(binding.key, term.TerminalId, StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(binding.key, term.Result,     StringComparison.OrdinalIgnoreCase))
                {
                    binding.onOutcome?.Invoke();
                }
            }
        }
    }

    [Serializable]
    public class OutcomeBinding
    {
        [Tooltip("terminal_id or result from the server (case-insensitive)")]
        public string     key;
        public UnityEvent onOutcome;
    }
}
