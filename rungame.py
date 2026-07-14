import os
import sys
import asyncio
import requests
from dotenv import load_dotenv
from game_logs import log_msg
from helpers.api_config import get_bots_config, BASE_URL, WS_URL
from helpers.state_router import check_agent_state
from helpers.game_connection import connect_and_join_room

# Memuat konfigurasi berkas .env
load_dotenv()

def fetch_api_version() -> str:
    """
    Mengambil versi game terbaru dari endpoint versi SOT.
    """
    url = f"{BASE_URL}/version"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("version") or data.get("data", {}).get("version", "1.0.0")
    except Exception:
        pass
    return "1.0.0"

async def run_bot_instance(bot_config: dict, version: str):
    bot_name = bot_config["name"]
    api_key = bot_config["api_key"]
    preference = bot_config["room_preference"]

    await log_msg(bot_name, "INFO", f"Preparing bot to join a {preference.upper()} room...")

    # 1. Verifikasi Status Agen via REST API
    state, data = check_agent_state(api_key, version, preference)
    
    if state == "ERROR":
        await log_msg(bot_name, "ERROR", f"Account pre-check failed: {data}")
        return
    elif state == "NO_ACCOUNT":
        await log_msg(bot_name, "ERROR", "Credentials rejected/unauthorized.")
        return
    elif state == "IN_GAME":
        game_id = data.get("id", "N/A")
        short_id = game_id[:8] if len(game_id) > 8 else game_id
        await log_msg(bot_name, "SUCCESS", f"Bot is already active in an ongoing game (ID: {short_id})")
        return

    # 2. Buka Koneksi WebSocket & Gabung Antrean Room
    async def bot_log_callback(level: str, msg: str):
        await log_msg(bot_name, level, msg)

    ws_session = await connect_and_join_room(
        api_key=api_key,
        version=version,
        ws_url=WS_URL,
        room_preference=preference,
        log_callback=bot_log_callback
    )

    if ws_session:
        try:
            await log_msg(bot_name, "SUCCESS", "Game session active. Holding connection to stay in arena...")
            # Tetap mendengarkan frame data/heartbeat untuk menjaga koneksi tetap hidup
            async for message in ws_session:
                pass
        except Exception as e:
            await log_msg(bot_name, "WARN", f"Session disconnected: {str(e)}")
        finally:
            await ws_session.close()

async def main():
    print("="*60)
    print("        CLAW ROYALE - MULTI-BOT CONNECTION ENGINE")
    print("="*60)

    # Dapatkan versi game global
    version = fetch_api_version()
    print(f"[*] Server Game Version: {version}")

    # Membaca daftar konfigurasi seluruh agen dari .env
    bots = get_bots_config()
    if not bots:
        print("[!] No active bots configured. Please check your .env file.")
        return

    print(f"[*] Found {len(bots)} bot(s) configured. Initializing launch sequence...")

    tasks = []
    for bot_config in bots:
        tasks.append(asyncio.create_task(run_bot_instance(bot_config, version)))
        # Jeda waktu rilis (staggered launch) 2 detik untuk menghindari rate-limit IP
        await asyncio.sleep(2.0)

    # Jalankan seluruh task bot secara bersamaan (concurrency)
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Shutdown sequence initiated. Connection engine stopped.")