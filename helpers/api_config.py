import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Memuat variabel lingkungan dari .env
load_dotenv()

BASE_URL = os.getenv("API_URL", "https://cdn.clawroyale.ai/api").rstrip("/")
WS_URL = os.getenv("WS_URL", "wss://cdn.clawroyale.ai/ws/join").rstrip("/")
WS_GAMEPLAY_URL = os.getenv("WS_GAMEPLAY_URL", "wss://cdn.clawroyale.ai/ws/agent").rstrip("/")

# Aturan Sistem Tiga-Dompet (Three-Wallet System) sesuai panduan web
THREE_WALLET_RULES = {
    "OWNER_WALLET": "Used for whitelisting and management. Controlled by the player.",
    "CLAWROYALE_WALLET": "Smart contract wallet that holds Moltz and CROSS. Paid room fees are deducted from here.",
    "AGENT_WALLET": "In-game EOA signer used only for signing game actions. Never send Moltz here directly."
}

def get_api_endpoints() -> Dict[str, str]:
    """
    Mengembalikan seluruh rute REST API resmi yang terdaftar pada SOT (api-summary.md).
    Mendukung manajemen loadout, inventori, transaksi, marketplace, profil, dan dashboard.
    """
    return {
        # Diagnostics
        "version": f"{BASE_URL}/version",
        "paid_fee": f"{BASE_URL}/paid/fee",
        
        # Accounts & Wallet
        "me": f"{BASE_URL}/accounts/me",
        "accounts": f"{BASE_URL}/accounts",
        "register": f"{BASE_URL}/accounts",
        "accounts_wallet": f"{BASE_URL}/accounts/wallet",
        "accounts_history": f"{BASE_URL}/accounts/history",
        "create_wallet": f"{BASE_URL}/create/wallet",
        "whitelist_request": f"{BASE_URL}/whitelist/request",
        
        # Identity (ERC-8004) & Agent Token (Forge)
        "identity": f"{BASE_URL}/identity",
        "agent_token_register": f"{BASE_URL}/agent-token/register",
        
        # Dashboard & Performance (Returns raw JSON without envelope)
        "dashboard_overview": f"{BASE_URL}/accounts/me/dashboard/overview",
        "dashboard_daily": f"{BASE_URL}/accounts/me/dashboard/daily",
        "dashboard_combat": f"{BASE_URL}/accounts/me/dashboard/combat",
        "dashboard_games": f"{BASE_URL}/accounts/me/dashboard/games",
        "acquisitions": f"{BASE_URL}/accounts/me/acquisitions",
        "leaderboard_rank": f"{BASE_URL}/accounts/me/leaderboard-rank",
        
        # Inventory Management
        "inventory_relics": f"{BASE_URL}/inventory/relics",
        "inventory_relics_id": f"{BASE_URL}/inventory/relics/{{id}}",
        "inventory_packs": f"{BASE_URL}/inventory/packs",
        "inventory_packs_id": f"{BASE_URL}/inventory/packs/{{id}}",
        "inventory_materials": f"{BASE_URL}/inventory/items?category=material",
        
        # Loadout Configuration (Wajib fullset agar status pasif aktif)
        "loadout": f"{BASE_URL}/loadout",
        "loadout_pack": f"{BASE_URL}/loadout/pack",
        "loadout_sub_pack": f"{BASE_URL}/loadout/sub-pack",
        "loadout_slot": f"{BASE_URL}/loadout/slot/{{typeIndex}}", # typeIndex: 0, 1, atau 2
        
        # Shop & Promo Redemption
        "shop_listings": f"{BASE_URL}/shop/listings",
        "shop_purchase": f"{BASE_URL}/shop/purchase",
        "redeem": f"{BASE_URL}/redeem",
        
        # Weekly & Reforge
        "weekly_claim": f"{BASE_URL}/weekly/claim",
        "weekly_status": f"{BASE_URL}/accounts/me/weekly",
        "reforge": f"{BASE_URL}/reforge",
        
        # P2P Marketplace
        "marketplace_listings": f"{BASE_URL}/marketplace/listings",
        "marketplace_buy": f"{BASE_URL}/marketplace/listings/{{id}}/buy",
        "marketplace_delete": f"{BASE_URL}/marketplace/listings/{{id}}",
        
        # Notification Box (Inbox)
        "notifications": f"{BASE_URL}/notifications",
        "notifications_read": f"{BASE_URL}/notifications/{{id}}/read",
        "notifications_read_all": f"{BASE_URL}/notifications/read-all",
        "notifications_delete": f"{BASE_URL}/notifications/{{id}}",
        "notifications_clear_all": f"{BASE_URL}/notifications/clear-all",
        
        # Profile
        "profiles": f"{BASE_URL}/profiles",
        "profile_update": f"{BASE_URL}/accounts/me/profile",
    }

def get_bots_config() -> List[Dict[str, Any]]:
    """
    Mengurai berkas .env untuk mengumpulkan data multi-bot berbasis indeks secara dinamis.
    """
    num_bots_str = os.getenv("NUM_BOTS", "1")
    try:
        num_bots = int(num_bots_str)
    except ValueError:
        num_bots = 1

    default_preference = os.getenv("ROOM_PREFERENCE", "free")
    bots = []

    for i in range(1, num_bots + 1):
        name = os.getenv(f"BOT{i}_NAME")
        api_key = os.getenv(f"BOT{i}_API_KEY")
        preference = os.getenv(f"BOT{i}_ROOM_PREFERENCE", default_preference)

        if name and api_key:
            bots.append({
                "index": i,
                "name": name,
                "api_key": api_key,
                "room_preference": preference
            })
    return bots

def get_headers(api_key: str, version: str) -> Dict[str, str]:
    return {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": version,
        "Content-Type": "application/json"
    }

def get_headers_jwt(token: str, version: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Version": version,
        "Content-Type": "application/json"
    }