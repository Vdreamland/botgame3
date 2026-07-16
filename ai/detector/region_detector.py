from typing import Dict, Any, List
from helpers.world_parser import (
    get_region_adjacency_map,
    get_current_region,
    get_visible_regions,
    get_visible_agents,
    get_visible_monsters
)
from helpers.entities import MONSTERS, GUARDIAN_STATS
from helpers.items_spec import WEAPONS

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
                "interactables": current_reg.get("interactables", []),
                "is_death_zone": current_reg.get("isDeathZone", False)
            }
    for r in get_visible_regions(frame_data):
        r_id = r.get("id")
        if r_id:
            region_info[r_id] = {
                "items": r.get("items", []),
                "interactables": r.get("interactables", []),
                "is_death_zone": r.get("isDeathZone", False)
            }
    agents_by_region = {}
    monsters_by_region = {}
    for agent in get_visible_agents(frame_data):
        reg_id = agent.get("regionId")
        if reg_id:
            name = agent.get("name") or agent.get("username") or "Agent"
            hp = agent.get("hp", 0)
            ep = agent.get("ep", 0)
            base_atk = agent.get("atk", 25)
            def_val = agent.get("def", 5)
            if "Guardian" in name:
                atk = GUARDIAN_STATS.get("atk", 12)
                def_val = GUARDIAN_STATS.get("def", 120)
                if reg_id not in monsters_by_region:
                    monsters_by_region[reg_id] = []
                monsters_by_region[reg_id].append(f"{name} (HP {hp}/ATK {atk}/DEF {def_val})")
            else:
                if reg_id not in agents_by_region:
                    agents_by_region[reg_id] = []
                kills = agent.get("kills", agent.get("killCount", 0))
                weapon = agent.get("equippedWeapon")
                weapon_name = "none"
                weapon_bonus = 0
                if weapon:
                    weapon_name = weapon.get("name") if isinstance(weapon, dict) else weapon
                    if weapon_name == "Fist":
                        weapon_name = "none"
                    if weapon_name != "none":
                        weapon_key = weapon_name.lower().replace(" ", "_")
                        weapon_bonus = WEAPONS.get(weapon_key, {}).get("atk_bonus", 0)
                armor = agent.get("equippedArmor")
                armor_name = "none"
                if armor:
                    armor_name = armor.get("name") if isinstance(armor, dict) else armor
                effective_atk = base_atk + weapon_bonus
                agents_by_region[reg_id].append(f"{name} (HP {hp}/EP {ep}/ATK {effective_atk}/DEF {def_val}/KILLS {kills} | Weapon: {weapon_name} | Armour: {armor_name})")
    for monster in get_visible_monsters(frame_data):
        reg_id = monster.get("regionId")
        if reg_id:
            if reg_id not in monsters_by_region:
                monsters_by_region[reg_id] = []
            name = monster.get("name") or monster.get("typeId") or "Monster"
            hp = monster.get("hp", 0)
            type_id = (monster.get("typeId") or monster.get("name") or "").lower()
            if "guardian" in type_id:
                static_stats = GUARDIAN_STATS
            else:
                static_stats = MONSTERS.get(type_id, {})
            atk = monster.get("atk") or static_stats.get("atk", 0)
            def_val = monster.get("def") or static_stats.get("def", 0)
            monsters_by_region[reg_id].append(f"{name} (HP {hp}/ATK {atk}/DEF {def_val})")
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
        is_death_zone = details.get("is_death_zone", False)
        agents_in_reg = agents_by_region.get(r_id, [])
        monsters_in_reg = monsters_by_region.get(r_id, [])
        region_title = base_name
        if is_death_zone:
            region_title = f"{base_name} (\033[91mDEATH ZONE\033[0m)"
        region_block = [f"  {region_title} :"]
        if agents_in_reg:
            region_block.append(f"    Player : {', '.join(agents_in_reg)}")
        if monsters_in_reg:
            region_block.append(f"    Monster : {', '.join(monsters_in_reg)}")
        item_parts = []
        if items:
            items_summary = ", ".join(item.get("name", "item") for item in items)
            item_parts.append(f"Loot: {items_summary}")
        if interactables:
            facs_summary = ", ".join(fac.get("name", "facility") for fac in interactables)
            item_parts.append(f"Facility: {facs_summary}")
        if item_parts:
            region_block.append(f"    Item : {' | '.join(item_parts)}")
        region_str = "\n".join(region_block)
        layers[dist].append(region_str)
    return layers

def format_region_layers(layers: Dict[int, List[str]]) -> str:
    lines = ["Region Detector :"]
    for dist in sorted(layers.keys()):
        lines.append(f"Layer {dist} :")
        regions_str = "\n\n".join(layers[dist])
        lines.append(regions_str)
    return "\n".join(lines)