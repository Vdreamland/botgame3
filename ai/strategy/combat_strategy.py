import math
from typing import Dict, Any, List, Optional
from helpers.world_parser import get_self_agent, get_visible_agents, get_visible_monsters, get_current_region, get_available_actions
from helpers.actions_payload import attack_payload
from helpers.entities import MONSTERS, GUARDIAN_STATS
from helpers.game_constants import WEATHER_MODIFIERS
from ai.memory import BotMemory

def get_combat_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    self_data = get_self_agent(frame_data)
    if not self_data:
        return None
    current_region = get_current_region(frame_data)
    current_id = current_region.get("id") if current_region else ""
    weather = current_region.get("weather", "clear") if current_region else "clear"
    weather_mod = WEATHER_MODIFIERS.get(weather.lower(), 0)
    our_hp = self_data.get("hp", 0)
    our_atk = self_data.get("atk", 25)
    our_def = self_data.get("def", 5)
    our_ep = self_data.get("ep", 0)
    available_actions = get_available_actions(frame_data)
    attack_ok = available_actions.get("attack", {}).get("ok", False)
    attack_cost = available_actions.get("attack", {}).get("cost", 1)
    if not attack_ok or our_ep < attack_cost:
        return None
    targets = []
    for agent in get_visible_agents(frame_data):
        if agent.get("regionId") == current_id and agent.get("hp", 0) > 0:
            name = agent.get("name", "")
            if "Guardian" in name or agent.get("isGuardian", False):
                continue
            targets.append({
                "id": agent.get("id"),
                "name": name,
                "hp": agent.get("hp", 0),
                "atk": agent.get("atk", 25),
                "def": agent.get("def", 5),
                "type": "agent"
            })
    for monster in get_visible_monsters(frame_data):
        if monster.get("regionId") == current_id and monster.get("hp", 0) > 0:
            name = monster.get("name", "")
            type_id = (monster.get("type") or monster.get("typeId") or monster.get("name") or "").lower()
            if "guardian" in type_id:
                continue
            static_stats = MONSTERS.get(type_id, {})
            targets.append({
                "id": monster.get("id"),
                "name": name,
                "hp": monster.get("hp", 0),
                "atk": monster.get("atk") or static_stats.get("atk", 0),
                "def": monster.get("def") or static_stats.get("def", 0),
                "type": "monster"
            })
    if not targets:
        return None
    best_target = None
    best_target_score = -999999
    for t in targets:
        t_hp = t["hp"]
        t_atk = t["atk"]
        t_def = t["def"]
        our_dmg = max(1, our_atk - t_def + weather_mod)
        enemy_dmg = max(1, t_atk - our_def + weather_mod)
        turns_to_kill_enemy = math.ceil(t_hp / our_dmg)
        turns_to_kill_us = math.ceil(our_hp / enemy_dmg)
        score = turns_to_kill_us - turns_to_kill_enemy
        if t["type"] == "monster":
            score += 0.5
        if score > best_target_score:
            best_target_score = score
            best_target = t
    if best_target:
        t_hp = best_target["hp"]
        t_def = best_target["def"]
        our_dmg = max(1, our_atk - t_def + weather_mod)
        turns_to_kill_enemy = math.ceil(t_hp / our_dmg)
        if best_target_score >= 0 or t_hp < 30 or turns_to_kill_enemy <= 2:
            return attack_payload(best_target["id"], best_target["type"], f"Attacking {best_target['name']} (Est. turns: {turns_to_kill_enemy})")
    return None