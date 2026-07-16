from typing import Dict, Any, Optional

def create_action_payload(action_type: str, data: Dict[str, Any], thought: Optional[str] = None) -> Dict[str, Any]:
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

def move_payload(region_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("move", {
        "regionId": region_id,
        "region_id": region_id
    }, thought)

def explore_payload(thought: str) -> Dict[str, Any]:
    return create_action_payload("explore", {}, thought)

def attack_payload(target_id: str, target_type: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("attack", {
        "targetId": target_id,
        "targetType": target_type,
        "target_id": target_id,
        "target_type": target_type
    }, thought)

def use_item_payload(item_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("use_item", {
        "itemId": item_id,
        "item_id": item_id
    }, thought)

def interact_payload(interactable_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("interact", {
        "interactableId": interactable_id,
        "interactable_id": interactable_id
    }, thought)

def rest_payload(thought: str) -> Dict[str, Any]:
    return create_action_payload("rest", {}, thought)

def pickup_payload(item_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("pickup", {
        "itemId": item_id,
        "item_id": item_id
    }, thought)

def drop_payload(item_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("drop", {
        "itemId": item_id,
        "item_id": item_id
    }, thought)

def equip_payload(item_id: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("equip", {
        "itemId": item_id,
        "item_id": item_id
    }, thought)

def talk_payload(message: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("talk", {
        "message": message
    }, thought)

def whisper_payload(target_id: str, message: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("whisper", {
        "targetId": target_id,
        "target_id": target_id,
        "message": message
    }, thought)

def broadcast_payload(message: str, thought: str) -> Dict[str, Any]:
    return create_action_payload("broadcast", {
        "message": message
    }, thought)