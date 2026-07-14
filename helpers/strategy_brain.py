from typing import Dict, Any, List, Optional

def calculate_final_damage(atk: int, weapon_bonus: int, def_val: int, weather_mod: int) -> int:
    """
    Kalkulasi damage akhir sesuai formula resmi SOT:
    Final Damage = max(1, ATK + weaponBonus - DEF + weatherMod)
    """
    raw_damage = atk + weapon_bonus - def_val + weather_mod
    return max(1, raw_damage)

def resolve_connected_region(entry: Any, visible_regions: List[Any]) -> Optional[Dict[str, Any]]:
    """
    SOT Rule (gotchas.md): Mengatasi ketidakpastian format connectedRegions.
    Mengembalikan objek Region penuh jika terdeteksi/berada dalam vision, 
    atau None jika connectedRegion tersebut berada di luar jarak pandang (hanya berupa bare-string ID).
    """
    if isinstance(entry, dict):
        return entry
    
    # Jika entry berupa bare-string ID, cari objek lengkapnya di visible_regions
    for r in visible_regions:
        if isinstance(r, dict) and r.get("id") == entry:
            return r
    return None

def is_region_safe_from_death_zone(region_id: str, pending_deathzones: List[Any]) -> bool:
    """
    SOT Rule (gotchas.md): Memeriksa keamanan wilayah sebelum bergerak.
    Mengembalikan False jika wilayah tersebut masuk dalam daftar perluasan deathzone pada turn berikutnya.
    """
    for dz in pending_deathzones:
        if isinstance(dz, dict) and dz.get("id") == region_id:
            return False
        elif isinstance(dz, str) and dz == region_id:
            return False
    return True

class AgentMemory:
    """
    Mengelola memori spasial dan taktis regional untuk masing-masing agen secara aman (thread-safe).
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_region_id: Optional[str] = None
        self.visible_players: Dict[str, Dict[str, Any]] = {}
        self.visible_monsters: Dict[str, Dict[str, Any]] = {}
        self.visible_items: Dict[str, Dict[str, Any]] = {}
        self.ruins_states: Dict[str, Dict[str, Any]] = {}
        self.adjacency_map: Dict[str, List[str]] = {}

    def update_state(self, agent_view: Dict[str, Any]) -> None:
        """
        Memperbarui status taktis lokal berdasarkan frame visual dari server.
        """
        self.current_region_id = agent_view.get("currentRegionId")
        
        # Bersihkan dan petakan pemain lain yang terlihat
        self.visible_players.clear()
        for player in agent_view.get("visiblePlayers", []):
            if player.get("id") != self.agent_id:
                self.visible_players[player["id"]] = player

        # Bersihkan dan petakan monster yang terlihat
        self.visible_monsters.clear()
        for monster in agent_view.get("visibleMonsters", []):
            self.visible_monsters[monster["id"]] = monster

        # Bersihkan dan petakan barang di tanah yang terlihat
        self.visible_items.clear()
        for item in agent_view.get("visibleItems", []):
            self.visible_items[item["id"]] = item

        # Perbarui status reruntuhan (ruins) yang terdeteksi
        for ruin in agent_view.get("visibleRuins", []):
            self.ruins_states[ruin["id"]] = ruin

    def get_priority_target(self) -> Optional[Dict[str, Any]]:
        """
        Hierarki Pengambilan Keputusan Target:
        1. Pemain lawan dengan HP sekarat (HP < 30) untuk eliminasi cepat.
        2. Monster biasa terdekat jika HP agen dalam kondisi prima.
        3. Menghindari Guardian kecuali jika loadout senjata/armor sudah optimal.
        """
        # 1. Target pemain sekarat
        for player_id, player in self.visible_players.items():
            if player.get("hp", 100) < 30 and player.get("isAlive", True):
                return {"id": player_id, "type": "agent", "data": player}

        # 2. Target monster biasa terdekat
        for monster_id, monster in self.visible_monsters.items():
            if monster.get("isAlive", True) and monster.get("monsterType") != "guardian":
                return {"id": monster_id, "type": "monster", "data": monster}

        # 3. Target pemain lain yang masih hidup
        for player_id, player in self.visible_players.items():
            if player.get("isAlive", True):
                return {"id": player_id, "type": "agent", "data": player}
                
        return None

    def get_explorable_ruin(self) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan reruntuhan (ruins) dengan gauge < 3 dan sedang tidak diokupasi agen lain.
        """
        for ruin_id, ruin in self.ruins_states.items():
            gauge = ruin.get("gauge", 0)
            occupied_by = ruin.get("occupiedBy")
            if gauge < 3 and (occupied_by is None or occupied_by == self.agent_id):
                return ruin
        return None