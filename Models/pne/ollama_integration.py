"""
Psychological Narrative Engine - Ollama Integration
Name: ollama_integration.py

Prompt structure
----------------
  IDENTITY      – name, age, faction, position, ideology
  WORLD CONTEXT – personal history, known events/figures, player history
  BDI STATE     – belief / intention this turn
  ACTING NOTES  – tone, confrontation, wildcard
  RESPONSE RANGE– min/max calibration variants
  HISTORY       – last 6 lines of conversation
  INSTRUCTION   – generate one line of dialogue
"""

from typing import List
import requests
from .cognitive import ThoughtReaction
from .social import BehaviouralIntention
from .outcomes import InteractionOutcome


# ── Emotional expression → plain-English acting direction ──────────────────
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

# ── Confrontation level → acting note ──────────────────────────────────────
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


# ── Player relation → disposition note ─────────────────────────────────────
def _relation_note(relation: float) -> str:
    if relation >= 0.8:
        return "You've come to trust them — still vigilant but genuinely open."
    if relation >= 0.6:
        return "Cautious respect. They haven't earned full trust yet."
    if relation >= 0.4:
        return "Neutral. Watching them carefully."
    if relation >= 0.2:
        return "Sceptical. Your guard is up."
    return "Deep distrust. You're close to shutting this down."


# ── Emotional valence → per-turn psychological reaction note ────────────────
def _valence_note(v: float) -> str:
    if v >= 0.5:
        return "open and receptive — they responded positively"
    if v >= 0.2:
        return "mildly positive — cautiously receptive"
    if v > -0.2:
        return "neutral — unmoved either way"
    if v > -0.5:
        return "negative — feels threatened or manipulated"
    return "strongly negative — hostile, resistant, or contemptuous"


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
        """
        Build a fully-grounded prompt that integrates all NPC data including
        the world context block (personal_history, known_events, known_figures,
        player_history, player_relation).

        Attribute access is wrapped in try/except throughout so the prompt
        degrades gracefully if any field is missing or not yet loaded.
        """
        parts: List[str] = []

        # ── Helper: safe attribute getter ────────────────────────────────
        def _get(obj, *attrs, default=""):
            try:
                for attr in attrs:
                    obj = getattr(obj, attr)
                return obj if obj is not None else default
            except Exception:
                return default

        # ================================================================
        # IDENTITY
        # ================================================================
        name     = _get(npc, "name", default="Unknown")
        age      = _get(npc, "age", default="")
        faction  = _get(npc, "social", "faction", default="")
        position = _get(npc, "social", "social_position", default="")
        wildcard = _get(npc, "social", "wildcard", default="")
        soc = getattr(npc, "social", None)

        # social_position may be an enum
        position_str = position.value if hasattr(position, "value") else str(position)

        age_str = f", age {age}" if age else ""
        parts.append(f"You are {name}{age_str}.")

        if position_str and faction:
            parts.append(f"Role: {position_str} of the {faction}.")
        elif faction:
            parts.append(f"Faction: {faction}.")

        dominant_ideology = ""
        try:
            dominant_ideology = npc.social.get_dominant_ideology()
        except Exception:
            pass
        if dominant_ideology:
            parts.append(f"Dominant ideology: {dominant_ideology}.")

        # Cognitive stats
        cog = getattr(npc, "cognitive", None)
        if cog is not None:
            se  = int(round(_get(npc, "cognitive", "self_esteem",      default=0.5) * 100))
            loc = int(round(_get(npc, "cognitive", "locus_of_control", default=0.5) * 100))
            cf  = int(round(_get(npc, "cognitive", "cog_flexibility",  default=0.5) * 100))
            loc_label = "External" if loc < 50 else "Internal"
            parts.append(
                f"Self-esteem: {se}/100  |  "
                f"Locus of control: {loc}/100 ({loc_label})  |  "
                f"Cognitive flexibility: {cf}/100"
            )

        # Social stats
        if soc is not None:
            ast = int(round(_get(npc, "social", "assertion",  default=0.5) * 100))
            cid = int(round(_get(npc, "social", "conf_indep", default=0.5) * 100))
            emp = int(round(_get(npc, "social", "empathy",    default=0.5) * 100))
            parts.append(
                f"Assertion: {ast}/100  |  "
                f"Conf. independence: {cid}/100  |  "
                f"Empathy: {emp}/100"
            )

        parts.append("")

        # ================================================================
        # WORLD CONTEXT
        # ================================================================
        world = getattr(npc, "world", None)
        has_world = world is not None

        personal_history = _get(npc, "world", "personal_history", default="") if has_world else ""
        player_history   = _get(npc, "world", "player_history",   default="") if has_world else ""
        player_relation  = _get(npc, "world", "player_relation",  default=0.5) if has_world else 0.5
        known_events     = _get(npc, "world", "known_events",     default=[])  if has_world else []
        known_figures    = _get(npc, "world", "known_figures",    default=[])  if has_world else []

        parts.append("## BACKGROUND")

        if personal_history:
            parts.append(f"Your history: {personal_history}")
        else:
            parts.append("(No personal history loaded.)")

        if player_history and player_history.strip():
            parts.append(f"Your history with this person: {player_history}")
        else:
            parts.append("This person is unknown to you.")

        if isinstance(known_events, list) and known_events:
            # Format as readable list rather than raw IDs
            events_str = ", ".join(
                e.replace("_", " ") for e in known_events
            )
            parts.append(f"Events you know of: {events_str}.")

        if isinstance(known_figures, list) and known_figures:
            figures_str = ", ".join(
                f.replace("_", " ") for f in known_figures
            )
            parts.append(f"Figures you know of: {figures_str}.")

        parts.append(f"Your current disposition toward this person: {_relation_note(float(player_relation))}")
        parts.append("")

        # ================================================================
        # BDI STATE
        # ================================================================
        parts.append("## CURRENT INTERNAL STATE")
        parts.append(f'BELIEF:    "{thought_reaction.subjective_belief}"')
        parts.append(f"INTENTION: {behavioural_intention.intention_type}")
        parts.append("")

        # ================================================================
        # ACTING NOTES
        # ================================================================
        expression        = behavioural_intention.emotional_expression
        expression_guide  = _EXPRESSION_GUIDE.get(expression, "Respond naturally.")
        conf_note         = _confrontation_note(behavioural_intention.confrontation_level)

        parts.append("## HOW TO SPEAK THIS TURN")
        parts.append(f"Tone      : {expression.upper()} — {expression_guide}")
        parts.append(f"Stance    : {conf_note}")

        if behavioural_intention.wildcard_triggered and wildcard:
            parts.append(
                f"⚠  Wildcard active ({wildcard}) — "
                f"let this trait colour everything you say this turn."
            )
        parts.append("")

        # ================================================================
        # RESPONSE RANGE  (calibration only)
        # ================================================================
        parts.append("## RESPONSE RANGE (calibration only — do NOT copy verbatim)")
        parts.append(f'Negative end: "{interaction_outcome.min_response}"')
        parts.append(f'Positive end: "{interaction_outcome.max_response}"')
        parts.append("")

        # ================================================================
        # RECENT CONVERSATION
        # ================================================================
        if conversation_history:
            recent = conversation_history[-6:]
            parts.append("## RECENT CONVERSATION")
            for line in recent:
                parts.append(line)
            parts.append("")

        # ================================================================
        # INSTRUCTION
        # ================================================================
        parts.append(
            f"Generate ONE line of dialogue as {name}. "
            "Stay in character. Do NOT describe actions in brackets. "
            "Respond directly to what was just said. Under 40 words."
        )

        return "\n".join(parts)

    def generate_response_with_direction(
        self,
        npc,
        thought: dict,
        intention: dict,
        interaction_outcome,
        history: list,
        scene_direction: str = "",
        check_success: bool = None,
        dice_description: str = "",
    ) -> str:
        """
        Generate NPC dialogue using BDI context dicts + the scenario node's
        npc_dialogue_prompt as an explicit scene direction.

        Called by the narrative engine after the BDI pipeline runs without Ollama,
        so we control the full prompt rather than letting the BDI generate it blindly.
        """
        def _get(obj, *attrs, default=""):
            try:
                for attr in attrs:
                    obj = getattr(obj, attr)
                return obj if obj is not None else default
            except Exception:
                return default

        name = _get(npc, "name", default="NPC")
        parts = []

        # Identity
        age = _get(npc, "age", default="")
        faction = _get(npc, "social", "faction", default="")
        age_str = f", age {age}" if age else ""
        parts.append(f"You are {name}{age_str}.")
        if faction:
            parts.append(f"Faction: {faction}.")
        parts.append("")

        # Background
        world = getattr(npc, "world", None)
        personal_history = _get(npc, "world", "personal_history", default="") if world else ""
        player_relation = float(_get(npc, "world", "player_relation", default=0.5) if world else 0.5)
        parts.append("## BACKGROUND")
        if personal_history:
            parts.append(f"Your history: {personal_history}")
        parts.append(f"Your current disposition toward this person: {_relation_note(player_relation)}")
        parts.append("")

        # BDI state
        belief = thought.get("subjective_belief", "") if isinstance(thought, dict) else ""
        intention_type = intention.get("intention_type", "") if isinstance(intention, dict) else ""
        confrontation = float(intention.get("confrontation_level", 0.5) if isinstance(intention, dict) else 0.5)
        emotional_valence = float(thought.get("emotional_valence", 0.0) if isinstance(thought, dict) else 0.0)
        parts.append("## CURRENT INTERNAL STATE")
        parts.append(f'BELIEF:    "{belief}"')
        parts.append(f"INTENTION: {intention_type}")
        parts.append(f"Stance:    {_confrontation_note(confrontation)}")
        parts.append(f"Emotional reaction this turn: {emotional_valence:+.2f}  ({_valence_note(emotional_valence)})")
        parts.append("")

        # Scene direction (from node's npc_dialogue_prompt) — general stance context
        if scene_direction:
            parts.append("## SCENE DIRECTION")
            parts.append(scene_direction)
            parts.append("")

        # Dice context — placed AFTER scene direction so the LLM prioritises it.
        # When dice were rolled, this section overrides the general scene stance.
        if check_success is not None and dice_description:
            parts.append("## DICE CONTEXT — OVERRIDES SCENE DIRECTION ABOVE")
            if check_success:
                parts.append(
                    f"The player's skill check SUCCEEDED {dice_description}. "
                    "Their approach got through to you. Let this show in your response — "
                    "even a guarded character can feel a genuine touch land."
                )
            else:
                parts.append(
                    f"The player's skill check FAILED {dice_description}. "
                    "Their approach didn't land. You weren't moved — "
                    "respond dismissively, sceptically, or simply unmoved."
                )
            parts.append("")

        # Response range calibration
        min_r = max_r = ""
        if interaction_outcome is not None:
            if isinstance(interaction_outcome, dict):
                min_r = interaction_outcome.get("min_response", "")
                max_r = interaction_outcome.get("max_response", "")
            else:
                min_r = getattr(interaction_outcome, "min_response", "")
                max_r = getattr(interaction_outcome, "max_response", "")
        if min_r or max_r:
            parts.append("## RESPONSE RANGE (calibration — do NOT copy verbatim)")
            if min_r:
                parts.append(f'Negative end: "{min_r}"')
            if max_r:
                parts.append(f'Positive end:  "{max_r}"')
            parts.append("")

        # Recent conversation
        recent = history[-6:] if len(history) > 6 else history
        if recent:
            parts.append("## RECENT CONVERSATION")
            for entry in recent:
                parts.append(f"{entry['speaker']}: {entry['text']}")
            parts.append("")

        parts.append(
            f"Generate ONE line of dialogue as {name}. "
            "Stay in character. Do NOT describe actions in brackets. "
            "Respond directly to what was just said. Under 40 words."
        )

        prompt = "\n".join(parts)
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
        except Exception as e:
            print(f"[Ollama Error: {str(e)}]")

        # Fallback to calibration range or empty
        return min_r or max_r or ""

    def generate_terminal(
        self,
        npc,
        terminal_prompt: str,
        history: List[dict],
    ) -> str:
        """
        Generate a final NPC line for a terminal node.

        Uses a stripped-down prompt: NPC identity, recent conversation,
        and the terminal node's npc_dialogue_prompt as the instruction.
        """
        name = getattr(npc, "name", "NPC")
        recent = history[-4:] if len(history) > 4 else history
        history_lines = "\n".join(
            f"{e['speaker']}: {e['text']}" for e in recent
        )

        relation = 0.5
        try:
            relation = float(npc.world.player_relation)
        except Exception:
            pass

        prompt = (
            f"You are {name}.\n"
            f"Your current disposition toward this person: {_relation_note(relation)}\n\n"
            f"RECENT CONVERSATION:\n{history_lines}\n\n"
            f"INSTRUCTION: {terminal_prompt}\n\n"
            f"Generate ONE final line of dialogue as {name}. "
            "Stay in character. Do NOT describe actions in brackets. Under 30 words."
        )

        options = self._build_ollama_options(npc)
        options["num_predict"] = 60  # shorter for final lines

        try:
            print(f"  → [Terminal] Connecting to Ollama at {self.base_url}...")
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
        except Exception as e:
            print(f"[Ollama Terminal Error: {str(e)}]")

        return ""