from typing import Dict, Any, List, Optional
from helpers.world_parser import get_self_agent, get_current_region
from helpers.actions_payload import pickup_payload
from ai.strategy.inventory_manager import analyze_inventory, is_item_needed, MELEE_SCORES, RANGED_SCORES, ARMOR_SCORES

def get_pickup_action(frame_data: Dict[str, Any], memory: Any) -> Optional[Dict[str, Any]]:
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
            type_id = item.get("typeId", "").lower().replace(" ", "_")
            if type_id in ["smoltz", "moltz"]:
                memory.pickup_attempts.add(item_id)
                memory.last_target_id = item_id
                memory.last_action_type = "pickup"
                return pickup_payload(item_id, "Picking up sMoltz")
    if len(inventory) >= 10:
        return None
    best_melee_val = -1.0
    best_ranged_val = -1.0
    best_armor_val = -1.0
    for item in items:
        item_id = item.get("id")
        if item_id and item_id not in memory.failed_items:
            t_id = item.get("typeId", "").lower().replace(" ", "_")
            if t_id in MELEE_SCORES:
                best_melee_val = max(best_melee_val, float(MELEE_SCORES[t_id]))
            elif t_id in RANGED_SCORES:
                best_ranged_val = max(best_ranged_val, float(RANGED_SCORES[t_id]))
            elif t_id in ARMOR_SCORES:
                best_armor_val = max(best_armor_val, float(ARMOR_SCORES[t_id]))
    for item in items:
        item_id = item.get("id")
        if item_id and item_id not in memory.failed_items and item_id not in memory.pickup_attempts:
            type_id = item.get("typeId", "").lower().replace(" ", "_")
            if type_id in ["smoltz", "moltz"]:
                continue
            if type_id in MELEE_SCORES and float(MELEE_SCORES[type_id]) < best_melee_val:
                continue
            if type_id in RANGED_SCORES and float(RANGED_SCORES[type_id]) < best_ranged_val:
                continue
            if type_id in ARMOR_SCORES and float(ARMOR_SCORES[type_id]) < best_armor_val:
                continue
            if is_item_needed(item, inv_analysis):
                memory.pickup_attempts.add(item_id)
                memory.last_target_id = item_id
                memory.last_action_type = "pickup"
                item_name = item.get("typeId") or "item"
                return pickup_payload(item_id, f"Picking up {item_name}")
    return None

def get_interact_action(frame_data: Dict[str, Any], memory: Any) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import interact_payload
    self_data = get_self_agent(frame_data)
    if not self_data:
        return None
    current_region = get_current_region(frame_data)
    if not current_region:
        return None
    interactables = current_region.get("interactables", [])
    for fac in interactables:
        fac_id = fac.get("id")
        if fac_id and fac_id not in memory.failed_facilities:
            type_id = fac.get("typeId", "")
            if type_id == "Supply Cache":
                return interact_payload(fac_id, "Interacting with supply cache")
            elif type_id == "Medical Facility":
                return interact_payload(fac_id, "Interacting with medical facility")
    return None

def find_target_regions(frame_data: Dict[str, Any], memory: Any) -> List[str]:
    from helpers.world_parser import get_visible_regions
    from ai.strategy.inventory_manager import is_item_needed, analyze_inventory
    self_data = get_self_agent(frame_data)
    if not self_data:
        return []
    inventory = self_data.get("inventory", [])
    inv_analysis = analyze_inventory(inventory)
    target_regions = []
    for r in get_visible_regions(frame_data):
        r_id = r.get("id")
        if r_id:
            if r.get("isDeathZone", False):
                continue
            items = r.get("items", [])
            has_smoltz = any(item.get("typeId", "").lower() in ["smoltz", "moltz"] for item in items)
            if r_id in memory.move_history and not has_smoltz:
                continue
            if has_smoltz:
                target_regions.append(r_id)
                continue
            has_needed_item = any(is_item_needed(item, inv_analysis) for item in items)
            if has_needed_item:
                target_regions.append(r_id)
                continue
            interactables = r.get("interactables", [])
            has_facility = any(f.get("typeId", "") in ["Supply Cache", "Medical Facility"] for f in interactables)
            if has_facility:
                target_regions.append(r_id)
                continue
            connections = r.get("connections", [])
            if len(connections) > 0 and r.get("terrain", "") == "ruins":
                target_regions.append(r_id)
    return target_regions