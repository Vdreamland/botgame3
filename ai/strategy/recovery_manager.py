from typing import Dict, Any, Optional
from ai.memory import BotMemory

def is_enemy_nearby(frame_data: Dict[str, Any], current_id: str) -> bool:
    from helpers.world_parser import get_visible_agents, get_visible_monsters, get_current_region
    current_reg = get_current_region(frame_data)
    connections = current_reg.get("connections", []) if current_reg else []
    nearby_regions = set(connections) | {current_id}
    for agent in get_visible_agents(frame_data):
        reg_id = agent.get("regionId")
        hp = agent.get("hp", 0)
        if reg_id in nearby_regions and hp > 0:
            return True
    for monster in get_visible_monsters(frame_data):
        reg_id = monster.get("regionId")
        hp = monster.get("hp", 0)
        if reg_id in nearby_regions and hp > 0:
            return True
    return False

def get_recovery_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import use_item_payload
    from helpers.world_parser import get_self_agent, get_current_region
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return None
    current_id = current_region.get("id")
    hp_threshold = 60
    if is_enemy_nearby(frame_data, current_id):
        hp_threshold = 80
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    inventory = self_data.get("inventory", [])
    if hp < hp_threshold:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id == "medkit":
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Using medkit under low HP")
                elif type_id == "emergency_food":
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Using emergency food under low HP")
                elif type_id == "bandage":
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Using bandage under low HP")
    if ep < 2:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id == "energy_drink":
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Drinking energy drink under low EP")
                elif type_id == "emergency_food":
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Eating emergency food under low EP")
    return None

def should_rest_for_ep(self_data: Dict[str, Any], current_region: Dict[str, Any]) -> bool:
    ep = self_data.get("ep", 0)
    is_death_zone = current_region.get("isDeathZone", False)
    if ep < 3 and not is_death_zone:
        return True
    return False