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
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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

    turn = frame_data.get("turn", 1)
    day = (turn - 1) // 4 + 1
    
    view_data = frame_data.get("view", {})
    self_data = view_data.get("self", {})
    is_alive = self_data.get("isAlive", True)

    print("")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    async with _print_lock:
        if is_alive:
            print(f"[{timestamp}] Day: {day} | Turn: {turn} | [{bot_name}] | Status: \033[92mALIVE\033[0m")
            print(get_formatted_log(frame_data))
            print("")
            layers = get_region_layers(frame_data)
            print(format_region_layers(layers))
        else:
            print(f"[{timestamp}] Day: {day} | Turn: {turn} | [{bot_name}] | Status: \033[91mELIMINATED (DEAD)\033[0m")
        sys.stdout.flush()