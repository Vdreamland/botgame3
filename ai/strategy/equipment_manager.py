from typing import Dict, Any, Optional
from helpers.actions_payload import equip_payload
from ai.memory import BotMemory
from ai.strategy.inventory_manager import MELEE_SCORES, RANGED_SCORES, ARMOR_SCORES

def get_equipment_action(
    self_data: Dict[str, Any],
    inv_analysis: Dict[str, Any],
    is_sm: bool,
    enemy_at_dist_0: bool,
    enemy_at_dist_range: bool,
    memory: BotMemory
) -> Optional[Dict[str, Any]]:
    eq_weapon = self_data.get("equippedWeapon")
    eq_armor = self_data.get("equippedArmor")
    eq_type = (eq_weapon.get("typeId") or eq_weapon.get("name") or "").lower().replace(" ", "_") if eq_weapon else ""
    best_inv_weapon = None
    best_inv_score = 0.0
    melee_score = float(inv_analysis["best_melee_score"])
    ranged_score = float(inv_analysis["best_ranged_score"])
    if enemy_at_dist_0:
        if melee_score > 0.0:
            melee_score += 0.1
        if melee_score >= ranged_score:
            best_inv_score = melee_score
            best_inv_weapon = inv_analysis["best_melee"]
        else:
            best_inv_score = ranged_score
            best_inv_weapon = inv_analysis["best_ranged"]
    elif enemy_at_dist_range:
        if is_sm:
            if melee_score >= ranged_score:
                best_inv_score = melee_score
                best_inv_weapon = inv_analysis["best_melee"]
            else:
                best_inv_score = ranged_score
                best_inv_weapon = inv_analysis["best_ranged"]
        else:
            if ranged_score > 0.0:
                best_inv_score = ranged_score
                best_inv_weapon = inv_analysis["best_ranged"]
            else:
                best_inv_score = melee_score
                best_inv_weapon = inv_analysis["best_melee"]
    else:
        if melee_score >= ranged_score:
            best_inv_score = melee_score
            best_inv_weapon = inv_analysis["best_melee"]
        else:
            best_inv_score = ranged_score
            best_inv_weapon = inv_analysis["best_ranged"]
    if not eq_weapon and best_inv_weapon:
        item_id = best_inv_weapon.get("id")
        item_name = best_inv_weapon.get("typeId", "weapon")
        if item_id and item_id not in memory.equipped_attempts:
            memory.equipped_attempts.add(item_id)
            return equip_payload(item_id, f"Equipping stronger weapon: {item_name}")
    should_swap = False
    if eq_weapon and best_inv_weapon:
        best_inv_type = best_inv_weapon.get("typeId", "").lower()
        if enemy_at_dist_0 and best_inv_type in MELEE_SCORES and eq_type in RANGED_SCORES:
            from helpers.items_spec import WEAPONS
            inv_atk = WEAPONS.get(best_inv_type, {}).get("atk_bonus", 0)
            eq_atk = WEAPONS.get(eq_type, {}).get("atk_bonus", 0)
            if inv_atk > eq_atk:
                should_swap = True
        elif is_sm and eq_type in RANGED_SCORES and best_inv_type in MELEE_SCORES:
            should_swap = True
        elif enemy_at_dist_0 and best_inv_type in MELEE_SCORES and eq_type in RANGED_SCORES and not should_swap:
            pass
        elif not enemy_at_dist_0 and enemy_at_dist_range and best_inv_type in RANGED_SCORES and eq_type in MELEE_SCORES and not is_sm:
            should_swap = True
        elif best_inv_type in MELEE_SCORES and eq_type in MELEE_SCORES and MELEE_SCORES[best_inv_type] > MELEE_SCORES[eq_type]:
            should_swap = True
        elif best_inv_type in RANGED_SCORES and eq_type in RANGED_SCORES and RANGED_SCORES[best_inv_type] > RANGED_SCORES[eq_type]:
            should_swap = True
        elif not enemy_at_dist_0 and not enemy_at_dist_range:
            best_inv_rating = float(MELEE_SCORES.get(best_inv_type, RANGED_SCORES.get(best_inv_type, 0.0)))
            eq_rating = float(MELEE_SCORES.get(eq_type, RANGED_SCORES.get(eq_type, 0.0)))
            if is_sm:
                if best_inv_type in MELEE_SCORES:
                    best_inv_rating += 5.0
                if eq_type in MELEE_SCORES:
                    eq_rating += 5.0
            if best_inv_rating > eq_rating:
                should_swap = True
    if should_swap and best_inv_weapon:
        item_id = best_inv_weapon.get("id")
        item_name = best_inv_weapon.get("typeId", "weapon")
        if item_id and item_id not in memory.equipped_attempts:
            memory.equipped_attempts.add(item_id)
            return equip_payload(item_id, f"Equipping stronger weapon: {item_name}")
    eq_armor_type = (eq_armor.get("typeId") or eq_armor.get("name") or "").lower().replace(" ", "_") if eq_armor else ""
    eq_armor_score = ARMOR_SCORES.get(eq_armor_type, 0)
    if inv_analysis["best_armor_score"] > eq_armor_score and inv_analysis["best_armor"]:
        item_id = inv_analysis["best_armor"].get("id")
        item_name = inv_analysis["best_armor"].get("typeId", "armor")
        if item_id and item_id not in memory.equipped_attempts:
            memory.equipped_attempts.add(item_id)
            return equip_payload(item_id, f"Equipping stronger armor: {item_name}")
    return None