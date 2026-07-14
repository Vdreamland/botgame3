import requests
from typing import Dict, Any, Tuple
from helpers.api_config import get_api_endpoints, get_headers

def check_agent_state(api_key: str, version: str, preference: str) -> Tuple[str, Any]:
    """
    Melakukan verifikasi akun via GET /accounts/me untuk menentukan alur state pra-game.
    Mengembalikan Tuple berupa (state_name, data_or_error_message).
    """
    endpoints = get_api_endpoints()
    headers = get_headers(api_key, version)
    
    try:
        response = requests.get(endpoints["me"], headers=headers, timeout=10)
        
        if response.status_code in [401, 403]:
            return "NO_ACCOUNT", "Unauthorized API Key."
        elif response.status_code == 426:
            return "ERROR", "VERSION_MISMATCH"
        elif response.status_code != 200:
            return "ERROR", f"HTTP {response.status_code}: {response.text}"
        
        res_json = response.json()
        if not res_json.get("success", False):
            return "ERROR", res_json.get("error", {}).get("message", "API Error")
        
        data = res_json.get("data", {})
        
        # Deteksi jika agen masih memiliki game aktif di arena
        current_games = data.get("currentGames", [])
        for game in current_games:
            if game.get("isAlive", False) and game.get("gameStatus") != "finished":
                return "IN_GAME", game
                
        # Deteksi kelayakan status paid room
        readiness = data.get("readiness", {})
        if preference == "paid" and readiness.get("paidReady", False):
            return "READY_PAID", data
        
        return "READY_FREE", data

    except requests.exceptions.RequestException as e:
        return "ERROR", str(e)