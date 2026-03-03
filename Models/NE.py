"""
Entry point for the Psychological Narrative Engine.

Run from the Models/ directory:
    python NE.py <npc1.json> [npc2.json ...] <scenario.json> [--no-ollama]

Examples:
    python NE.py npcs/morisson_moses.json scenarios/dgn.json
    python NE.py npcs/troy.json scenarios/dgn.json
    python NE.py npcs/troy.json scenarios/dgn.json --no-ollama
"""

import sys
import os

# Ensure the Models/ directory (this file's own directory) is on sys.path
# so narrative_engine package and pne module are importable regardless of cwd.
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from narrative_engine.cli import main

if __name__ == "__main__":
    main()
