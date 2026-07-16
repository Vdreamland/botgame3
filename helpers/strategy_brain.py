from typing import Dict, Any, List, Optional

def calculate_final_damage(atk: int, weapon_bonus: int, def_val: int, weather_mod: int) -> int:
    raw_damage = atk + weapon_bonus - def_val + weather_mod
    return max(1, raw_damage)

def resolve_connected_region(entry: Any, visible_regions: List[Any]) -> Optional[Dict[str, Any]]:
    if isinstance(entry, dict):
        return entry
    for r in visible_regions:
        if isinstance(r, dict) and r.get("id") == entry:
            return r
    return None

def is_region_safe_from_death_zone(region_id: str, pending_deathzones: List[Any]) -> bool:
    for dz in pending_deathzones:
        if isinstance(dz, dict) and dz.get("id") == region_id:
            return False
        elif isinstance(dz, str) and dz == region_id:
            return False
    return True