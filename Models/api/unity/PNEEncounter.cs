// PNEEncounter.cs
// Pure data asset — defines which NPC and scenario an encounter uses.
// Create via: Assets → Create → PNE → Encounter
//
// Outcome wiring (what happens when the conversation ends) lives in
// PNEOutcomeHandler on a scene GameObject, so it can reference scene objects.

using System.Collections.Generic;
using UnityEngine;

namespace PNE
{
    [CreateAssetMenu(fileName = "NewEncounter", menuName = "PNE/Encounter")]
    public class PNEEncounter : ScriptableObject
    {
        [Header("Identity")]
        public string encounterName = "New Encounter";

        [Header("Participants")]
        [Tooltip("Paths relative to the PNE Models directory, e.g. npcs/troy.json")]
        public List<string> npcPaths     = new List<string> { "npcs/troy.json" };
        public string       scenarioPath  = "scenarios/dgn.json";
        public string       difficulty    = "STANDARD";
    }
}
