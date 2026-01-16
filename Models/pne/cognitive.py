"""
Psychological Narrative Engine - Cognitive Interpretation Layer
Name: cognitive.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any
import requests
from .player_input import PlayerDialogueInput


@dataclass
class ThoughtReaction:
    """NPC's internal subjective thought (not spoken)"""
    internal_thought: str  # What NPC thinks privately
    cognitive_state: Dict[str, float]  # Updated cognitive attributes
    emotional_valence: float  # -1 (negative) to 1 (positive)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'internal_thought': self.internal_thought,
            'cognitive_state': self.cognitive_state,
            'emotional_valence': self.emotional_valence
        }


class CognitiveInterpreter:
    """Processes input through NPC's cognitive model"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """Initialize cognitive interpreter with LLM connection"""
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
    
    def interpret(self, player_input: PlayerDialogueInput, npc) -> ThoughtReaction:
        """
        Generate subjective thought using LLM based on cognitive distortions
        """
        # Generate internal thought via LLM
        internal_thought = self._generate_subjective_thought(player_input, npc)
        
        # Calculate emotional valence from tone analysis
        emotional_valence = self._calculate_emotional_valence(player_input, npc)
        
        cognitive_state = {
            'self_esteem': npc.cognitive.self_esteem,
            'locus_of_control': npc.cognitive.locus_of_control,
            'cog_flexibility': npc.cognitive.cog_flexibility
        }
        
        return ThoughtReaction(
            internal_thought=internal_thought,
            cognitive_state=cognitive_state,
            emotional_valence=emotional_valence
        )
    
    def _generate_subjective_thought(self, player_input: PlayerDialogueInput, npc) -> str:
        """Generate NPC's private interpretation of player's words using LLM"""
        
        prompt = self._build_thought_prompt(player_input, npc)
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 30  # Keep thoughts brief
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                thought = result.get("response", "").strip()
                # Truncate to 75 chars max
                if len(thought) > 75:
                    thought = thought[:72] + "..."
                return thought if thought else "I need to think about this..."
            else:
                return "I need to process what they said..."
        
        except Exception as e:
            print(f"[Cognitive Interpreter Error: {str(e)}]")
            return "What are they really saying...?"
    
    def _build_thought_prompt(self, player_input: PlayerDialogueInput, npc) -> str:
        """Build prompt for generating subjective thought"""
        
        prompt_parts = []
        prompt_parts.append("Generate ONLY the NPC's private internal thought (max 75 characters). This is what they THINK, not what they SAY.MAKE IT FIRST PERSON, FOCAL ON THEIR IMMEDIATE EMOTIONAL REACTION.\n")
        
        prompt_parts.append(f"NPC Cognitive State:")
        prompt_parts.append(f"- Self-Esteem: {npc.cognitive.self_esteem:.2f} (low=insecure, high=confident)")
        prompt_parts.append(f"- Locus of Control: {npc.cognitive.locus_of_control:.2f} (low=blames others, high=self-responsible)")
        prompt_parts.append(f"- Cognitive Flexibility: {npc.cognitive.cog_flexibility:.2f} (low=rigid, high=open-minded)")
        
        prompt_parts.append(f"\nPlayer said: \"{player_input.choice_text}\"")
        prompt_parts.append(f"Rhetoric style: {player_input.language_art.value}")
        
        # Cognitive distortion hints
        if npc.cognitive.self_esteem < 0.4:
            prompt_parts.append("\nNPC has LOW self-esteem: likely to interpret negatively, feel threatened or inadequate")
        if npc.cognitive.locus_of_control < 0.5:
            prompt_parts.append("NPC has EXTERNAL locus: likely to blame others, see player as controlling")
        if npc.cognitive.cog_flexibility < 0.4:
            prompt_parts.append("NPC is RIGID: likely to resist change, see challenge as attack")
        
        prompt_parts.append("\nGenerate NPC's private thought (under 75 chars):")
        
        return "\n".join(prompt_parts)
    
    def _calculate_emotional_valence(self, player_input: PlayerDialogueInput, npc) -> float:
        """Calculate emotional reaction based on cognitive state and input tones"""
        valence = 0.0
        
        # Low self-esteem reacts negatively to authority/manipulation
        if npc.cognitive.self_esteem < 0.4:
            valence -= (player_input.authority_tone * 0.3)
            valence -= (player_input.manipulation_tone * 0.5)
        
        # External locus attributes hostility to others
        if npc.cognitive.locus_of_control < 0.5:
            valence -= (player_input.authority_tone * 0.4)
        
        # High flexibility responds positively to diplomacy
        if npc.cognitive.cog_flexibility > 0.6:
            valence += (player_input.diplomacy_tone * 0.4)
            valence += (player_input.empathy_tone * 0.3)
        
        # Rigid thinking resists persuasion
        if npc.cognitive.cog_flexibility < 0.4:
            valence -= (player_input.diplomacy_tone * 0.2)
        
        return max(-1.0, min(1.0, valence))