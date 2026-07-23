from typing import Dict, Any, List, Set, Optional

class BotMemory:
    def __init__(self):
        self.failed_items: Set[str] = set()
        self.failed_facilities: Set[str] = set()
        self.failed_attacks: Set[str] = set()
        self.move_history: List[str] = []
        self.last_target_id: Optional[str] = None
        self.last_action_type: Optional[str] = None
        self.action_counter: int = 0
        self.equipped_attempts: Set[str] = set()
        self.drop_attempts: Set[str] = set()
        self.use_attempts: Set[str] = set()
        self.pickup_attempts: Set[str] = set()
        self.death_regions: Set[str] = set()
        self.known_death_zones: Set[str] = set()
        self.last_failure_turn: int = -1

    def add_visited_region(self, region_id: str) -> None:
        self.move_history.append(region_id)
        if len(self.move_history) > 4:
            self.move_history.pop(0)

    def track_action_failure(self, current_item_ids: Set[str], current_fac_ids: Set[str], current_enemy_ids: Set[str], current_turn: int = 0) -> None:
        if current_turn == self.last_failure_turn:
            return
        self.last_failure_turn = current_turn
        if self.last_target_id and self.last_action_type:
            still_exists = False
            if self.last_action_type == "pickup" and self.last_target_id in current_item_ids:
                still_exists = True
            elif self.last_action_type == "interact" and self.last_target_id in current_fac_ids:
                still_exists = True
            elif self.last_action_type == "attack" and self.last_target_id in current_enemy_ids:
                still_exists = True
            if still_exists:
                self.action_counter += 1
                if self.action_counter >= 2:
                    if self.last_action_type == "pickup":
                        self.failed_items.add(self.last_target_id)
                    elif self.last_action_type == "interact":
                        self.failed_facilities.add(self.last_target_id)
                    elif self.last_action_type == "attack":
                        self.failed_attacks.add(self.last_target_id)
                    self.action_counter = 0
                    self.last_target_id = None
                    self.last_action_type = None
            else:
                self.action_counter = 0
                self.last_target_id = None
                self.last_action_type = None