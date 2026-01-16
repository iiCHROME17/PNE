"""
Psychological Narrative Engine - Visual Conversation Designer
name: narrative_designer_gui.py
Author: Jerome Bawa

A GUI tool for narrative designers to create NPCs, conversations, and outcomes
without manually writing JSON files.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid


# ============================================================================
# DATA MODELS FOR GUI
# ============================================================================

@dataclass
class GUIChoice:
    """Represents a dialogue choice in the GUI"""
    choice_id: str
    text: str
    language_art: str = "neutral"
    authority_tone: float = 0.5
    diplomacy_tone: float = 0.5
    empathy_tone: float = 0.5
    manipulation_tone: float = 0.5
    ideology_alignment: str = ""
    next_node: str = "end"
    
    # Outcomes
    interaction_outcomes: List[Dict[str, Any]] = None
    terminal_outcomes: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.interaction_outcomes is None:
            self.interaction_outcomes = []
        if self.terminal_outcomes is None:
            self.terminal_outcomes = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_id": self.choice_id,
            "text": self.text,
            "language_art": self.language_art,
            "authority_tone": self.authority_tone,
            "diplomacy_tone": self.diplomacy_tone,
            "empathy_tone": self.empathy_tone,
            "manipulation_tone": self.manipulation_tone,
            "ideology_alignment": self.ideology_alignment if self.ideology_alignment else None,
            "next_node": self.next_node,
            "interaction_outcomes": self.interaction_outcomes,
            "terminal_outcomes": self.terminal_outcomes
        }


@dataclass
class GUINode:
    """Represents a dialogue node in the GUI"""
    node_id: str
    npc_dialogue: str = ""
    choices: List[GUIChoice] = None
    
    def __post_init__(self):
        if self.choices is None:
            self.choices = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "npc_dialogue": self.npc_dialogue,
            "choices": [choice.to_dict() for choice in self.choices]
        }


@dataclass
class GUIScenario:
    """Represents a complete conversation scenario"""
    scenario_id: str
    title: str
    opening: str
    npc_intent: Dict[str, str]
    nodes: List[GUINode] = None
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.scenario_id,
            "title": self.title,
            "opening": self.opening,
            "npc_intent": self.npc_intent,
            "nodes": [node.to_dict() for node in self.nodes]
        }


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class NarrativeDesignerApp:
    """Main GUI application for narrative design"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Psychological Narrative Engine - Conversation Designer")
        self.root.geometry("1400x900")
        
        # Data storage
        self.current_scenario: Optional[GUIScenario] = None
        self.current_node: Optional[GUINode] = None
        self.current_choice: Optional[GUIChoice] = None
        
        # Setup UI
        self.setup_menu()
        self.setup_main_layout()
        
    def setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Scenario", command=self.new_scenario)
        file_menu.add_command(label="Open Scenario", command=self.open_scenario)
        file_menu.add_command(label="Save Scenario", command=self.save_scenario)
        file_menu.add_separator()
        file_menu.add_command(label="New NPC", command=self.create_npc_dialog)
        file_menu.add_command(label="Open NPC", command=self.open_npc)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_main_layout(self):
        """Setup main application layout"""
        # Create main paned window
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Node tree
        left_frame = ttk.Frame(main_pane, width=300)
        main_pane.add(left_frame, weight=1)
        self.setup_node_tree(left_frame)
        
        # Right panel - Editor
        right_frame = ttk.Frame(main_pane, width=800)
        main_pane.add(right_frame, weight=3)
        self.setup_editor_panel(right_frame)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_node_tree(self, parent):
        """Setup node tree view"""
        ttk.Label(parent, text="Conversation Structure", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Scenario info
        info_frame = ttk.LabelFrame(parent, text="Scenario Info")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.scenario_title_label = ttk.Label(info_frame, text="No scenario loaded")
        self.scenario_title_label.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add Node", command=self.add_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete Node", command=self.delete_node).pack(side=tk.LEFT, padx=2)
        
        # Tree view
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.node_tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.node_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.node_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.node_tree.configure(yscrollcommand=scrollbar.set)
        
        self.node_tree.bind('<<TreeviewSelect>>', self.on_node_select)
    
    def setup_editor_panel(self, parent):
        """Setup main editor panel"""
        # Notebook for different editing modes
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Scenario Settings
        self.scenario_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scenario_tab, text="Scenario Settings")
        self.setup_scenario_editor(self.scenario_tab)
        
        # Tab 2: Node Editor
        self.node_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.node_tab, text="Node Editor")
        self.setup_node_editor(self.node_tab)
        
        # Tab 3: Choice Editor
        self.choice_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.choice_tab, text="Choice Editor")
        self.setup_choice_editor(self.choice_tab)
        
        # Tab 4: Preview
        self.preview_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_tab, text="Preview JSON")
        self.setup_preview_tab(self.preview_tab)
    
    def setup_scenario_editor(self, parent):
        """Setup scenario settings editor"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scenario ID
        ttk.Label(scrollable_frame, text="Scenario ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.scenario_id_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.scenario_id_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Title
        ttk.Label(scrollable_frame, text="Title:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.scenario_title_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.scenario_title_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # Opening
        ttk.Label(scrollable_frame, text="Opening Narration:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.scenario_opening_text = scrolledtext.ScrolledText(scrollable_frame, width=50, height=4)
        self.scenario_opening_text.grid(row=2, column=1, padx=5, pady=5)
        
        # NPC Intent section
        ttk.Label(scrollable_frame, text="NPC Intent", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        ttk.Label(scrollable_frame, text="Baseline Belief:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.intent_belief_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.intent_belief_var, width=40).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(scrollable_frame, text="Long-term Desire:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.intent_desire_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.intent_desire_var, width=40).grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(scrollable_frame, text="Immediate Intention:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.intent_intention_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.intent_intention_var, width=40).grid(row=6, column=1, padx=5, pady=5)
        
        ttk.Label(scrollable_frame, text="Stakes:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.intent_stakes_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.intent_stakes_var, width=40).grid(row=7, column=1, padx=5, pady=5)
        
        # Save button
        ttk.Button(scrollable_frame, text="Update Scenario Settings", command=self.update_scenario_settings).grid(row=8, column=0, columnspan=2, pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_node_editor(self, parent):
        """Setup node editor"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Node ID
        ttk.Label(scrollable_frame, text="Node ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.node_id_label = ttk.Label(scrollable_frame, text="", font=('Arial', 10, 'bold'))
        self.node_id_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # NPC Dialogue
        ttk.Label(scrollable_frame, text="NPC Dialogue:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
        self.node_dialogue_text = scrolledtext.ScrolledText(scrollable_frame, width=60, height=6)
        self.node_dialogue_text.grid(row=1, column=1, padx=5, pady=5)
        
        # Choices section
        ttk.Label(scrollable_frame, text="Player Choices", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        # Choice list
        choice_frame = ttk.Frame(scrollable_frame)
        choice_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        self.choice_listbox = tk.Listbox(choice_frame, height=8)
        self.choice_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.choice_listbox.bind('<<ListboxSelect>>', self.on_choice_select)
        
        choice_scroll = ttk.Scrollbar(choice_frame, orient=tk.VERTICAL, command=self.choice_listbox.yview)
        choice_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.choice_listbox.configure(yscrollcommand=choice_scroll.set)
        
        # Choice buttons
        choice_btn_frame = ttk.Frame(scrollable_frame)
        choice_btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Button(choice_btn_frame, text="Add Choice", command=self.add_choice).pack(side=tk.LEFT, padx=5)
        ttk.Button(choice_btn_frame, text="Edit Choice", command=self.edit_choice).pack(side=tk.LEFT, padx=5)
        ttk.Button(choice_btn_frame, text="Delete Choice", command=self.delete_choice).pack(side=tk.LEFT, padx=5)
        
        # Update button
        ttk.Button(scrollable_frame, text="Update Node", command=self.update_node).grid(row=5, column=0, columnspan=2, pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_choice_editor(self, parent):
        """Setup choice editor with outcomes"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Choice text
        ttk.Label(scrollable_frame, text="Choice Text:").grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
        self.choice_text = scrolledtext.ScrolledText(scrollable_frame, width=50, height=3)
        self.choice_text.grid(row=0, column=1, padx=5, pady=5)
        
        # Language Art
        ttk.Label(scrollable_frame, text="Language Art:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_language_var = tk.StringVar(value="neutral")
        language_combo = ttk.Combobox(scrollable_frame, textvariable=self.choice_language_var, 
                                      values=["challenge", "diplomatic", "empathetic", "manipulative", "neutral"],
                                      state="readonly", width=20)
        language_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Tone sliders
        ttk.Label(scrollable_frame, text="Tone Settings", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        # Authority
        ttk.Label(scrollable_frame, text="Authority:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_authority_var = tk.DoubleVar(value=0.5)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.choice_authority_var, orient=tk.HORIZONTAL, length=300).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, textvariable=self.choice_authority_var).grid(row=3, column=2, padx=5)
        
        # Diplomacy
        ttk.Label(scrollable_frame, text="Diplomacy:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_diplomacy_var = tk.DoubleVar(value=0.5)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.choice_diplomacy_var, orient=tk.HORIZONTAL, length=300).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, textvariable=self.choice_diplomacy_var).grid(row=4, column=2, padx=5)
        
        # Empathy
        ttk.Label(scrollable_frame, text="Empathy:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_empathy_var = tk.DoubleVar(value=0.5)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.choice_empathy_var, orient=tk.HORIZONTAL, length=300).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, textvariable=self.choice_empathy_var).grid(row=5, column=2, padx=5)
        
        # Manipulation
        ttk.Label(scrollable_frame, text="Manipulation:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_manipulation_var = tk.DoubleVar(value=0.5)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.choice_manipulation_var, orient=tk.HORIZONTAL, length=300).grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, textvariable=self.choice_manipulation_var).grid(row=6, column=2, padx=5)
        
        # Next node
        ttk.Label(scrollable_frame, text="Next Node:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_next_node_var = tk.StringVar(value="end")
        ttk.Entry(scrollable_frame, textvariable=self.choice_next_node_var, width=30).grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Ideology alignment
        ttk.Label(scrollable_frame, text="Ideology Alignment:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.choice_ideology_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.choice_ideology_var, width=30).grid(row=8, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Outcomes section
        ttk.Label(scrollable_frame, text="Outcomes", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=3, sticky=tk.W, padx=5, pady=10)
        
        ttk.Button(scrollable_frame, text="Add Interaction Outcome", command=self.add_interaction_outcome).grid(row=10, column=0, columnspan=2, pady=5)
        ttk.Button(scrollable_frame, text="Add Terminal Outcome", command=self.add_terminal_outcome).grid(row=11, column=0, columnspan=2, pady=5)
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Choice", command=self.save_choice, style='Accent.TButton').grid(row=12, column=0, columnspan=2, pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_preview_tab(self, parent):
        """Setup JSON preview tab"""
        ttk.Label(parent, text="JSON Preview", font=('Arial', 12, 'bold')).pack(pady=5)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh Preview", command=self.refresh_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_json).pack(side=tk.LEFT, padx=5)
        
        self.preview_text = scrolledtext.ScrolledText(parent, width=80, height=40)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # ========================================================================
    # SCENARIO OPERATIONS
    # ========================================================================
    
    def new_scenario(self):
        """Create a new scenario"""
        scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
        self.current_scenario = GUIScenario(
            scenario_id=scenario_id,
            title="New Scenario",
            opening="",
            npc_intent={
                "baseline_belief": "",
                "long_term_desire": "",
                "immediate_intention": "",
                "stakes": ""
            },
            nodes=[]
        )
        
        # Add start node
        start_node = GUINode(node_id="start", npc_dialogue="", choices=[])
        self.current_scenario.nodes.append(start_node)
        
        self.load_scenario_to_ui()
        self.refresh_tree()
        self.set_status("New scenario created")
    
    def open_scenario(self):
        """Open existing scenario JSON"""
        filepath = filedialog.askopenfilename(
            title="Open Scenario",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Parse JSON into GUI objects
            self.current_scenario = self.parse_scenario_from_json(data)
            self.load_scenario_to_ui()
            self.refresh_tree()
            self.set_status(f"Loaded scenario from {filepath}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load scenario: {str(e)}")
    
    def save_scenario(self):
        """Save current scenario to JSON"""
        if not self.current_scenario:
            messagebox.showwarning("Warning", "No scenario to save")
            return
        
        # Update scenario from UI first
        self.update_scenario_settings()
        
        filepath = filedialog.asksaveasfilename(
            title="Save Scenario",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.current_scenario.to_dict(), f, indent=2)
            
            self.set_status(f"Saved scenario to {filepath}")
            messagebox.showinfo("Success", "Scenario saved successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scenario: {str(e)}")
    
    def parse_scenario_from_json(self, data: Dict[str, Any]) -> GUIScenario:
        """Parse JSON data into GUI scenario object"""
        nodes = []
        for node_data in data.get('nodes', []):
            choices = []
            for choice_data in node_data.get('choices', []):
                choice = GUIChoice(
                    choice_id=choice_data['choice_id'],
                    text=choice_data['text'],
                    language_art=choice_data.get('language_art', 'neutral'),
                    authority_tone=choice_data.get('authority_tone', 0.5),
                    diplomacy_tone=choice_data.get('diplomacy_tone', 0.5),
                    empathy_tone=choice_data.get('empathy_tone', 0.5),
                    manipulation_tone=choice_data.get('manipulation_tone', 0.5),
                    ideology_alignment=choice_data.get('ideology_alignment', ''),
                    next_node=choice_data.get('next_node', 'end'),
                    interaction_outcomes=choice_data.get('interaction_outcomes', []),
                    terminal_outcomes=choice_data.get('terminal_outcomes', [])
                )
                choices.append(choice)
            
            node = GUINode(
                node_id=node_data['id'],
                npc_dialogue=node_data.get('npc_dialogue', ''),
                choices=choices
            )
            nodes.append(node)
        
        return GUIScenario(
            scenario_id=data['id'],
            title=data['title'],
            opening=data['opening'],
            npc_intent=data['npc_intent'],
            nodes=nodes
        )
    
    def load_scenario_to_ui(self):
        """Load current scenario data into UI fields"""
        if not self.current_scenario:
            return
        
        self.scenario_id_var.set(self.current_scenario.scenario_id)
        self.scenario_title_var.set(self.current_scenario.title)
        self.scenario_opening_text.delete('1.0', tk.END)
        self.scenario_opening_text.insert('1.0', self.current_scenario.opening)
        
        self.intent_belief_var.set(self.current_scenario.npc_intent.get('baseline_belief', ''))
        self.intent_desire_var.set(self.current_scenario.npc_intent.get('long_term_desire', ''))
        self.intent_intention_var.set(self.current_scenario.npc_intent.get('immediate_intention', ''))
        self.intent_stakes_var.set(self.current_scenario.npc_intent.get('stakes', ''))
        
        self.scenario_title_label.config(text=self.current_scenario.title)
        self.set_status("Scenario settings updated")
    
    # ========================================================================
    # NODE OPERATIONS
    # ========================================================================
    
    def refresh_tree(self):
        """Refresh the node tree view"""
        self.node_tree.delete(*self.node_tree.get_children())
        
        if not self.current_scenario:
            return
        
        for node in self.current_scenario.nodes:
            display_text = f"{node.node_id} ({len(node.choices)} choices)"
            self.node_tree.insert('', 'end', node.node_id, text=display_text)
    
    def on_node_select(self, event):
        """Handle node selection in tree"""
        selection = self.node_tree.selection()
        if not selection:
            return
        
        node_id = selection[0]
        self.current_node = self.find_node_by_id(node_id)
        
        if self.current_node:
            self.load_node_to_ui()
            self.notebook.select(self.node_tab)
    
    def find_node_by_id(self, node_id: str) -> Optional[GUINode]:
        """Find node by ID"""
        if not self.current_scenario:
            return None
        
        for node in self.current_scenario.nodes:
            if node.node_id == node_id:
                return node
        return None
    
    def load_node_to_ui(self):
        """Load current node data into UI"""
        if not self.current_node:
            return
        
        self.node_id_label.config(text=self.current_node.node_id)
        self.node_dialogue_text.delete('1.0', tk.END)
        self.node_dialogue_text.insert('1.0', self.current_node.npc_dialogue)
        
        # Load choices
        self.choice_listbox.delete(0, tk.END)
        for choice in self.current_node.choices:
            display = f"{choice.choice_id}: {choice.text[:50]}..."
            self.choice_listbox.insert(tk.END, display)
    
    def add_node(self):
        """Add a new node"""
        if not self.current_scenario:
            messagebox.showwarning("Warning", "Create a scenario first")
            return
        
        node_id = self.prompt_node_id()
        if not node_id:
            return
        
        # Check if node already exists
        if self.find_node_by_id(node_id):
            messagebox.showerror("Error", "Node ID already exists")
            return
        
        new_node = GUINode(node_id=node_id, npc_dialogue="", choices=[])
        self.current_scenario.nodes.append(new_node)
        self.refresh_tree()
        self.set_status(f"Added node: {node_id}")
    
    def delete_node(self):
        """Delete selected node"""
        selection = self.node_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a node to delete")
            return
        
        node_id = selection[0]
        
        if node_id == "start":
            messagebox.showerror("Error", "Cannot delete start node")
            return
        
        if messagebox.askyesno("Confirm", f"Delete node '{node_id}'?"):
            self.current_scenario.nodes = [n for n in self.current_scenario.nodes if n.node_id != node_id]
            self.refresh_tree()
            self.set_status(f"Deleted node: {node_id}")
    
    def update_node(self):
        """Update current node from UI"""
        if not self.current_node:
            return
        
        self.current_node.npc_dialogue = self.node_dialogue_text.get('1.0', tk.END).strip()
        self.refresh_tree()
        self.set_status(f"Updated node: {self.current_node.node_id}")
    
    def prompt_node_id(self) -> Optional[str]:
        """Prompt for node ID"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Node ID")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter Node ID:").pack(pady=10)
        
        node_id_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=node_id_var, width=30)
        entry.pack(pady=5)
        entry.focus()
        
        result = [None]
        
        def on_ok():
            result[0] = node_id_var.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        dialog.wait_window()
        return result[0]
    
    # ========================================================================
    # CHOICE OPERATIONS
    # ========================================================================
    
    def on_choice_select(self, event):
        """Handle choice selection"""
        selection = self.choice_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if self.current_node and 0 <= idx < len(self.current_node.choices):
            self.current_choice = self.current_node.choices[idx]
            self.load_choice_to_ui()
    
    def add_choice(self):
        """Add new choice to current node"""
        if not self.current_node:
            messagebox.showwarning("Warning", "Select a node first")
            return
        
        choice_id = f"choice_{uuid.uuid4().hex[:8]}"
        new_choice = GUIChoice(
            choice_id=choice_id,
            text="New choice text",
            language_art="neutral"
        )
        
        self.current_node.choices.append(new_choice)
        self.load_node_to_ui()
        self.set_status(f"Added choice: {choice_id}")
    
    def edit_choice(self):
        """Edit selected choice"""
        selection = self.choice_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a choice to edit")
            return
        
        idx = selection[0]
        if self.current_node and 0 <= idx < len(self.current_node.choices):
            self.current_choice = self.current_node.choices[idx]
            self.load_choice_to_ui()
            self.notebook.select(self.choice_tab)
    
    def delete_choice(self):
        """Delete selected choice"""
        selection = self.choice_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a choice to delete")
            return
        
        idx = selection[0]
        if messagebox.askyesno("Confirm", "Delete this choice?"):
            del self.current_node.choices[idx]
            self.load_node_to_ui()
            self.set_status("Deleted choice")
    
    def load_choice_to_ui(self):
        """Load choice data into UI"""
        if not self.current_choice:
            return
        
        self.choice_text.delete('1.0', tk.END)
        self.choice_text.insert('1.0', self.current_choice.text)
        
        self.choice_language_var.set(self.current_choice.language_art)
        self.choice_authority_var.set(self.current_choice.authority_tone)
        self.choice_diplomacy_var.set(self.current_choice.diplomacy_tone)
        self.choice_empathy_var.set(self.current_choice.empathy_tone)
        self.choice_manipulation_var.set(self.current_choice.manipulation_tone)
        self.choice_next_node_var.set(self.current_choice.next_node)
        self.choice_ideology_var.set(self.current_choice.ideology_alignment or "")
    
    def save_choice(self):
        """Save current choice from UI"""
        if not self.current_choice:
            messagebox.showwarning("Warning", "No choice selected")
            return
        
        self.current_choice.text = self.choice_text.get('1.0', tk.END).strip()
        self.current_choice.language_art = self.choice_language_var.get()
        self.current_choice.authority_tone = round(self.choice_authority_var.get(), 2)
        self.current_choice.diplomacy_tone = round(self.choice_diplomacy_var.get(), 2)
        self.current_choice.empathy_tone = round(self.choice_empathy_var.get(), 2)
        self.current_choice.manipulation_tone = round(self.choice_manipulation_var.get(), 2)
        self.current_choice.next_node = self.choice_next_node_var.get()
        self.current_choice.ideology_alignment = self.choice_ideology_var.get()
        
        self.load_node_to_ui()
        self.set_status("Choice saved")
        messagebox.showinfo("Success", "Choice saved successfully!")
    
    # ========================================================================
    # OUTCOME OPERATIONS
    # ========================================================================
    
    def add_interaction_outcome(self):
        """Add interaction outcome to current choice"""
        if not self.current_choice:
            messagebox.showwarning("Warning", "Select a choice first")
            return
        
        dialog = InteractionOutcomeDialog(self.root)
        outcome = dialog.show()
        
        if outcome:
            self.current_choice.interaction_outcomes.append(outcome)
            self.set_status("Added interaction outcome")
            messagebox.showinfo("Success", "Interaction outcome added!")
    
    def add_terminal_outcome(self):
        """Add terminal outcome to current choice"""
        if not self.current_choice:
            messagebox.showwarning("Warning", "Select a choice first")
            return
        
        dialog = TerminalOutcomeDialog(self.root)
        outcome = dialog.show()
        
        if outcome:
            self.current_choice.terminal_outcomes.append(outcome)
            self.set_status("Added terminal outcome")
            messagebox.showinfo("Success", "Terminal outcome added!")
    
    # ========================================================================
    # NPC OPERATIONS
    # ========================================================================
    
    def create_npc_dialog(self):
        """Open NPC creation dialog"""
        dialog = NPCCreationDialog(self.root)
        npc_data = dialog.show()
        
        if npc_data:
            filepath = filedialog.asksaveasfilename(
                title="Save NPC",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                with open(filepath, 'w') as f:
                    json.dump(npc_data, f, indent=2)
                
                self.set_status(f"NPC saved to {filepath}")
                messagebox.showinfo("Success", "NPC created and saved!")
    
    def open_npc(self):
        """Open NPC JSON file"""
        filepath = filedialog.askopenfilename(
            title="Open NPC",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            with open(filepath, 'r') as f:
                npc_data = json.load(f)
            
            messagebox.showinfo("NPC Loaded", f"Loaded: {npc_data.get('name', 'Unknown')}")
            self.set_status(f"Loaded NPC from {filepath}")
    
    # ========================================================================
    # PREVIEW & UTILITY
    # ========================================================================
    
    def refresh_preview(self):
        """Refresh JSON preview"""
        if not self.current_scenario:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', "No scenario loaded")
            return
        
        # Update from UI first
        self.update_scenario_settings()
        if self.current_node:
            self.update_node()
        
        json_str = json.dumps(self.current_scenario.to_dict(), indent=2)
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', json_str)
    
    def copy_json(self):
        """Copy JSON to clipboard"""
        self.refresh_preview()
        json_content = self.preview_text.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_content)
        self.set_status("JSON copied to clipboard")
    
    def set_status(self, message: str):
        """Update status bar"""
        self.status_bar.config(text=message)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Quick Start Guide:

1. Create New Scenario (File → New Scenario)
2. Fill in scenario settings (title, opening, NPC intent)
3. Add nodes to create conversation flow
4. For each node, add NPC dialogue and player choices
5. Configure each choice's tone and outcomes
6. Preview JSON and save

Tips:
- Start node is always required
- Use node IDs to link choices (next_node)
- Use "end" as next_node to terminate conversation
- Interaction outcomes modify NPC state during conversation
- Terminal outcomes end the conversation with results
        """
        messagebox.showinfo("Quick Start", help_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Psychological Narrative Engine
Conversation Designer v1.0

A visual tool for designing dynamic NPC conversations
with psychological depth and branching outcomes.

Created by Jerome Bawa
        """
        messagebox.showinfo("About", about_text)


# ============================================================================
# DIALOG WINDOWS
# ============================================================================

class InteractionOutcomeDialog:
    """Dialog for creating interaction outcomes"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show dialog and return result"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Interaction Outcome")
        dialog.geometry("500x600")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Outcome ID
        ttk.Label(dialog, text="Outcome ID:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        outcome_id_var = tk.StringVar(value=f"outcome_{uuid.uuid4().hex[:8]}")
        ttk.Entry(dialog, textvariable=outcome_id_var, width=30).grid(row=0, column=1, padx=10, pady=5)
        
        # Relation delta
        ttk.Label(dialog, text="Relation Delta:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        relation_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dialog, from_=-1.0, to=1.0, increment=0.1, textvariable=relation_var, width=28).grid(row=1, column=1, padx=10, pady=5)
        
        # Intention shift
        ttk.Label(dialog, text="Intention Shift:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        intention_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=intention_var, width=30).grid(row=2, column=1, padx=10, pady=5)
        
        # Min response
        ttk.Label(dialog, text="Min Response:").grid(row=3, column=0, sticky=tk.NW, padx=10, pady=5)
        min_text = scrolledtext.ScrolledText(dialog, width=35, height=3)
        min_text.grid(row=3, column=1, padx=10, pady=5)
        
        # Max response
        ttk.Label(dialog, text="Max Response:").grid(row=4, column=0, sticky=tk.NW, padx=10, pady=5)
        max_text = scrolledtext.ScrolledText(dialog, width=35, height=3)
        max_text.grid(row=4, column=1, padx=10, pady=5)
        
        # Stance deltas
        ttk.Label(dialog, text="Stance Deltas (Optional):").grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        ttk.Label(dialog, text="social.assertion:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=2)
        assertion_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dialog, from_=-0.5, to=0.5, increment=0.05, textvariable=assertion_var, width=28).grid(row=6, column=1, padx=10, pady=2)
        
        ttk.Label(dialog, text="social.empathy:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        empathy_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dialog, from_=-0.5, to=0.5, increment=0.05, textvariable=empathy_var, width=28).grid(row=7, column=1, padx=10, pady=2)
        
        ttk.Label(dialog, text="cognitive.self_esteem:").grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        esteem_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dialog, from_=-0.5, to=0.5, increment=0.05, textvariable=esteem_var, width=28).grid(row=8, column=1, padx=10, pady=2)
        
        def on_ok():
            stance_delta = {}
            if assertion_var.get() != 0:
                stance_delta['social.assertion'] = assertion_var.get()
            if empathy_var.get() != 0:
                stance_delta['social.empathy'] = empathy_var.get()
            if esteem_var.get() != 0:
                stance_delta['cognitive.self_esteem'] = esteem_var.get()
            
            self.result = {
                "outcome_id": outcome_id_var.get(),
                "stance_delta": stance_delta,
                "relation_delta": relation_var.get(),
                "intention_shift": intention_var.get() if intention_var.get() else None,
                "min_response": min_text.get('1.0', tk.END).strip(),
                "max_response": max_text.get('1.0', tk.END).strip(),
                "scripted": False
            }
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return self.result


class TerminalOutcomeDialog:
    """Dialog for creating terminal outcomes"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show dialog and return result"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Terminal Outcome")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Terminal ID
        ttk.Label(dialog, text="Terminal Type:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        terminal_var = tk.StringVar(value="succeed")
        ttk.Combobox(dialog, textvariable=terminal_var, 
                    values=["succeed", "fail", "negotiate", "delay", "escalate"],
                    state="readonly", width=28).grid(row=0, column=1, padx=10, pady=5)
        
        # Condition
        ttk.Label(dialog, text="Condition:").grid(row=1, column=0, sticky=tk.NW, padx=10, pady=5)
        condition_var = tk.StringVar(value="lambda npc, conv: npc.world.player_relation > 0.7")
        condition_text = scrolledtext.ScrolledText(dialog, width=35, height=3)
        condition_text.insert('1.0', condition_var.get())
        condition_text.grid(row=1, column=1, padx=10, pady=5)
        
        # Result
        ttk.Label(dialog, text="Result:").grid(row=2, column=0, sticky=tk.NW, padx=10, pady=5)
        result_text = scrolledtext.ScrolledText(dialog, width=35, height=3)
        result_text.grid(row=2, column=1, padx=10, pady=5)
        
        # Final dialogue
        ttk.Label(dialog, text="Final Dialogue:").grid(row=3, column=0, sticky=tk.NW, padx=10, pady=5)
        dialogue_text = scrolledtext.ScrolledText(dialog, width=35, height=3)
        dialogue_text.grid(row=3, column=1, padx=10, pady=5)
        
        def on_ok():
            self.result = {
                "terminal_id": terminal_var.get(),
                "condition": condition_text.get('1.0', tk.END).strip(),
                "result": result_text.get('1.0', tk.END).strip(),
                "final_dialogue": dialogue_text.get('1.0', tk.END).strip()
            }
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return self.result


class NPCCreationDialog:
    """Dialog for creating NPCs"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show dialog and return NPC data"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create NPC")
        dialog.geometry("600x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Basic info
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Age:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        age_var = tk.IntVar(value=30)
        ttk.Spinbox(frame, from_=18, to=100, textvariable=age_var, width=28).grid(row=1, column=1, padx=10, pady=5)
        
        # Cognitive
        ttk.Label(frame, text="Cognitive Attributes", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        ttk.Label(frame, text="Self-Esteem (0-1):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        esteem_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=esteem_var, orient=tk.HORIZONTAL, length=200).grid(row=3, column=1, padx=10, pady=2)
        
        ttk.Label(frame, text="Locus of Control (0-1):").grid(row=4, column=0, sticky=tk.W, padx=10, pady=2)
        locus_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=locus_var, orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=10, pady=2)
        
        ttk.Label(frame, text="Cognitive Flexibility (0-1):").grid(row=5, column=0, sticky=tk.W, padx=10, pady=2)
        flex_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=flex_var, orient=tk.HORIZONTAL, length=200).grid(row=5, column=1, padx=10, pady=2)
        
        # Social
        ttk.Label(frame, text="Social Attributes", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        ttk.Label(frame, text="Assertion (0-1):").grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        assertion_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=assertion_var, orient=tk.HORIZONTAL, length=200).grid(row=7, column=1, padx=10, pady=2)
        
        ttk.Label(frame, text="Independence (0-1):").grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        indep_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=indep_var, orient=tk.HORIZONTAL, length=200).grid(row=8, column=1, padx=10, pady=2)
        
        ttk.Label(frame, text="Empathy (0-1):").grid(row=9, column=0, sticky=tk.W, padx=10, pady=2)
        empathy_var = tk.DoubleVar(value=0.5)
        ttk.Scale(frame, from_=0, to=1, variable=empathy_var, orient=tk.HORIZONTAL, length=200).grid(row=9, column=1, padx=10, pady=2)
        
        # Faction
        ttk.Label(frame, text="Faction:").grid(row=10, column=0, sticky=tk.W, padx=10, pady=5)
        faction_var = tk.StringVar()
        ttk.Entry(frame, textvariable=faction_var, width=30).grid(row=10, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Social Position:").grid(row=11, column=0, sticky=tk.W, padx=10, pady=5)
        position_var = tk.StringVar(value="Member")
        ttk.Combobox(frame, textvariable=position_var, 
                    values=["Boss", "Vice", "Higher", "Member"],
                    state="readonly", width=28).grid(row=11, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Wildcard:").grid(row=12, column=0, sticky=tk.W, padx=10, pady=5)
        wildcard_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=wildcard_var, 
                    values=["", "Martyr", "Napoleon", "Inferiority"],
                    width=28).grid(row=12, column=1, padx=10, pady=5)
        
        def on_ok():
            self.result = {
                "name": name_var.get(),
                "age": age_var.get(),
                "cognitive": {
                    "self_esteem": round(esteem_var.get(), 2),
                    "locus_of_control": round(locus_var.get(), 2),
                    "cog_flexibility": round(flex_var.get(), 2)
                },
                "social": {
                    "assertion": round(assertion_var.get(), 2),
                    "conf_indep": round(indep_var.get(), 2),
                    "empathy": round(empathy_var.get(), 2),
                    "ideology": {},
                    "wildcard": wildcard_var.get() if wildcard_var.get() else None,
                    "faction": faction_var.get() if faction_var.get() else None,
                    "social_position": position_var.get()
                },
                "world": {
                    "world_history": "",
                    "personal_history": "",
                    "player_history": "",
                    "player_relation": 0.5
                }
            }
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=13, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Create NPC", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        dialog.wait_window()
        return self.result


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the narrative designer application"""
    root = tk.Tk()
    app = NarrativeDesignerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

    
    def update_scenario_settings(self):
        """Update scenario from UI fields"""
        if not self.current_scenario:
            return
        
        self.current_scenario.scenario_id = self.scenario_id_var.get()
        self.current_scenario.title = self.scenario_title_var.get()
        self.current_scenario.opening = self.scenario_opening_text.get('1.0', tk.END).strip()
        
        self.current_scenario.npc_intent = {
            'baseline_belief': self.intent_belief_var.get(),
            'long_term_desire': self.intent_desire_var.get(),
            'immediate_intention': self.intent_intention_var.get(),
            'stakes': self.intent_stakes_var.get()
        }
        
        self.scenario_title_label.config(text=self.current_scenario.title)