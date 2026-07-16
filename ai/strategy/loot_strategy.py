from typing import Dict, Any, Optional, List
from helpers.world_parser import get_current_region, get_visible_regions
from ai.memory import BotMemory
from ai.strategy.inventory_manager import analyze_inventory, is_item_needed

def find_current_region_targets(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import pickup_payload, interact_payload
    from helpers.world_parser import get_self_agent
    self_data = get_self_agent(frame_data)
    inv = self_data.get("inventory", [])
    inv_analysis = analyze_inventory(inv)
    current_region = get_current_region(frame_data)
    if not current_region:
        return None
    is_death_zone = current_region.get("isDeathZone", False)
    items = current_region.get("items", [])
    interactables = current_region.get("interactables", [])
    for item in items:
        item_id = item.get("id")
        if item_id and item_id not in memory.failed_items:
            if is_item_needed(item, inv_analysis):
                memory.last_target_id = item_id
                memory.last_action_type = "pickup"
                return pickup_payload(item_id, "Picking up ground item")
    if not is_death_zone:
        for fac in interactables:
            fac_id = fac.get("id")
            fac_name = fac.get("name", "")
            is_used = fac.get("isUsed", False)
            if fac_id and fac_name in ["Supply Cache", "Medical Facility"] and not is_used and fac_id not in memory.failed_facilities:
                memory.last_target_id = fac_id
                memory.last_action_type = "interact"
                return interact_payload(fac_id, "Interacting with facility")
    return None

def find_target_regions(frame_data: Dict[str, Any], memory: BotMemory) -> List[str]:
    from helpers.world_parser import get_self_agent
    self_data = get_self_agent(frame_data)
    inv = self_data.get("inventory", [])
    inv_analysis = analyze_inventory(inv)
    target_region_ids = []
    visible_regions = get_visible_regions(frame_data)
    for r in visible_regions:
        r_id = r.get("id")
        if not r_id:
            continue
        if r.get("isDeathZone", False):
            continue
        has_valid_targets = False
        for item in r.get("items", []):
            item_id = item.get("id")
            if item_id and item_id not in memory.failed_items:
                if is_item_needed(item, inv_analysis):
                    has_valid_targets = True
                    break
        for fac in r.get("interactables", []):
            fac_id = fac.get("id")
            fac_name = fac.get("name", "")
            is_used = fac.get("isUsed", False)
            if fac_id and fac_name in ["Supply Cache", "Medical Facility"] and not is_used and fac_id not in memory.failed_facilities:
                has_valid_targets = True
                break
        if has_valid_targets:
            target_region_ids.append(r_id)
    return target_region_ids