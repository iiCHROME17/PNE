"""
Psychological Narrative Engine - Cognitive Thought Matcher
Name: cognitive_thought_matcher.py

Replaces the LLM-based CognitiveInterpreter thought generation with a
weighted template-matching system. Templates are defined in cognitive_thoughts.json.

Matching algorithm
------------------
Each template defines match_weights for a set of parameters drawn from
the current player input and NPC state. The algorithm:

  1. Scores every template by summing the weights of matched parameters.
  2. Normalises each score against the template's total possible weight.
  3. Picks the highest-scoring template above THRESHOLD (0.35).
  4. Falls back to a "cynical_realism" template if nothing clears the bar.
  5. Picks a random variant from the winner's thought_variants / belief_variants.

Parameter schema in match_weights
----------------------------------
  "language_art": {"challenge": 0.8, "diplomatic": 0.4}
      → discrete lookup; max value counts toward total possible weight.

  "npc_self_esteem": {"max": 0.5, "weight": 0.6}
      → numeric gate; value must be ≤ max to score `weight` points.

  "authority_tone": {"min": 0.6, "weight": 0.7}
      → numeric gate; value must be ≥ min to score `weight` points.

  "npc_locus_of_control": {"min": 0.3, "max": 0.6, "weight": 0.5}
      → range gate; value must be within [min, max].

Supported numeric parameters
-----------------------------
  npc_self_esteem, npc_locus_of_control, npc_cog_flexibility
  authority_tone, diplomacy_tone, empathy_tone, manipulation_tone
  player_relation
"""

import json
import random
from pathlib import Path


class CognitiveThoughtMatcher:
    """Template-based replacement for the LLM ``CognitiveInterpreter``.

    Instead of calling an Ollama model for every turn, this class scores each
    template in ``cognitive_thoughts.json`` against the current player input
    and NPC state, then picks the highest-scoring winner above ``THRESHOLD``.

    The result is deterministic (given the same seed) and much faster than an
    LLM call — useful for testing, low-resource deployments, or as a fallback
    when Ollama is unavailable.

    Class Attributes:
        THRESHOLD: Minimum normalised score (0.0–1.0) a template must reach to
            be selected.  Templates scoring below this fall back to
            ``FALLBACK_BIAS``.
        FALLBACK_BIAS: The ``bias_type`` string used to locate the default
            template when nothing clears ``THRESHOLD``.

    Instance Attributes:
        templates: List of template dicts loaded from ``cognitive_thoughts.json``.
    """

    THRESHOLD = 0.35
    FALLBACK_BIAS = "cynical_realism"

    # Maps parameter names used in template ``match_weights`` to lambdas that
    # extract the corresponding float value from (player_input, npc).
    _PARAM_GETTERS = {
        "npc_self_esteem":      lambda pi, npc: npc.cognitive.self_esteem,
        "npc_locus_of_control": lambda pi, npc: npc.cognitive.locus_of_control,
        "npc_cog_flexibility":  lambda pi, npc: npc.cognitive.cog_flexibility,
        "authority_tone":       lambda pi, npc: pi.authority_tone,
        "diplomacy_tone":       lambda pi, npc: pi.diplomacy_tone,
        "empathy_tone":         lambda pi, npc: pi.empathy_tone,
        "manipulation_tone":    lambda pi, npc: pi.manipulation_tone,
        "player_relation":      lambda pi, npc: float(npc.world.player_relation),
    }

    def __init__(self, templates_path: str = None):
        """Load cognitive thought templates from JSON.

        Args:
            templates_path: Absolute path to a ``cognitive_thoughts.json`` file.
                Defaults to ``<package_dir>/cognitive_thoughts.json``.

        Raises:
            FileNotFoundError: If the templates file does not exist at the
                resolved path.
        """
        if templates_path is None:
            templates_path = str(Path(__file__).parent / "cognitive_thoughts.json")
        with open(templates_path, encoding="utf-8") as f:
            self.templates = json.load(f)

    def match(self, player_input, npc) -> tuple:
        """Find the best-matching cognitive template for this player input + NPC.

        Scores every template in ``self.templates`` and picks the highest-
        normalised winner above ``THRESHOLD``.  If none qualify, falls back to
        the ``FALLBACK_BIAS`` template (or the first template in the list).

        A random variant is then drawn from the winner's ``thought_variants``
        and ``belief_variants`` lists, giving natural variation across repeated
        uses of the same template.

        Args:
            player_input: A ``PlayerDialogueInput`` providing tone scores and
                ``language_art``.
            npc: An ``NPCModel`` providing ``cognitive`` and ``world`` attributes.

        Returns:
            A 3-tuple ``(bias_type, internal_thought, subjective_belief)`` where:
              - ``bias_type`` is the cognitive bias label (e.g. ``"hostile_attribution"``).
              - ``internal_thought`` is the NPC's private reaction text.
              - ``subjective_belief`` is the NPC's conscious interpretation of the player.
        """
        la = player_input.language_art.value if hasattr(player_input.language_art, "value") else str(player_input.language_art)

        best_score, best = -1.0, None
        for template in self.templates:
            score, total = self._score(template, la, player_input, npc)
            norm = score / total if total > 0 else 0.0
            if norm > best_score:
                best_score, best = norm, template

        if best_score < self.THRESHOLD or best is None:
            best = next(
                (t for t in self.templates if t["bias_type"] == self.FALLBACK_BIAS),
                self.templates[0],
            )

        return (
            best["bias_type"],
            random.choice(best["thought_variants"]),
            random.choice(best["belief_variants"]),
        )

    def _score(self, template: dict, la: str, player_input, npc) -> tuple:
        """Score a single template against the current player input and NPC state.

        Accumulates a weighted score by evaluating each entry in the template's
        ``match_weights`` dict:

        - ``language_art`` — discrete lookup: the player's current language art
          is looked up in the weight table; the table's max value counts toward
          ``total`` so other language arts are relatively penalised.
        - Numeric parameters — each uses a gate (``min``, ``max``, or both) to
          award ``weight`` points if the extracted value falls in range.

        Args:
            template: A single template dict from ``cognitive_thoughts.json``.
            la: The player's current language art as a lowercase string.
            player_input: The ``PlayerDialogueInput`` for this turn.
            npc: The ``NPCModel`` being addressed.

        Returns:
            A 2-tuple ``(score, total_possible)`` where ``score / total_possible``
            gives the normalised fit in [0.0, 1.0].
        """
        weights = template.get("match_weights", {})
        score, total = 0.0, 0.0

        # ── language_art: discrete lookup ──────────────────────────────
        if "language_art" in weights:
            la_tbl = weights["language_art"]
            max_val = max(la_tbl.values(), default=0.0)
            total += max_val
            score += la_tbl.get(la, 0.0)

        # ── numeric parameters ──────────────────────────────────────────
        for key, getter in self._PARAM_GETTERS.items():
            if key not in weights:
                continue
            cfg = weights[key]
            w = float(cfg.get("weight", 0.0))
            total += w
            try:
                val = float(getter(player_input, npc))
            except Exception:
                continue
            lo = cfg.get("min")
            hi = cfg.get("max")
            if lo is not None and hi is not None:
                if float(lo) <= val <= float(hi):
                    score += w
            elif lo is not None:
                if val >= float(lo):
                    score += w
            elif hi is not None:
                if val <= float(hi):
                    score += w

        return score, total
