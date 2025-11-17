"""
Psychological Narrative Engine - Dialogue Pipeline
Author: Jerome Bawa 

Handles player input, skill checks, cognitive filtering, and Ollama-powered response generation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
import random
import requests

# ============================================================================
# ENUMS
# ============================================================================

class LanguageArt(Enum):
    """Player Dialogue Approaches"""
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


# ============================================================================
# PLAYER INPUT STRUCTURES
# ============================================================================

@dataclass
class PlayerDialogueInput:
    """Structured Player dialogue"""
    choice_text: str
    language_art: LanguageArt
    contextual_references: List[str] = field(default_factory=list)
    
    # Parsed traits from choice text
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    ideology_alignment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_text": self.choice_text,
            "language_art": self.language_art.value,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "ideology_alignment": self.ideology_alignment,
            "contextual_references": self.contextual_references
        }


@dataclass
class PlayerSkillSet:
    """Player's skill proficiencies (0-10 scale)"""
    authority: int = 0
    diplomacy: int = 0
    empathy: int = 0
    manipulation: int = 0

    def __post_init__(self):
        """Validate skill values are within acceptable range"""
        for attr in ["authority", "diplomacy", "empathy", "manipulation"]:
            value = getattr(self, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} skill must be between 0 and 10, got {value}")
            
    def get_skill(self, skill: PlayerSkill) -> int:
        """Retrieve skill value by PlayerSkill enum"""
        skill_map = {
            PlayerSkill.AUTHORITY: self.authority,
            PlayerSkill.DIPLOMACY: self.diplomacy,
            PlayerSkill.EMPATHY: self.empathy,
            PlayerSkill.MANIPULATION: self.manipulation
        }
        return skill_map[skill]
    
    def get_skill_normalized(self, skill: PlayerSkill) -> float:
        """Get skill value normalized to 0-1 range"""
        return self.get_skill(skill) / 10.0


# ============================================================================
# SKILL CHECK SYSTEM
# ============================================================================

@dataclass
class SkillCheckResult:
    """Result of a skill check"""
    success: bool
    skill_used: PlayerSkill
    player_val: int
    threshold: float
    margin: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_used": self.skill_used.value,
            "player_val": self.player_val,
            "threshold": self.threshold,
            "margin": self.margin
        }


class SkillCheckSystem:
    """Handles skill checks based on player input and NPC modifier application"""
    
    # Map LanguageArt to PlayerSkill
    LANGUAGE_ART_TO_SKILL = {
        LanguageArt.CHALLENGE: PlayerSkill.AUTHORITY,
        LanguageArt.DIPLOMATIC: PlayerSkill.DIPLOMACY,
        LanguageArt.EMPATHETIC: PlayerSkill.EMPATHY,
        LanguageArt.MANIPULATIVE: PlayerSkill.MANIPULATION,
        LanguageArt.NEUTRAL: None
    }

    # Map skill to NPC attribute modifiers
    SKILL_MODIFIERS = {
        PlayerSkill.AUTHORITY: [
            ('social.assertion', lambda npc, margin: npc.social.assertion * (1 - margin * 0.5))
        ],
        PlayerSkill.MANIPULATION: [
            ('cognitive.self_esteem', lambda npc, margin: npc.cognitive.self_esteem * (1 - margin * 0.5))
        ],
        PlayerSkill.DIPLOMACY: [
            ('cognitive.cog_flexibility', lambda npc, margin: min(1.0, npc.cognitive.cog_flexibility * (1 + margin * 0.5)))
        ],
        PlayerSkill.EMPATHY: [
            ('social.empathy', lambda npc, margin: min(1.0, npc.social.empathy * (1 + margin * 0.5)))
        ]
    }

    @staticmethod
    def calc_threshold(npc, skill: PlayerSkill) -> float:
        """Calculate skill check threshold based on NPC attributes.
        Higher NPC attributes make checks harder."""

        if skill == PlayerSkill.AUTHORITY:
            # High Assertion = hard to intimidate
            return 0.3 + (npc.social.assertion * 0.4)
        
        elif skill == PlayerSkill.MANIPULATION:
            # High Self-Esteem = hard to manipulate
            return 0.2 + (npc.cognitive.self_esteem * 0.5)
        
        elif skill == PlayerSkill.EMPATHY:
            # High Empathy = Easy to connect with
            return 0.4 - (npc.social.empathy * 0.2)
        
        elif skill == PlayerSkill.DIPLOMACY:
            # High Cognitive Flexibility = Easy to persuade
            return 0.3 - (npc.cognitive.cog_flexibility * 0.3)
        
        return 0.5  # Neutral baseline

    @staticmethod
    def perform_check(
        player_input: PlayerDialogueInput,
        player_skills: PlayerSkillSet,
        npc
    ) -> Optional[SkillCheckResult]:
        """Perform skill check based on player input and NPC attributes.
        Returns None if language art doesn't trigger skill check."""

        skill = SkillCheckSystem.LANGUAGE_ART_TO_SKILL.get(player_input.language_art)
        if skill is None:
            return None
        
        player_val = player_skills.get_skill(skill)
        threshold = SkillCheckSystem.calc_threshold(npc, skill)

        # Determine success with randomness
        roll = random.uniform(-0.1, 0.1)  # Small randomness factor
        eff_val = (player_val / 10.0) + roll  # Normalize skill to [0,1]

        success = eff_val >= threshold
        margin = eff_val - threshold

        return SkillCheckResult(
            success=success,
            skill_used=skill,
            player_val=player_val,
            threshold=threshold,
            margin=margin
        )

    @staticmethod
    def apply_modifiers(npc, check_result: SkillCheckResult):
        """Apply NPC attribute modifiers based on skill check result"""
        if not check_result.success:
            return
        
        modifiers = SkillCheckSystem.SKILL_MODIFIERS.get(check_result.skill_used, [])

        for attr_path, mod_func in modifiers:
            new_value = mod_func(npc, abs(check_result.margin))
            npc.apply_temp_mod(attr_path, new_value)


# ============================================================================
# COGNITIVE FILTER SYSTEM
# ============================================================================

@dataclass
class FilteredDialogue:
    """Player dialogue after NPC cognitive filtering"""
    original_input: PlayerDialogueInput
    perceived_authority: float
    perceived_diplomacy: float
    perceived_empathy: float
    perceived_manipulation: float
    trust_modifier: float  # -1 to 1
    ideological_alignment: float  # -1 to 1
    emotional_reaction: str  # "defensive", "receptive", "neutral", "hostile"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_text': self.original_input.choice_text,
            'perceived_authority': self.perceived_authority,
            'perceived_diplomacy': self.perceived_diplomacy,
            'perceived_empathy': self.perceived_empathy,
            'perceived_manipulation': self.perceived_manipulation,
            'trust_modifier': self.trust_modifier,
            'ideological_alignment': self.ideological_alignment,
            'emotional_reaction': self.emotional_reaction
        }


class CognitiveFilter:
    """Filters player input through NPC's cognitive and social models"""
    
    @staticmethod
    def filter(player_input: PlayerDialogueInput, npc) -> FilteredDialogue:
        """Process player input through NPC's perceptual filters"""
        
        # Base perception from input
        perceived_authority = player_input.authority_tone
        perceived_diplomacy = player_input.diplomacy_tone
        perceived_empathy = player_input.empathy_tone
        perceived_manipulation = player_input.manipulation_tone
        
        # Modify based on NPC's locus of control
        # External locus = attributes more to player's nature (amplifies perceptions)
        if npc.cognitive.locus_of_control < 0.5:
            perceived_authority *= 1.3
            perceived_manipulation *= 1.2
        
        # Trust modifier from player history and relation
        trust_modifier = CognitiveFilter._calculate_trust(npc, player_input)
        
        # Ideological alignment check
        ideological_alignment = CognitiveFilter._check_ideology(npc, player_input)
        
        # Emotional reaction based on filtered perceptions
        emotional_reaction = CognitiveFilter._determine_reaction(
            npc, perceived_authority, perceived_diplomacy, 
            perceived_empathy, trust_modifier, ideological_alignment
        )
        
        return FilteredDialogue(
            original_input=player_input,
            perceived_authority=min(1.0, perceived_authority),
            perceived_diplomacy=min(1.0, perceived_diplomacy),
            perceived_empathy=min(1.0, perceived_empathy),
            perceived_manipulation=min(1.0, perceived_manipulation),
            trust_modifier=trust_modifier,
            ideological_alignment=ideological_alignment,
            emotional_reaction=emotional_reaction
        )
    
    @staticmethod
    def _calculate_trust(npc, player_input: PlayerDialogueInput) -> float:
        """Calculate trust modifier based on relation and context"""
        base_trust = npc.world.player_relation
        
        # Check for contextual references that might affect trust
        for ref in player_input.contextual_references:
            if npc.social.faction and npc.social.faction.lower() in ref.lower():
                base_trust += 0.1
        
        return max(-1.0, min(1.0, base_trust * 2 - 1))  # Scale to -1 to 1
    
    @staticmethod
    def _check_ideology(npc, player_input: PlayerDialogueInput) -> float:
        """Check if player's implied ideology aligns with NPC"""
        if not player_input.ideology_alignment or not npc.social.ideology:
            return 0.0
        
        player_ideology = player_input.ideology_alignment
        
        # Check if player ideology matches NPC's ideologies
        if player_ideology in npc.social.ideology:
            return npc.social.ideology[player_ideology]
        
        return 0.0
    
    @staticmethod
    def _determine_reaction(
        npc, authority: float, diplomacy: float, 
        empathy: float, trust: float, ideology: float
    ) -> str:
        """Determine NPC's emotional reaction to filtered input"""
        
        # High assertion NPC reacts negatively to authority
        if npc.social.assertion > 0.7 and authority > 0.7:
            if trust < 0:
                return "hostile"
            return "defensive"
        
        # Low self-esteem with high authority
        if npc.cognitive.self_esteem < 0.4 and authority > 0.6:
            return "defensive"
        
        # High empathy NPC responds to empathy
        if npc.social.empathy > 0.6 and empathy > 0.6:
            return "receptive"
        
        # Diplomatic approach with flexible NPC
        if npc.cognitive.cog_flexibility > 0.6 and diplomacy > 0.6:
            return "receptive"
        
        # Ideological alignment
        if ideology > 0.5:
            return "receptive"
        elif ideology < -0.5:
            return "hostile"
        
        # Trust-based
        if trust > 0.5:
            return "receptive"
        elif trust < -0.5:
            return "hostile"
        
        return "neutral"


# ============================================================================
# OLLAMA INTEGRATION
# ============================================================================

class OllamaResponseGenerator:
    """Generates NPC dialogue responses using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model to use (default: qwen2.5:3b)
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
    
    def generate_response(
        self,
        npc,
        filtered_dialogue: FilteredDialogue,
        skill_check: Optional[SkillCheckResult],
        conversation_history: List[str] = None
    ) -> str:
        """
        Generate NPC response using Ollama
        
        Args:
            npc: NPCModel instance
            filtered_dialogue: FilteredDialogue after cognitive processing
            skill_check: SkillCheckResult (if applicable)
            conversation_history: Previous dialogue exchanges
        
        Returns:
            Generated NPC response text
        """
        
        # Build context-rich prompt
        prompt = self._build_prompt(npc, filtered_dialogue, skill_check, conversation_history)
        
        try:
            # Debug: Print attempting connection
            print(f"  → Connecting to Ollama at {self.base_url}...")
            print(f"  → Using model: {self.model}")
            
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_predict": 150
                    }
                },
                timeout=60  # Increased timeout for first load
            )
            
            print(f"  → Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated = result.get("response", "").strip()
                if not generated:
                    return "[Error: Empty response from Ollama]"
                return generated
            elif response.status_code == 404:
                return f"[Error: Model '{self.model}' not found. Run: ollama pull {self.model}]"
            else:
                error_detail = response.text[:200] if response.text else "No details"
                return f"[Error: Ollama returned {response.status_code} - {error_detail}]"
        
        except requests.exceptions.Timeout:
            return f"[Error: Request timeout - Ollama took too long to respond]"
        except requests.exceptions.ConnectionError:
            return f"[Error: Cannot connect to Ollama at {self.base_url}. Is it running?]"
        except requests.exceptions.RequestException as e:
            return f"[Error: Request failed - {str(e)}]"
        except Exception as e:
            return f"[Error: Unexpected error - {str(e)}]"
    
    def _build_prompt(
        self,
        npc,
        filtered_dialogue: FilteredDialogue,
        skill_check: Optional[SkillCheckResult],
        conversation_history: List[str] = None
    ) -> str:
        """Build comprehensive prompt for Ollama"""
        
        prompt_parts = []
        
        # System context
        prompt_parts.append("You are generating dialogue for an NPC in a narrative game.Respond only as the NPC. Do NOT mention your internal thoughts, reasoning, or game mechanics.  Focus only on natural speech that the character would realistically say.\n")
        
        # NPC profile
        prompt_parts.append(f"## NPC PROFILE")
        prompt_parts.append(f"Name: {npc.name}")
        prompt_parts.append(f"Age: {npc.age}")
        prompt_parts.append(f"Faction: {npc.social.faction}")
        prompt_parts.append(f"Position: {npc.social.social_position.value}")
        prompt_parts.append(f"Dominant Ideology: {npc.social.get_dominant_ideology()}")
        if npc.social.wildcard:
            prompt_parts.append(f"Psychological Trait: {npc.social.wildcard}")
        
        # Personality state
        prompt_parts.append(f"\n## PERSONALITY STATE")
        prompt_parts.append(f"Self-Esteem: {npc.cognitive.self_esteem:.2f} (0=low, 1=high)")
        prompt_parts.append(f"Assertion: {npc.social.assertion:.2f} (0=passive, 1=assertive)")
        prompt_parts.append(f"Empathy: {npc.social.empathy:.2f} (0=self-focused, 1=empathetic)")
        prompt_parts.append(f"Cognitive Flexibility: {npc.cognitive.cog_flexibility:.2f} (0=rigid, 1=adaptive)")
        
        # Relationship context
        prompt_parts.append(f"\n## RELATIONSHIP")
        prompt_parts.append(f"Relation with Player: {npc.world.player_relation:.2f} (0=hostile, 1=friendly)")
        if npc.world.player_history:
            prompt_parts.append(f"Player History: {npc.world.player_history}")
        
        # Current emotional state
        prompt_parts.append(f"\n## CURRENT EMOTIONAL STATE")
        prompt_parts.append(f"Emotional Reaction: {filtered_dialogue.emotional_reaction.upper()}")
        prompt_parts.append(f"Trust Level: {filtered_dialogue.trust_modifier:+.2f}")
        
        # Skill check result
        if skill_check:
            prompt_parts.append(f"\n## SKILL CHECK")
            prompt_parts.append(f"Player used: {skill_check.skill_used.value}")
            prompt_parts.append(f"Result: {'SUCCESS' if skill_check.success else 'FAILURE'}")
            if skill_check.success:
                prompt_parts.append(f"Effect: You feel slightly influenced by the player's approach")
        
        # Conversation history
        if conversation_history:
            prompt_parts.append(f"\n## CONVERSATION HISTORY")
            for line in conversation_history[-3:]:  # Last 3 exchanges
                prompt_parts.append(line)
        
        # Player's current statement
        prompt_parts.append(f"\n## PLAYER SAYS")
        prompt_parts.append(f'"{filtered_dialogue.original_input.choice_text}"')
        
        # Response instructions
        prompt_parts.append(f"\n## YOUR RESPONSE")
        prompt_parts.append(f"Respond as {npc.name}, considering your emotional state ({filtered_dialogue.emotional_reaction}), personality traits, and relationship with the player.")
        prompt_parts.append(f"Keep response under 100 words. Be authentic to the character.")
        
        if filtered_dialogue.emotional_reaction == "hostile":
            prompt_parts.append("You are feeling hostile. Be confrontational but stay in character.")
        elif filtered_dialogue.emotional_reaction == "defensive":
            prompt_parts.append("You are feeling defensive. Push back against the player's approach.")
        elif filtered_dialogue.emotional_reaction == "receptive":
            prompt_parts.append("You are feeling receptive. Be more open to the player's perspective.")
        
        prompt_parts.append(f"\nResponse:")
        
        return "\n".join(prompt_parts)


# ============================================================================
# RESPONSE CONTEXT
# ============================================================================

@dataclass
class ResponseContext:
    """Complete context for NPC response"""
    npc_name: str
    npc_age: int
    filtered_dialogue: FilteredDialogue
    skill_check: Optional[SkillCheckResult]
    current_cognitive_state: Dict[str, float]
    current_social_state: Dict[str, Any]
    generated_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'npc_name': self.npc_name,
            'npc_age': self.npc_age,
            'filtered_dialogue': self.filtered_dialogue.to_dict(),
            'skill_check': self.skill_check.to_dict() if self.skill_check else None,
            'cognitive_state': self.current_cognitive_state,
            'social_state': self.current_social_state,
            'generated_response': self.generated_response
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DIALOGUE PROCESSOR
# ============================================================================

class DialogueProcessor:
    """Main processor coordinating all pipeline stages"""
    
    def __init__(
        self, 
        npc, 
        player_skills: PlayerSkillSet,
        use_ollama: bool = True,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b"
    ):
        self.npc = npc
        self.player_skills = player_skills
        self.conversation_history: List[str] = []
        
        # Ollama integration
        self.use_ollama = use_ollama
        if use_ollama:
            self.ollama = OllamaResponseGenerator(ollama_url, ollama_model)
        else:
            self.ollama = None
    
    def process_dialogue(
        self, 
        player_input: PlayerDialogueInput,
        generate_response: bool = True
    ) -> ResponseContext:
        """
        Complete pipeline: Input -> Skill Check -> Filtering -> Response
        
        Args:
            player_input: Player's dialogue choice
            generate_response: Whether to generate NPC response using Ollama
        """
        
        # Stage 1: Skill Check
        skill_check = SkillCheckSystem.perform_check(
            player_input, 
            self.player_skills, 
            self.npc
        )
        
        # Apply modifiers if skill check succeeded
        if skill_check and skill_check.success:
            SkillCheckSystem.apply_modifiers(self.npc, skill_check)
        
        # Stage 2: Cognitive Filtering
        filtered = CognitiveFilter.filter(player_input, self.npc)
        
        # Stage 3: Build Response Context
        context = ResponseContext(
            npc_name=self.npc.name,
            npc_age=self.npc.age,
            filtered_dialogue=filtered,
            skill_check=skill_check,
            current_cognitive_state={
                'self_esteem': self.npc.cognitive.self_esteem,
                'locus_of_control': self.npc.cognitive.locus_of_control,
                'cog_flexibility': self.npc.cognitive.cog_flexibility
            },
            current_social_state={
                'assertion': self.npc.social.assertion,
                'conf_indep': self.npc.social.conf_indep,
                'empathy': self.npc.social.empathy,
                'dominant_ideology': self.npc.social.get_dominant_ideology(),
                'faction': self.npc.social.faction,
                'social_position': self.npc.social.social_position.value
            }
        )
        
        # Stage 4: Generate Response (if requested and Ollama enabled)
        if generate_response and self.use_ollama and self.ollama:
            response = self.ollama.generate_response(
                self.npc,
                filtered,
                skill_check,
                self.conversation_history
            )
            context.generated_response = response
            
            # Add to conversation history
            self.conversation_history.append(f"Player: {player_input.choice_text}")
            self.conversation_history.append(f"{self.npc.name}: {response}")
        
        return context
    
    def end_conversation(self):
        """Reset temporary modifiers after conversation ends"""
        self.npc.reset_temp_mods()
        self.conversation_history.clear()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import sys
    import os

    # Import NPC models
    try:
        from PNE_Models import NPCFactory
    except ImportError:
        print("Error: Cannot import PNE_Models. Make sure it's in the same directory.")
        sys.exit(1)

    # Create NPCs
    moses = NPCFactory.create_morisson_moses()
    amourie = NPCFactory.create_amourie_othella()
    krakk = NPCFactory.create_krystian_krakk()
    
    npc_options = {
        "1": moses,
        "2": amourie,
        "3": krakk
    }

    # Create player skills
    player_skills = PlayerSkillSet(
        authority=2,
        manipulation=10,
        empathy=2,
        diplomacy=2
    )

    while True:
        print("\nSelect NPC for dialogue test (or 'q' to quit):")
        print("1. Moses")
        print("2. Amourie")
        print("3. Krakk")
        choice = input("Enter number: ").strip()

        if choice.lower() == "q":
            print("Exiting dialogue test.")
            break

        selected_npc = npc_options.get(choice)
        if not selected_npc:
            print("Invalid choice. Please try again.")
            continue

        print("=" * 70)
        print(f"DIALOGUE PIPELINE TEST - {selected_npc.name.upper()}")
        print("=" * 70)

        print(f"\n✓ NPC: {selected_npc.name}")
        print(f"✓ Player Skills: Manipulation={player_skills.manipulation}/10, "
              f"Diplomacy={player_skills.diplomacy}/10\n")

        # Initialize processor with Ollama
        processor = DialogueProcessor(
            selected_npc,
            player_skills,
            use_ollama=True,
            ollama_model="qwen2.5:3b"
        )

        # Test dialogue
        print("=" * 70)
        print("TEST: Challenging Dialogue")
        print("=" * 70)

        player_choice = PlayerDialogueInput(
            choice_text="You humans didn't want to listen to Cherubians and now the land is fucked up. Another one came and you wont listen to them? Do you think I'm telling you shit for my own ego? I'm trying to save you so fucking listen to me.",
            language_art=LanguageArt.MANIPULATIVE,
            authority_tone=0.5,
            diplomacy_tone=0.2,
            empathy_tone=0.1,
            manipulation_tone=0.85,
            contextual_references=[]
        )

        print(f"\nPlayer: {player_choice.choice_text}\n")

        # Process with Ollama response generation
        context = processor.process_dialogue(player_choice, generate_response=True)

        print(f"Skill Check:")
        if context.skill_check:
            print(f"  • Skill: {context.skill_check.skill_used.value}")
            print(f"  • Success: {context.skill_check.success}")
            print(f"  • Player Value: {context.skill_check.player_val}/10")
            print(f"  • Threshold: {context.skill_check.threshold:.2f}")
            print(f"  • Margin: {context.skill_check.margin:+.2f}")

        print(f"\nNPC Reaction:")
        print(f"  • Emotional State: {context.filtered_dialogue.emotional_reaction.upper()}")
        print(f"  • Trust Level: {context.filtered_dialogue.trust_modifier:+.2f}")

        if context.generated_response:
            print(f"\n{selected_npc.name}: {context.generated_response}")

        # End conversation
        processor.end_conversation()
        print(f"\n✓ Conversation ended, modifiers reset\n")
        print("=" * 70)
