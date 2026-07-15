from typing import Dict, Any

def get_agent_stats(frame_data: Dict[str, Any]) -> Dict[str, int]:
    view_data = frame_data.get("view", {})
    self_data = view_data.get("self", {})
    return {
        "hp": self_data.get("hp", 0),
        "ep": self_data.get("ep", 0),
        "atk": self_data.get("atk", 0),
        "def": self_data.get("def", 0),
        "kills": self_data.get("kills", self_data.get("killCount", 0))
    }

def get_formatted_log(frame_data: Dict[str, Any]) -> str:
    stats = get_agent_stats(frame_data)
    current_id = (
        frame_data.get("currentRegionId") or 
        frame_data.get("view", {}).get("currentRegionId") or 
        frame_data.get("view", {}).get("self", {}).get("regionId") or 
        frame_data.get("view", {}).get("self", {}).get("currentRegionId")
    )
    regions = (
        frame_data.get("view", {}).get("visibleRegions") or 
        frame_data.get("view", {}).get("regions") or 
        []
    )
    current_region = {}
    for r in regions:
        if r.get("id") == current_id:
            current_region = r
            break
    terrain = current_region.get("terrain", "unknown")
    weather = current_region.get("weather", "unknown")
    vision = current_region.get("vision", 0)
    links = len(current_region.get("connectedRegions", []))
    return f"Agent Info :\nHP {stats['hp']} / EP {stats['ep']} / ATK {stats['atk']} / DEF {stats['def']} / KILLS {stats['kills']}\nLocation : {terrain} / {weather} / {vision} / {links}"