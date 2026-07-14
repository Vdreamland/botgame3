import math
from typing import Dict, Any, Tuple

SEASON_START: str = "2026-07-08"
SEASON_END: str = "2026-07-31"

CROSS_REWARD_POOLS: Dict[str, int] = {
    "leaderboard_top_100": 8000,
    "lucky_draw": 2000  # Menyelesaikan minimal tier 5 pada 10 trek stepped
}

WEEKLY_CLAIM_RESET_DAY: str = "Wednesday"  # Klaim berganti setiap hari Rabu 00:00 UTC

# Struktur 10 Trek Stepped Quests beserta tipe kurvanya
STEPPED_TRACKS: Dict[str, Dict[str, Any]] = {
    "kills": {"curve": "diminish", "base_req": 1, "step_reward": 5},
    "damage": {"curve": "diminish", "base_req": 100, "step_reward": 10},
    "top5": {"curve": "diminish", "base_req": 1, "step_reward": 15},
    "survival": {"curve": "diminish", "base_req": 300, "step_reward": 5},
    "explore": {"curve": "diminish", "base_req": 10, "step_reward": 5},
    "items": {"curve": "diminish", "base_req": 5, "step_reward": 5},
    "paid_games": {"curve": "exp", "base_req": 1, "step_reward": 20},
    "reforge": {"curve": "exp", "base_req": 5, "step_reward": 10},
    "moltz": {"curve": "exp", "base_req": 500, "step_reward": 15},
    "attendance": {"curve": "linear", "base_req": 1, "step_reward": 5}
}

def calculate_quest_requirements(track_key: str, tier: int) -> Tuple[int, int]:
    """
    Menghitung (syarat_target, poin_reward) untuk trek dan tier yang diberikan (tier dimulai dari 1).
    Kurva:
    - exp: Req = base * 2^(tier-1); Reward = step * tier
    - diminish: Req = base * 2^(tier-1); Reward = step * ceil(sqrt(tier))
    - linear: Req = base * tier; Reward = step * tier
    """
    track = STEPPED_TRACKS.get(track_key)
    if not track:
        return 0, 0
    
    curve = track["curve"]
    base = track["base_req"]
    step = track["step_reward"]
    
    if curve == "exp":
        req = base * (2 ** (tier - 1))
        reward = step * tier
    elif curve == "diminish":
        req = base * (2 ** (tier - 1))
        reward = step * math.ceil(math.sqrt(tier))
    else:  # linear
        req = base * tier
        reward = step * tier
        
    return int(req), int(reward)