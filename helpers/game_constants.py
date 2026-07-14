from typing import Dict, Any, List

# Konfigurasi waktu dan EP (Action Points)
TURN_DURATION_SECONDS: int = 30
COOLDOWN_MS: int = 30000
MAX_EP: int = 10
PASSIVE_EP_REGEN: int = 1
REST_EP_REGEN: int = 2

# Modifikator flat cuaca pada kalkulasi damage
WEATHER_MODIFIERS: Dict[str, int] = {
    "clear": 0,
    "rain": -5,
    "fog": -10,
    "storm": -15
}

# Biaya EP gerakan (Terrain tidak memengaruhi biaya langkah default)
TERRAIN_MOVE_EP_COST: int = 2

def is_loadout_complete(main_pack: Any, sub_pack: Any, relics: List[Any]) -> bool:
    """
    Memeriksa kepatuhan loadout lengkap (fullSet).
    Harus memiliki 1 Main Pack, 1 Sub Pack, dan tepat 3 Relik.
    Jika tidak lengkap, agen bertarung tanpa efek pack pasif dan status tambahan relik.
    """
    if not main_pack or not sub_pack:
        return False
    if not relics or len(relics) != 3:
        return False
    return True