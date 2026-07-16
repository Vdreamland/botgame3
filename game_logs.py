import os
import sys
import asyncio
from typing import Dict, Any
from colorama import init, Fore, Style

init(autoreset=True)

RESET = Style.RESET_ALL
BLUE = Fore.BLUE
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
CYAN = Fore.CYAN

_print_lock = asyncio.Lock()
_last_logged_turns = {}

async def log_msg(bot_name: str, level: str, message: str):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    color = CYAN
    if level == "SUCCESS":
        color = GREEN
    elif level == "WARN":
        color = YELLOW
    elif level == "ERROR":
        color = RED
    elif level == "DEBUG":
        color = BLUE
    async with _print_lock:
        print(f"[{timestamp}] [{color}{level}{RESET}] [{bot_name}] -> {message}")

async def log_frame_update(bot_name: str, frame_data: Dict[str, Any]):
    from ai.detector.agent_info import get_formatted_log
    from ai.detector.region_detector import get_region_layers, format_region_layers
    from helpers.world_parser import (
        get_turn,
        get_self_agent,
        is_bot_dead_in_logs,
        get_bot_death_details,
        get_agent_id,
        get_my_combat_events
    )
    turn = get_turn(frame_data)
    self_data = get_self_agent(frame_data)
    is_alive = self_data.get("isAlive", True)
    detected_dead_in_logs = is_bot_dead_in_logs(frame_data, bot_name)
    current_alive = is_alive and not detected_dead_in_logs
    state_key = (turn, current_alive)
    if _last_logged_turns.get(bot_name) == state_key:
        return
    _last_logged_turns[bot_name] = state_key
    day = (turn - 1) // 4 + 1
    print("")
    async with _print_lock:
        if current_alive:
            print(f"Day: {day} | Turn: {turn} | [{bot_name}] | Status: {GREEN}ALIVE{RESET}")
            my_id = get_agent_id(frame_data)
            combat_events = get_my_combat_events(frame_data, my_id)
            outbound = combat_events.get("outbound", [])
            for event in outbound:
                target = event.get("target_name", "unknown")
                dmg = event.get("damage", 0)
                new_hp = event.get("new_hp", 0)
                print(f"{GREEN}[*] DAMAGE DEALT: {dmg} HP to {target} (HP {new_hp} remaining)!{RESET}")
            inbound = combat_events.get("inbound", [])
            for event in inbound:
                attacker = event.get("attacker_name", "unknown")
                dmg = event.get("damage", 0)
                print(f"{RED}[*] DAMAGE TAKEN: {dmg} HP from {attacker}!{RESET}")
            print(get_formatted_log(frame_data))
            print("")
            print(format_region_layers(get_region_layers(frame_data)))
        else:
            print(f"Day: {day} | Turn: {turn} | [{bot_name}] | Status: {RED}ELIMINATED (DEAD){RESET}")
            death_details = get_bot_death_details(frame_data, bot_name)
            if death_details:
                killer = death_details.get("killer", "unknown")
                dmg = death_details.get("damage", "unknown")
                print(f"Eliminated by: {killer} (Damage taken: {dmg})")
            else:
                print("Player has been eliminated from the game session")