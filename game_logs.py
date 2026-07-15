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