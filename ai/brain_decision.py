import json
from typing import Dict, Any, Optional
from helpers.world_parser import get_current_region, get_self_agent
from helpers.actions_payload import move_payload, explore_payload, rest_payload
from ai.memory import BotMemory
from ai.strategy.loot_strategy import find_current_region_targets, find_target_regions
from ai.strategy.movement_strategy import find_shortest_path

class BrainDecision:
    def __init__(self):
        self.memory = BotMemory()

    def get_next_action(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_region = get_current_region(frame_data)
        self_data = get_self_agent(frame_data)
        if not current_region or not self_data:
            return None
        current_id = current_region.get("id")
        self.memory.add_visited_region(current_id)
        current_items = current_region.get("items", [])
        current_interactables = current_region.get("interactables", [])
        current_item_ids = {item.get("id") for item in current_items if item.get("id")}
        current_fac_ids = {fac.get("id") for fac in current_interactables if fac.get("id")}
        self.memory.track_action_failure(current_item_ids, current_fac_ids)
        action = find_current_region_targets(frame_data, self.memory)
        if action:
            return action
        target_regions = find_target_regions(frame_data, self.memory)
        if target_regions:
            path = find_shortest_path(frame_data, target_regions)
            if path and len(path) > 1:
                next_region_id = path[1]
                self.memory.last_target_id = None
                self.memory.last_action_type = "move"
                return move_payload(next_region_id, "Moving to target region")
        ep = self_data.get("ep", 0)
        connections = current_region.get("connections", [])
        unvisited_connections = [c for c in connections if c not in self.memory.move_history]
        next_fallback_id = None
        if unvisited_connections:
            next_fallback_id = unvisited_connections[0]
        elif connections:
            next_fallback_id = connections[0]
        ruin_gauge = current_region.get("ruinGauge", 3)
        if ruin_gauge < 3 and ep >= 2:
            return explore_payload("Exploring ruin")
        if ep >= 2 and next_fallback_id:
            self.memory.last_target_id = None
            self.memory.last_action_type = "move"
            return move_payload(next_fallback_id, "Moving to unvisited region to search")
        if ep < 2:
            return rest_payload("Resting to recover EP")
        return explore_payload("Exploring local region")