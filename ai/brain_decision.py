import json
from typing import Dict, Any, Optional
from helpers.world_parser import get_current_region, get_self_agent, get_visible_regions
from helpers.actions_payload import move_payload, explore_payload, rest_payload, equip_payload, drop_payload
from ai.memory import BotMemory
from ai.strategy.inventory_manager import analyze_inventory, get_item_to_drop, MELEE_SCORES, RANGED_SCORES, ARMOR_SCORES
from ai.strategy.recovery_manager import get_recovery_action, should_rest_for_ep
from ai.strategy.loot_strategy import find_current_region_targets, find_target_regions
from ai.strategy.movement_strategy import find_shortest_path

class BrainDecision:
    def __init__(self):
        self.memory = BotMemory()

    def get_next_action(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_region = get_current_region(frame_data)
        self_data = get_self_agent(frame_data)
        if not current_region or not self_data:
            return None
        current_id = current_region.get("id")
        self.memory.add_visited_region(current_id)
        current_items = current_region.get("items", [])
        current_interactables = current_region.get("interactables", [])
        current_item_ids = {item.get("id") for item in current_items if item.get("id")}
        current_fac_ids = {fac.get("id") for fac in current_interactables if fac.get("id")}
        self.memory.track_action_failure(current_item_ids, current_fac_ids)
        recovery_action = get_recovery_action(frame_data, self.memory)
        if recovery_action:
            return recovery_action
        inv = self_data.get("inventory", [])
        inv_analysis = analyze_inventory(inv)
        eq_weapon = self_data.get("equippedWeapon")
        eq_type = eq_weapon.get("typeId", "").lower() if eq_weapon else ""
        eq_score = 0
        if eq_type in MELEE_SCORES:
            eq_score = MELEE_SCORES[eq_type]
        elif eq_type in RANGED_SCORES:
            eq_score = RANGED_SCORES[eq_type]
        best_inv_weapon = None
        best_inv_score = 0
        if inv_analysis["best_melee_score"] > best_inv_score:
            best_inv_score = inv_analysis["best_melee_score"]
            best_inv_weapon = inv_analysis["best_melee"]
        if inv_analysis["best_ranged_score"] > best_inv_score:
            best_inv_score = inv_analysis["best_ranged_score"]
            best_inv_weapon = inv_analysis["best_ranged"]
        if best_inv_score > eq_score and best_inv_weapon:
            item_id = best_inv_weapon.get("id")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, "Equipping stronger weapon")
        eq_armor = self_data.get("equippedArmor")
        eq_armor_type = eq_armor.get("typeId", "").lower() if eq_armor else ""
        eq_armor_score = ARMOR_SCORES.get(eq_armor_type, 0)
        if inv_analysis["best_armor_score"] > eq_armor_score and inv_analysis["best_armor"]:
            item_id = inv_analysis["best_armor"].get("id")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, "Equipping stronger armor")
        item_to_drop_id = get_item_to_drop(inv_analysis, inv)
        if item_to_drop_id and item_to_drop_id not in self.memory.drop_attempts:
            self.memory.drop_attempts.add(item_to_drop_id)
            return drop_payload(item_to_drop_id, "Dropping weaker redundant item")
        action = find_current_region_targets(frame_data, self.memory)
        if action:
            return action
        target_regions = find_target_regions(frame_data, self.memory)
        if target_regions:
            path = find_shortest_path(frame_data, target_regions)
            if path and len(path) > 1:
                next_region_id = path[1]
                self.memory.last_target_id = None
                self.memory.last_action_type = "move"
                return move_payload(next_region_id, "Moving to target region")
        visible_regions = get_visible_regions(frame_data)
        safe_region_ids = set()
        for r in visible_regions:
            r_id = r.get("id")
            if r_id and not r.get("isDeathZone", False):
                safe_region_ids.add(r_id)
        connections = current_region.get("connections", [])
        safe_connections = [c for c in connections if c in safe_region_ids]
        unvisited_connections = [c for c in safe_connections if c not in self.memory.move_history]
        next_fallback_id = None
        if unvisited_connections:
            next_fallback_id = unvisited_connections[0]
        elif safe_connections:
            next_fallback_id = safe_connections[0]
        elif connections:
            next_fallback_id = connections[0]
        ruin_gauge = current_region.get("ruinGauge", 3)
        if ruin_gauge < 3 and self_data.get("ep", 0) >= 2:
            return explore_payload("Exploring ruin")
        if self_data.get("ep", 0) >= 2 and next_fallback_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(next_fallback_id, "Moving to unvisited region to search")
        if should_rest_for_ep(self_data, current_region):
            return rest_payload("Resting to recover EP")
        if self_data.get("ep", 0) < 2:
            return rest_payload("Resting to recover EP")
        return explore_payload("Exploring local region")