from typing import Dict, Any, Optional

def get_recovery_action(self_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import use_item_payload
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    inventory = self_data.get("inventory", [])
    if hp < 40:
        for item in inventory:
            type_id = item.get("typeId", "").lower()
            if type_id == "medkit":
                return use_item_payload(item.get("id"), "Using medkit under low HP")
            elif type_id == "emergency_food":
                return use_item_payload(item.get("id"), "Using emergency food under low HP")
            elif type_id == "bandage":
                return use_item_payload(item.get("id"), "Using bandage under low HP")
    if ep < 2:
        for item in inventory:
            type_id = item.get("typeId", "").lower()
            if type_id == "energy_drink":
                return use_item_payload(item.get("id"), "Drinking energy drink under low EP")
            elif type_id == "emergency_food":
                return use_item_payload(item.get("id"), "Eating emergency food under low EP")
    return None

def should_rest_for_ep(self_data: Dict[str, Any], current_region: Dict[str, Any]) -> bool:
    ep = self_data.get("ep", 0)
    is_death_zone = current_region.get("isDeathZone", False)
    if ep < 3 and not is_death_zone:
        return True
    return False