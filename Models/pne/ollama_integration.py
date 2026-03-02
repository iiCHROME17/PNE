"""
Psychological Narrative Engine - Ollama Integration
Name: ollama_integration.py
Author: Jerome Bawa (original), prompt overhaul by AI assistant
"""

from typing import List
import requests
from .cognitive import ThoughtReaction
from .social import BehaviouralIntention
from .outcomes import InteractionOutcome


_EXPRESSION_GUIDE: dict = {
    "direct":      "Speak plainly and without excess. Get to the point.",
    "measured":    "Choose words carefully. You're calm but probing.",
    "analytical":  "Be logical and detached. Weigh them up clinically.",
    "open":        "Warm but not naive. You're choosing to trust — cautiously.",
    "guarded":     "Keep emotional distance. Don't give too much away.",
    "curious":     "Genuinely interested but not committed.",
    "cautious":    "Acknowledge what they said but reserve judgement.",
    "explosive":   "Passionate, intense, barely contained. This matters deeply.",
    "firm":        "Clear, non-negotiable. You've drawn a line.",
    "suspicious":  "Sceptical. You're looking for the lie.",
    "controlled":  "Deliberately calm despite the tension.",
    "aggressive":  "Dominant, threatening. You don't ask — you impose.",
    "assertive":   "Confident push-back. You won't be moved easily.",
    "suppressed":  "Deference masking resentment. Comply — but show the cost.",
}


def _confrontation_note(level: float) -> str:
    if level >= 0.8:
        return "very confrontational — challenge or pressure them directly"
    if level >= 0.6:
        return "moderately confrontational — push back with clear intent"
    if level >= 0.4:
        return "neutral — neither welcoming nor hostile"
    if level >= 0.2:
        return "low confrontation — cautious but not aggressive"
    return "non-confrontational — de-escalating or deferential"


class OllamaResponseGenerator:
    """Generates NPC dialogue responses using Ollama"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def _build_ollama_options(self, npc) -> dict:
        options = {
            "temperature": 0.85,
            "top_p": 0.8125,
            "top_k": 0,
            "repeat_penalty": 1.125,
            "num_predict": 100,
        }
        wildcard_cfg = {}
        try:
            social = getattr(npc, "social", None)
            if social and hasattr(social, "get_wildcard_config"):
                wildcard_cfg = social.get_wildcard_config() or {}
        except Exception:
            wildcard_cfg = {}

        if wildcard_cfg:
            base_temp = options.get("temperature", 0.85)
            temp_offset = wildcard_cfg.get("temp_offset")
            if isinstance(temp_offset, (int, float)):
                options["temperature"] = base_temp + float(temp_offset)
            for key in ("temperature", "top_p", "top_k", "repeat_penalty", "num_predict", "stop"):
                if key in wildcard_cfg:
                    options[key] = wildcard_cfg[key]

        return options

    def generate_response(
        self,
        npc,
        thought_reaction: ThoughtReaction,
        behavioural_intention: BehaviouralIntention,
        interaction_outcome: InteractionOutcome,
        conversation_history: List[str] = None,
    ) -> str:
        prompt = self._build_prompt(
            npc, thought_reaction, behavioural_intention,
            interaction_outcome, conversation_history,
        )
        options = self._build_ollama_options(npc)

        try:
            print(f"  → Connecting to Ollama at {self.base_url}...")
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": options,
                },
                timeout=60,
            )
            if response.status_code == 200:
                result = response.json()
                generated = result.get("response", "").strip()
                if generated:
                    return generated
            return interaction_outcome.get_response(thought_reaction.emotional_valence)

        except Exception as e:
            print(f"[Ollama Error: {str(e)}]")
            return interaction_outcome.get_response(thought_reaction.emotional_valence)

    def _build_prompt(
        self,
        npc,
        thought_reaction: ThoughtReaction,
        behavioural_intention: BehaviouralIntention,
        interaction_outcome: InteractionOutcome,
        conversation_history: List[str] = None,
    ) -> str:
        parts: List[str] = []

        # ── ROLE ────────────────────────────────────────────────────────
        dominant_ideology = ""
        try:
            dominant_ideology = npc.social.get_dominant_ideology()
        except Exception:
            pass

        parts.append(f"You are {npc.name}, a {npc.social.social_position.value} "
                     f"of the {npc.social.faction}.")
        if dominant_ideology:
            parts.append(f"Your dominant ideology: {dominant_ideology}.")
        parts.append("")

        # ── WORLD CONTEXT ────────────────────────────────────────────────
        world_context = getattr(npc, "world_context", None)
        if world_context:
            parts.append("## WORLD CONTEXT")
            parts.append(world_context.get_npc_context(npc))
            parts.append("")

        # ── BDI STATE ────────────────────────────────────────────────────
        parts.append("## CURRENT INTERNAL STATE")
        parts.append(f"BELIEF:    \"{thought_reaction.subjective_belief}\"")
        parts.append(f"INTENTION: {behavioural_intention.intention_type}")
        parts.append("")

        # ── ACTING DIRECTION ─────────────────────────────────────────────
        expression = behavioural_intention.emotional_expression
        expression_guide = _EXPRESSION_GUIDE.get(expression, "Respond naturally.")
        confrontation_note = _confrontation_note(behavioural_intention.confrontation_level)

        parts.append("## HOW TO SPEAK THIS TURN")
        parts.append(f"Tone style   : {expression.upper()} — {expression_guide}")
        parts.append(f"Confrontation: {confrontation_note}")
        if behavioural_intention.wildcard_triggered:
            parts.append(f"⚠  Wildcard active ({npc.social.wildcard}) — "
                         f"push this trait to the foreground.")
        parts.append("")

        # ── RESPONSE RANGE ───────────────────────────────────────────────
        parts.append("## RESPONSE RANGE (for calibration only — do NOT copy verbatim)")
        parts.append(f"Negative variant: \"{interaction_outcome.min_response}\"")
        parts.append(f"Positive variant: \"{interaction_outcome.max_response}\"")
        parts.append("")

        # ── CONVERSATION HISTORY ─────────────────────────────────────────
        if conversation_history:
            recent = conversation_history[-6:]
            parts.append("## RECENT CONVERSATION")
            for line in recent:
                parts.append(line)
            parts.append("")

        # ── INSTRUCTION ──────────────────────────────────────────────────
        parts.append(
            f"Generate ONE line of dialogue as {npc.name}. "
            f"Stay in character. Do NOT describe actions or emotions in brackets. "
            f"Respond to what was just said. Keep it under 40 words."
        )

        return "\n".join(parts)