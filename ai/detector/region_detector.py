from typing import Dict, Any, List
from helpers.world_parser import get_region_adjacency_map, get_current_region, get_visible_regions

def get_region_layers(frame_data: Dict[str, Any]) -> Dict[int, List[str]]:
    adj_data = get_region_adjacency_map(frame_data)
    current_id = adj_data["current_id"]
    id_to_name = adj_data["id_to_name"]
    graph = adj_data["graph"]
    region_info = {}
    current_reg = get_current_region(frame_data)
    if current_reg:
        r_id = current_reg.get("id")
        if r_id:
            region_info[r_id] = {
                "items": current_reg.get("items", []),
                "interactables": current_reg.get("interactables", [])
            }
    for r in get_visible_regions(frame_data):
        r_id = r.get("id")
        if r_id:
            region_info[r_id] = {
                "items": r.get("items", []),
                "interactables": r.get("interactables", [])
            }
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
        if dist not in layers:
            layers[dist] = []
        base_name = id_to_name[r_id]
        details = region_info.get(r_id, {})
        items = details.get("items", [])
        interactables = details.get("interactables", [])
        info_parts = []
        if items:
            items_summary = ", ".join(item.get("name", "item") for item in items)
            info_parts.append(f"Loot: {items_summary}")
        if interactables:
            facs_summary = ", ".join(fac.get("name", "facility") for fac in interactables)
            info_parts.append(f"Facility: {facs_summary}")
        if info_parts:
            region_str = f"{base_name} ({' | '.join(info_parts)})"
        else:
            region_str = base_name
        layers[dist].append(region_str)
    return layers

def format_region_layers(layers: Dict[int, List[str]]) -> str:
    lines = ["Region Detector :"]
    for dist in sorted(layers.keys()):
        regions_str = ", ".join(layers[dist])
        lines.append(f"Layer {dist} : {regions_str}")
    return "\n".join(lines)