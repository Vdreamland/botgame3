import math
from typing import Dict, Any, List, Tuple

def get_damage_dealt(attacker_atk: int, defender_def: int, weather_mod: int) -> int:
    return max(1, attacker_atk - defender_def + weather_mod)

def estimate_turns_to_kill(target_hp: int, damage_per_turn: int) -> int:
    if damage_per_turn <= 0:
        return 999
    return math.ceil(target_hp / damage_per_turn)

def evaluate_target_score(
    our_hp: int,
    our_dmg: int,
    enemy_hp: int,
    enemy_dmg: int,
    is_monster: bool
) -> float:
    turns_to_kill_enemy = estimate_turns_to_kill(enemy_hp, our_dmg)
    turns_to_kill_us = estimate_turns_to_kill(our_hp, enemy_dmg) if enemy_dmg > 0 else 999
    score = turns_to_kill_us - turns_to_kill_enemy
    if is_monster:
        score += 0.5
    return score