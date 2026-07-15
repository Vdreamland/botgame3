from typing import Dict, Any, List, Optional
from helpers.world_parser import (
    get_current_region,
    get_visible_agents,
    get_visible_monsters,
    get_visible_ruins
)

def calculate_final_damage(atk: int, weapon_bonus: int, def_val: int, weather_mod: int) -> int:
    raw_damage = atk + weapon_bonus - def_val + weather_mod
    return max(1, raw_damage)

def resolve_connected_region(entry: Any, visible_regions: List[Any]) -> Optional[Dict[str, Any]]:
    if isinstance(entry, dict):
        return entry
    for r in visible_regions:
        if isinstance(r, dict) and r.get("id") == entry:
            return r
    return None

def is_region_safe_from_death_zone(region_id: str, pending_deathzones: List[Any]) -> bool:
    for dz in pending_deathzones:
        if isinstance(dz, dict) and dz.get("id") == region_id:
            return False
        elif isinstance(dz, str) and dz == region_id:
            return False
    return True

class AgentMemory:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_region_id = None
        self.visible_players = {}
        self.visible_monsters = {}
        self.visible_items = {}
        self.ruins_states = {}
        self.adjacency_map = {}

    def update_state(self, agent_view: Dict[str, Any]) -> None:
        current_region = get_current_region(agent_view)
        self.current_region_id = current_region.get("id")
        
        self.visible_players.clear()
        for player in get_visible_agents(agent_view):
            p_id = player.get("id")
            if p_id != self.agent_id:
                self.visible_players[p_id] = player

        self.visible_monsters.clear()
        for monster in get_visible_monsters(agent_view):
            m_id = monster.get("id")
            self.visible_monsters[m_id] = monster

        self.visible_items.clear()
        regions = agent_view.get("view", {}).get("visibleRegions", [])
        current_reg = get_current_region(agent_view)
        all_regions = [current_reg] + regions
        for r in all_regions:
            for item in r.get("items", []):
                i_id = item.get("id")
                if i_id:
                    self.visible_items[i_id] = item

        for ruin in get_visible_ruins(agent_view):
            r_id = ruin.get("id")
            if r_id:
                self.ruins_states[r_id] = ruin

    def get_priority_target(self) -> Optional[Dict[str, Any]]:
        for player_id, player in self.visible_players.items():
            if player.get("hp", 100) < 30 and player.get("isAlive", True):
                return {"id": player_id, "type": "agent", "data": player}

        for monster_id, monster in self.visible_monsters.items():
            if monster.get("isAlive", True) and monster.get("monsterType") != "guardian":
                return {"id": monster_id, "type": "monster", "data": monster}

        for player_id, player in self.visible_players.items():
            if player.get("isAlive", True):
                return {"id": player_id, "type": "agent", "data": player}
                
        return None

    def get_explorable_ruin(self) -> Optional[Dict[str, Any]]:
        for ruin_id, ruin in self.ruins_states.items():
            gauge = ruin.get("gauge", 0)
            occupied_by = ruin.get("occupiedBy")
            if gauge < 3 and (occupied_by is None or occupied_by == self.agent_id):
                return ruin
        return None