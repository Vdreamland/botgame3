from typing import Dict, Any
from helpers.api_config import get_bots_config

def is_enemy_nearby(frame_data: Dict[str, Any], current_id: str) -> bool:
    from helpers.world_parser import get_visible_agents, get_visible_monsters, get_current_region
    current_reg = get_current_region(frame_data)
    connections = current_reg.get("connections", []) if current_reg else []
    nearby_regions = set(connections) | {current_id}
    friendly_names = {bot["name"] for bot in get_bots_config()}
    for agent in get_visible_agents(frame_data):
        reg_id = agent.get("regionId")
        hp = agent.get("hp", 0)
        name = agent.get("name", "")
        if name in friendly_names:
            continue
        if reg_id in nearby_regions and hp > 0 and "Guardian" not in name and not agent.get("isGuardian", False):
            weapon = agent.get("equippedWeapon")
            weapon_name = "none"
            if weapon:
                weapon_name = weapon.get("typeId", weapon.get("name", "none")) if isinstance(weapon, dict) else str(weapon)
            if weapon_name.lower() not in ["none", "fist", ""]:
                return True
    for monster in get_visible_monsters(frame_data):
        reg_id = monster.get("regionId")
        hp = monster.get("hp", 0)
        type_id = (monster.get("type") or monster.get("typeId") or "").lower()
        if reg_id in nearby_regions and hp > 0:
            if "guardian" in type_id:
                if reg_id == current_id:
                    return True
            else:
                return True
    return False