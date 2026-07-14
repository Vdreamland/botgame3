from typing import Dict, Any, Optional

def create_action_payload(action_type: str, data: Dict[str, Any], thought: Optional[str] = None) -> Dict[str, Any]:
    """
    Membungkus payload aksi ke dalam envelope standar komunikasi WebSocket.
    Membatasi thought maksimal 700 karakter sesuai batasan SOT.
    """
    payload = {
        "type": "action",
        "data": {
            "type": action_type,
            **data
        }
    }
    if thought:
        payload["thought"] = thought[:700]
    return payload

# AKSI BER-COOLDOWN (Mengkonsumsi EP atau memicu turn cooldown)
def move_payload(region_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("move", {"regionId": region_id}, thought)

def explore_payload(thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("explore", {}, thought)

def attack_payload(target_id: str, target_type: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("attack", {"targetId": target_id, "targetType": target_type}, thought)

def use_item_payload(item_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("use_item", {"itemId": item_id}, thought)

def interact_payload(interactable_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("interact", {"interactableId": interactable_id}, thought)

def rest_payload(thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("rest", {}, thought)

# AKSI INSTAN / BEBAS COOLDOWN (0 EP, Bisa dieksekusi kapan saja)
def pickup_payload(item_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("pickup", {"itemId": item_id}, thought)

def drop_payload(item_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("drop", {"itemId": item_id}, thought)

def equip_payload(item_id: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("equip", {"itemId": item_id}, thought)

def talk_payload(message: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("talk", {"message": message}, thought)

def whisper_payload(target_id: str, message: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("whisper", {"targetId": target_id, "message": message}, thought)

def broadcast_payload(message: str, thought: Optional[str] = None) -> Dict[str, Any]:
    return create_action_payload("broadcast", {"message": message}, thought)