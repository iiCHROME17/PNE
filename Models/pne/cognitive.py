"""
Psychological Narrative Engine - Cognitive Interpretation Layer
Name: cognitive.py
Author: Jerome Bawa
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple
import requests
from .player_input import PlayerDialogueInput


@dataclass
class ThoughtReaction:
    """NPC's internal subjective thought (not spoken)"""
    internal_thought: str  # First-person emotional reaction
    subjective_belief: str  # What NPC interprets is happening
    cognitive_state: Dict[str, float]  # Updated cognitive attributes
    emotional_valence: float  # -1 (negative) to 1 (positive)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'internal_thought': self.internal_thought,
            'subjective_belief': self.subjective_belief,
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
        Generate subjective thought and belief using LLM based on cognitive distortions
        """
        # Generate internal thought + belief via LLM
        internal_thought, subjective_belief = self._generate_subjective_thought(player_input, npc)
        
        # Calculate emotional valence from tone analysis
        emotional_valence = self._calculate_emotional_valence(player_input, npc)
        
        cognitive_state = {
            'self_esteem': npc.cognitive.self_esteem,
            'locus_of_control': npc.cognitive.locus_of_control,
            'cog_flexibility': npc.cognitive.cog_flexibility
        }
        
        return ThoughtReaction(
            internal_thought=internal_thought,
            subjective_belief=subjective_belief,
            cognitive_state=cognitive_state,
            emotional_valence=emotional_valence
        )
    
    def _generate_subjective_thought(self, player_input: PlayerDialogueInput, npc) -> Tuple[str, str]:
        """
        Generate NPC's private interpretation of player's words using LLM
        Returns: (internal_thought, subjective_belief)
        """
        
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
                        "num_predict": 80  # Increased for two outputs
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()
                
                # Parse structured output
                thought = "What are they really saying...?"
                belief = "Their intentions are unclear"
                
                if "THOUGHT:" in raw_response and "BELIEF:" in raw_response:
                    lines = raw_response.split("\n")
                    for line in lines:
                        if line.startswith("THOUGHT:"):
                            thought = line.replace("THOUGHT:", "").strip()
                            if len(thought) > 75:
                                thought = thought[:72] + "..."
                        elif line.startswith("BELIEF:"):
                            belief = line.replace("BELIEF:", "").strip()
                            if len(belief) > 100:
                                belief = belief[:97] + "..."
                
                return thought, belief
            else:
                return "I need to process what they said...", "Their intentions are unclear"
        
        except Exception as e:
            print(f"[Cognitive Interpreter Error: {str(e)}]")
            return "What are they really saying...?", "Their intentions are unclear"
    
    def _build_thought_prompt(self, player_input: PlayerDialogueInput, npc) -> str:
        """Build prompt for generating subjective thought + belief"""
        
        prompt_parts = [
            "Generate NPC's internal reaction in this EXACT format:",
            "THOUGHT: [First-person emotional reaction, max 75 chars]",
            "BELIEF: [What NPC interprets is happening, max 100 chars]",
            "",
            f"NPC: {npc.name}",
            f"NPC Cognitive State:",
            f"- Self-Esteem: {npc.cognitive.self_esteem:.2f} (low=insecure, high=confident)",
            f"- Locus of Control: {npc.cognitive.locus_of_control:.2f} (low=blames others, high=self-responsible)",
            f"- Cognitive Flexibility: {npc.cognitive.cog_flexibility:.2f} (low=rigid thinking, high=open-minded)",
            "",
            f"Player said: \"{player_input.choice_text}\"",
            f"Rhetoric style: {player_input.language_art.value}",
            f"Empathy tone: {player_input.empathy_tone:.2f}",
            ""
        ]
        
        # Cognitive distortion hints
        if npc.cognitive.self_esteem < 0.4:
            prompt_parts.append("⚠ NPC has LOW self-esteem → interprets messages negatively, feels threatened")
        if npc.cognitive.locus_of_control < 0.5:
            prompt_parts.append("⚠ NPC has EXTERNAL locus → blames others, sees player as manipulative")
        if npc.cognitive.cog_flexibility < 0.4:
            prompt_parts.append("⚠ NPC is RIGID → resists new ideas, sees challenges as attacks")
        
        prompt_parts.append("\nExamples:")
        prompt_parts.append("THOUGHT: Pretty words, but can I trust them?")
        prompt_parts.append("BELIEF: They claim empathy but may be opportunistic")
        prompt_parts.append("")
        prompt_parts.append("THOUGHT: They sound genuine... maybe.")
        prompt_parts.append("BELIEF: They seem sincere but words are cheap")
        prompt_parts.append("")
        prompt_parts.append("Now generate for this NPC:")
        
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