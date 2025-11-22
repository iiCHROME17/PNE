# ============================================================================
# OUTCOME SYSTEM
# ============================================================================
class OutcomeType(Enum):
    """Types of dialogue outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    REFUSAL = "refusal"
    HELPED = "helped"
    ATTACKED = "attacked"

@dataclass
class Outcome:
    """Individual outcome configuration"""
    id: str
    outcome_type: OutcomeType
    min_response: str
    max_response: str
    scripted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'outcome_type': self.outcome_type.value,
            'min_response': self.min_response,
            'max_response': self.max_response,
            'scripted': self.scripted
        }

@dataclass
class OutcomeIndex:
    """Collection of outcomes for a dialogue choice"""
    choice_id: str
    outcomes: List[Outcome] = field(default_factory=list)
    
    def add_outcome(self, outcome: Outcome):
        """Add an outcome to the index"""
        self.outcomes.append(outcome)
    
    def get_outcome(self, outcome_id: str) -> Optional[Outcome]:
        """Retrieve specific outcome by ID"""
        for outcome in self.outcomes:
            if outcome.id == outcome_id:
                return outcome
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'choice_id': self.choice_id,
            'outcomes': [o.to_dict() for o in self.outcomes]
        }

class OutcomeResolver:
    """Resolves which outcome to use based on NPC state"""
    
    @staticmethod
    def calculate_outcome_score(
        npc,
        filtered_dialogue: FilteredDialogue,
        skill_check: Optional[SkillCheckResult]
    ) -> float:
        """
        Calculate outcome score (0-1) determining min/max interpolation
        Higher score = better outcome (closer to max_response)
        """
        score = 0.5  # Neutral baseline
        
        # Skill check impact (+/- 0.2)
        if skill_check:
            if skill_check.success:
                score += 0.2 + (skill_check.margin * 0.1)
            else:
                score -= 0.2
        
        # Emotional reaction impact (+/- 0.15)
        reaction_modifiers = {
            "receptive": 0.15,
            "neutral": 0.0,
            "defensive": -0.1,
            "hostile": -0.15
        }
        score += reaction_modifiers.get(filtered_dialogue.emotional_reaction, 0.0)
        
        # Trust modifier impact (+/- 0.15)
        score += filtered_dialogue.trust_modifier * 0.15
        
        # Ideological alignment impact (+/- 0.1)
        score += filtered_dialogue.ideological_alignment * 0.1
        
        # NPC empathy (high empathy = more forgiving)
        if npc.social.empathy > 0.7:
            score += 0.05
        
        # NPC cognitive flexibility (rigid = harsher)
        if npc.cognitive.cog_flexibility < 0.3:
            score -= 0.05
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def interpolate_response(outcome: Outcome, score: float) -> str:
        """
        Interpolate between min and max response based on score
        If scripted=True, use exact min (score<0.5) or max (score>=0.5)
        """
        if outcome.scripted:
            return outcome.max_response if score >= 0.5 else outcome.min_response
        
        # For non-scripted, we return guidance for LLM
        # The LLM will blend these responses based on the score
        return f"[Interpolate between MIN (score={score:.2f}): '{outcome.min_response}' and MAX: '{outcome.max_response}']"
    
    @staticmethod
    def resolve_outcome(
        outcome: Outcome,
        npc,
        filtered_dialogue: FilteredDialogue,
        skill_check: Optional[SkillCheckResult]
    ) -> Tuple[float, str]:
        """
        Resolve outcome to specific response
        Returns: (score, response_text)
        """
        score = OutcomeResolver.calculate_outcome_score(
            npc, filtered_dialogue, skill_check
        )
        response = OutcomeResolver.interpolate_response(outcome, score)
        return score, response

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
    outcome_score: Optional[float] = None
    selected_outcome: Optional[Outcome] = None
    generated_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'npc_name': self.npc_name,
            'npc_age': self.npc_age,
            'filtered_dialogue': self.filtered_dialogue.to_dict(),
            'skill_check': self.skill_check.to_dict() if self.skill_check else None,
            'cognitive_state': self.current_cognitive_state,
            'social_state': self.current_social_state,
            'outcome_score': self.outcome_score,
            'selected_outcome': self.selected_outcome.to_dict() if self.selected_outcome else None,
            'generated_response': self.generated_response
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)