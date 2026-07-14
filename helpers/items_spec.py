from typing import Dict, Any

# Spesifikasi Senjata Melee & Ranged
WEAPONS: Dict[str, Dict[str, Any]] = {
    "fist": {"atk_bonus": 0, "range": 0, "base_ep_cost": 1},
    "knife": {"atk_bonus": 16, "range": 0, "base_ep_cost": 1},
    "sword": {"atk_bonus": 24, "range": 0, "base_ep_cost": 2},
    "katana": {"atk_bonus": 40, "range": 0, "base_ep_cost": 3},
    "bow": {"atk_bonus": 8, "range": 1, "base_ep_cost": 1},
    "pistol": {"atk_bonus": 15, "range": 1, "base_ep_cost": 2},
    "sniper": {"atk_bonus": 32, "range": 2, "base_ep_cost": 3}
}

# Spesifikasi Baju Zirah (Armor)
ARMORS: Dict[str, Dict[str, Any]] = {
    "leather": {"def_bonus": 4},
    "chainmail": {"def_bonus": 12},
    "plate": {"def_bonus": 20}
}

# Spesifikasi Item Pemulihan (Recovery)
RECOVERY_ITEMS: Dict[str, Dict[str, Any]] = {
    "bandage": {"hp_restore": 10, "ep_restore": 0},
    "emergency_food": {"hp_restore": 20, "ep_restore": 5},
    "energy_drink": {"hp_restore": 0, "ep_restore": 5},
    "medkit": {"hp_restore": 30, "ep_restore": 0}
}

# Spesifikasi Item Utilitas
UTILITY_ITEMS: Dict[str, Dict[str, Any]] = {
    "binoculars": {"vision_bonus": 1, "type": "passive"}
}

def calculate_attack_ep_cost(weapon_key: str, state_multipliers: Dict[str, Any]) -> int:
    """
    Menghitung biaya EP serangan dinamis berdasarkan rumus SOT:
    attack_ep = weaponEPCost + Goliath epCostExtra + Double-Attack epCostExtra + Ranged Sub epCostExtra + plunder ExtraEP
    """
    weapon = WEAPONS.get(weapon_key, WEAPONS["fist"])
    base_cost = weapon["base_ep_cost"]
    
    goliath_extra = state_multipliers.get("goliath_ep_cost_extra", 0)
    double_attack_extra = state_multipliers.get("double_attack_ep_cost_extra", 0)
    ranged_sub_extra = state_multipliers.get("ranged_sub_ep_cost_extra", 0)
    plunder_extra = state_multipliers.get("plunder_extra_ep", 0)
    
    return base_cost + goliath_extra + double_attack_extra + ranged_sub_extra + plunder_extra