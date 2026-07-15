from typing import Dict, Any, List

def get_region_layers(frame_data: Dict[str, Any]) -> Dict[int, List[str]]:
    current_id = (
        frame_data.get("currentRegionId") or 
        frame_data.get("view", {}).get("currentRegionId") or 
        frame_data.get("view", {}).get("self", {}).get("regionId") or 
        frame_data.get("view", {}).get("self", {}).get("currentRegionId")
    )
    regions = (
        frame_data.get("view", {}).get("visibleRegions") or 
        frame_data.get("view", {}).get("regions") or 
        []
    )
    
    graph = {}
    id_to_name = {}
    for r in regions:
        r_id = r.get("id")
        r_name = r.get("name", r_id)
        id_to_name[r_id] = r_name
        
        connections = r.get("connectedRegions", [])
        neighbors = []
        for conn in connections:
            if isinstance(conn, dict):
                neighbors.append(conn.get("id"))
            else:
                neighbors.append(conn)
        graph[r_id] = neighbors

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