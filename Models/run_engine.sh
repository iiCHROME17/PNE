#!/bin/bash
# ===========================
# run_engine.sh
# Default NPC and Scenario
# ===========================

# Set defaults
DEFAULT_NPC="troy.json"
DEFAULT_SCENARIO="dgn.json"

# Use arguments if provided, otherwise defaults
NPC="${1:-$DEFAULT_NPC}"
SCENARIO="${2:-$DEFAULT_SCENARIO}"

# Run the Python script
python3 NE.py npcs/$NPC scenarios/$SCENARIO
