from typing import Dict, Any, List, Optional
from helpers.world_parser import get_region_adjacency_map

def find_shortest_path(frame_data: Dict[str, Any], target_region_ids: List[str]) -> Optional[List[str]]:
    adj_data = get_region_adjacency_map(frame_data)
    start_id = adj_data.get("current_id")
    graph = adj_data.get("graph", {})
    if not start_id or not target_region_ids:
        return None
    if start_id in target_region_ids:
        return [start_id]
    from helpers.world_parser import get_visible_ruins, get_self_agent
    self_data = get_self_agent(frame_data)
    our_id = self_data.get("id") if self_data else None
    visible_ruins = get_visible_ruins(frame_data)
    occupied_ruin_ids = set()
    for ruin in visible_ruins:
        r_id = ruin.get("id") or ruin.get("ruinId")
        if r_id:
            occupied_by = ruin.get("occupiedBy")
            if occupied_by and occupied_by != our_id:
                occupied_ruin_ids.add(r_id)
    view = frame_data.get("view", {})
    death_zones = {r.get("id") for r in view.get("visibleRegions", []) if r.get("isDeathZone", False)}
    dangerous_zones = set(death_zones)
    for r_id in death_zones:
        for neighbor in graph.get(r_id, []):
            dangerous_zones.add(neighbor)
    from collections import deque
    queue = deque([[start_id]])
    visited = {start_id}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node in target_region_ids:
            return path
        for neighbor in graph.get(node, []):
            if neighbor not in visited and neighbor not in dangerous_zones and neighbor not in occupied_ruin_ids:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    queue = deque([[start_id]])
    visited = {start_id}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node in target_region_ids:
            return path
        for neighbor in graph.get(node, []):
            if neighbor not in visited and neighbor not in death_zones and neighbor not in occupied_ruin_ids:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None