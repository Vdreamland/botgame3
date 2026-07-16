import math
from collections import deque
from typing import Dict, Any, List, Optional
from helpers.world_parser import get_self_agent, get_visible_agents, get_visible_monsters, get_current_region, get_available_actions, get_region_adjacency_map
from helpers.actions_payload import attack_payload
from helpers.entities import MONSTERS, GUARDIAN_STATS
from helpers.game_constants import WEATHER_MODIFIERS
from helpers.items_spec import WEAPONS
from ai.memory import BotMemory
from helpers.combat_controller import get_damage_dealt, estimate_turns_to_kill, evaluate_target_score

def get_combat_action(frame_data: Dict[str, Any], memory: BotMemory) -> Optional[Dict[str, Any]]:
    self_data = get_self_agent(frame_data)
    if not self_data:
        return None
    current_region = get_current_region(frame_data)
    adj_data = get_region_adjacency_map(frame_data)
    current_id = adj_data.get("current_id")
    graph = adj_data.get("graph", {})
    if not current_id:
        return None
    distances = {current_id: 0}
    queue = deque([current_id])
    while queue:
        node = queue.popleft()
        dist = distances[node]
        for nbr in graph.get(node, []):
            if nbr not in distances:
                distances[nbr] = dist + 1
                queue.append(nbr)
    weather = current_region.get("weather", "clear") if current_region else "clear"
    weather_mod = WEATHER_MODIFIERS.get(weather.lower(), 0)
    our_hp = self_data.get("hp", 0)
    our_atk = self_data.get("atk", 25)
    our_def = self_data.get("def", 5)
    our_ep = self_data.get("ep", 0)
    our_weapon = self_data.get("equippedWeapon")
    our_range = 0
    if our_weapon:
        w_type = our_weapon.get("typeId", "").lower().replace(" ", "_")
        w_data = WEAPONS.get(w_type, {})
        our_atk += w_data.get("atk_bonus", 0)
        our_range = w_data.get("range", 0)
    available_actions = get_available_actions(frame_data)
    attack_cost = available_actions.get("attack", {}).get("cost", 1)
    if our_ep < attack_cost:
        return None
    targets = []
    for agent in get_visible_agents(frame_data):
        r_id = agent.get("regionId")
        if r_id in distances and distances[r_id] <= our_range and agent.get("hp", 0) > 0:
            agent_id = agent.get("id")
            if agent_id in memory.failed_attacks:
                continue
            name = agent.get("name", "")
            if "Guardian" in name or agent.get("isGuardian", False):
                continue
            t_atk = agent.get("atk", 25)
            t_wep = agent.get("equippedWeapon")
            t_range = 0
            if t_wep:
                t_w_type = t_wep.get("typeId", "").lower().replace(" ", "_")
                w_data = WEAPONS.get(t_w_type, {})
                t_atk += w_data.get("atk_bonus", 0)
                t_range = w_data.get("range", 0)
            targets.append({
                "id": agent_id,
                "name": name,
                "hp": agent.get("hp", 0),
                "atk": t_atk,
                "def": agent.get("def", 5),
                "type": "agent",
                "dist": distances[r_id],
                "range": t_range
            })
    for monster in get_visible_monsters(frame_data):
        r_id = monster.get("regionId")
        if r_id in distances and distances[r_id] <= our_range and monster.get("hp", 0) > 0:
            monster_id = monster.get("id")
            if monster_id in memory.failed_attacks:
                continue
            type_id = (monster.get("type") or monster.get("typeId") or monster.get("name") or "").lower()
            if "guardian" in type_id:
                continue
            static_stats = MONSTERS.get(type_id, {})
            name = monster.get("name", "") or monster.get("typeId", "Monster")
            targets.append({
                "id": monster_id,
                "name": name,
                "hp": monster.get("hp", 0),
                "atk": monster.get("atk") or static_stats.get("atk", 0),
                "def": monster.get("def") or static_stats.get("def", 0),
                "type": "monster",
                "dist": distances[r_id],
                "range": 0
            })
    if not targets:
        return None
    best_target = None
    best_target_score = -999999
    for t in targets:
        t_hp = t["hp"]
        t_atk = t["atk"]
        t_def = t["def"]
        t_dist = t["dist"]
        t_range = t["range"]
        is_monster = (t["type"] == "monster")
        our_dmg = get_damage_dealt(our_atk, t_def, weather_mod)
        enemy_dmg = get_damage_dealt(t_atk, our_def, weather_mod) if t_range >= t_dist else 0
        score = evaluate_target_score(our_hp, our_dmg, t_hp, enemy_dmg, False)
        if is_monster:
            score -= 3.0
        score -= t_dist * 2.0
        if score > best_target_score:
            best_target_score = score
            best_target = t
    if best_target:
        our_dmg = get_damage_dealt(our_atk, best_target["def"], weather_mod)
        turns_to_kill_enemy = estimate_turns_to_kill(best_target["hp"], our_dmg)
        if best_target_score >= -50.0 or best_target["hp"] < 30 or turns_to_kill_enemy <= 2:
            memory.last_target_id = best_target["id"]
            memory.last_action_type = "attack"
            return attack_payload(best_target["id"], best_target["type"], f"Attacking {best_target['name']} at dist {best_target['dist']} (Est. turns: {turns_to_kill_enemy})")
    return None