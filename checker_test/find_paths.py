import json

def find_paths(obj, target="turkey", path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if target.lower() in str(k).lower() or target.lower() in str(v).lower():
                if isinstance(v, (str, int, float, bool)):
                    print(f"Match at path '{new_path}': {v}")
                else:
                    find_paths(v, target, new_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_paths(item, target, f"{path}[{i}]")

data = open("debug/network/exact_1790775259896.json", "r", encoding="utf-8").read()
if data.startswith("for (;;);"):
    data = data.replace("for (;;);", "")
j = json.loads(data)
print("Searching in Threads exact network capture:")
find_paths(j, "turkey")
find_paths(j, "september")
