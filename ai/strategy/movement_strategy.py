from typing import Dict, Any, List, Optional
from collections import deque
from helpers.world_parser import get_region_adjacency_map

def find_shortest_path(frame_data: Dict[str, Any], target_region_ids: List[str]) -> Optional[List[str]]:
    adj_data = get_region_adjacency_map(frame_data)
    start_id = adj_data.get("current_id")
    graph = adj_data.get("graph", {})
    if not start_id or not target_region_ids:
        return None
    target_set = set(target_region_ids)
    if start_id in target_set:
        return [start_id]
    queue = deque([[start_id]])
    visited = {start_id}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                new_path = list(path) + [neighbor]
                if neighbor in target_set:
                    return new_path
                visited.add(neighbor)
                queue.append(new_path)
    return None