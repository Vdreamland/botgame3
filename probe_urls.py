import requests

variants = [
    # 1. Menggunakan domain utama (clawroyale.ai)
    "https://clawroyale.ai/references/setup.md",
    "https://clawroyale.ai/references/setup",
    "https://clawroyale.ai/skill.md",
    
    # 2. Menggunakan alias (moltyroyale.com)
    "https://moltyroyale.com/references/setup.md",
    "https://moltyroyale.com/references/setup",
    "https://moltyroyale.com/skill.md",
    
    # 3. Menggunakan API reference endpoint (tanpa .md)
    "https://cdn.clawroyale.ai/api/reference/setup",
    "https://cdn.clawroyale.ai/api/reference/relics-and-packs",
    "https://cdn.clawroyale.ai/api/reference/combat-items",
    "https://cdn.clawroyale.ai/api/reference/loadout-setup",
    
    # 4. Menggunakan CDN dengan variasi subfolder
    "https://cdn.clawroyale.ai/references/setup.md",
    "https://cdn.clawroyale.ai/references/setup",
    "https://cdn.clawroyale.ai/skill.md"
]

print("Mulai memindai variasi URL untuk menemukan rute dokumentasi...\n")
session = requests.Session()

for url in variants:
    try:
        resp = session.head(url, allow_redirects=True, timeout=5)
        print(f"URL: {url}")
        print(f"  -> Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  -> [DITEMUKAN!]")
    except Exception as e:
        print(f"URL: {url} -> Error: {e}")
    print("-" * 50)