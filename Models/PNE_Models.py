"""
Psychological Narrative Engine - Core Models
Author: Jerome Bawa
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Any
from enum import Enum
import json

# -----------------------------
# Enums
# -----------------------------
class SocialPosition(Enum):
    """Defines social positions within a faction."""
    BOSS = "Boss"
    VICE = "Vice"
    HIGHER = "Higher"
    MEMBER = "Member"

# -----------------------------
# Cognitive Model
# -----------------------------
@dataclass
class CognitiveModel:
    """Represents a cognitive mode for the NPC's internal belief system."""
    self_esteem: float = 0.5  # 0-1 - Confidence in self-worth
    locus_of_control: float = 0.5  # 0-1 - 0 External, 1 Internal
    cog_flexibility: float = 0.5  # 0-1 - 0 Rigid, 1 Adaptive

    def __post_init__(self):
        self._validate_ranges()

    def _validate_ranges(self):
        """Validate that all attributes are within the range [0, 1]."""
        for attr in ['self_esteem', 'locus_of_control', 'cog_flexibility']:
            value = getattr(self, attr)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CognitiveModel':
        return cls(**data)

# -----------------------------
# Social Personality Model
# -----------------------------
@dataclass
class SocialPersonalityModel:
    """Defines NPC's social personality and ideology."""
    assertion: float = 0.5  # 0-1 - 0 Passive, 1 Aggressive
    conf_indep: float = 0.5  # 0-1 - 0 Conformist, 1 Independent
    empathy: float = 0.5  # 0-1 - 0 Self-Focus, 1 High Empathy
    ideology: Dict[str, float] = field(default_factory=dict)
    wildcard: Optional[str] = None  # E.g "Inferiority Complex"
    faction: Optional[str] = None  # E.g "Rebels"
    social_position: SocialPosition = SocialPosition.MEMBER

    def __post_init__(self):
        self._validate_ranges()
        self._normalize_ideology()

    def _validate_ranges(self):
        for attr in ['assertion', 'conf_indep', 'empathy']:
            value = getattr(self, attr)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")

    def _normalize_ideology(self):
        total = sum(self.ideology.values())
        if total > 0:
            self.ideology = {k: v / total for k, v in self.ideology.items()}

    def get_dominant_ideology(self) -> Optional[str]:
        if not self.ideology:
            return None
        return max(self.ideology, key=self.ideology.get)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['social_position'] = self.social_position.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialPersonalityModel':
        if 'social_position' in data:
            data['social_position'] = SocialPosition(data['social_position'])
        return cls(**data)

# -----------------------------
# World Perception Model
# -----------------------------
@dataclass
class WorldPerceptionModel:
    """NPC knowledge about the world and player."""
    world_history: str = ""
    personal_history: str = ""
    player_history: str = ""
    player_relation: float = 0.5  # 0-1 - 0 Hostile, 1 Friendly

    def __post_init__(self):
        if not 0 <= self.player_relation <= 1:
            raise ValueError(f"player_relation must be between 0 and 1, got {self.player_relation}")

    def update_relation(self, change: float):
        self.player_relation = max(0.0, min(1.0, self.player_relation + change))

    def update_personal_history(self, event: str):
        self.personal_history += (" " if self.personal_history else "") + event

    def update_player_history(self, event: str):
        self.player_history += (" " if self.player_history else "") + event

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# -----------------------------
# NPC Brain
# -----------------------------
@dataclass
class NPCModel:
    """Complete NPC Brain model combining all sub-models."""
    name: str
    age: int
    cognitive: CognitiveModel
    social: SocialPersonalityModel
    world: WorldPerceptionModel
    _temp_modifiers: Dict[str, float] = field(default_factory=dict, repr=False)

    def get_attribute(self, attr_path: str) -> Any:
        obj = self
        for part in attr_path.split('.'):
            obj = getattr(obj, part)
        return obj

    def apply_temp_mod(self, attr_path: str, modifier: float):
        original = self.get_attribute(attr_path)
        if attr_path not in self._temp_modifiers:
            self._temp_modifiers[attr_path] = original

        parts = attr_path.split('.')
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], max(0.0, min(1.0, modifier)))

    def reset_temp_mods(self):
        for attr_path, original_value in self._temp_modifiers.items():
            parts = attr_path.split('.')
            obj = self
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], original_value)
        self._temp_modifiers.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "cognitive": self.cognitive.to_dict(),
            "social": self.social.to_dict(),
            "world": self.world.to_dict()
        }

    def to_json(self, filepath: Optional[str] = None) -> str:
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        return json_str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCModel':
        return cls(
            name=data['name'],
            age=data.get('age', 0),
            cognitive=CognitiveModel.from_dict(data['cognitive']),
            social=SocialPersonalityModel.from_dict(data['social']),
            world=WorldPerceptionModel.from_dict(data['world'])
        )

    @classmethod
    def from_json(cls, json_source: str) -> 'NPCModel':
        try:
            with open(json_source, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, OSError):
            data = json.loads(json_source)
        return cls.from_dict(data)

# -----------------------------
# NPC Factory
# -----------------------------
class NPCFactory:
    @staticmethod
    def create_morisson_moses() -> NPCModel:
        return NPCModel(
            name="Morisson Moses",
            age=35,
            cognitive=CognitiveModel(self_esteem=0.8, locus_of_control=0.475, cog_flexibility=0.3),
            social=SocialPersonalityModel(
                assertion=1.0,
                conf_indep=0.7,
                empathy=0.45,
                ideology={"Utilitarianism": 0.8, "Authoritarianism": 0.2},
                wildcard="Martyr",
                faction="Insurgency",
                social_position=SocialPosition.BOSS
            ),
            world=WorldPerceptionModel(world_history="Full world history...", personal_history="Moses' personal journey...", player_history="", player_relation=0.5)
        )

# -----------------------------
# Usage Example
# -----------------------------
if __name__ == "__main__":
    moses = NPCFactory.create_morisson_moses()
    moses.to_json("moses.json")
    print(f"Created {moses.name}")
    print(f"Dominant ideology: {moses.social.get_dominant_ideology()}")

    loaded_moses = NPCModel.from_json("moses.json")
    print(f"\nLoaded {loaded_moses.name} from file")

    print(f"\nOriginal assertion: {moses.social.assertion}")
    moses.apply_temp_mod("social.assertion", 0.5)
    print(f"Modified assertion: {moses.social.assertion}")
    moses.reset_temp_mods()
    print(f"Reset assertion: {moses.social.assertion}")
