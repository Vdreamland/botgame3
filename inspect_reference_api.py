from pathlib import Path

spec_path = Path("docs/openapi.yaml")
if not spec_path.exists():
    print("docs/openapi.yaml tidak ditemukan!")
    exit(1)

print("Membaca dokumentasi rute /api/reference/{section}...")
with open(spec_path, "r", encoding="utf-8") as f:
    try:
        content = f.read()
        lines = content.splitlines()
        
        found = False
        indent_level = -1
        for line in lines:
            if line.startswith("  /api/reference/{section}:"):
                found = True
                print(line)
                continue
            
            if found:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() == "":
                    print(line)
                    continue
                if current_indent <= 2 and not line.startswith("  /api/reference/{section}:"):
                    break
                print(line)
                
    except Exception as e:
        print(f"Error: {e}")