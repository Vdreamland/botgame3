import os
import sys
import json
import asyncio
import requests
from dotenv import load_dotenv
from game_logs import log_msg
from helpers.api_config import get_bots_config, BASE_URL, WS_URL, WS_GAMEPLAY_URL
from helpers.state_router import check_agent_state
from helpers.game_connection import connect_and_join_room, connect_and_resume_game
from ai.detector.agent_info import get_formatted_log

load_dotenv()

def fetch_api_version():
    url = f"{BASE_URL}/version"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("version") or data.get("data", {}).get("version", "1.0.0")
    except Exception:
        pass
    return "1.0.0"

async def run_bot_instance(bot_config, version):
    bot_name = bot_config["name"]
    api_key = bot_config["api_key"]
    preference = bot_config["room_preference"]

    await log_msg(bot_name, "INFO", f"Preparing bot to join a {preference.upper()} room...")

    while True:
        state, data = check_agent_state(api_key, version, preference)
        
        if state == "ERROR":
            await log_msg(bot_name, "ERROR", f"Account pre-check failed: {data}")
            await asyncio.sleep(10.0)
            continue
        elif state == "NO_ACCOUNT":
            await log_msg(bot_name, "ERROR", "Credentials rejected/unauthorized.")
            return

        async def bot_log_callback(level, msg):
            await log_msg(bot_name, level, msg)

        ws_session = None

        if state == "IN_GAME":
            game_id = data.get("id", "N/A")
            short_id = game_id[:8] if len(game_id) > 8 else game_id
            await log_msg(bot_name, "SUCCESS", f"Bot is already active in an ongoing game (ID: {short_id})")
            
            ws_session = await connect_and_resume_game(
                api_key=api_key,
                version=version,
                ws_url=WS_GAMEPLAY_URL,
                log_callback=bot_log_callback
            )
        else:
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
                async for message in ws_session:
                    frame_data = json.loads(message)
                    msg_type = frame_data.get("type")
                    
                    if msg_type in ["agent_view", "turn_advanced"]:
                        turn = frame_data.get("turn", 1)
                        day = (turn - 1) // 4 + 1
                        
                        view_data = frame_data.get("view", {})
                        self_data = view_data.get("self", {})
                        is_alive = self_data.get("isAlive", True)
                        
                        print("")
                        
                        if is_alive:
                            await log_msg(bot_name, "INFO", f"Match Progress -> Day: {day} | Turn: {turn} | Status: ALIVE")
                            
                            info_msg = get_formatted_log(frame_data)
                            await log_msg(bot_name, "INFO", info_msg)
                        else:
                            await log_msg(bot_name, "WARN", f"Match Progress -> Day: {day} | Turn: {turn} | Status: ELIMINATED (DEAD)")
                            await ws_session.close()
                            break
                            
            except Exception as e:
                await log_msg(bot_name, "WARN", f"Session disconnected: {str(e)}")
            finally:
                try:
                    await ws_session.close()
                except Exception:
                    pass

        print("")
        await log_msg(bot_name, "INFO", "Waiting 10 seconds post-match to check eligibility for a new game...")
        await asyncio.sleep(10.0)

        while True:
            next_state, next_data = check_agent_state(api_key, version, preference)
            if next_state == "IN_GAME":
                print("")
                await log_msg(bot_name, "INFO", "Previous game slot is still active on server. Waiting for game to end...")
                await asyncio.sleep(10.0)
            else:
                print("")
                await log_msg(bot_name, "SUCCESS", "Eligible to join a new match! Re-entering queue...")
                break

async def main():
    print("="*60)
    print("        CLAW ROYALE - MULTI-BOT CONNECTION ENGINE")
    print("="*60)

    version = fetch_api_version()
    print(f"[*] Server Game Version: {version}")

    bots = get_bots_config()
    if not bots:
        print("[!] No active bots configured. Please check your .env file.")
        return

    print(f"[*] Found {len(bots)} bot(s) configured. Initializing launch sequence...")

    tasks = []
    for bot_config in bots:
        tasks.append(asyncio.create_task(run_bot_instance(bot_config, version)))
        await asyncio.sleep(2.0)

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Shutdown sequence initiated. Connection engine stopped.")