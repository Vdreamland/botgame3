from typing import Dict, Any, List, Optional

MELEE_SCORES: Dict[str, int] = {
    "katana": 3,
    "sword": 2,
    "knife": 1,
    "dagger": 1
}

RANGED_SCORES: Dict[str, int] = {
    "sniper": 3,
    "sniper_rifle": 3,
    "pistol": 2,
    "bow": 1
}

ARMOR_SCORES: Dict[str, int] = {
    "plate": 3,
    "plate_armor": 3,
    "chainmail": 2,
    "leather": 1,
    "leather_armor": 1
}

def analyze_inventory(inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    binocular_items = []
    hp_count = 0
    ep_count = 0
    for item in inventory:
        cat = item.get("category", "")
        type_id = item.get("typeId", "").lower().replace(" ", "_")
        if type_id in ["bandage", "medkit"]:
            hp_count += 1
        elif type_id in ["energy_drink", "emergency_food"]:
            ep_count += 1
        if cat == "weapon":
            if type_id in MELEE_SCORES:
                melee_items.append(item)
                score = MELEE_SCORES[type_id]
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
        elif type_id == "binoculars":
            binocular_items.append(item)
            has_binoculars = True
    return {
        "best_melee": best_melee,
        "best_melee_score": best_melee_score,
        "melee_items": melee_items,
        "best_ranged": best_ranged,
        "best_ranged_score": best_ranged_score,
        "ranged_items": ranged_items,
        "best_armor": best_armor,
        "best_armor_score": best_armor_score,
        "armor_items": armor_items,
        "has_binoculars": has_binoculars,
        "binocular_items": binocular_items,
        "hp_count": hp_count,
        "ep_count": ep_count
    }

def is_item_needed(item: Dict[str, Any], inv_analysis: Dict[str, Any]) -> bool:
    cat = item.get("category", "")
    type_id = item.get("typeId", "").lower().replace(" ", "_")
    if cat == "weapon":
        if type_id in MELEE_SCORES:
            score = MELEE_SCORES[type_id]
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
    if len(inv_analysis["binocular_items"]) > 1:
        return inv_analysis["binocular_items"][1].get("id")
    if len(inventory) >= 10:
        for item in inventory:
            if item.get("typeId", "").lower() == "bandage":
                return item.get("id")
    return None