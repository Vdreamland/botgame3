from typing import Dict, Any, Optional
from ai.memory import BotMemory

def is_enemy_nearby(frame_data: Dict[str, Any], current_id: str) -> bool:
    from helpers.world_parser import get_visible_agents, get_visible_monsters, get_current_region
    current_reg = get_current_region(frame_data)
    connections = current_reg.get("connections", []) if current_reg else []
    nearby_regions = set(connections) | {current_id}
    for agent in get_visible_agents(frame_data):
        reg_id = agent.get("regionId")
        hp = agent.get("hp", 0)
        name = agent.get("name", "")
        if reg_id in nearby_regions and hp > 0 and "Guardian" not in name and not agent.get("isGuardian", False):
            return True
    for monster in get_visible_monsters(frame_data):
        reg_id = monster.get("regionId")
        hp = monster.get("hp", 0)
        type_id = (monster.get("type") or monster.get("typeId") or monster.get("name") or "").lower()
        if reg_id in nearby_regions and hp > 0 and "guardian" not in type_id:
            return True
    return False

def get_recovery_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    from helpers.actions_payload import use_item_payload
    from helpers.world_parser import get_self_agent, get_current_region, get_visible_agents
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return None
    current_id = current_region.get("id")
    hp = self_data.get("hp", 0)
    has_easy_kill = any(
        a.get("regionId") == current_id and 0 < a.get("hp", 0) <= 25 and "Guardian" not in a.get("name", "")
        for a in get_visible_agents(frame_data)
    )
    if has_easy_kill and hp > 40:
        return None
    hp_threshold = 60
    if is_enemy_nearby(frame_data, current_id):
        hp_threshold = 80
    ep = self_data.get("ep", 0)
    inventory = self_data.get("inventory", [])
    if hp < hp_threshold:
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
    ground_items = current_region.get("items", [])
    ground_type_ids = {item.get("typeId", "").lower() for item in ground_items if item.get("typeId")}
    has_ground_hp_item = any(tid in ["medkit", "emergency_food", "bandage"] for tid in ground_type_ids)
    has_ground_ep_item = any(tid in ["energy_drink", "emergency_food"] for tid in ground_type_ids)
    if has_ground_hp_item:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id == "medkit" and hp <= 70:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming medkit since replacements are on the ground")
                elif type_id == "emergency_food" and hp <= 80:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming emergency food since replacements are on the ground")
                elif type_id == "bandage" and hp <= 90:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, "Proactive HP restore: consuming bandage since replacements are on the ground")
    if has_ground_ep_item:
        for item in inventory:
            item_id = item.get("id")
            type_id = item.get("typeId", "").lower()
            if item_id and item_id not in memory.use_attempts:
                if type_id in ["energy_drink", "emergency_food"] and ep <= 5:
                    memory.use_attempts.add(item_id)
                    return use_item_payload(item_id, f"Proactive EP restore: consuming {type_id} since replacements are on the ground")
    return None

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
    has_threat = False
    for agent in get_visible_agents(frame_data):
        if agent.get("regionId") == current_id and agent.get("hp", 0) > 0:
            name = agent.get("name", "")
            if "Guardian" not in name and not agent.get("isGuardian", False):
                if agent.get("hp", 0) <= 25:
                    continue
                has_threat = True
                break
    for monster in get_visible_monsters(frame_data):
        if monster.get("regionId") == current_id and monster.get("hp", 0) > 0:
            type_id = (monster.get("type") or monster.get("typeId") or monster.get("name") or "").lower()
            if "guardian" not in type_id:
                has_threat = True
                break
    if has_threat and hp < 60:
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
            if reg_id in region_threat_counts and agent.get("hp", 0) > 0 and "Guardian" not in name and not agent.get("isGuardian", False):
                region_threat_counts[reg_id] += 1
        for monster in get_visible_monsters(frame_data):
            reg_id = monster.get("regionId")
            type_id = (monster.get("type") or monster.get("typeId") or monster.get("name") or "").lower()
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

def should_rest_for_ep(self_data: Dict[str, Any], current_region: Dict[str, Any]) -> bool:
    ep = self_data.get("ep", 0)
    is_death_zone = current_region.get("isDeathZone", False)
    if ep < 3 and not is_death_zone:
        return True
    return False