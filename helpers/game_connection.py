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
    
    await log_callback("INFO", f"Connecting to WebSocket: {ws_url}")
    
    try:
        # Membuka koneksi WebSocket menggunakan 'additional_headers' untuk versi websockets>=11.0
        websocket = await websockets.connect(ws_url, additional_headers=headers)
        
        # 1. Membaca Frame 'welcome'
        welcome_msg = await websocket.recv()
        welcome_data = json.loads(welcome_msg)
        
        if welcome_data.get("type") != "welcome":
            await log_callback("ERROR", f"Expected welcome frame, but received: {welcome_msg}")
            await websocket.close()
            return None
            
        decision = welcome_data.get("decision")
        await log_callback("INFO", f"Welcome frame received. Decision: {decision}")
        
        if decision == "BLOCKED":
            await log_callback("ERROR", "Connection blocked by the game server.")
            await websocket.close()
            return None
        
        # Menentukan entryType berdasarkan instruksi decision server
        entry_type = room_preference
        if decision == "FREE_ONLY":
            entry_type = "free"
        elif decision == "PAID_ONLY":
            entry_type = "paid"
            
        # 2. Mengirimkan Frame Handshake 'hello'
        hello_payload = {
            "type": "hello",
            "entryType": entry_type,
            "mode": "offchain"
        }
        await log_callback("INFO", f"Sending hello handshake payload for entryType: {entry_type}")
        await websocket.send(json.dumps(hello_payload))
        
        # 3. Mendengarkan Frame Antrean & Status Pertarungan
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "queued":
                await log_callback("INFO", "Agent successfully entered the room matchmaking queue.")
            elif msg_type in ["assigned", "joined", "joined_game"]:
                game_id = data.get("gameId", "UNKNOWN")
                await log_callback("SUCCESS", f"Successfully entered game session! Game ID: {game_id}")
                return websocket
            elif msg_type == "error":
                await log_callback("ERROR", f"WS Server returned error: {data.get('message')}")
                await websocket.close()
                return None
            else:
                await log_callback("DEBUG", f"Received metadata frame: {message}")
                
    except websockets.exceptions.ConnectionClosed as e:
        await log_callback("ERROR", f"WebSocket closed unexpectedly. Code {e.code}, Reason: {e.reason}")
    except Exception as e:
        await log_callback("ERROR", f"Network connection failed: {str(e)}")
        
    return None