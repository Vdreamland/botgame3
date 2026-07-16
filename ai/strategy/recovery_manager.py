from typing import Dict, Any, Optional
from ai.memory import BotMemory

def get_recovery_action(self_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import use_item_payload
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    inventory = self_data.get("inventory", [])
    if hp < 40:
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