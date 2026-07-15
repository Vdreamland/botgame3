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