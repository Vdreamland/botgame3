import requests
import os
import shutil
from pathlib import Path

BASE_URL = "https://clawroyale.ai"

REFERENCES = [
    "setup.md",
    "identity.md",
    "free-games.md",
    "paid-games.md",
    "game-loop.md",
    "errors.md",
    "game-systems.md",
    "actions.md",
    "economy.md",
    "limits.md",
    "api-summary.md",
    "contracts.md",
    "shop.md",
    "reforge.md",
    "preseason1-quests.md",
    "owner-guidance.md",
    "gotchas.md",
    "runtime-modes.md",
    "agent-memory.md",
    "agent-token.md",
    "sc-wallet-policy.md",
    "combat-items.md",
    "marketplace.md",
    "changelog.md"
]

TOP_LEVEL_FILES = [
    "skill.md",
    "heartbeat.md",
    "game-guide.md",
    "game-knowledge/strategy.md",
    "cross-forge-trade.md",
    "forge-token-deployer.md",
    "x402-quickstart.md",
    "x402-skill.md",
    "openapi.yaml"
]

def cleanup_old_files():
    for file in TOP_LEVEL_FILES:
        old_path = Path(file)
        if old_path.exists():
            try:
                old_path.unlink()
                print(f"Cleared old root file: {file}")
            except Exception:
                pass
    
    old_game_knowledge = Path("game-knowledge")
    if old_game_knowledge.exists() and old_game_knowledge.is_dir():
        try:
            shutil.rmtree(old_game_knowledge)
            print("Cleared old root game-knowledge directory")
        except Exception:
            pass

    old_ref_dir = Path("references")
    if old_ref_dir.exists() and old_ref_dir.is_dir():
        try:
            shutil.rmtree(old_ref_dir)
            print("Cleared old root references directory")
        except Exception:
            pass

def download_all():
    cleanup_old_files()
    
    session = requests.Session()
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    ref_dir = docs_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n--- Mengunduh Berkas Referensi ke docs/references/ ---")
    for ref in REFERENCES:
        url = f"{BASE_URL}/references/{ref}"
        filepath = ref_dir / ref
        
        print(f"Downloading {ref}...")
        resp = session.get(url)
        
        if resp.status_code == 200:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"✓ Berhasil: {ref}")
        else:
            print(f"✗ Gagal {ref} - Status: {resp.status_code}")
            
    print("\n--- Mengunduh Berkas Utama ke docs/ ---")
    for file in TOP_LEVEL_FILES:
        url = f"{BASE_URL}/{file}"
        filepath = docs_dir / file
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading {file}...")
        resp = session.get(url)
        
        if resp.status_code == 200:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"✓ Berhasil: {file}")
        else:
            print(f"✗ Gagal {file} - Status: {resp.status_code}")
            
    print("\nSemua unduhan selesai dan struktur telah ditata rapi!")

if __name__ == "__main__":
    download_all()