// ImageSwapper.cs
// Swaps a UI Image or SpriteRenderer from a sprite array by index.
// Accessible from UnityEvents, PNEEncounter outcome bindings, or code.
//
// Inspector setup:
//   1. Assign Target Image (UI) or Target Renderer (world sprite)
//   2. Populate the Sprites array
//
// Code / UnityEvent:
//   imageSwapper.Swap(0);   // first sprite
//   imageSwapper.Swap(1);   // second sprite

using UnityEngine;
using UnityEngine.UI;

namespace PNE.Demo
{
    public class ImageSwapper : MonoBehaviour
    {
        [Header("Target (assign one)")]
        public Image          targetImage;
        public SpriteRenderer targetRenderer;

        [Header("Sprites")]
        public Sprite[] sprites;

        // ── Public API ────────────────────────────────────────────────────────

        public void Swap(int index)
        {
            if (sprites == null || index < 0 || index >= sprites.Length)
            {
                Debug.LogWarning($"[ImageSwapper] Index {index} out of range (length {sprites?.Length ?? 0}).");
                return;
            }

            Apply(sprites[index]);
        }

        public void ResetToDefault() => Swap(0);

        // ── Internal ──────────────────────────────────────────────────────────

        void Apply(Sprite sprite)
        {
            if (targetImage    != null) { targetImage.sprite    = sprite; return; }
            if (targetRenderer != null) { targetRenderer.sprite = sprite; return; }
            Debug.LogWarning("[ImageSwapper] No target Image or SpriteRenderer assigned.");
        }
    }
}
