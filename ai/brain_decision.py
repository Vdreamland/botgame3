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
    drop_payload,
    pickup_payload
)
from ai.memory import BotMemory
from ai.strategy.inventory_manager import analyze_inventory, get_item_to_drop, MELEE_SCORES, RANGED_SCORES, ARMOR_SCORES, is_sword_master_active
from ai.strategy.survival_manager import get_recovery_action, get_flee_action, should_rest_for_ep
from ai.strategy.combat_strategy import get_combat_action
from ai.strategy.loot_strategy import get_pickup_action, get_interact_action, find_target_regions
from ai.strategy.movement_strategy import find_shortest_path
from ai.strategy.ruins_explore_strategy import get_ruin_explore_action
from helpers.api_config import get_bots_config

class BrainDecision:
    def __init__(self):
        self.memory = BotMemory()
        self.last_turn = -1

    def get_next_action(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_region = get_current_region(frame_data)
        self_data = get_self_agent(frame_data)
        if not current_region or not self_data:
            return None
        current_id = current_region.get("id")
        self.memory.add_visited_region(current_id)
        turn = frame_data.get("turn", 0)
        if turn != self.last_turn:
            self.last_turn = turn
            self.memory.pickup_attempts.clear()
            self.memory.equipped_attempts.clear()
            self.memory.drop_attempts.clear()
            self.memory.use_attempts.clear()
            self.memory.failed_attacks.clear()
            self.memory.failed_items.clear()
            self.memory.failed_facilities.clear()
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
        current_enemy_ids = {a.get("id") for a in get_visible_agents(frame_data) if a.get("id")} | {m.get("id") for m in get_visible_monsters(frame_data) if m.get("id")}
        self.memory.track_action_failure(current_item_ids, current_fac_ids, current_enemy_ids)
        if not hasattr(self.memory, "known_death_zones"):
            self.memory.known_death_zones = set()
        visible_regions = get_visible_regions(frame_data)
        for r in visible_regions:
            r_id = r.get("id")
            if r_id and r.get("isDeathZone", False):
                self.memory.known_death_zones.add(r_id)
        inv = self_data.get("inventory", [])
        sim_inv = list(inv)
        for item in current_items:
            i_id = item.get("id")
            if i_id and i_id in self.memory.pickup_attempts:
                if not any(x.get("id") == i_id for x in sim_inv):
                    sim_inv.append(item)
        sim_inv = [x for x in sim_inv if x.get("id") not in self.memory.drop_attempts]
        is_sm = is_sword_master_active(self_data)
        inv_analysis = analyze_inventory(sim_inv, is_sm)
        eq_weapon = self_data.get("equippedWeapon")
        eq_armor = self_data.get("equippedArmor")
        has_good_weapon = False
        if eq_weapon:
            eq_w_type = (eq_weapon.get("typeId") or eq_weapon.get("name") or "").lower().replace(" ", "_")
            if eq_w_type in MELEE_SCORES and MELEE_SCORES[eq_w_type] >= 2:
                has_good_weapon = True
            elif eq_w_type in RANGED_SCORES and RANGED_SCORES[eq_w_type] >= 2:
                has_good_weapon = True
        has_good_armor = False
        if eq_armor:
            eq_a_type = (eq_armor.get("typeId") or eq_armor.get("name") or "").lower().replace(" ", "_")
            if eq_a_type in ARMOR_SCORES and ARMOR_SCORES[eq_a_type] >= 2:
                has_good_armor = True
        has_recovery = (inv_analysis.get("hp_count", 0) + inv_analysis.get("ep_count", 0)) >= 2
        is_loadout_optimal = has_good_weapon and has_good_armor and has_recovery
        eq_type = (eq_weapon.get("typeId") or eq_weapon.get("name") or "").lower().replace(" ", "_") if eq_weapon else ""
        enemy_at_dist_0 = any(
            agent.get("regionId") == current_id and agent.get("hp", 0) > 0 and "Guardian" not in agent.get("name", "") and not agent.get("isGuardian", False)
            for agent in get_visible_agents(frame_data)
        )
        enemy_at_dist_range = any(
            agent.get("regionId") != current_id and agent.get("hp", 0) > 0 and "Guardian" not in agent.get("name", "") and not agent.get("isGuardian", False)
            for agent in get_visible_agents(frame_data)
        )
        eq_score = 0.0
        if eq_type in MELEE_SCORES:
            eq_score = float(MELEE_SCORES[eq_type])
            if is_sm:
                eq_score += 5.0
            if enemy_at_dist_0:
                eq_score += 0.1
        elif eq_type in RANGED_SCORES:
            eq_score = float(RANGED_SCORES[eq_type])
            if not enemy_at_dist_0 and enemy_at_dist_range:
                eq_score += 0.1
        best_inv_weapon = None
        best_inv_score = 0.0
        melee_score = float(inv_analysis["best_melee_score"])
        ranged_score = float(inv_analysis["best_ranged_score"])
        if enemy_at_dist_0:
            if melee_score > 0.0:
                melee_score += 0.1
            if melee_score >= ranged_score:
                best_inv_score = melee_score
                best_inv_weapon = inv_analysis["best_melee"]
            else:
                best_inv_score = ranged_score
                best_inv_weapon = inv_analysis["best_ranged"]
        elif enemy_at_dist_range:
            if is_sm:
                if melee_score >= ranged_score:
                    best_inv_score = melee_score
                    best_inv_weapon = inv_analysis["best_melee"]
                else:
                    best_inv_score = ranged_score
                    best_inv_weapon = inv_analysis["best_ranged"]
            else:
                if ranged_score > 0.0:
                    best_inv_score = ranged_score
                    best_inv_weapon = inv_analysis["best_ranged"]
                else:
                    best_inv_score = melee_score
                    best_inv_weapon = inv_analysis["best_melee"]
        else:
            if melee_score >= ranged_score:
                best_inv_score = melee_score
                best_inv_weapon = inv_analysis["best_melee"]
            else:
                best_inv_score = ranged_score
                best_inv_weapon = inv_analysis["best_ranged"]
        flee_action = get_flee_action(frame_data, self.memory)
        if flee_action:
            return flee_action
        if not eq_weapon and best_inv_weapon:
            item_id = best_inv_weapon.get("id")
            item_name = best_inv_weapon.get("typeId", "weapon")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, f"Equipping stronger weapon: {item_name}")
        should_swap = False
        if eq_weapon and best_inv_weapon:
            best_inv_type = best_inv_weapon.get("typeId", "").lower()
            if is_sm and eq_type in RANGED_SCORES and best_inv_type in MELEE_SCORES:
                should_swap = True
            elif enemy_at_dist_0 and best_inv_type in MELEE_SCORES and eq_type in RANGED_SCORES:
                should_swap = True
            elif not enemy_at_dist_0 and enemy_at_dist_range and best_inv_type in RANGED_SCORES and eq_type in MELEE_SCORES and not is_sm:
                should_swap = True
            elif best_inv_type in MELEE_SCORES and eq_type in MELEE_SCORES and MELEE_SCORES[best_inv_type] > MELEE_SCORES[eq_type]:
                should_swap = True
            elif best_inv_type in RANGED_SCORES and eq_type in RANGED_SCORES and RANGED_SCORES[best_inv_type] > RANGED_SCORES[eq_type]:
                should_swap = True
            elif not enemy_at_dist_0 and not enemy_at_dist_range:
                best_inv_rating = float(MELEE_SCORES.get(best_inv_type, RANGED_SCORES.get(best_inv_type, 0.0)))
                eq_rating = float(MELEE_SCORES.get(eq_type, RANGED_SCORES.get(eq_type, 0.0)))
                if is_sm:
                    if best_inv_type in MELEE_SCORES:
                        best_inv_rating += 5.0
                    if eq_type in MELEE_SCORES:
                        eq_rating += 5.0
                if best_inv_rating > eq_rating:
                    should_swap = True
        if should_swap and best_inv_weapon:
            item_id = best_inv_weapon.get("id")
            item_name = best_inv_weapon.get("typeId", "weapon")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, f"Equipping stronger weapon: {item_name}")
        eq_armor_type = (eq_armor.get("typeId") or eq_armor.get("name") or "").lower().replace(" ", "_") if eq_armor else ""
        eq_armor_score = ARMOR_SCORES.get(eq_armor_type, 0)
        if inv_analysis["best_armor_score"] > eq_armor_score and inv_analysis["best_armor"]:
            item_id = inv_analysis["best_armor"].get("id")
            item_name = inv_analysis["best_armor"].get("typeId", "armor")
            if item_id and item_id not in self.memory.equipped_attempts:
                self.memory.equipped_attempts.add(item_id)
                return equip_payload(item_id, f"Equipping stronger armor: {item_name}")
        hp = self_data.get("hp", 0)
        emergency_threshold = 40
        if enemy_at_dist_0:
            emergency_threshold = 70
        if hp < emergency_threshold:
            recovery_action = get_recovery_action(frame_data, self.memory)
            if recovery_action:
                return recovery_action
        has_weapon = (best_inv_score > 0.0) or (eq_score > 0.0)
        pickup_action = None
        if not has_weapon and len(sim_inv) < 10:
            local_weapon = next((item for item in current_items if item.get("category", "").lower() == "weapon"), None)
            if local_weapon and local_weapon.get("id") not in self.memory.pickup_attempts and local_weapon.get("id") not in self.memory.failed_items:
                item_name = local_weapon.get("typeId", "weapon")
                item_id = local_weapon.get("id")
                self.memory.pickup_attempts.add(item_id)
                self.memory.last_target_id = item_id
                self.memory.last_action_type = "pickup"
                pickup_action = pickup_payload(item_id, f"Picking up local weapon: {item_name}")
        if not pickup_action:
            pickup_action = get_pickup_action(frame_data, self.memory)
        if pickup_action:
            return pickup_action
        combat_action = get_combat_action(frame_data, self.memory)
        if combat_action:
            return combat_action
        item_to_drop_id = get_item_to_drop(inv_analysis, sim_inv)
        if item_to_drop_id and item_to_drop_id not in self.memory.drop_attempts:
            self.memory.drop_attempts.add(item_to_drop_id)
            self.memory.pickup_attempts.clear()
            dropped_item = next((item for item in sim_inv if item.get("id") == item_to_drop_id), None)
            dropped_name = dropped_item.get("typeId") if dropped_item else "item"
            return drop_payload(item_to_drop_id, f"Dropping weaker redundant item: {dropped_name}")
        recovery_action = get_recovery_action(frame_data, self.memory)
        if recovery_action:
            return recovery_action
        if not is_loadout_optimal:
            interact_action = get_interact_action(frame_data, self.memory)
            if interact_action:
                return interact_action
        ruin_action = get_ruin_explore_action(frame_data)
        if ruin_action:
            return ruin_action
        full_curr_region = next((r for r in visible_regions if r.get("id") == current_id), current_region)
        connections_raw = full_curr_region.get("connections", [])
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
        bypass_combat_for_loot = False
        urgent_loot_region_id = None
        if move_ok and self_data.get("ep", 0) >= move_cost:
            for r in visible_regions:
                r_id = r.get("id")
                if r_id in connections and not r.get("isDeathZone", False):
                    items = r.get("items", [])
                    if any(item.get("typeId", "").lower() in ["smoltz", "moltz"] for item in items):
                        urgent_loot_region_id = r_id
                        bypass_combat_for_loot = True
                        break
        if combat_action:
            if not enemy_at_dist_0 and bypass_combat_for_loot and urgent_loot_region_id:
                self.memory.last_target_id = None
                self.memory.last_action_type = "move"
                return move_payload(urgent_loot_region_id, "Bypassing combat to secure adjacent sMoltz")
            return combat_action
        if move_ok and self_data.get("ep", 0) >= move_cost and chase_target_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(chase_target_id, "Chasing low HP target in adjacent region")
        if is_loadout_optimal and move_ok and self_data.get("ep", 0) >= move_cost:
            visible_enemies = []
            friendly_names = {bot["name"] for bot in get_bots_config()}
            for agent in get_visible_agents(frame_data):
                if agent.get("hp", 0) > 0 and agent.get("id") != self_data.get("id"):
                    name = agent.get("name", "")
                    if name in friendly_names:
                        continue
                    if "Guardian" not in name and not agent.get("isGuardian", False):
                        r_id = agent.get("regionId")
                        if r_id:
                            visible_enemies.append(r_id)
            if visible_enemies:
                path = find_shortest_path(frame_data, visible_enemies)
                if path and len(path) > 1:
                    next_region_id = path[1]
                    self.memory.last_target_id = None
                    self.memory.last_action_type = "move"
                    return move_payload(next_region_id, "Hunting visible player in adjacent region")
        if move_ok and self_data.get("ep", 0) >= move_cost:
            target_regions = find_target_regions(frame_data, self.memory)
            if target_regions:
                path = find_shortest_path(frame_data, target_regions)
                if path and len(path) > 1:
                    next_region_id = path[1]
                    self.memory.last_target_id = None
                    self.memory.last_action_type = "move"
                    return move_payload(next_region_id, "Moving to target region")
        safe_region_ids = set()
        death_zones = set()
        for r in visible_regions:
            r_id = r.get("id")
            if r_id:
                if r.get("isDeathZone", False) or r_id in self.memory.known_death_zones:
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
        fallback_link_counts = {}
        for c_id in connections:
            r_obj = next((r for r in visible_regions if r.get("id") == c_id), None)
            if r_obj:
                links = len(r_obj.get("connections", []))
                fallback_link_counts[c_id] = links
            else:
                fallback_link_counts[c_id] = 0
        safe_connections = sorted([c for c in connections if c in safe_region_ids], key=lambda x: fallback_link_counts.get(x, 0), reverse=True)
        ultra_safe_connections = sorted([c for c in connections if c in ultra_safe_region_ids], key=lambda x: fallback_link_counts.get(x, 0), reverse=True)
        unvisited_ultra = sorted([c for c in ultra_safe_connections if c not in self.memory.move_history], key=lambda x: fallback_link_counts.get(x, 0), reverse=True)
        unvisited_safe = sorted([c for c in safe_connections if c not in self.memory.move_history], key=lambda x: fallback_link_counts.get(x, 0), reverse=True)
        active_connections = [c for c in connections if c not in death_zones and c not in self.memory.known_death_zones]
        active_connections = sorted(active_connections, key=lambda x: fallback_link_counts.get(x, 0), reverse=True)
        next_fallback_id = None
        if unvisited_ultra:
            next_fallback_id = unvisited_ultra[0]
        elif ultra_safe_connections:
            next_fallback_id = ultra_safe_connections[0]
        elif unvisited_safe:
            next_fallback_id = unvisited_safe[0]
        elif safe_connections:
            next_fallback_id = safe_connections[0]
        elif active_connections:
            next_fallback_id = active_connections[0]
        if self_data.get("ep", 0) >= move_cost and next_fallback_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(next_fallback_id, "Moving to unvisited region to search")
        if should_rest_for_ep(frame_data):
            return rest_payload("Resting to recover EP")
        if self_data.get("ep", 0) < move_cost:
            return rest_payload("Resting to recover EP")
        return explore_payload("Exploring local region")