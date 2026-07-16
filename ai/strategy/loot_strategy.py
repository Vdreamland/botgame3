from typing import Dict, Any, List, Optional
from helpers.world_parser import get_current_region

def get_pickup_action(frame_data: Dict[str, Any], memory: Any) -> Optional[Dict[str, Any]]:
    from helpers.world_parser import get_self_agent
    from helpers.actions_payload import pickup_payload
    from ai.strategy.inventory_manager import analyze_inventory, is_item_needed
    self_data = get_self_agent(frame_data)
    if not self_data:
        return None
    current_region = get_current_region(frame_data)
    if not current_region:
        return None
    inventory = self_data.get("inventory", [])
    inv_analysis = analyze_inventory(inventory)
    items = current_region.get("items", [])
    for item in items:
        item_id = item.get("id")
        if item_id and item_id not in memory.failed_items and item_id not in memory.pickup_attempts:
            if is_item_needed(item, inv_analysis):
                memory.pickup_attempts.add(item_id)
                memory.last_target_id = item_id
                memory.last_action_type = "pickup"
                item_name = item.get("typeId") or "item"
                return pickup_payload(item_id, f"Picking up {item_name}")
    return None

def get_interact_action(frame_data: Dict[str, Any], memory: Any) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import interact_payload
    current_region = get_current_region(frame_data)
    if not current_region:
        return None
    is_death_zone = current_region.get("isDeathZone", False)
    if is_death_zone:
        return None
    interactables = current_region.get("interactables", [])
    for fac in interactables:
        fac_id = fac.get("id")
        fac_type = fac.get("typeId")
        if fac_id and fac_id not in memory.failed_facilities:
            if fac_type in ["Supply Cache", "Medical Facility"] and not fac.get("isUsed", False):
                memory.last_target_id = fac_id
                memory.last_action_type = "interact"
                return interact_payload(fac_id, f"Interacting with {fac_type}")
    return None

def find_target_regions(frame_data: Dict[str, Any], memory: Any) -> List[str]:
    from helpers.world_parser import get_visible_regions, get_visible_ruins
    from ai.strategy.inventory_manager import analyze_inventory, is_item_needed
    self_data = frame_data.get("view", {}).get("self", {})
    inv = self_data.get("inventory", [])
    inv_analysis = analyze_inventory(inv)
    visible_regions = get_visible_regions(frame_data)
    visible_ruins = get_visible_ruins(frame_data)
    death_targets = []
    other_targets = []
    our_id = self_data.get("id")
    active_ruin_ids = set()
    for ruin in visible_ruins:
        r_id = ruin.get("id")
        if r_id:
            gauge = ruin.get("gauge", ruin.get("ruinGauge", 0))
            occupied_by = ruin.get("occupiedBy")
            is_empty = ruin.get("isEmpty", False)
            if not is_empty and gauge < 3 and (not occupied_by or occupied_by == our_id):
                active_ruin_ids.add(r_id)
    for r in visible_regions:
        r_id = r.get("id")
        if not r_id:
            continue
        has_valuable = False
        if r_id in active_ruin_ids:
            has_valuable = True
        else:
            items = r.get("items", [])
            for item in items:
                item_id = item.get("id")
                if item_id and item_id not in memory.failed_items and item_id not in memory.pickup_attempts:
                    if is_item_needed(item, inv_analysis):
                        has_valuable = True
                        break
            if not has_valuable:
                interactables = r.get("interactables", [])
                for fac in interactables:
                    fac_id = fac.get("id")
                    fac_type = fac.get("typeId")
                    if fac_id and fac_id not in memory.failed_facilities:
                        if fac_type in ["Supply Cache", "Medical Facility"] and not fac.get("isUsed", False):
                            has_valuable = True
                            break
        if has_valuable:
            if r.get("isDeathZone", False):
                death_targets.append(r_id)
            else:
                other_targets.append(r_id)
    return death_targets + other_targets