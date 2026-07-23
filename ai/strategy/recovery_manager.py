from typing import Dict, Any, Optional
from ai.memory import BotMemory
from helpers.actions_payload import use_item_payload
from helpers.world_parser import get_self_agent, get_current_region, get_visible_agents, get_available_actions
from helpers.api_config import get_bots_config
from ai.strategy.threat_detector import is_enemy_nearby

def get_recovery_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return None
    current_id = current_region.get("id")
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    if current_region.get("isDeathZone", False) and ep >= 2:
        return None
    friendly_names = {bot["name"] for bot in get_bots_config()}
    has_easy_kill = any(
        a.get("regionId") == current_id and 0 < a.get("hp", 0) <= 25 and "Guardian" not in a.get("name", "") and a.get("name", "") not in friendly_names
        for a in get_visible_agents(frame_data)
    )
    if has_easy_kill and hp > 40:
        return None
    hp_threshold = 60
    if is_enemy_nearby(frame_data, current_id):
        hp_threshold = 80
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
    available_actions = get_available_actions(frame_data)
    attack_cost = available_actions.get("attack", {}).get("cost", 1)
    if ep < attack_cost:
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
    ground_items = current_region.get("items", [])
    ground_type_ids = {item.get("typeId", "").lower() for item in ground_items if item.get("typeId")}
    has_ground_hp_item = any(tid in ["medkit", "emergency_food", "bandage"] for tid in ground_type_ids)
    has_ground_ep_item = any(tid in ["energy_drink", "emergency_food"] for tid in ground_type_ids)
    has_ground_emergency_food = "emergency_food" in ground_type_ids
    if has_ground_hp_item:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id == "medkit" and hp <= 70:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming medkit since replacements are on the ground")
                elif type_id == "emergency_food" and hp <= 80 and has_ground_emergency_food:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming emergency food since replacements are on the ground")
                elif type_id == "bandage" and hp <= 90:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming bandage since replacements are on the ground")
    if has_ground_ep_item:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id == "energy_drink" and ep <= attack_cost + 3:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, f"Proactive EP restore: consuming {type_id} since replacements are on the ground")
                elif type_id == "emergency_food" and ep <= attack_cost + 3 and has_ground_emergency_food:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, f"Proactive EP restore: consuming {type_id} since replacements are on the ground")
    return None

def should_rest_for_ep(frame_data: Dict[str, Any]) -> bool:
    from helpers.world_parser import get_self_agent, get_current_region, get_available_actions
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return False
    ep = self_data.get("ep", 0)
    is_death_zone = current_region.get("isDeathZone", False) or current_region.get("is_death_zone", False)
    available_actions = get_available_actions(frame_data)
    attack_cost = available_actions.get("attack", {}).get("cost", 1)
    if ep < attack_cost and not is_death_zone:
        return True
    return False