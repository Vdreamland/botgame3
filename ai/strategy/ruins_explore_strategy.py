from typing import Dict, Any, Optional
from helpers.actions_payload import explore_payload
from helpers.world_parser import get_current_region, get_self_agent

def get_ruin_explore_action(frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    self_data = get_self_agent(frame_data)
    if not self_data:
        return None
    alert_gauge = self_data.get("alertGauge") or self_data.get("alert_gauge") or 0
    alert_active = self_data.get("alertActive") or self_data.get("alert_active") or False
    if alert_active or alert_gauge >= 8:
        return None
    current_region = get_current_region(frame_data)
    if not current_region:
        return None
    terrain = current_region.get("terrain", "").lower()
    if terrain != "ruins":
        return None
    gauge = current_region.get("ruinGauge") or current_region.get("ruin_gauge") or 0
    occupied = current_region.get("ruinOccupant") or current_region.get("ruin_occupant")
    if gauge >= 3:
        return None
    if occupied and occupied != self_data.get("name") and occupied != self_data.get("id"):
        return None
    ep = self_data.get("ep", 0)
    if ep >= 2:
        return explore_payload("Exploring ruins")
    return None