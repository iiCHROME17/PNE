#!/bin/bash
# ===========================
# run_engine.sh
# Default NPC and Scenario
# ===========================

# Set defaults
DEFAULT_NPC="amourie_othella.json"
DEFAULT_SCENARIO="door_guard_scenario_filtered.json"

# Use arguments if provided, otherwise defaults
NPC="${1:-$DEFAULT_NPC}"
SCENARIO="${2:-$DEFAULT_SCENARIO}"

# Run the Python script
python3 narrative_engine.py npcs/$NPC scenarios/$SCENARIO
