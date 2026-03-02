#!/bin/bash
# ===========================
# PNE.sh
# Default NPC and Scenario
# Inspired by deprecated run_engine.sh
# ===========================

# Set defaults
DEFAULT_NPC="amourie_othella.json"
DEFAULT_SCENARIO="door_guard_scenario_filtered.json"

# Use arguments if provided, otherwise defaults
NPC="${1:-$DEFAULT_NPC}"
SCENARIO="${2:-$DEFAULT_SCENARIO}"

# Ensure we run from the Models directory so 'pne' package is on sys.path
cd "$(dirname "$0")"

# Run the Python script via the new narrative engine
python3 narrative_engine/engine.py "npcs/$NPC" "scenarios/$SCENARIO"
