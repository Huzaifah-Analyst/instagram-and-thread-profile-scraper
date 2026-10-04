import json

def analyze(filename):
    print(f"\n================ ANALYZING {filename} ================")
    data = json.load(open(filename, "r", encoding="utf-8"))
    for idx, req in enumerate(data):
        url = req["url"]
        post = req.get("post_data") or ""
        body = req.get("body_snippet") or ""
        
        # Check if URL or body contains interesting info
        if "graphql" in url or "ajax" in url or "api" in url:
            print(f"\n[{idx}] {req['method']} {url}")
            if post:
                print(f"    Post Data: {post[:200]}")
            if body:
                print(f"    Body snippet: {body[:250].strip()}")

analyze("debug/network/all_ig_requests.json")
analyze("debug/network/all_threads_requests.json")
