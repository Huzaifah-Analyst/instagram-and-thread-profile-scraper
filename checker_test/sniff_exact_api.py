import json
import time
from playwright.sync_api import sync_playwright
import config

def sniff_endpoints():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        captured = []
        
        def handle_response(response):
            try:
                req = response.request
                url = response.url
                ct = response.headers.get("content-type", "")
                
                # Check for graphql or api calls
                if "graphql" in url or "api" in url or "ajax" in url:
                    try:
                        text = response.text()
                    except Exception:
                        text = ""
                        
                    low = text.lower()
                    # Check if response contains user profile transparency info
                    if any(k in low for k in ["date_joined", "formatted_date", "location_name", "country_name", "account_based_in", "based in", "september", "turkey", "100m+"]):
                        fn = config.DEBUG_NETWORK_DIR / f"sniff_{int(time.time()*1000)}.json"
                        with open(fn, "w", encoding="utf-8") as f:
                            json.dump({
                                "url": url,
                                "method": req.method,
                                "post_data": req.post_data,
                                "headers": req.headers,
                                "response_status": response.status,
                                "response_body": text
                            }, f, indent=2)
                        print(f"\n[FOUND MATCHING API RESP] URL: {url}")
                        print(f"  Method: {req.method} | Saved: {fn.name}")
                        print(f"  Post data: {req.post_data}")
                        captured.append({"url": url, "file": str(fn), "method": req.method, "post_data": req.post_data})
            except Exception as e:
                pass
                
        page.on("response", handle_response)
        
        # Test 1: Instagram About this account for ece25051
        print("\n=== Testing Instagram Network for @ece25051 ===")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(3)
        dots = page.locator("header div[aria-haspopup='dialog']").first
        if dots.count():
            dots.click()
            time.sleep(1.5)
            about = page.locator(":text('About this account')").first
            if about.count():
                about.click()
                time.sleep(4)
                
        # Test 2: Threads About this profile for ece25051
        print("\n=== Testing Threads Network for @ece25051 ===")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        card = page.locator("div:has-text('ece25051'):has-text('Follow')").last
        if not card.count():
            card = page.locator("div[role='main']").first
        dots_thr = card.locator("div[aria-haspopup='dialog']").first
        if dots_thr.count():
            dots_thr.click()
            time.sleep(1.5)
            about_thr = page.locator(":text('About this profile')").first
            if about_thr.count():
                about_thr.click()
                time.sleep(4)
                
        context.close()

if __name__ == "__main__":
    sniff_endpoints()
