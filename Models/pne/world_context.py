"""
Psychological Narrative Engine - World Context
Name: world_context.py
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class WorldContext:
    """Shared world data — one instance, referenced by all NPCs"""
    world_history: str
    factions: Dict[str, Any] = field(default_factory=dict)
    key_events: Dict[str, Any] = field(default_factory=dict)  # keyed by id
    locations: Dict[str, str] = field(default_factory=dict)
    concepts: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "WorldContext":
        with open(path) as f:
            data = json.load(f)
        events = {e["id"]: e for e in data.get("key_events", [])}
        return cls(
            world_history=data.get("world_history", ""),
            factions=data.get("factions", {}),
            key_events=events,
            locations=data.get("locations", {}),
            concepts=data.get("concepts", {}),
        )

    def get_npc_context(self, npc) -> str:
        """
        Build world context string for a specific NPC,
        filtered to what they actually know.
        """
        parts = [f"WORLD: {self.world_history}"]

        faction_id = getattr(npc.social, "faction", None)
        if faction_id and faction_id in self.factions:
            f = self.factions[faction_id]
            parts.append(f"FACTION ({faction_id}): {f['history']}")
            parts.append(f"FACTION IDEOLOGY: {f['ideology']}")

        known = getattr(npc.world, "known_events", [])
        for event_id in known:
            if event_id in self.key_events:
                e = self.key_events[event_id]
                parts.append(f"EVENT ({e['year']}): {e['description']}")

        parts.append(f"PERSONAL HISTORY: {npc.world.personal_history}")

        if npc.world.player_history:
            parts.append(f"HISTORY WITH PLAYER: {npc.world.player_history}")

        return "\n".join(parts)