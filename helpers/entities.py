from typing import Dict, Any

# Statistik Monster Arena
MONSTERS: Dict[str, Dict[str, Any]] = {
    "wolf": {
        "hp": 25,
        "atk": 15,
        "def": 1,
        "loot": ["bandage", "knife", "smoltz"]
    },
    "bear": {
        "hp": 30,
        "atk": 12,
        "def": 3,
        "loot": ["medkit", "sword", "smoltz"]
    },
    "bandit": {
        "hp": 40,
        "atk": 25,
        "def": 5,
        "loot": ["katana", "pistol", "smoltz"]
    }
}

# Parameter Guardian (Hostile AI)
GUARDIAN_STATS: Dict[str, Any] = {
    "hp": 150,
    "atk": 12,
    "def": 150,
    "ep": 10,
    "vision": 1,
    "curse_enabled": False,  # Curse dimatikan sementara di PreSeason 1
    "whisper_flavor_chance": 0.30
}

# Distribusi Guardian di Peta
ROOM_GUARDIAN_SPAWNS: Dict[str, int] = {
    "free": 15,  # 1 per reruntuhan
    "paid": 2    # 1 per reruntuhan
}