class BotMemory:
    def __init__(self):
        self.failed_items = set()
        self.failed_facilities = set()
        self.failed_attacks = set()
        self.move_history = []
        self.last_target_id = None
        self.last_action_type = None
        self.action_counter = 0
        self.equipped_attempts = set()
        self.drop_attempts = set()
        self.use_attempts = set()
        self.pickup_attempts = set()
        self.death_regions = set()
        self.known_death_zones = set()

    def add_visited_region(self, region_id: str):
        self.move_history.append(region_id)
        if len(self.move_history) > 4:
            self.move_history.pop(0)

    def track_action_failure(self, current_item_ids, current_fac_ids, current_enemy_ids):
        if self.last_action_type == "pickup" and self.last_target_id:
            if self.last_target_id in current_item_ids:
                self.action_counter += 1
                if self.action_counter >= 2:
                    self.failed_items.add(self.last_target_id)
            else:
                self.action_counter = 0
                self.last_target_id = None
                self.last_action_type = None
        elif self.last_action_type == "interact" and self.last_target_id:
            if self.last_target_id in current_fac_ids:
                self.action_counter += 1
                if self.action_counter >= 2:
                    self.failed_facilities.add(self.last_target_id)
            else:
                self.action_counter = 0
                self.last_target_id = None
                self.last_action_type = None
        elif self.last_action_type == "attack" and self.last_target_id:
            if self.last_target_id in current_enemy_ids:
                self.action_counter += 1
                if self.action_counter >= 2:
                    self.failed_attacks.add(self.last_target_id)
            else:
                self.action_counter = 0
                self.last_target_id = None
                self.last_action_type = None