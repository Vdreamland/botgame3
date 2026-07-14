import os
import sys
import asyncio
from datetime import datetime

# Mengaktifkan dukungan ANSI warna pada Windows PowerShell/CMD secara aman
if sys.platform == "win32":
    os.system("")

# ANSI Colors
RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"

_print_lock = asyncio.Lock()

async def log_msg(bot_name: str, level: str, message: str):
    """
    Handler penulisan log asinkron (thread-safe) menggunakan Bahasa Inggris (English logging)
    dan mendukung pewarnaan terminal Windows.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    color = RESET
    
    lvl = level.upper()
    if lvl == "INFO":
        color = BLUE
    elif lvl == "SUCCESS":
        color = GREEN
    elif lvl == "WARN":
        color = YELLOW
    elif lvl == "ERROR":
        color = RED
    elif lvl == "DEBUG":
        color = CYAN

    formatted = f"[{timestamp}] [{color}{lvl}{RESET}] [{bot_name}] -> {message}"
    
    async with _print_lock:
        print(formatted)
        sys.stdout.flush()