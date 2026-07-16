from typing import Dict, Any

WEAPONS: Dict[str, Dict[str, int]] = {
    "fist": {
        "atk_bonus": 0,
        "range": 1,
        "base_ep_cost": 2
    },
    "dagger": {
        "atk_bonus": 16,
        "range": 1,
        "base_ep_cost": 2
    },
    "sword": {
        "atk_bonus": 24,
        "range": 1,
        "base_ep_cost": 2
    },
    "katana": {
        "atk_bonus": 40,
        "range": 1,
        "base_ep_cost": 3
    },
    "bow": {
        "atk_bonus": 8,
        "range": 2,
        "base_ep_cost": 2
    },
    "pistol": {
        "atk_bonus": 15,
        "range": 2,
        "base_ep_cost": 3
    },
    "sniper_rifle": {
        "atk_bonus": 32,
        "range": 3,
        "base_ep_cost": 3
    },
    "sniper": {
        "atk_bonus": 32,
        "range": 3,
        "base_ep_cost": 3
    }
}

ARMORS: Dict[str, int] = {
    "leather": 4,
    "leather_armor": 4,
    "chainmail": 12,
    "plate": 20,
    "plate_armor": 20
}

RECOVERY_ITEMS: Dict[str, Dict[str, int]] = {
    "bandage": {
        "hp": 20,
        "ep": 0
    },
    "emergency_food": {
        "hp": 30,
        "ep": 3
    },
    "energy_drink": {
        "hp": 0,
        "ep": 5
    },
    "medkit": {
        "hp": 60,
        "ep": 0
    }
}

UTILITY_ITEMS: Dict[str, Dict[str, int]] = {
    "binoculars": {
        "vision_bonus": 1
    }
}

FACILITIES: Dict[str, Dict[str, str]] = {
    "Broadcast Station": {
        "effect": "reveal_all_players",
        "desc": "Reveals the location of all living players in the game."
    },
    "Supply Cache": {
        "effect": "spawn_high_value_loot",
        "desc": "Spawns rare tier 3 or tier 4 items in this region."
    },
    "Medical Facility": {
        "effect": "heal_full",
        "desc": "Restores the using player's HP to 100% instantly."
    },
    "Watchtower": {
        "effect": "passive_vision_bonus",
        "desc": "Permanently increases the adjacent sight range of this region."
    },
    "Cave": {
        "effect": "escape_route",
        "desc": "Allows players to bypass adjacent walls and move to distant regions."
    },
    "Ruin": {
        "effect": "relic_excavation",
        "desc": "Allows players to dig up ancient relics for passive bonuses."
    }
}

def calculate_attack_ep_cost(weapon_key: str, state_multipliers: Dict[str, Any]) -> int:
    base = WEAPONS.get(weapon_key, {}).get("base_ep_cost", 2)
    if state_multipliers.get("goliath_ep_cost_extra"):
        base += 1
    if state_multipliers.get("double_attack_ep_cost_extra"):
        base += 1
    if state_multipliers.get("ranged_sub_ep_cost_extra"):
        base += 1
    if state_multipliers.get("plunder_extra_ep"):
        base += 1
    return base