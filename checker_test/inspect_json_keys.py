import json
from pathlib import Path

network_dir = Path("debug/network")
for f in network_dir.glob("*.json"):
    try:
        data = f.read_text(encoding="utf-8")
        low = data.lower()
        print(f"\n--- FILE: {f.name} (size: {len(data)}) ---")
        if "turkey" in low:
            print("  Found 'turkey' in response!")
        if "september" in low:
            print("  Found 'september' in response!")
        if "date_joined" in low or "joined" in low:
            print("  Found 'joined' in response!")
            
        # Parse JSON structure if possible
        if data.startswith("for (;;);"):
            clean = data.replace("for (;;);", "")
            j = json.loads(clean)
            print("  Cleaned Facebook/Threads JSON keys:", list(j.keys()))
        elif data.startswith("{"):
            j = json.loads(data)
            print("  JSON Top Keys:", list(j.keys()))
    except Exception as e:
        print(f"  Error reading {f.name}: {e}")
