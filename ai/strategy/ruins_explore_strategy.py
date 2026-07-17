from typing import Dict, Any, Optional
from helpers.world_parser import get_visible_ruins, get_self_agent, get_current_region
from helpers.actions_payload import explore_payload

def get_ruin_explore_action(frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    self_data = get_self_agent(frame_data)
    current_region = get_current_region(frame_data)
    if not self_data or not current_region:
        return None
    current_id = current_region.get("id")
    ep = self_data.get("ep", 0)
    if ep < 2:
        return None
    visible_ruins = get_visible_ruins(frame_data)
    local_ruin = next((r for r in visible_ruins if (r.get("id") or r.get("ruinId")) == current_id), None)
    if local_ruin:
        gauge = local_ruin.get("gauge", local_ruin.get("ruinGauge", 0))
        occupied_by = local_ruin.get("occupiedBy")
        our_id = self_data.get("id")
        if gauge < 3 and (not occupied_by or occupied_by == our_id):
            return explore_payload("Exploring local ruin")
    return None