from typing import Dict, Any, List, Optional

def get_agent_id(frame_data: Dict[str, Any]) -> str:
    return frame_data.get("agentId", "")

def get_game_id(frame_data: Dict[str, Any]) -> str:
    return frame_data.get("gameId", "")

def get_game_status(frame_data: Dict[str, Any]) -> str:
    return frame_data.get("status", "")

def get_turn(frame_data: Dict[str, Any]) -> int:
    return frame_data.get("turn", 1)

def get_self_agent(frame_data: Dict[str, Any]) -> Dict[str, Any]:
    return frame_data.get("view", {}).get("self", {})

def get_current_region(frame_data: Dict[str, Any]) -> Dict[str, Any]:
    return frame_data.get("view", {}).get("currentRegion", {})

def get_visible_regions(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("visibleRegions", [])

def get_visible_agents(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("visibleAgents", [])

def get_visible_monsters(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("visibleMonsters", [])

def get_visible_npcs(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("visibleNPCs", [])

def get_visible_ruins(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("visibleRuins", [])

def get_my_relics(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("myRelics", [])

def get_my_packs(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("myPacks", [])

def get_recent_logs(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return frame_data.get("view", {}).get("recentLogs", [])

def get_alive_count(frame_data: Dict[str, Any]) -> int:
    return frame_data.get("view", {}).get("aliveCount", 0)

def get_available_actions(frame_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return frame_data.get("view", {}).get("availableActions", {})

def get_region_details(region_obj: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": region_obj.get("id", ""),
        "name": region_obj.get("name", "unknown"),
        "terrain": region_obj.get("terrain", "unknown"),
        "weather": region_obj.get("weather", "unknown"),
        "vision": region_obj.get("visionModifier", 0),
        "links": len(region_obj.get("connections", [])),
        "connections": region_obj.get("connections", []),
        "is_death_zone": region_obj.get("isDeathZone", False),
        "interactables": region_obj.get("interactables", [])
    }

def get_agent_inventory(self_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return self_data.get("inventory", [])

def get_equipped_weapon(self_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return self_data.get("equippedWeapon")

def get_applied_affixes(self_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return self_data.get("appliedAffixes", [])

def get_relic_stats(self_data: Dict[str, Any]) -> Dict[str, int]:
    return self_data.get("relicStats", {})

def get_region_adjacency_map(frame_data: Dict[str, Any]) -> Dict[str, Any]:
    current_reg = get_current_region(frame_data)
    current_id = current_reg.get("id")
    graph = {}
    id_to_name = {}
    if current_id:
        id_to_name[current_id] = current_reg.get("name", current_id)
        graph[current_id] = current_reg.get("connections", [])
    for r in get_visible_regions(frame_data):
        r_id = r.get("id")
        id_to_name[r_id] = r.get("name", r_id)
        graph[r_id] = r.get("connections", [])
    return {
        "current_id": current_id,
        "id_to_name": id_to_name,
        "graph": graph
    }

def get_death_logs(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    deaths = []
    for entry in get_recent_logs(frame_data):
        log_obj = entry.get("log", {})
        if log_obj.get("type") == "death":
            details = log_obj.get("details", {})
            deaths.append({
                "message": log_obj.get("message", ""),
                "target_id": log_obj.get("target", ""),
                "target_name": details.get("targetName", ""),
                "killed_by": details.get("killedBy") or log_obj.get("agentId", ""),
                "killer_name": details.get("killerName", "")
            })
    return deaths

def get_combat_logs(frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    combat = []
    for entry in get_recent_logs(frame_data):
        log_obj = entry.get("log", {})
        details = log_obj.get("details", {})
        if details.get("verb") == "attack" or log_obj.get("type") == "attack":
            combat.append({
                "attacker_id": log_obj.get("agentId", ""),
                "attacker_name": log_obj.get("message", "").split(" attacked ")[0] if " attacked " in log_obj.get("message", "") else "unknown",
                "target_id": details.get("targetId", ""),
                "target_name": details.get("targetName", ""),
                "damage": details.get("damage", 0),
                "actual_hp_drop": details.get("actualHpDrop", 0),
                "new_hp": details.get("newHp", 0)
            })
    return combat

def get_my_combat_events(frame_data: Dict[str, Any], my_id: str) -> Dict[str, List[Dict[str, Any]]]:
    combat_logs = get_combat_logs(frame_data)
    outbound = []
    inbound = []
    for log in combat_logs:
        if log["attacker_id"] == my_id:
            outbound.append(log)
        if log["target_id"] == my_id:
            inbound.append(log)
    return {
        "outbound": outbound,
        "inbound": inbound
    }

def is_bot_dead_in_logs(frame_data: Dict[str, Any], bot_name: str) -> bool:
    self_data = frame_data.get("view", {}).get("self", {})
    actual_name = self_data.get("name", "")
    for log_entry in get_death_logs(frame_data):
        msg = log_entry.get("message", "")
        if bot_name in msg or (actual_name and actual_name in msg):
            return True
    return False

def get_bot_death_details(frame_data: Dict[str, Any], bot_name: str) -> Optional[Dict[str, Any]]:
    self_data = frame_data.get("view", {}).get("self", {})
    actual_name = self_data.get("name", "")
    for log in get_combat_logs(frame_data):
        t_name = log.get("target_name")
        if (t_name == bot_name or (actual_name and t_name == actual_name)) and log.get("new_hp") == 0:
            return {
                "killer": log.get("attacker_name", "unknown"),
                "damage": log.get("damage", 0)
            }
    for log in get_death_logs(frame_data):
        msg = log.get("message", "")
        if bot_name in msg or (actual_name and actual_name in msg):
            return {
                "killer": log.get("killer_name") or "unknown",
                "damage": "unknown"
            }
    return None