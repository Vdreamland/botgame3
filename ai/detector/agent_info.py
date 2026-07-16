from typing import Dict, Any
from helpers.world_parser import get_self_agent, get_current_region, get_region_details
from helpers.items_spec import WEAPONS

def get_agent_stats(frame_data: Dict[str, Any]) -> Dict[str, int]:
    self_data = get_self_agent(frame_data)
    base_atk = self_data.get("atk", 25)
    weapon = self_data.get("equippedWeapon")
    weapon_name = "none"
    weapon_bonus = 0
    if weapon:
        weapon_name = weapon.get("name") if isinstance(weapon, dict) else weapon
    if weapon_name == "Fist":
        weapon_name = "none"
    if weapon_name != "none":
        weapon_key = weapon_name.lower().replace(" ", "_")
        weapon_bonus = WEAPONS.get(weapon_key, {}).get("atk_bonus", 0)
    return {
        "hp": self_data.get("hp", 0),
        "ep": self_data.get("ep", 0),
        "atk": base_atk + weapon_bonus,
        "def": self_data.get("def", 0),
        "kills": self_data.get("kills", self_data.get("killCount", 0))
    }

def get_formatted_log(frame_data: Dict[str, Any]) -> str:
    stats = get_agent_stats(frame_data)
    current_region = get_current_region(frame_data)
    details = get_region_details(current_region)
    self_data = get_self_agent(frame_data)
    weapon = self_data.get("equippedWeapon")
    weapon_name = "none"
    if weapon:
        weapon_name = weapon.get("name") if isinstance(weapon, dict) else weapon
    if weapon_name == "Fist":
        weapon_name = "none"
    armor = self_data.get("equippedArmor")
    armor_name = "none"
    if armor:
        armor_name = armor.get("name") if isinstance(armor, dict) else armor
    return f"Agent Info :\nHP {stats['hp']} / EP {stats['ep']} / ATK {stats['atk']} / DEF {stats['def']} / KILLS {stats['kills']}\nWeapon : {weapon_name} | Armour : {armor_name}\nLocation : {details['name']} ({details['terrain']}) | Weather: {details['weather']} | Vision: {details['vision']} | Links: {details['links']}"