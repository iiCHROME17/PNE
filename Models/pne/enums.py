"""
Psychological Narrative Engine - Core Enumerations
Name: enums.py
Author: Jerome Bawa
"""

from enum import Enum


class LanguageArt(Enum):
    """Player Dialogue Approaches (Rhetoric)"""
    CHALLENGE = "challenge"
    DIPLOMATIC = "diplomatic"
    EMPATHETIC = "empathetic"
    MANIPULATIVE = "manipulative"
    NEUTRAL = "neutral"


class PlayerSkill(Enum):
    """Player's skill proficiencies"""
    AUTHORITY = "authority"
    DIPLOMACY = "diplomacy"
    EMPATHY = "empathy"
    MANIPULATION = "manipulation"


class TerminalOutcomeType(Enum):
    """Terminal outcome types"""
    SUCCEED = "succeed"
    FAIL = "fail"
    NEGOTIATE = "negotiate"
    DELAY = "delay"
    ESCALATE = "escalate"


class Difficulty(Enum):
    """Global dice difficulty setting.

    Adjusts the player's die-weight bias before every roll:
      SIMPLE   (+0.15) — player rolls skew higher; success is more forgiving
      STANDARD ( 0.00) — default balanced behaviour
      STRICT   (-0.15) — player rolls skew lower; NPC resists more effectively
    """
    SIMPLE = "simple"
    STANDARD = "standard"
    STRICT = "strict"