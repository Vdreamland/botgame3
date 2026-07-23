from typing import Dict, Any, List, Optional
from helpers.world_parser import get_visible_agents, get_visible_monsters
from helpers.actions_payload import move_payload
from helpers.api_config import get_bots_config
from ai.strategy.movement_strategy import find_shortest_path
from ai.memory import BotMemory

def get_chase_action(
    frame_data: Dict[str, Any],
    self_data: Dict[str, Any],
    connections: List[str],
    memory: BotMemory
) -> Optional[Dict[str, Any]]:
    chase_target_id = None
    friendly_names = {bot["name"] for bot in get_bots_config()}
    for agent in get_visible_agents(frame_data):
        r_id = agent.get("regionId")
        t_hp = agent.get("hp", 0)
        if r_id in connections and 0 < t_hp <= 30:
            name = agent.get("name", "")
            if "Guardian" not in name and not agent.get("isGuardian", False):
                chase_target_id = r_id
                break
    if not chase_target_id:
        for monster in get_visible_monsters(frame_data):
            r_id = monster.get("regionId")
            t_hp = monster.get("hp", 0)
            if r_id in connections and 0 < t_hp <= 15:
                type_id = (monster.get("type") or monster.get("typeId") or "").lower()
                if "guardian" not in type_id:
                    chase_target_id = r_id
                    break
    if chase_target_id:
        memory.last_target_id = None
        memory.last_action_type = "move"
        return move_payload(chase_target_id, "Chasing low HP target in adjacent region")
    return None

def get_hunt_action(
    frame_data: Dict[str, Any],
    self_data: Dict[str, Any],
    is_loadout_optimal: bool
) -> Optional[Dict[str, Any]]:
    if is_loadout_optimal:
        visible_enemies = []
        friendly_names = {bot["name"] for bot in get_bots_config()}
        for agent in get_visible_agents(frame_data):
            if agent.get("hp", 0) > 0 and agent.get("id") != self_data.get("id"):
                name = agent.get("name", "")
                if name in friendly_names:
                    continue
                if "Guardian" not in name and not agent.get("isGuardian", False):
                    r_id = agent.get("regionId")
                    if r_id:
                        visible_enemies.append(r_id)
        if visible_enemies:
            path = find_shortest_path(frame_data, visible_enemies)
            if path and len(path) > 1:
                next_region_id = path[1]
                return move_payload(next_region_id, "Hunting visible player in adjacent region")
    return None