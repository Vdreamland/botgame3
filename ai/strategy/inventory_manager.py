from typing import Dict, Any, List, Optional
from helpers.items_spec import WEAPONS, ARMORS

MELEE_SCORES: Dict[str, int] = {
 "katana": 3,
 "sword": 2,
 "knife": 1,
 "dagger": 1
}

RANGED_SCORES: Dict[str, int] = {
 "sniper_rifle": 4,
 "sniper": 4,
 "pistol": 3,
 "bow": 2
}

ARMOR_SCORES: Dict[str, int] = {
 "plate": 3,
 "plate_armor": 3,
 "chainmail": 2,
 "leather": 1,
 "leather_armor": 1
}

def is_sword_master_active(self_data: Dict[str, Any]) -> bool:
    loadout = self_data.get("loadout") or {}
    if isinstance(loadout, dict):
        main_pack = loadout.get("mainPack") or {}
        sub_pack = loadout.get("subPack") or {}
        main_family = ""
        if isinstance(main_pack, dict):
            main_family = main_pack.get("family") or main_pack.get("typeId") or ""
        elif isinstance(main_pack, str):
            main_family = main_pack
        sub_family = ""
        if isinstance(sub_pack, dict):
            sub_family = sub_pack.get("family") or sub_pack.get("typeId") or ""
        elif isinstance(sub_pack, str):
            sub_family = sub_pack
        for fam in [main_family, sub_family]:
            if isinstance(fam, str) and "sword" in fam.lower() and "master" in fam.lower():
                return True
    return False

def analyze_inventory(inventory: List[Dict[str, Any]], is_sword_master: bool = False) -> Dict[str, Any]:
    hp_count = 0
    ep_count = 0
    best_melee = None
    best_melee_score = 0
    best_ranged = None
    best_ranged_score = 0
    best_armor = None
    best_armor_score = 0
    has_binoculars = False
    melee_items = []
    ranged_items = []
    armor_items = []
    melee_scores = dict(MELEE_SCORES)
    if is_sword_master:
        for k in melee_scores:
            melee_scores[k] += 5
    for item in inventory:
        type_id = item.get("typeId", "").lower().replace(" ", "_")
        cat = item.get("category", "").lower()
        if type_id in ["bandage", "medkit"]:
            hp_count += 1
        elif type_id in ["energy_drink", "emergency_food"]:
            ep_count += 1
        if type_id == "binoculars":
            has_binoculars = True
        if cat == "weapon":
            if type_id in melee_scores:
                melee_items.append(item)
                score = melee_scores[type_id]
                if score > best_melee_score:
                    best_melee_score = score
                    best_melee = item
            elif type_id in RANGED_SCORES:
                ranged_items.append(item)
                score = RANGED_SCORES[type_id]
                if score > best_ranged_score:
                    best_ranged_score = score
                    best_ranged = item
        elif cat == "armor" or type_id in ARMOR_SCORES:
            armor_items.append(item)
            score = ARMOR_SCORES.get(type_id, 0)
            if score > best_armor_score:
                best_armor_score = score
                best_armor = item
    return {
        "hp_count": hp_count,
        "ep_count": ep_count,
        "best_melee": best_melee,
        "best_melee_score": best_melee_score,
        "best_ranged": best_ranged,
        "best_ranged_score": best_ranged_score,
        "best_armor": best_armor,
        "best_armor_score": best_armor_score,
        "has_binoculars": has_binoculars,
        "melee_items": melee_items,
        "ranged_items": ranged_items,
        "armor_items": armor_items
    }

def is_item_needed(item: Dict[str, Any], inv_analysis: Dict[str, Any], is_sword_master: bool = False) -> bool:
    cat = item.get("category", "").lower()
    type_id = item.get("typeId", "").lower().replace(" ", "_")
    melee_scores = dict(MELEE_SCORES)
    if is_sword_master:
        for k in melee_scores:
            melee_scores[k] += 5
    if cat == "weapon":
        if type_id in melee_scores:
            score = melee_scores[type_id]
            return score > inv_analysis["best_melee_score"]
        elif type_id in RANGED_SCORES:
            score = RANGED_SCORES[type_id]
            return score > inv_analysis["best_ranged_score"]
    elif cat == "armor" or type_id in ARMOR_SCORES:
        score = ARMOR_SCORES.get(type_id, 0)
        return score > inv_analysis["best_armor_score"]
    elif type_id == "binoculars":
        return not inv_analysis["has_binoculars"]
    if type_id in ["bandage", "medkit"]:
        return inv_analysis.get("hp_count", 0) < 2
    if type_id in ["energy_drink", "emergency_food"]:
        return inv_analysis.get("ep_count", 0) < 3
    return True

def get_item_to_drop(inv_analysis: Dict[str, Any], inventory: List[Dict[str, Any]]) -> Optional[str]:
    best_melee_id = inv_analysis["best_melee"].get("id") if inv_analysis["best_melee"] else None
    for item in inv_analysis["melee_items"]:
        if item.get("id") != best_melee_id:
            return item.get("id")
    best_ranged_id = inv_analysis["best_ranged"].get("id") if inv_analysis["best_ranged"] else None
    for item in inv_analysis["ranged_items"]:
        if item.get("id") != best_ranged_id:
            return item.get("id")
    best_armor_id = inv_analysis["best_armor"].get("id") if inv_analysis["best_armor"] else None
    for item in inv_analysis["armor_items"]:
        if item.get("id") != best_armor_id:
            return item.get("id")
    has_seen_binoculars = False
    for item in inventory:
        if item.get("typeId", "").lower() == "binoculars":
            if has_seen_binoculars:
                return item.get("id")
            has_seen_binoculars = True
    if len(inventory) >= 10:
        for item in inventory:
            if item.get("typeId", "").lower() == "bandage":
                return item.get("id")
    return None