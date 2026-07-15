import os
import sys
import json
import asyncio
import requests
from dotenv import load_dotenv
from game_logs import log_msg, log_frame_update
from helpers.api_config import get_bots_config, BASE_URL, WS_URL, WS_GAMEPLAY_URL
from helpers.state_router import check_agent_state
from helpers.game_connection import connect_and_join_room, connect_and_resume_game
from helpers.world_parser import get_self_agent, is_bot_dead_in_logs

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

async def check_bot_alive_loop(bot_name, api_key, version, preference, ws_session):
    while True:
        await asyncio.sleep(10.0)
        state, data = await asyncio.to_thread(check_agent_state, api_key, version, preference)
        if state != "IN_GAME":
            print("")
            await log_msg(bot_name, "WARN", "Status: ELIMINATED (DEAD)")
            print("Player has been detected dead in world history")
            try:
                await ws_session.close()
            except Exception:
                pass
            break

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
            checker_task = asyncio.create_task(
                check_bot_alive_loop(bot_name, api_key, version, preference, ws_session)
            )
            try:
                await log_msg(bot_name, "SUCCESS", "Game session active. Holding connection to stay in arena...")
                while True:
                    message = await asyncio.wait_for(ws_session.recv(), timeout=45.0)
                    frame_data = json.loads(message)
                    msg_type = frame_data.get("type")
                    
                    if msg_type in ["agent_view", "turn_advanced"]:
                        await log_frame_update(bot_name, frame_data)
                        
                        self_data = get_self_agent(frame_data)
                        is_alive = self_data.get("isAlive", True)
                        detected_dead_in_logs = is_bot_dead_in_logs(frame_data, bot_name)
                        
                        if not is_alive or detected_dead_in_logs:
                            await ws_session.close()
                            break
                    elif msg_type == "game_ended":
                        await log_msg(bot_name, "SUCCESS", "Game session has officially ended on the server.")
                        await ws_session.close()
                        break
                                
            except asyncio.TimeoutError:
                print("")
                await log_msg(bot_name, "WARN", "Connection timed out. Game turn advance delayed. Retrying...")
                try:
                    await ws_session.close()
                except Exception:
                    pass
            except Exception as e:
                await log_msg(bot_name, "WARN", f"Session disconnected: {str(e)}")
            finally:
                checker_task.cancel()
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