from typing import Dict, Any, Optional
from ai.memory import BotMemory
from helpers.items_spec import WEAPONS
from helpers.game_constants import WEATHER_MODIFIERS
from helpers.strategy_brain import calculate_final_damage, get_loadout_damage_multiplier
from helpers.api_config import get_bots_config

def get_flee_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    from helpers.world_parser import get_self_agent, get_current_region, get_visible_agents, get_visible_monsters
    from helpers.actions_payload import move_payload
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return None
    current_id = current_region.get("id")
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    if ep < 2:
        return None
    inventory = self_data.get("inventory", [])
    eq_weapon = self_data.get("equippedWeapon")
    best_w_bonus = 0
    if not eq_weapon:
        for item in inventory:
            if item.get("category", "").lower() == "weapon":
                w_type = item.get("typeId", "").lower().replace(" ", "_")
                best_w_bonus = max(best_w_bonus, WEAPONS.get(w_type, {}).get("atk_bonus", 0))
    our_atk = self_data.get("atk", 25)
    our_def = self_data.get("def", 5)
    weather = current_region.get("weather", "clear") if current_region else "clear"
    weather_mod = WEATHER_MODIFIERS.get(weather.lower(), 0)
    friendly_names = {bot["name"] for bot in get_bots_config()}
    threat_count = 0
    for agent in get_visible_agents(frame_data):
        if agent.get("regionId") == current_id and agent.get("hp", 0) > 0 and agent.get("id") != self_data.get("id"):
            name = agent.get("name", "")
            if name in friendly_names:
                continue
            if "Guardian" not in name and not agent.get("isGuardian", False):
                threat_count += 1
    for monster in get_visible_monsters(frame_data):
        if monster.get("regionId") == current_id and monster.get("hp", 0) > 0:
            type_id = (monster.get("type") or monster.get("typeId") or "").lower()
            if "guardian" not in type_id:
                if hp < 40:
                    threat_count += 1
    has_easy_kill = False
    dmg_mult = get_loadout_damage_multiplier(self_data)
    for agent in get_visible_agents(frame_data):
        if agent.get("regionId") == current_id and agent.get("hp", 0) > 0 and agent.get("id") != self_data.get("id"):
            name = agent.get("name", "")
            if name in friendly_names:
                continue
            if "Guardian" not in name and not agent.get("isGuardian", False):
                t_hp = agent.get("hp", 0)
                t_def = agent.get("def", 5)
                est_dmg = calculate_final_damage(our_atk, best_w_bonus, t_def, weather_mod, dmg_mult)
                enemy_atk = agent.get("atk", 25)
                enemy_dmg = calculate_final_damage(enemy_atk, 0, our_def, weather_mod)
                turns_to_kill_them = (t_hp + est_dmg - 1) // est_dmg if est_dmg > 0 else 999
                turns_to_kill_us = (hp + enemy_dmg - 1) // enemy_dmg if enemy_dmg > 0 else 999
                if threat_count >= 2:
                    if t_hp <= est_dmg:
                        has_easy_kill = True
                        break
                else:
                    if est_dmg > 0 and (t_hp <= est_dmg or turns_to_kill_them <= turns_to_kill_us):
                        has_easy_kill = True
                        break
    if not has_easy_kill:
        for monster in get_visible_monsters(frame_data):
            if monster.get("regionId") == current_id and monster.get("hp", 0) > 0:
                type_id = (monster.get("type") or monster.get("typeId") or "").lower()
                if "guardian" not in type_id:
                    t_hp = monster.get("hp", 0)
                    t_def = monster.get("def", 5)
                    est_dmg = calculate_final_damage(our_atk, best_w_bonus, t_def, weather_mod, dmg_mult)
                    m_atk = monster.get("atk", 10)
                    enemy_dmg = calculate_final_damage(m_atk, 0, our_def, weather_mod)
                    turns_to_kill_them = (t_hp + est_dmg - 1) // est_dmg if est_dmg > 0 else 999
                    turns_to_kill_us = (hp + enemy_dmg - 1) // enemy_dmg if enemy_dmg > 0 else 999
                    if threat_count >= 2:
                        if t_hp <= est_dmg:
                            break
                    else:
                        if est_dmg > 0 and (t_hp <= est_dmg or turns_to_kill_them <= turns_to_kill_us):
                            has_easy_kill = True
                            break
    if has_easy_kill:
        return None
    is_death_zone = current_region.get("isDeathZone", False) or current_region.get("is_death_zone", False)
    should_flee = False
    has_guardian_on_tile = any(
        (monster.get("regionId") == current_id and monster.get("hp", 0) > 0 and "guardian" in (monster.get("type") or monster.get("typeId") or "").lower())
        for monster in get_visible_monsters(frame_data)
    )
    alert_active = self_data.get("alertActive") or self_data.get("alert_active") or False
    if has_guardian_on_tile and (alert_active or hp < 70):
        should_flee = True
    elif is_death_zone and ep >= 2:
        should_flee = True
    else:
        flee_threshold = 60
        if threat_count >= 2:
            flee_threshold = 90
        if threat_count > 0 and hp < flee_threshold:
            should_flee = True
    if should_flee:
        visible_regions = frame_data.get("view", {}).get("visibleRegions", [])
        safe_regions = set()
        region_threat_counts = {}
        for r in visible_regions:
            r_id = r.get("id")
            if r_id and not r.get("isDeathZone", False):
                safe_regions.add(r_id)
                region_threat_counts[r_id] = 0
        for agent in get_visible_agents(frame_data):
            reg_id = agent.get("regionId")
            name = agent.get("name", "")
            if name in friendly_names:
                continue
            if reg_id in region_threat_counts and agent.get("hp", 0) > 0 and "Guardian" not in name and not agent.get("isGuardian", False):
                region_threat_counts[reg_id] += 1
        for monster in get_visible_monsters(frame_data):
            reg_id = monster.get("regionId")
            type_id = (monster.get("type") or monster.get("typeId") or "").lower()
            if reg_id in region_threat_counts and monster.get("hp", 0) > 0 and "guardian" not in type_id:
                region_threat_counts[reg_id] += 1
        connections = current_region.get("connections", [])
        safe_connections = [c for c in connections if c in safe_regions]
        if not safe_connections:
            return None
        best_escape_id = None
        min_threat = 999999
        unvisited_connections = [c for c in safe_connections if c not in memory.move_history]
        candidates = unvisited_connections if unvisited_connections else safe_connections
        for c in candidates:
            threat = region_threat_counts.get(c, 0)
            if threat < min_threat:
                min_threat = threat
                best_escape_id = c
        if best_escape_id:
            memory.last_target_id = None
            memory.last_action_type = "move"
            return move_payload(best_escape_id, f"Fleeing threat to safe region (Threat count: {min_threat})")
    return None