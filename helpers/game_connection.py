import json
import asyncio
import websockets
from typing import Dict, Any, Callable, Awaitable, Optional

async def connect_and_join_room(
    api_key: str,
    version: str,
    ws_url: str,
    room_preference: str,
    log_callback: Callable[[str, str], Awaitable[None]]
) -> Optional[websockets.WebSocketClientProtocol]:
    """
    Melakukan koneksi WebSocket terpadu ke /ws/join, memproses handshake hello,
    hingga berhasil masuk ke status queued dan assigned/joined.
    """
    headers = {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": version
    }
    
    await log_callback("INFO", "Opening secure connection to game server...")
    
    try:
        websocket = await websockets.connect(ws_url, additional_headers=headers)
        
        welcome_msg = await websocket.recv()
        welcome_data = json.loads(welcome_msg)
        
        if welcome_data.get("type") != "welcome":
            await log_callback("ERROR", f"Invalid server response: {welcome_msg}")
            await websocket.close()
            return None
            
        decision = welcome_data.get("decision")
        await log_callback("INFO", "Successfully authenticated with game server.")
        
        if decision == "BLOCKED":
            await log_callback("ERROR", "Access denied: Account is currently blocked.")
            await websocket.close()
            return None
        
        entry_type = room_preference
        if decision == "FREE_ONLY":
            entry_type = "free"
        elif decision == "PAID_ONLY":
            entry_type = "paid"
            
        await log_callback("INFO", f"Requesting matchmaking entry for {entry_type.upper()} room...")
        
        hello_payload = {
            "type": "hello",
            "entryType": entry_type,
            "mode": "offchain"
        }
        await websocket.send(json.dumps(hello_payload))
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "queued":
                await log_callback("INFO", "Waiting in matchmaking queue...")
            elif msg_type in ["assigned", "joined", "joined_game"]:
                game_id = data.get("gameId", "UNKNOWN")
                short_id = game_id[:8] if len(game_id) > 8 else game_id
                await log_callback("SUCCESS", f"Match Found! Successfully joined game room (ID: {short_id})")
                return websocket
            elif msg_type == "error":
                await log_callback("ERROR", f"Server error: {data.get('message')}")
                await websocket.close()
                return None
            else:
                await log_callback("DEBUG", f"Server update: {message}")
                
    except websockets.exceptions.ConnectionClosed as e:
        await log_callback("ERROR", f"Connection closed abruptly (Code: {e.code})")
    except Exception as e:
        await log_callback("ERROR", f"Connection failed: {str(e)}")
        
    return None

async def connect_and_resume_game(
    api_key: str,
    version: str,
    ws_url: str,
    log_callback: Callable[[str, str], Awaitable[None]]
) -> Optional[websockets.WebSocketClientProtocol]:
    """
    SOT Rule: IN_GAME -> Menghubungkan kembali agen yang sedang dalam permainan aktif ke arena
    menggunakan rute WebSocket resmi /ws/agent (WS_GAMEPLAY_URL).
    """
    headers = {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": version
    }
    
    await log_callback("INFO", "Reconnecting to active game session...")
    
    try:
        websocket = await websockets.connect(ws_url, additional_headers=headers)
        await log_callback("SUCCESS", "Successfully reconnected to active arena! Listening to game updates...")
        return websocket
    except Exception as e:
        await log_callback("ERROR", f"Failed to reconnect to active arena: {str(e)}")
        
    return None