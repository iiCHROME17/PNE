"""
Psychological Narrative Engine - Core Models
name: PNE_Models.py
Author: Jerome Bawa

A modular narrative engine backend for dynamic NPC behavior
Compatible with Unity, Unreal Engine, and Godot
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import os

# Wildcard configuration index.
# Primary source: external JSON file under /home/jerome/Programs/cs3ip/Config/wildcards.json
# Falls back to the in-code defaults below if loading fails.
_DEFAULT_WILDCARD_OLLAMA_CONFIG: Dict[str, Dict[str, Any]] = {
    "Martyr": {
        "temp_offset": 0.1,
        "repeat_penalty": 1.15,
        "num_predict": 150,
    },
    "Berserker": {
        "temperature": 1.2,
        "top_p": 0.95,
        "top_k": 100,
        "stop": ["."],
    },
    "Logician": {
        "temperature": 0.1,
        "top_p": 0.1,
        "repeat_penalty": 1.0,
    },
}

def _load_wildcard_config_from_json() -> Dict[str, Dict[str, Any]]:
    """
    Attempt to load wildcard → Ollama-config mapping from JSON.
    If anything goes wrong, return the in-code default mapping.
    """
    # Adjust this path if you move the JSON later.
    config_path = "/home/jerome/Programs/cs3ip/Config/wildcards.json"
    try:
        if not os.path.exists(config_path):
            return _DEFAULT_WILDCARD_OLLAMA_CONFIG
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure it's a dict of dicts; otherwise fall back.
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return _DEFAULT_WILDCARD_OLLAMA_CONFIG

WILDCARD_OLLAMA_CONFIG: Dict[str, Dict[str, Any]] = _load_wildcard_config_from_json()

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SocialPosition(Enum):
    """NPC rank within faction"""
    BOSS = "Boss"
    VICE = "Vice"
    HIGHER = "Higher"
    MEMBER = "Member"


# ============================================================================
# COGNITIVE MODEL
# ============================================================================

@dataclass
class CognitiveModel:
    """Represents NPC's internal psychological state"""
    self_esteem: float = 0.5  # 0-1: confidence and self-worth
    locus_of_control: float = 0.5  # 0=external (blames fate), 1=internal (self-responsible)
    cog_flexibility: float = 0.5  # 0=rigid/dogmatic, 1=adaptive/open
    
    def __post_init__(self):
        self._validate_ranges()
    
    def _validate_ranges(self):
        """Ensure all values are within 0-1 range"""
        for attr in ['self_esteem', 'locus_of_control', 'cog_flexibility']:
            value = getattr(self, attr)
            if not 0 <= value <= 1:
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CognitiveModel':
        return cls(**data)


# ============================================================================
# SOCIAL PERSONALITY MODEL
# ============================================================================

@dataclass
class SocialPersonalityModel:
    """Defines NPC's social behavior and ideological stance"""
    assertion: float = 0.5  # 0=passive/easily persuaded, 1=assertive/challenges player
    conf_indep: float = 0.5  # 0=conformist (follows group), 1=independent (autonomous)
    empathy: float = 0.5  # 0=self-focused, 1=empathetic
    
    # Ideology as key-value pairs (weights sum to 1.0)
    ideology: Dict[str, float] = field(default_factory=dict)
    
    # Psychological modifier (e.g., "Martyr", "Napoleon Complex", "Inferiority Complex")
    wildcard: Optional[str] = None
    
    # Faction affiliation
    faction: Optional[str] = None
    social_position: SocialPosition = SocialPosition.MEMBER
    
    def __post_init__(self):
        self._validate_ranges()
        self._normalize_ideology()
    
    def _validate_ranges(self):
        """Ensure float values are within 0-1 range"""
        for attr in ['assertion', 'conf_indep', 'empathy']:
            value = getattr(self, attr)
            if not 0 <= value <= 1:
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")
    
    def _normalize_ideology(self):
        """Ensure ideology weights sum to 1.0"""
        if self.ideology:
            total = sum(self.ideology.values())
            if total > 0:
                self.ideology = {k: v/total for k, v in self.ideology.items()}
    
    def get_dominant_ideology(self) -> Optional[str]:
        """Returns the ideology with highest weight"""
        if not self.ideology:
            return None
        return max(self.ideology, key=self.ideology.get)
    
    def get_wildcard_config(self) -> Dict[str, Any]:
        """
        Look up this NPC's wildcard in the global wildcard→Ollama-config index.

        Returns a (possibly empty) dict which may contain:
        - absolute overrides: temperature, top_p, top_k, repeat_penalty, num_predict, stop
        - relative modifiers: temp_offset (float added to base temperature)
        """
        if not self.wildcard:
            return {}
        return WILDCARD_OLLAMA_CONFIG.get(self.wildcard, {})
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['social_position'] = self.social_position.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialPersonalityModel':
        if 'social_position' in data:
            data['social_position'] = SocialPosition(data['social_position'])
        return cls(**data)


# ============================================================================
# WORLD PERCEPTION MODEL
# ============================================================================

@dataclass
class WorldPerceptionModel:
    """Stores NPC's knowledge and relationship with player"""
    world_history: str = ""
    personal_history: str = ""
    player_history: str = ""
    player_relation: float = 0.5  # 0=contempt, 0.5=neutral, 1=friendship
    
    def __post_init__(self):
        if not 0 <= self.player_relation <= 1:
            raise ValueError(f"player_relation must be between 0 and 1, got {self.player_relation}")
    
    def update_relation(self, delta: float):
        """Adjust relation value, clamped to 0-1"""
        self.player_relation = max(0.0, min(1.0, self.player_relation + delta))
    
    def update_personal_history(self, event: str):
        """Append to personal history"""
        separator = "\n- " if self.personal_history else "- "
        self.personal_history += separator + event
    
    def update_player_history(self, event: str):
        """Append to player history"""
        separator = "\n- " if self.player_history else "- "
        self.player_history += separator + event
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldPerceptionModel':
        """Create WorldPerceptionModel from dictionary"""
        return cls(
            world_history=data.get('world_history', ""),
            personal_history=data.get('personal_history', ""),
            player_history=data.get('player_history', ""),
            player_relation=data.get('player_relation', 0.5)
        )


# ============================================================================
# COMPLETE NPC MODEL
# ============================================================================

@dataclass
class NPCModel:
    """Complete NPC personality and state"""
    name: str
    age: int
    cognitive: CognitiveModel
    social: SocialPersonalityModel
    world: WorldPerceptionModel
    
    # Temporary modifiers (reset after conversation)
    _temp_modifiers: Dict[str, float] = field(default_factory=dict, repr=False)
    
    def get_attribute(self, attr_path: str) -> Any:
        """
        Retrieve attribute using dot notation
        Example: 'cognitive.self_esteem' or 'social.assertion'
        """
        parts = attr_path.split('.')
        obj = self
        for part in parts:
            obj = getattr(obj, part)
        return obj
    
    def apply_temp_mod(self, attr_path: str, modifier: float):
        """Apply temporary modifier to an attribute (conversation-scoped)"""
        original = self.get_attribute(attr_path)
        if attr_path not in self._temp_modifiers:
            self._temp_modifiers[attr_path] = original
        
        # Apply modifier
        parts = attr_path.split('.')
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        final_attr = parts[-1]
        new_value = max(0.0, min(1.0, modifier))  # Clamp to 0-1
        setattr(obj, final_attr, new_value)
    
    def reset_temp_mods(self):
        """Reset all temporary modifiers after conversation"""
        for attr_path, original_value in self._temp_modifiers.items():
            parts = attr_path.split('.')
            obj = self
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], original_value)
        self._temp_modifiers.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'name': self.name,
            'age': self.age,
            'cognitive': self.cognitive.to_dict(),
            'social': self.social.to_dict(),
            'world': self.world.to_dict()
        }
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """Serialize to JSON string or file"""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCModel':
        """Deserialize from dictionary"""
        return cls(
            name=data['name'],
            age=data.get('age', 30),
            cognitive=CognitiveModel.from_dict(data['cognitive']),
            social=SocialPersonalityModel.from_dict(data['social']),
            world=WorldPerceptionModel.from_dict(data['world'])
        )
    
    @classmethod
    def from_json(cls, json_source: str) -> 'NPCModel':
        """
        Deserialize from JSON string or file path
        Automatically detects if input is filepath or JSON string
        """
        try:
            # Try as filepath first
            with open(json_source, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, OSError):
            # Parse as JSON string
            data = json.loads(json_source)
        
        return cls.from_dict(data)


# ============================================================================
# EXAMPLE NPC FACTORY
# ============================================================================

class NPCFactory:
    """Factory for creating predefined NPCs"""
    
    @staticmethod
    def create_morisson_moses() -> NPCModel:
        """Creates Morisson Moses with documented attributes"""
        return NPCModel(
            name="Morisson Moses",
            age=35,
            cognitive=CognitiveModel(
                self_esteem=0.8,
                locus_of_control=0.475,
                cog_flexibility=0.3
            ),
            social=SocialPersonalityModel(
                assertion=1.0,
                conf_indep=0.7,
                empathy=0.45,
                ideology={
                    "Utilitarianism": 0.8,
                    "Authoritarianism": 0.2
                },
                wildcard="Martyr",
                faction="Insurgency",
                social_position=SocialPosition.BOSS
            ),
            world=WorldPerceptionModel(
                world_history="Full world history here...",
                personal_history="Moses' personal journey...",
                player_history="",
                player_relation=0.5
            )
        )
    
    @staticmethod
    def create_amourie_othella() -> NPCModel:
        """Creates Amourie Othella with documented attributes"""
        return NPCModel(
            name="Amourie Othella",
            age=42,
            cognitive=CognitiveModel(
                self_esteem=0.9,
                locus_of_control=0.2,
                cog_flexibility=0.8
            ),
            social=SocialPersonalityModel(
                assertion=0.5,
                conf_indep=0.6,
                empathy=0.25,
                ideology={
                    "Communitarianism": 0.7,
                    "Pragmatism": 0.3
                },
                wildcard="Napoleon",
                faction="The Commonman",
                social_position=SocialPosition.BOSS
            ),
            world=WorldPerceptionModel(
                world_history="Full world history here...",
                personal_history="Othella's journey...",
                player_history="",
                player_relation=0.5
            )
        )
    
    @staticmethod
    def create_krystian_krakk() -> NPCModel:
        """Creates Krystian 'Krakk' Klikowicz"""
        return NPCModel(
            name="Krystian 'Krakk' Klikowicz",
            age=28,
            cognitive=CognitiveModel(
                self_esteem=0.5,
                locus_of_control=0.8,
                cog_flexibility=0.4
            ),
            social=SocialPersonalityModel(
                assertion=0.3,
                conf_indep=0.9,
                empathy=0.8,
                ideology={
                    "Libertarianism": 0.9,
                    "Individualism": 0.1
                },
                wildcard="Inferiority",
                faction="The Runner Networks",
                social_position=SocialPosition.BOSS
            ),
            world=WorldPerceptionModel(
                world_history="Full world history here...",
                personal_history="Krakk's story...",
                player_history="",
                player_relation=0.5
            )
        )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("=== Creating NPCs ===\n")
    
    # Create NPCs
    moses = NPCFactory.create_morisson_moses()
    amourie = NPCFactory.create_amourie_othella()
    krakk = NPCFactory.create_krystian_krakk()

    npcs = [moses, amourie, krakk]

    # Export to JSON and display details
    for npc in npcs:
        file_name = f"{npc.name.lower().replace(' ', '_')}.json"
        npc.to_json(file_name)
        print(f"✓ Created {npc.name} (Age: {npc.age})")
        print(f"  Dominant ideology: {npc.social.get_dominant_ideology()}")
        print(f"  Faction: {npc.social.faction}")
        print(f"  Position: {npc.social.social_position.value}\n")

    # Load from JSON
    print("=== Loading from JSON ===\n")
    loaded_npcs = []
    for npc in npcs:
        file_name = f"{npc.name.lower().replace(' ', '_')}.json"
        loaded_npc = NPCModel.from_json(file_name)
        loaded_npcs.append(loaded_npc)
        print(f"✓ Loaded {loaded_npc.name} from file")
        print(f"  Age: {loaded_npc.age}")
        print(f"  Self-esteem: {loaded_npc.cognitive.self_esteem}\n")

    # Test temporary modifiers
    print("=== Testing Temporary Modifiers ===\n")
    for npc in npcs:
        print(f"Original assertion for {npc.name}: {npc.social.assertion}")
        npc.apply_temp_mod("social.assertion", 0.5)
        print(f"Modified assertion: {npc.social.assertion}")
        npc.reset_temp_mods()
        print(f"Reset assertion: {npc.social.assertion}\n")

    # Test relation updates
    print("=== Testing Relation System ===\n")
    for npc in npcs:
        print(f"Initial relation for {npc.name}: {npc.world.player_relation}")
        npc.world.update_relation(0.2)
        print(f"After positive interaction: {npc.world.player_relation}")
        npc.world.update_relation(-0.3)
        print(f"After negative interaction: {npc.world.player_relation}\n")

    # Test history updates
    print("=== Testing History System ===\n")
    for npc in npcs:
        npc.world.update_player_history("Helped secure weapons cache")
        npc.world.update_player_history("Defended Insurgency base")
        print(f"Player history for {npc.name}:\n{npc.world.player_history}\n")

    print("✓ All tests passed!")
