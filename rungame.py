import asyncio
import json
import requests
import sys
from colorama import init, Fore, Style

from helpers.api_config import get_api_endpoints, get_bots_config, get_headers
from helpers.game_connection import connect_and_join_room, connect_and_resume_game
from helpers.world_parser import get_self_agent, is_bot_dead_in_logs, get_turn
from helpers.state_router import check_agent_state
from game_logs import log_frame_update, draw_terminal_header

init(autoreset=True)

VERSION = "1.13.0"

async def log_msg(bot_name, level, text):
    color = Fore.CYAN
    if level == "SUCCESS":
        color = Fore.GREEN
    elif level == "WARNING" or level == "WARN":
        color = Fore.YELLOW
    elif level == "ERROR":
        color = Fore.RED
    
    from datetime import datetime
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] [{color}{level}{Style.RESET_ALL}] [{Fore.MAGENTA}{bot_name}{Style.RESET_ALL}] -> {text}")

async def check_bot_alive_loop(bot_name, api_key, version, preference, ws_session):
    while True:
        await asyncio.sleep(10)
        try:
            state, data = check_agent_state(api_key, version, preference)
            if state != "IN_GAME":
                await log_msg(bot_name, "WARNING", "Status: ELIMINATED (DEAD)")
                print("Player has been detected dead in world history")
                try:
                    await ws_session.close()
                except Exception:
                    pass
                break
        except Exception:
            pass

async def run_bot_instance(bot_name, api_key, version, preference):
    endpoints = get_api_endpoints()
    
    while True:
        try:
            await log_msg(bot_name, "INFO", f"Preparing bot to join a {preference.upper()} room...")
            state, data = check_agent_state(api_key, version, preference)
            
            ws_session = None
            last_logged_turn = -1

            if state == "IN_GAME":
                await log_msg(bot_name, "SUCCESS", f"Bot is already active in an ongoing game (ID: {data.get('gameId', 'N/A')})")
                await log_msg(bot_name, "INFO", "Reconnecting to active game session...")
                ws_session = await connect_and_resume_game(api_key, version, endpoints["ws_gameplay"], lambda lvl, txt: log_msg(bot_name, lvl, txt))
                await log_msg(bot_name, "SUCCESS", "Successfully reconnected to active arena! Listening to game updates...")
            elif state in ["READY_PAID", "READY_FREE"]:
                await log_msg(bot_name, "INFO", "Opening secure connection to game server...")
                ws_session = await connect_and_join_room(api_key, version, endpoints["ws_join"], preference, lambda lvl, txt: log_msg(bot_name, lvl, txt))
            elif state == "NO_ACCOUNT":
                await log_msg(bot_name, "ERROR", "Account not registered. Please set up your account first.")
                await asyncio.sleep(30)
                continue
            else:
                await log_msg(bot_name, "ERROR", "Unknown account state or server error. Retrying in 15 seconds...")
                await asyncio.sleep(15)
                continue

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
                            current_turn = get_turn(frame_data)
                            if current_turn != last_logged_turn:
                                await log_frame_update(bot_name, frame_data)
                                last_logged_turn = current_turn
                            
                            self_data = get_self_agent(frame_data)
                            is_alive = self_data.get("isAlive", True)
                            
                            detected_dead_in_logs = is_bot_dead_in_logs(frame_data, bot_name)
                            
                            if not is_alive or detected_dead_in_logs:
                                await log_msg(bot_name, "WARNING", "Bot has been eliminated. Exiting game loop.")
                                try:
                                    await ws_session.close()
                                except Exception:
                                    pass
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
            
            await log_msg(bot_name, "INFO", "Waiting 10 seconds post-match to check eligibility for a new game...")
            await asyncio.sleep(10)
            
        except Exception as e:
            await log_msg(bot_name, "ERROR", f"Instance encountered unexpected error: {str(e)}")
            await asyncio.sleep(15)

async def main():
    draw_terminal_header(VERSION)
    bots = get_bots_config()
    if not bots:
        print("[*] No bots found in configuration! Please check your .env file.")
        return
    print(f"[*] Found {len(bots)} bot(s) configured. Initializing launch sequence...")
    
    tasks = []
    for bot in bots:
        tasks.append(
            run_bot_instance(bot["name"], bot["api_key"], VERSION, bot["preference"])
        )
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Shutdown sequence initiated. Exiting gracefully...")