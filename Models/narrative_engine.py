"""
Psychological Narrative Engine - Conversation Engine
name: narrative_engine.py
Author: Jerome Bawa

Simulates dialogue interactions between player and NPCs using JSON-defined scenarios
Integrates with pipeline.py's Purpose-Output Model
"""

from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import dataclass, field
from pathlib import Path

# Import from pipeline and models
from pipeline import (
    DialogueProcessor, NPCIntent, OutcomeIndex, InteractionOutcome,
    TerminalOutcome, TerminalOutcomeType, PlayerDialogueInput,
    PlayerSkillSet, LanguageArt, ConversationModel
)
from PNE_Models import NPCModel


# ============================================================================
# CONVERSATION STATE
# ============================================================================

@dataclass
class ConversationState:
    """Tracks the state of an ongoing conversation"""
    npc: NPCModel
    processor: DialogueProcessor
    current_node: str = "start"
    scenario_id: str = ""  # Store scenario_id for easy access
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    choices_made: List[str] = field(default_factory=list)
    turn_count: int = 0
    is_complete: bool = False
    terminal_result: Optional[str] = None
    
    def add_exchange(self, speaker: str, text: str, metadata: Optional[Dict] = None):
        """Add a dialogue exchange to history"""
        entry = {
            "turn": self.turn_count,
            "speaker": speaker,
            "text": text
        }
        if metadata:
            entry["metadata"] = metadata
        
        self.conversation_history.append(entry)
        
        if speaker == "Player":
            self.turn_count += 1
    
    def get_history_text(self) -> str:
        """Format conversation history as readable text"""
        lines = []
        for exchange in self.conversation_history:
            speaker = exchange["speaker"]
            text = exchange["text"]
            turn = exchange.get("turn", "")
            prefix = f"[Turn {turn}] " if turn else ""
            lines.append(f"{prefix}{speaker}: {text}")
        return "\n".join(lines)
    
    def mark_complete(self, terminal_result: str):
        """Mark conversation as complete with terminal outcome"""
        self.is_complete = True
        self.terminal_result = terminal_result


# ============================================================================
# SCENARIO NODE
# ============================================================================

@dataclass
class DialogueNode:
    """Represents a node in the conversation tree"""
    node_id: str
    npc_dialogue: Optional[str] = None
    choices: List[Dict[str, Any]] = field(default_factory=list)
    is_terminal: bool = False
    terminal_condition: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueNode':
        """Create DialogueNode from dictionary"""
        return cls(
            node_id=data['id'],
            npc_dialogue=data.get('npc_dialogue'),
            choices=data.get('choices', []),
            is_terminal=data.get('is_terminal', False),
            terminal_condition=data.get('terminal_condition')
        )


# ============================================================================
# SCENARIO LOADER
# ============================================================================

class ScenarioLoader:
    """Loads and parses JSON scenario files"""
    
    @staticmethod
    def load_scenario(filepath: str) -> Dict[str, Any]:
        """Load scenario from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def parse_npc_intent(data: Dict[str, Any]) -> NPCIntent:
        """Parse NPC intent from scenario data"""
        return NPCIntent(
            baseline_belief=data.get('baseline_belief', ''),
            long_term_desire=data.get('long_term_desire', ''),
            immediate_intention=data.get('immediate_intention', ''),
            stakes=data.get('stakes', '')
        )
    
    @staticmethod
    def parse_outcome_index(choice_data: Dict[str, Any]) -> OutcomeIndex:
        """Parse outcome index from choice data"""
        # Parse interaction outcomes
        interaction_outcomes = []
        for outcome_data in choice_data.get('interaction_outcomes', []):
            interaction_outcomes.append(InteractionOutcome(
                outcome_id=outcome_data['outcome_id'],
                stance_delta=outcome_data.get('stance_delta', {}),
                relation_delta=outcome_data.get('relation_delta', 0.0),
                intention_shift=outcome_data.get('intention_shift'),
                min_response=outcome_data['min_response'],
                max_response=outcome_data['max_response'],
                scripted=outcome_data.get('scripted', False)
            ))
        
        # Parse terminal outcomes
        terminal_outcomes = []
        for terminal_data in choice_data.get('terminal_outcomes', []):
            # Create condition function
            condition_str = terminal_data.get('condition', 'lambda npc, conv: False')
            condition_func = eval(condition_str)
            
            terminal_outcomes.append(TerminalOutcome(
                terminal_id=TerminalOutcomeType(terminal_data['terminal_id']),
                condition=condition_func,
                result=terminal_data['result'],
                final_dialogue=terminal_data['final_dialogue']
            ))
        
        return OutcomeIndex(
            choice_id=choice_data['choice_id'],
            interaction_outcomes=interaction_outcomes,
            terminal_outcomes=terminal_outcomes
        )
    
    @staticmethod
    def parse_player_input(choice_data: Dict[str, Any]) -> PlayerDialogueInput:
        """Parse player dialogue input from choice data"""
        return PlayerDialogueInput(
            choice_text=choice_data['text'],
            language_art=LanguageArt(choice_data.get('language_art', 'neutral')),
            authority_tone=choice_data.get('authority_tone', 0.5),
            diplomacy_tone=choice_data.get('diplomacy_tone', 0.5),
            empathy_tone=choice_data.get('empathy_tone', 0.5),
            manipulation_tone=choice_data.get('manipulation_tone', 0.5),
            ideology_alignment=choice_data.get('ideology_alignment'),
            contextual_references=choice_data.get('contextual_references', [])
        )


# ============================================================================
# NARRATIVE ENGINE
# ============================================================================

class NarrativeEngine:
    """
    Main engine for running dialogue conversations
    Integrates with pipeline.py's Purpose-Output Model
    """
    
    def __init__(self, use_ollama: bool = True, ollama_url: str = "http://localhost:11434"):
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.scenarios: Dict[str, Any] = {}
        self.npcs: Dict[str, NPCModel] = {}
        self.active_states: Dict[str, ConversationState] = {}
    
    def load_npc(self, filepath: str, npc_id: Optional[str] = None) -> str:
        """Load an NPC from JSON file"""
        npc = NPCModel.from_json(filepath)
        npc_id = npc_id or npc.name.lower().replace(' ', '_')
        self.npcs[npc_id] = npc
        print(f"✓ Loaded NPC: {npc.name} (ID: {npc_id})")
        return npc_id
    
    def load_scenario(self, filepath: str, scenario_id: Optional[str] = None) -> str:
        """Load a conversation scenario from JSON file"""
        scenario = ScenarioLoader.load_scenario(filepath)
        scenario_id = scenario_id or scenario.get('id', 'default_scenario')
        self.scenarios[scenario_id] = scenario
        print(f"✓ Loaded scenario: {scenario.get('title', scenario_id)} (ID: {scenario_id})")
        return scenario_id
    
    def start_conversation(
        self, 
        npc_id: str, 
        scenario_id: str,
        player_skills: Optional[PlayerSkillSet] = None
    ) -> ConversationState:
        """Initialize a new conversation"""
        if npc_id not in self.npcs:
            raise ValueError(f"NPC '{npc_id}' not loaded")
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not loaded")
        
        npc = self.npcs[npc_id]
        scenario = self.scenarios[scenario_id]
        
        # Use default player skills if not provided
        if player_skills is None:
            player_skills = PlayerSkillSet(authority=5, diplomacy=5, empathy=5, manipulation=5)
        
        # Parse NPC intent from scenario
        npc_intent = ScenarioLoader.parse_npc_intent(scenario.get('npc_intent', {}))
        
        # Create outcome index from scenario
        # We'll build this dynamically as choices are made
        initial_outcome_index = self._build_outcome_index_for_node(scenario, "start")
        
        # Create dialogue processor
        processor = DialogueProcessor(
            npc=npc,
            player_skills=player_skills,
            npc_intent=npc_intent,
            outcome_index=initial_outcome_index,
            conversation_id=f"{npc_id}_{scenario_id}",
            use_ollama=self.use_ollama,
            ollama_url=self.ollama_url
        )
        
        # Create conversation state
        state = ConversationState(
            npc=npc,
            processor=processor,
            current_node="start",
            scenario_id=scenario_id  # Store scenario_id in state
        )
        
        # Display opening
        self._display_opening(scenario, npc)
        opening = scenario.get('opening', "Conversation begins...")
        state.add_exchange("Narrator", opening)
        
        # Store active state
        conversation_key = f"{npc_id}_{scenario_id}"
        self.active_states[conversation_key] = state
        
        return state
    
    def _display_opening(self, scenario: Dict[str, Any], npc: NPCModel):
        """Display conversation opening"""
        print(f"\n{'='*70}")
        print(f"CONVERSATION: {scenario.get('title', 'Untitled')}")
        print(f"NPC: {npc.name}")
        print(f"{'='*70}\n")
        print(f"Narrator: {scenario.get('opening', 'Conversation begins...')}\n")
    
    def _build_outcome_index_for_node(
        self, 
        scenario: Dict[str, Any], 
        node_id: str
    ) -> OutcomeIndex:
        """Build outcome index for a specific node"""
        # Find the node
        node_data = None
        for node in scenario.get('nodes', []):
            if node['id'] == node_id:
                node_data = node
                break
        
        if not node_data:
            # Return empty outcome index
            return OutcomeIndex(
                choice_id="empty",
                interaction_outcomes=[],
                terminal_outcomes=[]
            )
        
        # Build outcome index from first choice (simplified)
        # In full implementation, you'd merge all choices
        choices = node_data.get('choices', [])
        if not choices:
            return OutcomeIndex(
                choice_id="empty",
                interaction_outcomes=[],
                terminal_outcomes=[]
            )
        
        # Use first choice as template
        return ScenarioLoader.parse_outcome_index(choices[0])
    
    def get_current_node(self, state: ConversationState) -> Optional[DialogueNode]:
        """Get current dialogue node"""
        scenario = self.scenarios.get(state.scenario_id)
        if not scenario:
            print(f"[Debug] Could not find scenario: {state.scenario_id}")
            return None
        
        for node_data in scenario.get('nodes', []):
            if node_data['id'] == state.current_node:
                return DialogueNode.from_dict(node_data)
        
        print(f"[Debug] Could not find node '{state.current_node}' in scenario")
        return None
    
    def display_choices(self, state: ConversationState) -> List[Dict[str, Any]]:
        """Display available choices and return them"""
        if state.is_complete:
            print("\n[Conversation has ended]")
            return []
        
        node = self.get_current_node(state)
        if not node:
            print("\n[No dialogue options available]")
            return []
        
        # Display NPC dialogue if present
        if node.npc_dialogue:
            print(f"{state.npc.name}: {node.npc_dialogue}\n")
            state.add_exchange(state.npc.name, node.npc_dialogue)
        
        # Get available choices
        available_choices = []
        print("Available choices:")
        
        for idx, choice in enumerate(node.choices, 1):
            print(f"  [{idx}] {choice['text']}")
            available_choices.append({
                'number': idx,
                'data': choice
            })
        
        if not available_choices:
            print("  [No available choices]")
        
        return available_choices
    
    def make_choice(
        self, 
        state: ConversationState, 
        choice_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute a dialogue choice and get NPC response"""
        # Parse player input
        player_input = ScenarioLoader.parse_player_input(choice_data)
        
        # Update processor's outcome index
        state.processor.outcome_index = ScenarioLoader.parse_outcome_index(choice_data)
        
        # Record player's choice
        print(f"\nPlayer: {player_input.choice_text}")
        state.add_exchange("Player", player_input.choice_text)
        state.choices_made.append(choice_data['choice_id'])
        
        # Process through pipeline
        context = state.processor.process_dialogue(
            player_input,
            generate_with_ollama=self.use_ollama
        )
        
        # Display NPC response
        npc_response = context['npc_response']
        print(f"\n[Internal Thought]: {context['thought_reaction']['internal_thought']}")
        print(f"[Intention]: {context['behavioural_intention']['intention_type']}")
        print(f"\n{state.npc.name}: {npc_response}\n")
        
        # Add to history
        state.add_exchange(
            state.npc.name, 
            npc_response,
            metadata={
                'thought': context['thought_reaction']['internal_thought'],
                'intention': context['behavioural_intention']['intention_type']
            }
        )
        
        # Check for terminal outcome
        if context['conversation_complete'] and context['terminal_outcome']:
            terminal = context['terminal_outcome']
            print(f"\n{'='*70}")
            print(f"TERMINAL OUTCOME: {terminal['terminal_id'].upper()}")
            print(f"Result: {terminal['result']}")
            print(f"{state.npc.name}: {terminal['final_dialogue']}")
            print(f"{'='*70}\n")
            
            state.mark_complete(terminal['result'])
            return context
        
        # Update current node
        state.current_node = choice_data.get('next_node', 'end')
        
        return context
    
    def run_interactive_conversation(
        self, 
        npc_id: str, 
        scenario_id: str,
        player_skills: Optional[PlayerSkillSet] = None
    ):
        """Run a full interactive conversation session"""
        state = self.start_conversation(npc_id, scenario_id, player_skills)
        
        while not state.is_complete and state.current_node != "end":
            choices = self.display_choices(state)
            
            if not choices:
                break
            
            # Get player input
            try:
                choice_input = input("\nYour choice (number or 'quit'): ").strip()
                
                if choice_input.lower() in ['quit', 'q', 'exit']:
                    print("\nConversation ended by player.")
                    break
                
                choice_num = int(choice_input)
                selected_choice = None
                
                for choice in choices:
                    if choice['number'] == choice_num:
                        selected_choice = choice['data']
                        break
                
                if not selected_choice:
                    print("Invalid choice number. Try again.")
                    continue
                
                self.make_choice(state, selected_choice)
                
            except ValueError:
                print("Please enter a valid number.")
                continue
            except KeyboardInterrupt:
                print("\n\nConversation interrupted.")
                break
        
        # Conversation ended
        self._display_conversation_end(state)
    
    def _display_conversation_end(self, state: ConversationState):
        """Display conversation end statistics"""
        print(f"\n{'='*70}")
        print("CONVERSATION ENDED")
        print(f"{'='*70}")
        
        print(f"\nFinal NPC State:")
        print(f"  Relation: {state.npc.world.player_relation:.2f}")
        print(f"  Self-esteem: {state.npc.cognitive.self_esteem:.2f}")
        print(f"  Assertion: {state.npc.social.assertion:.2f}")
        print(f"  Empathy: {state.npc.social.empathy:.2f}")
        print(f"\nChoices made: {len(state.choices_made)}")
        print(f"Conversation turns: {state.turn_count}")
        
        if state.terminal_result:
            print(f"\nOutcome: {state.terminal_result}")
    
    def export_conversation_log(self, state: ConversationState, filepath: str):
        """Export conversation history to JSON"""
        log_data = {
            'npc_name': state.npc.name,
            'conversation_id': state.processor.conversation.conversation_id,
            'turn_count': state.turn_count,
            'is_complete': state.is_complete,
            'terminal_result': state.terminal_result,
            'final_relation': state.npc.world.player_relation,
            'choices_made': state.choices_made,
            'conversation_history': state.conversation_history,
            'final_npc_state': state.npc.to_dict()
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n✓ Conversation log exported to {filepath}")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for the narrative engine"""
    import sys
    
    print("="*70)
    print("PSYCHOLOGICAL NARRATIVE ENGINE - CONVERSATION SIMULATOR")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\nUsage: python narrative_engine.py <npc_file.json> <scenario_file.json>")
        print("\nExample:")
        print("  python narrative_engine.py morisson_moses.json door_guard_scenario.json")
        print("\nOptional flags:")
        print("  --no-ollama : Disable Ollama integration (use fallback responses)")
        return
    
    npc_file = sys.argv[1]
    scenario_file = sys.argv[2]
    use_ollama = '--no-ollama' not in sys.argv
    
    try:
        # Create engine
        engine = NarrativeEngine(use_ollama=use_ollama)
        
        # Load NPC and scenario
        npc_id = engine.load_npc(npc_file)
        scenario_id = engine.load_scenario(scenario_file)
        
        # Optional: Set custom player skills
        player_skills = PlayerSkillSet(
            authority=5,
            diplomacy=5,
            empathy=5,
            manipulation=5
        )
        
        print(f"\nPlayer Skills: Authority={player_skills.authority}, "
              f"Diplomacy={player_skills.diplomacy}, "
              f"Empathy={player_skills.empathy}, "
              f"Manipulation={player_skills.manipulation}")
        
        # Run interactive conversation
        engine.run_interactive_conversation(npc_id, scenario_id, player_skills)
        
        # Optional: Export conversation log
        export = input("\nExport conversation log? (y/n): ").strip().lower()
        if export == 'y':
            log_file = input("Enter filename (e.g., conversation_log.json): ").strip()
            conversation_key = f"{npc_id}_{scenario_id}"
            if conversation_key in engine.active_states:
                engine.export_conversation_log(
                    engine.active_states[conversation_key], 
                    log_file
                )
        
    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()