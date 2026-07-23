from typing import Dict, Any, List, Optional

def calculate_final_damage(atk: int, weapon_bonus: int, def_val: int, weather_mod: int, dmg_multiplier: float = 1.0) -> int:
    raw_damage = atk + weapon_bonus - def_val + weather_mod
    return max(1, int(raw_damage * dmg_multiplier))

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

def get_loadout_damage_multiplier(self_data: Dict[str, Any]) -> float:
    mult = 1.0
    loadout = self_data.get("loadout") or {}
    if isinstance(loadout, dict):
        main_pack = loadout.get("mainPack") or {}
        sub_pack = loadout.get("subPack") or {}
        for pack in [main_pack, sub_pack]:
            if isinstance(pack, dict):
                rolled_params = pack.get("rolledParams") or pack.get("rolled_params") or {}
                if isinstance(rolled_params, dict):
                    dmg_mult = rolled_params.get("dmgMultiplier") or rolled_params.get("dmg_multiplier")
                    if dmg_mult is not None:
                        try:
                            mult *= float(dmg_mult)
                        except (ValueError, TypeError):
                            pass
    return mult