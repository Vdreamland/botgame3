import sys
from datetime import datetime
from colorama import Fore, Style, init

from helpers.world_parser import (
    get_turn,
    get_self_agent,
    get_current_region,
    get_visible_regions,
    is_bot_dead_in_logs,
    get_bot_death_details
)
from ai.detector.region_detector import detect_safe_regions_and_path

init(autoreset=True)

def draw_terminal_header(version):
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + f"        CLAW ROYALE - MULTI-BOT CONNECTION ENGINE v{version}")
    print(Fore.CYAN + "=" * 60)

def log_frame_update(bot_name, frame_data):
    turn = get_turn(frame_data)
    self_data = get_self_agent(frame_data)
    if not self_data:
        return
        
    hp = self_data.get("hp", 0)
    max_hp = self_data.get("maxHp", 100)
    ep = self_data.get("ep", 0)
    max_ep = self_data.get("maxEp", 10)
    atk = self_data.get("atk", 0)
    df = self_data.get("def", 0)
    kills = self_data.get("kills", 0)
    is_alive = self_data.get("isAlive", True)
    
    current_region_id = get_current_region(frame_data)
    weather = frame_data.get("weather", "clear")
    vision = self_data.get("visionRange", 1)
    
    adjacency_map = frame_data.get("adjacencyMap", {})
    links_count = len(adjacency_map.get(current_region_id, [])) if current_region_id else 0
    
    status_str = f"{Fore.GREEN}ALIVE{Style.RESET_ALL}" if is_alive else f"{Fore.RED}DEAD{Style.RESET_ALL}"
    
    print(f"\n{Fore.CYAN}Day: 1 | Turn: {turn} | [{bot_name}] | Status: {status_str}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Agent Info :{Style.RESET_ALL}")
    print(f"HP {hp} / {max_hp} | EP {ep} / {max_ep} | ATK {atk} | DEF {df} | KILLS {kills}")
    print(f"Location : {current_region_id} | Weather: {weather} | Vision: {vision} | Links: {links_count}")
    
    pending_deathzones = frame_data.get("pendingDeathzones", [])
    active_deathzones = frame_data.get("activeDeathzones", [])
    
    print(f"\n{Fore.MAGENTA}Region Detector :{Style.RESET_ALL}")
    
    safe_path = detect_safe_regions_and_path(
        current_region_id,
        adjacency_map,
        pending_deathzones,
        active_deathzones
    )
    
    if safe_path:
        for i, layer in enumerate(safe_path):
            layer_str = ", ".join(layer)
            print(f"Layer {i} : {layer_str}")
    else:
        print(f"Layer 0 : {current_region_id}")
    print("")