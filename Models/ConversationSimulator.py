"""
Conversation Simulator for Psychological Narrative Engine
name: ConversationSimulator.py
Author: Jerome Bawa

OLD PROTOTYPE! COMPLETELY DEPRECATED. EXEMPLAR FOR narrative_engine.py

Simulates dialogue interactions between player and NPCs using JSON-defined scenarios
"""

from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, field

# Import from the main engine (assumes narrative_engine.py is in same directory)
try:
    from pipeline import (
        NPCModel, DialogueManager, OutcomeIndex, 
        Outcome, OutcomeType
    )
except ImportError:
    print("Error: Make sure pipeline.py is in the same directory")
    exit(1)


@dataclass
class ConversationState:
    """Tracks the state of an ongoing conversation"""
    npc: NPCModel
    current_node: str = "start"
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    choices_made: List[str] = field(default_factory=list)
    
    def add_exchange(self, speaker: str, text: str):
        """Add a dialogue exchange to history"""
        self.conversation_history.append({
            "speaker": speaker,
            "text": text
        })
    
    def get_history_text(self) -> str:
        """Format conversation history as readable text"""
        lines = []
        for exchange in self.conversation_history:
            speaker = exchange["speaker"]
            text = exchange["text"]
            lines.append(f"{speaker}: {text}")
        return "\n".join(lines)


class ConversationSimulator:
    """
    Main simulator for running conversations with NPCs
    Uses JSON files for NPC data and dialogue scenarios
    """
    
    def __init__(self):
        self.dialogue_manager = DialogueManager()
        self.scenarios: Dict[str, Any] = {}
        self.npcs: Dict[str, NPCModel] = {}
    
    def load_npc(self, filepath: str, npc_id: Optional[str] = None) -> str:
        """
        Load an NPC from JSON file
        Returns the NPC ID for reference
        """
        npc = NPCModel.from_json(filepath)
        npc_id = npc_id or npc.name.lower().replace(' ', '_')
        self.npcs[npc_id] = npc
        print(f"✓ Loaded NPC: {npc.name} (ID: {npc_id})")
        return npc_id
    
    def load_scenario(self, filepath: str, scenario_id: Optional[str] = None) -> str:
        """
        Load a conversation scenario from JSON file
        Returns the scenario ID for reference
        """
        with open(filepath, 'r') as f:
            scenario = json.load(f)
        
        scenario_id = scenario_id or scenario.get('id', 'default_scenario')
        self.scenarios[scenario_id] = scenario
        
        # Register all choices with the dialogue manager
        for choice_data in scenario.get('choices', []):
            outcome_index = OutcomeIndex.from_dict(choice_data)
            self.dialogue_manager.register_choice(outcome_index)
        
        print(f"✓ Loaded scenario: {scenario.get('title', scenario_id)} (ID: {scenario_id})")
        return scenario_id
    
    def start_conversation(self, npc_id: str, scenario_id: str) -> ConversationState:
        """Initialize a new conversation"""
        if npc_id not in self.npcs:
            raise ValueError(f"NPC '{npc_id}' not loaded")
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not loaded")
        
        npc = self.npcs[npc_id]
        scenario = self.scenarios[scenario_id]
        
        state = ConversationState(npc=npc, current_node="start")
        
        # Display opening
        opening = scenario.get('opening', "Conversation begins...")
        print(f"\n{'='*60}")
        print(f"CONVERSATION: {scenario.get('title', 'Untitled')}")
        print(f"NPC: {npc.name}")
        print(f"{'='*60}\n")
        print(f"Narrator: {opening}\n")
        
        state.add_exchange("Narrator", opening)
        
        return state
    
    def display_choices(self, state: ConversationState, scenario_id: str) -> List[Dict[str, Any]]:
        """
        Display available choices for current node
        Returns list of choice dictionaries
        """
        scenario = self.scenarios[scenario_id]
        current_node = state.current_node
        
        # Find the current node in scenario
        node_data = None
        for node in scenario.get('nodes', []):
            if node['id'] == current_node:
                node_data = node
                break
        
        if not node_data:
            print("No more dialogue options available.")
            return []
        
        # Display NPC's dialogue if present
        if 'npc_dialogue' in node_data:
            npc_text = node_data['npc_dialogue']
            print(f"{state.npc.name}: {npc_text}\n")
            state.add_exchange(state.npc.name, npc_text)
        
        # Get available choices
        choices = node_data.get('choices', [])
        available_choices = []
        
        print("Available choices:")
        choice_num = 1
        for choice in choices:
            choice_id = choice['choice_id']
            
            # Check if choice is available based on NPC state
            outcome_index = self.dialogue_manager.outcome_indices.get(choice_id)
            if outcome_index and not outcome_index.is_available(state.npc):
                continue
            
            print(f"  [{choice_num}] {choice['text']}")
            available_choices.append({
                'number': choice_num,
                'choice_id': choice_id,
                'text': choice['text'],
                'outcome_type': choice.get('outcome_type', 'SUCCESS'),
                'next_node': choice.get('next_node', 'end')
            })
            choice_num += 1
        
        if not available_choices:
            print("  [No available choices]")
        
        return available_choices
    
    def make_choice(
        self, 
        state: ConversationState, 
        choice: Dict[str, Any]
    ) -> Optional[str]:
        """
        Execute a dialogue choice and get NPC response
        Returns the response text or None if invalid
        """
        choice_id = choice['choice_id']
        outcome_type_str = choice['outcome_type']
        
        # Convert string to OutcomeType enum
        try:
            outcome_type = OutcomeType(outcome_type_str)
        except ValueError:
            outcome_type = OutcomeType.SUCCESS
        
        # Record player's choice
        player_text = choice['text']
        print(f"\nPlayer: {player_text}")
        state.add_exchange("Player", player_text)
        state.choices_made.append(choice_id)
        
        # Execute the choice and get response
        response = self.dialogue_manager.execute_choice(
            choice_id, 
            outcome_type, 
            state.npc
        )
        
        if response:
            print(f"{state.npc.name}: {response}\n")
            state.add_exchange(state.npc.name, response)
        
        # Update current node
        state.current_node = choice['next_node']
        
        return response
    
    def run_interactive_conversation(self, npc_id: str, scenario_id: str):
        """Run a full interactive conversation session"""
        state = self.start_conversation(npc_id, scenario_id)
        
        while state.current_node != "end":
            choices = self.display_choices(state, scenario_id)
            
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
                        selected_choice = choice
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
        print(f"\n{'='*60}")
        print("CONVERSATION ENDED")
        print(f"{'='*60}")
        
        # Display final stats
        self.display_conversation_stats(state)
    
    def display_conversation_stats(self, state: ConversationState):
        """Display statistics about the conversation"""
        print(f"\nFinal NPC State:")
        print(f"  Relation: {state.npc.world.player_relation:.2f}")
        print(f"  Self-esteem: {state.npc.cognitive.self_esteem:.2f}")
        print(f"  Assertion: {state.npc.social.assertion:.2f}")
        print(f"  Empathy: {state.npc.social.empathy:.2f}")
        print(f"\nChoices made: {len(state.choices_made)}")
        print(f"Conversation turns: {len(state.conversation_history)}")
    
    def export_conversation_log(self, state: ConversationState, filepath: str):
        """Export conversation history to JSON"""
        log_data = {
            'npc_name': state.npc.name,
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
    """Main entry point for the simulator"""
    import sys
    
    simulator = ConversationSimulator()
    
    print("="*60)
    print("PSYCHOLOGICAL NARRATIVE ENGINE - CONVERSATION SIMULATOR")
    print("="*60)
    
    if len(sys.argv) < 3:
        print("\nUsage: python conversation_simulator.py <npc_file.json> <scenario_file.json>")
        print("\nExample:")
        print("  python conversation_simulator.py moses.json door_scenario.json")
        return
    
    npc_file = sys.argv[1]
    scenario_file = sys.argv[2]
    
    try:
        # Load NPC and scenario
        npc_id = simulator.load_npc(npc_file)
        scenario_id = simulator.load_scenario(scenario_file)
        
        # Run interactive conversation
        simulator.run_interactive_conversation(npc_id, scenario_id)
        
        # Optional: Export conversation log
        export = input("\nExport conversation log? (y/n): ").strip().lower()
        if export == 'y':
            log_file = input("Enter filename (e.g., conversation_log.json): ").strip()
            # Note: Would need to pass state here in actual implementation
            print("Export feature requires conversation state to be stored.")
        
    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()