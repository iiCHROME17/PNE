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