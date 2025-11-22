"""
Psychological Narrative Engine - Core Models with Outcome System
Author: Jerome Bawa

A modular narrative engine backend for dynamic NPC behavior with outcome handling
Compatible with Unity, Unreal Engine, and Godot
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SocialPosition(Enum):
    """NPC rank within faction"""
    BOSS = "Boss"
    VICE = "Vice"
    HIGHER = "Higher"
    MEMBER = "Member"


class OutcomeType(Enum):
    """Types of outcomes from dialogue/action choices"""
    SUCCESS = "Success"
    FAILURE = "Failure"
    NEUTRAL = "Neutral"
    REFUSAL = "Refusal"
    HELPED = "Helped"
    ATTACKED = "Attacked"


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
        return cls(
            world_history=data.get('world_history', ""),
            personal_history=data.get('personal_history', ""),
            player_history=data.get('player_history', ""),
            player_relation=data.get('player_relation', 0.5)
        )


# ============================================================================
# OUTCOME SYSTEM
# ============================================================================

@dataclass
class Outcome:
    """
    Represents a single possible outcome from a dialogue choice or action
    """
    id: str  # Identifier like "door_interaction", "npc_encouragement"
    outcome_type: OutcomeType  # SUCCESS, FAILURE, NEUTRAL, etc.
    min_response: str  # Worst-case or hostile reaction
    max_response: str  # Best-case or cooperative reaction
    scripted: bool = False  # If true, only use min or max with no interpolation
    
    # Optional: Relation change triggered by this outcome
    relation_delta: Optional[float] = None
    
    # Optional: Attribute modifiers applied when this outcome triggers
    attribute_modifiers: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.outcome_type, str):
            self.outcome_type = OutcomeType(self.outcome_type)
    
    def get_interpolated_response(self, npc_model: 'NPCModel') -> str:
        """
        Generate a response based on NPC's psychological state
        If scripted=True, returns min or max based on relation
        If scripted=False, interpolates between min and max
        """
        if self.scripted:
            # Use relation to pick min or max
            return self.max_response if npc_model.world.player_relation > 0.5 else self.min_response
        
        # Calculate interpolation factor based on NPC psychology
        factor = self._calculate_response_factor(npc_model)
        
        # For now, return weighted choice (in production, this could blend text)
        return self.max_response if factor > 0.5 else self.min_response
    
    def _calculate_response_factor(self, npc_model: 'NPCModel') -> float:
        """
        Calculate 0-1 factor for response interpolation based on NPC state
        Higher values favor max_response, lower values favor min_response
        """
        # Weight factors
        relation_weight = 0.4
        empathy_weight = 0.2
        assertion_weight = 0.2
        flexibility_weight = 0.2
        
        # Calculate weighted average
        factor = (
            npc_model.world.player_relation * relation_weight +
            npc_model.social.empathy * empathy_weight +
            (1.0 - npc_model.social.assertion) * assertion_weight +
            npc_model.cognitive.cog_flexibility * flexibility_weight
        )
        
        return max(0.0, min(1.0, factor))
    
    def apply_effects(self, npc_model: 'NPCModel'):
        """Apply relation changes and attribute modifiers to NPC"""
        if self.relation_delta is not None:
            npc_model.world.update_relation(self.relation_delta)
        
        for attr_path, value in self.attribute_modifiers.items():
            npc_model.apply_temp_mod(attr_path, value)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['outcome_type'] = self.outcome_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Outcome':
        if 'outcome_type' in data:
            data['outcome_type'] = OutcomeType(data['outcome_type'])
        return cls(**data)


@dataclass
class OutcomeIndex:
    """
    Maps a dialogue choice or action to its possible outcomes
    """
    choice_id: str  # Identifier for the choice triggering these outcomes
    outcomes: List[Outcome] = field(default_factory=list)
    
    # Optional: Conditions that must be met for this choice to be available
    requires_relation_min: Optional[float] = None
    requires_faction: Optional[str] = None
    
    def add_outcome(self, outcome: Outcome):
        """Add an outcome to this choice"""
        self.outcomes.append(outcome)
    
    def get_outcome_by_type(self, outcome_type: OutcomeType) -> Optional[Outcome]:
        """Retrieve a specific outcome by type"""
        for outcome in self.outcomes:
            if outcome.outcome_type == outcome_type:
                return outcome
        return None
    
    def is_available(self, npc_model: 'NPCModel') -> bool:
        """Check if this choice is available based on NPC state"""
        if self.requires_relation_min is not None:
            if npc_model.world.player_relation < self.requires_relation_min:
                return False
        
        if self.requires_faction is not None:
            if npc_model.social.faction != self.requires_faction:
                return False
        
        return True
    
    def execute_outcome(self, outcome_type: OutcomeType, npc_model: 'NPCModel') -> Optional[str]:
        """
        Execute a specific outcome and return the response text
        Returns None if outcome type doesn't exist
        """
        outcome = self.get_outcome_by_type(outcome_type)
        if not outcome:
            return None
        
        response = outcome.get_interpolated_response(npc_model)
        outcome.apply_effects(npc_model)
        
        return response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'choice_id': self.choice_id,
            'outcomes': [o.to_dict() for o in self.outcomes],
            'requires_relation_min': self.requires_relation_min,
            'requires_faction': self.requires_faction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutcomeIndex':
        outcomes = [Outcome.from_dict(o) for o in data.get('outcomes', [])]
        return cls(
            choice_id=data['choice_id'],
            outcomes=outcomes,
            requires_relation_min=data.get('requires_relation_min'),
            requires_faction=data.get('requires_faction')
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
            with open(json_source, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, OSError):
            data = json.loads(json_source)
        
        return cls.from_dict(data)


# ============================================================================
# DIALOGUE MANAGER
# ============================================================================

class DialogueManager:
    """
    Manages dialogue choices and outcomes for NPCs
    """
    def __init__(self):
        self.outcome_indices: Dict[str, OutcomeIndex] = {}
    
    def register_choice(self, outcome_index: OutcomeIndex):
        """Register a dialogue choice with its outcomes"""
        self.outcome_indices[outcome_index.choice_id] = outcome_index
    
    def get_available_choices(self, npc_model: NPCModel) -> List[str]:
        """Get list of choice IDs available for this NPC"""
        return [
            choice_id for choice_id, index in self.outcome_indices.items()
            if index.is_available(npc_model)
        ]
    
    def execute_choice(
        self, 
        choice_id: str, 
        outcome_type: OutcomeType, 
        npc_model: NPCModel
    ) -> Optional[str]:
        """
        Execute a dialogue choice with specific outcome type
        Returns the NPC's response or None if invalid
        """
        if choice_id not in self.outcome_indices:
            return None
        
        outcome_index = self.outcome_indices[choice_id]
        return outcome_index.execute_outcome(outcome_type, npc_model)
    
    def load_from_json(self, filepath: str):
        """Load dialogue choices from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for choice_data in data.get('choices', []):
            outcome_index = OutcomeIndex.from_dict(choice_data)
            self.register_choice(outcome_index)
    
    def save_to_json(self, filepath: str):
        """Save all dialogue choices to JSON file"""
        data = {
            'choices': [idx.to_dict() for idx in self.outcome_indices.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dumps(data, f, indent=2)


# ============================================================================
# EXAMPLE FACTORIES
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


class OutcomeFactory:
    """Factory for creating example outcome indices"""
    
    @staticmethod
    def create_door_interaction() -> OutcomeIndex:
        """Example: Player tries to get NPC to open a door"""
        index = OutcomeIndex(choice_id="ask_open_door")
        
        index.add_outcome(Outcome(
            id="door_success",
            outcome_type=OutcomeType.SUCCESS,
            min_response="Fine. I'll open it. But you owe me.",
            max_response="Of course! Let me get that for you right away.",
            relation_delta=0.05
        ))
        
        index.add_outcome(Outcome(
            id="door_refusal",
            outcome_type=OutcomeType.REFUSAL,
            min_response="Absolutely not. I don't trust you.",
            max_response="I'm sorry, I can't do that right now.",
            relation_delta=-0.05
        ))
        
        return index
    
    @staticmethod
    def create_faction_recruitment() -> OutcomeIndex:
        """Example: Player tries to recruit NPC to their faction"""
        index = OutcomeIndex(
            choice_id="recruit_to_faction",
            requires_relation_min=0.6
        )
        
        index.add_outcome(Outcome(
            id="recruit_success",
            outcome_type=OutcomeType.SUCCESS,
            min_response="I'll join you, but I have conditions.",
            max_response="I've been waiting for you to ask. Count me in!",
            scripted=False,
            relation_delta=0.15,
            attribute_modifiers={"social.conf_indep": 0.4}
        ))
        
        index.add_outcome(Outcome(
            id="recruit_failure",
            outcome_type=OutcomeType.FAILURE,
            min_response="You must be joking. I would never betray my people.",
            max_response="I appreciate the offer, but my loyalty lies elsewhere.",
            relation_delta=-0.1
        ))
        
        return index


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("=== Narrative Engine with Outcome System ===\n")
    
    # Create NPC
    moses = NPCFactory.create_morisson_moses()
    print(f"✓ Created {moses.name}")
    print(f"  Faction: {moses.social.faction}")
    print(f"  Initial Relation: {moses.world.player_relation}\n")
    
    # Create dialogue manager
    dialogue_mgr = DialogueManager()
    
    # Register dialogue choices
    door_choice = OutcomeFactory.create_door_interaction()
    recruit_choice = OutcomeFactory.create_faction_recruitment()
    
    dialogue_mgr.register_choice(door_choice)
    dialogue_mgr.register_choice(recruit_choice)
    
    print("=== Testing Door Interaction ===\n")
    
    # Try door interaction (should work)
    response = dialogue_mgr.execute_choice(
        "ask_open_door",
        OutcomeType.SUCCESS,
        moses
    )
    print(f"Player asks Moses to open door...")
    print(f"Moses: \"{response}\"")
    print(f"Relation after: {moses.world.player_relation}\n")
    
    print("=== Testing Recruitment (Insufficient Relation) ===\n")
    
    # Check available choices (recruitment shouldn't be available yet)
    available = dialogue_mgr.get_available_choices(moses)
    print(f"Available choices: {available}")
    print(f"Note: 'recruit_to_faction' requires relation >= 0.6\n")
    
    # Improve relation
    print("=== Improving Relation ===\n")
    moses.world.update_relation(0.15)
    print(f"Relation improved to: {moses.world.player_relation}")
    
    # Now recruitment should be available
    available = dialogue_mgr.get_available_choices(moses)
    print(f"Available choices: {available}\n")
    
    print("=== Testing Recruitment (Success) ===\n")
    response = dialogue_mgr.execute_choice(
        "recruit_to_faction",
        OutcomeType.SUCCESS,
        moses
    )
    print(f"Player: 'Join our cause, Moses.'")
    print(f"Moses: \"{response}\"")
    print(f"Relation after: {moses.world.player_relation}")
    print(f"Independence modified: {moses.social.conf_indep}\n")
    
    # Reset temporary modifiers
    moses.reset_temp_mods()
    print(f"After conversation reset:")
    print(f"Independence restored: {moses.social.conf_indep}\n")
    
    print("✓ All tests passed!")