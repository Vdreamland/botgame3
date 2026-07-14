import sys
import asyncio
from datetime import datetime

# ANSI Terminal Colors
RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"

_print_lock = asyncio.Lock()

async def log_msg(bot_name: str, level: str, message: str):
    """
    Handler penulisan log asinkron (thread-safe) menggunakan Bahasa Inggris (English logging).
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = RESET
    
    if level.upper() == "INFO":
        color = BLUE
    elif level.upper() == "SUCCESS":
        color = GREEN
    elif level.upper() == "WARN":
        color = YELLOW
    elif level.upper() == "ERROR":
        color = RED
    elif level.upper() == "DEBUG":
        color = CYAN

    formatted = f"[{timestamp}] [{color}{level.upper()}{RESET}] [Bot: {bot_name}] -> {message}"
    
    async with _print_lock:
        print(formatted)
        sys.stdout.flush()