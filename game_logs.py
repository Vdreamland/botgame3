import os
import sys
import asyncio
from datetime import datetime

if sys.platform == "win32":
    os.system("")

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"

_print_lock = asyncio.Lock()

async def log_msg(bot_name, level, message):
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    color = RESET
    
    lvl = level.upper()
    if lvl == "INFO":
        color = CYAN
    elif lvl == "SUCCESS":
        color = GREEN
    elif lvl == "WARN":
        color = YELLOW
    elif lvl == "ERROR":
        color = RED
    elif lvl == "DEBUG":
        color = BLUE

    async with _print_lock:
        for line in message.split("\n"):
            formatted = f"[{timestamp}] [{color}{lvl}{RESET}] [{bot_name}] -> {line}"
            print(formatted)
            sys.stdout.flush()

async def log_frame_update(bot_name, frame_data):
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
    day = (turn - 1) // 4 + 1
    
    self_data = get_self_agent(frame_data)
    is_alive = self_data.get("isAlive", True)
    detected_dead_in_logs = is_bot_dead_in_logs(frame_data, bot_name)

    print("")

    async with _print_lock:
        if is_alive and not detected_dead_in_logs:
            print(f"Day: {day} | Turn: {turn} | [{bot_name}] | Status: \033[92mALIVE\033[0m")
            
            my_id = get_agent_id(frame_data)
            combat_events = get_my_combat_events(frame_data, my_id)
            for event in combat_events.get("inbound", []):
                dmg = event.get("damage", 0)
                attacker = event.get("attacker_name", "unknown")
                print(f"\033[91mHit!\033[0m Suffered {dmg} damage from {attacker}")
            
            print(get_formatted_log(frame_data))
            print("")
            layers = get_region_layers(frame_data)
            print(format_region_layers(layers))
        else:
            print(f"Day: {day} | Turn: {turn} | [{bot_name}] | Status: \033[91mELIMINATED (DEAD)\033[0m")
            death_details = get_bot_death_details(frame_data, bot_name)
            if death_details:
                killer = death_details.get("killer", "unknown")
                dmg = death_details.get("damage", "unknown")
                print(f"Player has been detected dead in world history: Killed by {killer} ({dmg} damage)")
            else:
                print("Player has been detected dead in world history")
        sys.stdout.flush()