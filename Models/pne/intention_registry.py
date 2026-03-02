"""
Psychological Narrative Engine - Canonical Intention Registry
Name: intention_registry.py

Defines the closed vocabulary of NPC behavioural intentions.
Both SocialisationFilter and TransitionResolver reference this registry,
ensuring transitions can always match the intention the BDI pipeline produces.

Each intention has:
  - A canonical name (used in transitions)
  - A desire_type it belongs to
  - The desire keywords that activate it
  - NPC attribute conditions that gate it
  - A confrontation_level range
  - An emotional_expression
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class IntentionTemplate:
    """
    A canonical intention entry.
    SocialisationFilter picks from these.
    TransitionResolver matches against these names.
    """
    name: str                          # Canonical name — used in scenario transitions
    desire_type: str                   # Which desire type produces this
    desire_keywords: List[str]         # Keywords in desire text that activate this
    confrontation_min: float           # Valid confrontation range
    confrontation_max: float
    emotional_expression: str
    wildcard_required: Optional[str] = None   # e.g. "Martyr" — NPC must have this wildcard
    npc_conditions: Dict[str, Any] = field(default_factory=dict)
    # e.g. {"social.assertion": (">", 0.7)} — extra NPC attribute gates


# ============================================================================
# THE CANONICAL INTENTION VOCABULARY
# ============================================================================
# Scenario transitions reference these names in "intention_match" fields.
# SocialisationFilter selects from this list based on desire + NPC profile.

INTENTION_REGISTRY: List[IntentionTemplate] = [

    # ── INFORMATION-SEEKING ───────────────────────────────────────────────

    IntentionTemplate(
        name="Challenge to Reveal Truth",
        desire_type="information-seeking",
        desire_keywords=["test", "probe", "scrutinize", "commitment", "sincerity"],
        confrontation_min=0.6,
        confrontation_max=0.9,
        emotional_expression="direct",
        npc_conditions={"social.assertion": (">", 0.7)},
    ),
    IntentionTemplate(
        name="Carefully Question Motives",
        desire_type="information-seeking",
        desire_keywords=["test", "probe", "scrutinize"],
        confrontation_min=0.3,
        confrontation_max=0.6,
        emotional_expression="measured",
        npc_conditions={"social.assertion": ("<=", 0.7)},
    ),
    IntentionTemplate(
        name="Neutral Evaluation",
        desire_type="information-seeking",
        desire_keywords=["evaluate", "assess", "understand", "align"],
        confrontation_min=0.3,
        confrontation_max=0.5,
        emotional_expression="analytical",
    ),

    # ── AFFILIATION ───────────────────────────────────────────────────────

    IntentionTemplate(
        name="Seek Connection",
        desire_type="affiliation",
        desire_keywords=["common ground", "trust", "build", "find"],
        confrontation_min=0.1,
        confrontation_max=0.3,
        emotional_expression="open",
        npc_conditions={"social.empathy": (">", 0.5)},
    ),
    IntentionTemplate(
        name="Cautious Openness",
        desire_type="affiliation",
        desire_keywords=["common ground", "trust", "build", "find"],
        confrontation_min=0.3,
        confrontation_max=0.5,
        emotional_expression="guarded",
        npc_conditions={"social.empathy": ("<=", 0.5)},
    ),
    IntentionTemplate(
        name="Explore Common Ground",
        desire_type="affiliation",
        desire_keywords=["explore", "shared", "values"],
        confrontation_min=0.2,
        confrontation_max=0.4,
        emotional_expression="curious",
    ),
    IntentionTemplate(
        name="Acknowledge with Reservation",
        desire_type="affiliation",
        desire_keywords=["acknowledge", "guarded", "connection"],
        confrontation_min=0.4,
        confrontation_max=0.6,
        emotional_expression="cautious",
    ),

    # ── PROTECTION ────────────────────────────────────────────────────────

    IntentionTemplate(
        name="Defend Cause Passionately",
        desire_type="protection",
        desire_keywords=["defend", "cause", "loyalty", "protect the cause"],
        confrontation_min=0.7,
        confrontation_max=1.0,
        emotional_expression="explosive",
        wildcard_required="Martyr",
    ),
    IntentionTemplate(
        name="Establish Boundaries",
        desire_type="protection",
        desire_keywords=["defend", "cause", "loyalty"],
        confrontation_min=0.5,
        confrontation_max=0.7,
        emotional_expression="firm",
    ),
    IntentionTemplate(
        name="Maintain Distance",
        desire_type="protection",
        desire_keywords=["protect", "deceived", "distance"],
        confrontation_min=0.4,
        confrontation_max=0.6,
        emotional_expression="suspicious",
    ),
    IntentionTemplate(
        name="De-escalate and Withdraw",
        desire_type="protection",
        desire_keywords=["boundaries", "de-escalate", "withdraw"],
        confrontation_min=0.2,
        confrontation_max=0.4,
        emotional_expression="controlled",
    ),

    # ── DOMINANCE ─────────────────────────────────────────────────────────

    IntentionTemplate(
        name="Assert Dominance Aggressively",
        desire_type="dominance",
        desire_keywords=["assert", "challenge", "dominate"],
        confrontation_min=0.8,
        confrontation_max=1.0,
        emotional_expression="aggressive",
        wildcard_required="Napoleon",
    ),
    IntentionTemplate(
        name="Challenge Back",
        desire_type="dominance",
        desire_keywords=["assert", "challenge", "push back"],
        confrontation_min=0.6,
        confrontation_max=0.8,
        emotional_expression="assertive",
    ),

    # ── WILDCARD OVERRIDES ────────────────────────────────────────────────

    IntentionTemplate(
        name="Submit",
        desire_type="protection",
        desire_keywords=["submit", "comply", "back down"],
        confrontation_min=0.0,
        confrontation_max=0.2,
        emotional_expression="suppressed",
        wildcard_required="Inferiority",
    ),

    # ── ACCEPTANCE / RESOLUTION ───────────────────────────────────────────

    IntentionTemplate(
        name="Accept Player for Trial",
        desire_type="information-seeking",
        desire_keywords=["trial", "accept", "chance", "prove", "task"],
        confrontation_min=0.3,
        confrontation_max=0.6,
        emotional_expression="direct",
    ),
    IntentionTemplate(
        name="Transactional Agreement",
        desire_type="affiliation",
        desire_keywords=["transactional", "deal", "supplies", "exchange"],
        confrontation_min=0.2,
        confrontation_max=0.5,
        emotional_expression="measured",
    ),
    IntentionTemplate(
        name="Resist Player",
        desire_type="protection",
        desire_keywords=["resist", "authority", "push back", "intimidate"],
        confrontation_min=0.6,
        confrontation_max=0.9,
        emotional_expression="direct",
    ),

    # ── FALLBACK ──────────────────────────────────────────────────────────

    IntentionTemplate(
        name="Neutral Response",
        desire_type="",
        desire_keywords=[],
        confrontation_min=0.4,
        confrontation_max=0.6,
        emotional_expression="direct",
    ),
]

# Fast lookup by name
INTENTION_BY_NAME: Dict[str, IntentionTemplate] = {
    t.name: t for t in INTENTION_REGISTRY
}

# All canonical intention names — used by scenario authors for transitions
INTENTION_NAMES = [t.name for t in INTENTION_REGISTRY]


def get_intention(name: str) -> Optional[IntentionTemplate]:
    return INTENTION_BY_NAME.get(name)


def list_by_desire_type(desire_type: str) -> List[IntentionTemplate]:
    return [t for t in INTENTION_REGISTRY if t.desire_type == desire_type]