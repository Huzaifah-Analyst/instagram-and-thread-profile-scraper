import json
from urllib.parse import parse_qs

data = json.load(open("debug/network/all_ig_requests.json", "r", encoding="utf-8"))
for idx, req in enumerate(data):
    if "graphql" in req["url"]:
        post = req.get("post_data") or ""
        qs = parse_qs(post)
        fn = qs.get("fb_api_req_friendly_name", ["unknown"])[0]
        doc_id = qs.get("doc_id", ["none"])[0]
        vars_ = qs.get("variables", ["{}"])[0]
        print(f"IG GraphQL [{idx}]: friendly_name={fn}, doc_id={doc_id}, vars={vars_}")

thr_data = json.load(open("debug/network/all_threads_requests.json", "r", encoding="utf-8"))
for idx, req in enumerate(thr_data):
    if "graphql" in req["url"]:
        post = req.get("post_data") or ""
        qs = parse_qs(post)
        fn = qs.get("fb_api_req_friendly_name", ["unknown"])[0]
        doc_id = qs.get("doc_id", ["none"])[0]
        vars_ = qs.get("variables", ["{}"])[0]
        print(f"Threads GraphQL [{idx}]: friendly_name={fn}, doc_id={doc_id}, vars={vars_}")
