"""
Psychological Narrative Engine - Ollama Integration
Name: ollama_integration.py
Author: Jerome Bawa
"""

from typing import List
import requests
from .cognitive import ThoughtReaction
from .social import BehaviouralIntention
from .outcomes import InteractionOutcome
#from ..PNE_Models import SocialPersonalityModel  # for type clarity; optional

class OllamaResponseGenerator:
    """Generates NPC dialogue responses using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi3:mini"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def _build_ollama_options(self, npc) -> dict:
        """
        Compute Ollama options for this NPC, consulting the wildcard index.

        Priority:
        1. Start from engine defaults.
        2. Apply temp_offset (if present) relative to base temperature.
        3. Apply any absolute overrides from the wildcard config.
        """
        # 1. Base defaults
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
            # 2. Relative modifier for temperature
            base_temp = options.get("temperature", 0.85)
            temp_offset = wildcard_cfg.get("temp_offset")
            if isinstance(temp_offset, (int, float)):
                options["temperature"] = base_temp + float(temp_offset)

            # 3. Absolute overrides; ignore meta-keys like temp_offset
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
        conversation_history: List[str] = None
    ) -> str:
        """Generate NPC response using Ollama with full pipeline context"""
        
        prompt = self._build_prompt(
            npc, thought_reaction, behavioural_intention, 
            interaction_outcome, conversation_history
        )

        # Build options based on wildcard profile before sending to Ollama
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
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated = result.get("response", "").strip()
                if not generated:
                    return interaction_outcome.get_response(thought_reaction.emotional_valence)
                return generated
            else:
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
        conversation_history: List[str] = None
    ) -> str:
        """Build prompt with pipeline context"""
        
        prompt_parts = []
        prompt_parts.append("You are generating dialogue for an NPC. Respond only as the NPC.\n")
        
        prompt_parts.append(f"## NPC: {npc.name}")
        prompt_parts.append(f"Faction: {npc.social.faction}")
        prompt_parts.append(f"Dominant Ideology: {npc.social.get_dominant_ideology()}")
        
        prompt_parts.append(f"\n## INTERNAL STATE")
        prompt_parts.append(f"Private Thought: \"{thought_reaction.internal_thought}\"")
        prompt_parts.append(f"Intended Behavior: {behavioural_intention.intention_type}")
        prompt_parts.append(f"Confrontation Level: {behavioural_intention.confrontation_level:.2f}")
        
        prompt_parts.append(f"\n## RESPONSE GUIDANCE")
        prompt_parts.append(f"Negative variant: \"{interaction_outcome.min_response}\"")
        prompt_parts.append(f"Positive variant: \"{interaction_outcome.max_response}\"")
        prompt_parts.append(f"\nGenerate response as {npc.name} based on the above context:")
        
        return "\n".join(prompt_parts)