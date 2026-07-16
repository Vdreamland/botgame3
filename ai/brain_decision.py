from typing import Dict, Any, List, Optional
from helpers.world_parser import (
    get_current_region,
    get_self_agent,
    get_visible_regions,
    get_visible_agents,
    get_visible_monsters,
    get_recent_logs,
    get_available_actions,
    get_region_adjacency_map
)
from helpers.actions_payload import (
    move_payload,
    explore_payload,
    rest_payload,
    equip_payload,
    drop_payload
)
from ai.memory import BotMemory
from ai.strategy.inventory_manager import analyze_inventory, get_item_to_drop, MELEE_SCORES, RANGED_SCORES, ARMOR_SCORES
from ai.strategy.survival_manager import get_recovery_action, get_flee_action, should_rest_for_ep
from ai.strategy.combat_strategy import get_combat_action
from ai.strategy.loot_strategy import get_pickup_action, get_interact_action, find_target_regions
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
        if current_id in self.memory.death_regions:
            self.memory.death_regions.remove(current_id)
        recent_logs = get_recent_logs(frame_data)
        for entry in recent_logs:
            log_obj = entry.get("log", {})
            if log_obj.get("type") == "death":
                reg_id = log_obj.get("regionId")
                if reg_id:
                    self.memory.death_regions.add(reg_id)
        current_items = current_region.get("items", [])
        current_interactables = current_region.get("interactables", [])
        current_item_ids = {item.get("id") for item in current_items if item.get("id")}
        current_fac_ids = {fac.get("id") for fac in current_interactables if fac.get("id")}
        current_enemy_ids = set()
        for agent in get_visible_agents(frame_data):
            if agent.get("hp", 0) > 0:
                current_enemy_ids.add(agent.get("id"))
        for monster in get_visible_monsters(frame_data):
            if monster.get("hp", 0) > 0:
                current_enemy_ids.add(monster.get("id"))
        self.memory.track_action_failure(current_item_ids, current_fac_ids, current_enemy_ids)
        inv = self_data.get("inventory", [])
        pickup_action = None
        if len(inv) < 10:
            pickup_action = get_pickup_action(frame_data, self.memory)
        if pickup_action:
            return pickup_action
        inv_analysis = analyze_inventory(inv)
        eq_weapon = self_data.get("equippedWeapon")
        eq_type = eq_weapon.get("typeId", "").lower() if eq_weapon else ""
        eq_score = 0.0
        if eq_type in MELEE_SCORES:
            eq_score = float(MELEE_SCORES[eq_type])
        elif eq_type in RANGED_SCORES:
            eq_score = float(RANGED_SCORES[eq_type]) + 0.1
        best_inv_weapon = None
        best_inv_score = 0.0
        melee_score = float(inv_analysis["best_melee_score"])
        ranged_score = float(inv_analysis["best_ranged_score"])
        if ranged_score > 0.0:
            ranged_score += 0.1
        if ranged_score >= melee_score:
            best_inv_score = ranged_score
            best_inv_weapon = inv_analysis["best_ranged"]
        else:
            best_inv_score = melee_score
            best_inv_weapon = inv_analysis["best_melee"]
        if best_inv_score > eq_score and best_inv_weapon:
            item_id = best_inv_weapon.get("id")
            item_name = best_inv_weapon.get("typeId", "weapon")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, f"Equipping stronger weapon: {item_name}")
        eq_armor = self_data.get("equippedArmor")
        eq_armor_type = eq_armor.get("typeId", "").lower() if eq_armor else ""
        eq_armor_score = ARMOR_SCORES.get(eq_armor_type, 0)
        if inv_analysis["best_armor_score"] > eq_armor_score and inv_analysis["best_armor"]:
            item_id = inv_analysis["best_armor"].get("id")
            item_name = inv_analysis["best_armor"].get("typeId", "armor")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, f"Equipping stronger armor: {item_name}")
        item_to_drop_id = get_item_to_drop(inv_analysis, inv)
        if item_to_drop_id and item_to_drop_id not in self.memory.drop_attempts:
            self.memory.drop_attempts.add(item_to_drop_id)
            self.memory.pickup_attempts.clear()
            dropped_item = next((item for item in inv if item.get("id") == item_to_drop_id), None)
            dropped_name = dropped_item.get("typeId") if dropped_item else "item"
            return drop_payload(item_to_drop_id, f"Dropping weaker redundant item: {dropped_name}")
        flee_action = get_flee_action(frame_data, self.memory)
        if flee_action:
            return flee_action
        hp = self_data.get("hp", 0)
        if hp < 40:
            recovery_action = get_recovery_action(frame_data, self.memory)
            if recovery_action:
                return recovery_action
            combat_action = get_combat_action(frame_data, self.memory)
            if combat_action:
                return combat_action
        else:
            combat_action = get_combat_action(frame_data, self.memory)
            if combat_action:
                return combat_action
            recovery_action = get_recovery_action(frame_data, self.memory)
            if recovery_action:
                return recovery_action
        interact_action = get_interact_action(frame_data, self.memory)
        if interact_action:
            return interact_action
        connections_raw = current_region.get("connections", [])
        connections = [c.get("id") if isinstance(c, dict) else str(c) for c in connections_raw]
        chase_target_id = None
        for agent in get_visible_agents(frame_data):
            r_id = agent.get("regionId")
            t_hp = agent.get("hp", 0)
            if r_id in connections and 0 < t_hp <= 30:
                name = agent.get("name", "")
                if "Guardian" not in name and not agent.get("isGuardian", False):
                    chase_target_id = r_id
                    break
        if not chase_target_id:
            for monster in get_visible_monsters(frame_data):
                r_id = monster.get("regionId")
                t_hp = monster.get("hp", 0)
                if r_id in connections and 0 < t_hp <= 15:
                    type_id = (monster.get("type") or monster.get("typeId") or "").lower()
                    if "guardian" not in type_id:
                        chase_target_id = r_id
                        break
        available_actions = get_available_actions(frame_data)
        move_ok = available_actions.get("move", {}).get("ok", False)
        move_cost = available_actions.get("move", {}).get("cost", 2)
        if move_ok and self_data.get("ep", 0) >= move_cost and chase_target_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(chase_target_id, "Chasing low HP target in adjacent region")
        ruin_local = next((fac for fac in current_region.get("interactables", []) if fac.get("typeId", "").lower() == "ruin"), None)
        if ruin_local:
            gauge = ruin_local.get("gauge", ruin_local.get("ruinGauge", 0))
            occupied_by = ruin_local.get("occupiedBy")
            our_id = self_data.get("id")
            if gauge < 3 and (not occupied_by or occupied_by == our_id) and self_data.get("ep", 0) >= 2:
                return explore_payload("Exploring local ruin")
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
        death_zones = set()
        for r in visible_regions:
            r_id = r.get("id")
            if r_id:
                if r.get("isDeathZone", False):
                    death_zones.add(r_id)
                else:
                    safe_region_ids.add(r_id)
        adj_data = get_region_adjacency_map(frame_data)
        graph = adj_data.get("graph", {})
        dangerous_adj = set()
        for r_id in death_zones:
            for neighbor in graph.get(r_id, []):
                dangerous_adj.add(neighbor)
        ultra_safe_region_ids = safe_region_ids - dangerous_adj
        safe_connections = [c for c in connections if c in safe_region_ids]
        ultra_safe_connections = [c for c in connections if c in ultra_safe_region_ids]
        unvisited_ultra = [c for c in ultra_safe_connections if c not in self.memory.move_history]
        unvisited_safe = [c for c in safe_connections if c not in self.memory.move_history]
        next_fallback_id = None
        if unvisited_ultra:
            next_fallback_id = unvisited_ultra[0]
        elif ultra_safe_connections:
            next_fallback_id = ultra_safe_connections[0]
        elif unvisited_safe:
            next_fallback_id = unvisited_safe[0]
        elif safe_connections:
            next_fallback_id = safe_connections[0]
        elif connections:
            next_fallback_id = connections[0]
        if self_data.get("ep", 0) >= 2 and next_fallback_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(next_fallback_id, "Moving to unvisited region to search")
        if should_rest_for_ep(self_data, current_region):
            return rest_payload("Resting to recover EP")
        if self_data.get("ep", 0) < 2:
            return rest_payload("Resting to recover EP")
        return explore_payload("Exploring local region")