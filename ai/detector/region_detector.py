from typing import Dict, Any, List
from helpers.world_parser import get_region_adjacency_map

def get_region_layers(frame_data: Dict[str, Any]) -> Dict[int, List[str]]:
    adj_data = get_region_adjacency_map(frame_data)
    current_id = adj_data["current_id"]
    id_to_name = adj_data["id_to_name"]
    graph = adj_data["graph"]

    from collections import deque
    queue = deque([(current_id, 0)])
    visited = {current_id: 0}
    
    while queue:
        node, dist = queue.popleft()
        neighbors = graph.get(node, [])
        for nbr in neighbors:
            if nbr in id_to_name and nbr not in visited:
                visited[nbr] = dist + 1
                queue.append((nbr, dist + 1))
    
    layers = {}
    for r_id, dist in visited.items():
        if dist == 0:
            continue
        if dist not in layers:
            layers[dist] = []
        layers[dist].append(id_to_name[r_id])
        
    return layers

def format_region_layers(layers: Dict[int, List[str]]) -> str:
    lines = ["Region Detector :"]
    for dist in sorted(layers.keys()):
        regions_str = ", ".join(layers[dist])
        lines.append(f"Layer {dist} : {regions_str}")
    return "\n".join(lines)