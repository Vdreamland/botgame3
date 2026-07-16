from typing import Dict, Any

WEAPONS: Dict[str, Dict[str, Any]] = {
    "fist": {"atk_bonus": 0, "range": 0, "base_ep_cost": 1},
    "dagger": {"atk_bonus": 16, "range": 0, "base_ep_cost": 1},
    "sword": {"atk_bonus": 24, "range": 0, "base_ep_cost": 2},
    "katana": {"atk_bonus": 40, "range": 0, "base_ep_cost": 3},
    "bow": {"atk_bonus": 8, "range": 1, "base_ep_cost": 1},
    "pistol": {"atk_bonus": 15, "range": 1, "base_ep_cost": 2},
    "sniper_rifle": {"atk_bonus": 32, "range": 2, "base_ep_cost": 3}
}

ARMORS: Dict[str, Dict[str, Any]] = {
    "leather": {"def_bonus": 4},
    "chainmail": {"def_bonus": 12},
    "plate": {"def_bonus": 20}
}

RECOVERY_ITEMS: Dict[str, Dict[str, Any]] = {
    "bandage": {"hp_restore": 10, "ep_restore": 0},
    "emergency_food": {"hp_restore": 20, "ep_restore": 5},
    "energy_drink": {"hp_restore": 0, "ep_restore": 5},
    "medkit": {"hp_restore": 30, "ep_restore": 0}
}

UTILITY_ITEMS: Dict[str, Dict[str, Any]] = {
    "binoculars": {"vision_bonus": 1, "type": "passive"}
}

FACILITIES: Dict[str, Dict[str, str]] = {
    "Broadcast Station": {"effect": "broadcast", "desc": "Broadcast to all agents in the game"},
    "Supply Cache": {"effect": "loot", "desc": "Random item drop"},
    "Medical Facility": {"effect": "heal", "desc": "Restore some HP"},
    "Watchtower": {"effect": "vision_boost", "desc": "Temporary vision +2"},
    "Cave": {"effect": "cave_in_out", "desc": "Enter: vision -2, req +2, cannot Move. Exit clears state."},
    "Ruin": {"effect": "explore", "desc": "Explore ruins for relic/pack"}
}

def calculate_attack_ep_cost(weapon_key: str, state_multipliers: Dict[str, Any]) -> int:
    weapon = WEAPONS.get(weapon_key, WEAPONS["fist"])
    base_cost = weapon["base_ep_cost"]
    goliath_extra = state_multipliers.get("goliath_ep_cost_extra", 0)
    double_attack_extra = state_multipliers.get("double_attack_ep_cost_extra", 0)
    ranged_sub_extra = state_multipliers.get("ranged_sub_ep_cost_extra", 0)
    plunder_extra = state_multipliers.get("plunder_extra_ep", 0)
    return base_cost + goliath_extra + double_attack_extra + ranged_sub_extra + plunder_extra