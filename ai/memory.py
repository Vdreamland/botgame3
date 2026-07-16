from typing import Set, List, Optional

class BotMemory:
    def __init__(self):
        self.failed_items: Set[str] = set()
        self.failed_facilities: Set[str] = set()
        self.move_history: List[str] = []
        self.last_target_id: Optional[str] = None
        self.last_action_type: Optional[str] = None
        self.action_counter: int = 0
        self.equipped_attempts: Set[str] = set()
        self.drop_attempts: Set[str] = set()
        self.use_attempts: Set[str] = set()
        self.death_regions: Set[str] = set()

    def add_visited_region(self, region_id: str):
        if not self.move_history or self.move_history[-1] != region_id:
            self.move_history.append(region_id)
            if len(self.move_history) > 4:
                self.move_history.pop(0)

    def track_action_failure(self, current_item_ids: Set[str], current_fac_ids: Set[str]):
        if self.last_target_id:
            target_exists = (self.last_target_id in current_item_ids) or (self.last_target_id in current_fac_ids)
            if target_exists:
                self.action_counter += 1
                if self.action_counter > 2:
                    if self.last_action_type == "pickup":
                        self.failed_items.add(self.last_target_id)
                    elif self.last_action_type == "interact":
                        self.failed_facilities.add(self.last_target_id)
                    self.last_target_id = None
                    self.action_counter = 0
            else:
                self.last_target_id = None
                self.action_counter = 0