from pathlib import Path

spec_path = Path("docs/openapi.yaml")
if not spec_path.exists():
    print("docs/openapi.yaml tidak ditemukan!")
    exit(1)

print("Membaca docs/openapi.yaml...")
with open(spec_path, "r", encoding="utf-8") as f:
    try:
        content = f.read()
        lines = content.splitlines()
        
        print("\n--- Daftar Seluruh Rute API dari openapi.yaml ---")
        in_paths = False
        for line in lines:
            if line.startswith("paths:"):
                in_paths = True
                continue
            if in_paths:
                if line.startswith("  /"):
                    current_path = line.strip().split(":")[0]
                    print(current_path)
                elif line.strip() and not line.startswith("  ") and not line.startswith("paths:"):
                    in_paths = False
    except Exception as e:
        print(f"Error: {e}")