from typing import Dict, Any, Optional, List, Set
from helpers.world_parser import get_current_region, get_visible_regions
from helpers.actions_payload import pickup_payload, interact_payload, move_payload
from ai.strategy.movement_strategy import find_shortest_path

class LootStrategy:
    def __init__(self):
        self.failed_items: Set[str] = set()
        self.failed_facilities: Set[str] = set()
        self.last_target_id: Optional[str] = None
        self.last_action_type: Optional[str] = None
        self.action_counter: int = 0

    def decide_action(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_region = get_current_region(frame_data)
        if not current_region:
            return None
        current_id = current_region.get("id")
        current_items = current_region.get("items", [])
        current_interactables = current_region.get("interactables", [])
        current_item_ids = {item.get("id") for item in current_items if item.get("id")}
        current_fac_ids = {fac.get("id") for fac in current_interactables if fac.get("id")}
        if self.last_target_id:
            target_still_exists = (self.last_target_id in current_item_ids) or (self.last_target_id in current_fac_ids)
            if target_still_exists:
                self.action_counter += 1
                if self.action_counter > 2:
                    if self.last_action_type == "pickup":
                        self.failed_items.add(self.last_target_id)
                    elif self.last_action_type == "interact":
                        self.failed_facilities.add(self.last_target_id)
                    self.last_target_id = None
                    self.action_counter = 0
            else:
                self.last_target_id = None
                self.action_counter = 0
        for item in current_items:
            item_id = item.get("id")
            if item_id and item_id not in self.failed_items:
                self.last_target_id = item_id
                self.last_action_type = "pickup"
                return pickup_payload(item_id, "Picking up ground item")
        for fac in current_interactables:
            fac_id = fac.get("id")
            fac_name = fac.get("name", "")
            is_used = fac.get("isUsed", False)
            if fac_id and fac_name in ["Supply Cache", "Medical Facility"] and not is_used and fac_id not in self.failed_facilities:
                self.last_target_id = fac_id
                self.last_action_type = "interact"
                return interact_payload(fac_id, "Interacting with facility")
        target_region_ids = []
        visible_regions = get_visible_regions(frame_data)
        for r in visible_regions:
            r_id = r.get("id")
            if not r_id:
                continue
            has_valid_targets = False
            for item in r.get("items", []):
                item_id = item.get("id")
                if item_id and item_id not in self.failed_items:
                    has_valid_targets = True
                    break
            for fac in r.get("interactables", []):
                fac_id = fac.get("id")
                fac_name = fac.get("name", "")
                is_used = fac.get("isUsed", False)
                if fac_id and fac_name in ["Supply Cache", "Medical Facility"] and not is_used and fac_id not in self.failed_facilities:
                    has_valid_targets = True
                    break
            if has_valid_targets:
                target_region_ids.append(r_id)
        if target_region_ids:
            path = find_shortest_path(frame_data, target_region_ids)
            if path and len(path) > 1:
                next_region_id = path[1]
                self.last_target_id = None
                self.last_action_type = "move"
                return move_payload(next_region_id, "Moving to target region")
        return None