import json
import time
from playwright.sync_api import sync_playwright
import config

def capture_network_exact():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        captured_endpoints = []
        def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "json" in ct or "text/javascript" in ct or "application/graphql" in ct:
                    t = response.text()
                    low = t.lower()
                    if "turkey" in low or "september" in low or "based_in" in low or "joined" in low or "about" in low:
                        fn = config.DEBUG_NETWORK_DIR / f"exact_{int(time.time()*1000)}.json"
                        with open(fn, "w", encoding="utf-8") as f:
                            f.write(t)
                        captured_endpoints.append({
                            "url": response.url,
                            "file": str(fn),
                            "length": len(t),
                            "preview": t[:300]
                        })
                        print(f"Captured: {response.url[:80]} -> {fn.name}")
            except Exception:
                pass
        
        page.on("response", on_response)
        
        # Test Threads ece25051
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        card = page.locator("div:has-text('ece25051'):has-text('Follow')").last
        if not card.count():
            card = page.locator("div[role='main']").first
        dots = card.locator("div[aria-haspopup='dialog']").first
        if dots.count() and dots.is_visible():
            dots.click()
            time.sleep(1.5)
            about_opt = page.locator(":text('About this profile')").first
            if about_opt.count():
                about_opt.click()
                time.sleep(3)
                
        # Test Instagram ece25051
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(3)
        dots_ig = page.locator("header div[aria-haspopup='dialog']").first
        if dots_ig.count():
            dots_ig.click()
            time.sleep(1.5)
            about_ig = page.locator(":text('About this account')").first
            if about_ig.count():
                about_ig.click()
                time.sleep(3)
                
        context.close()
        
        print("\nCaptured endpoints summary:")
        for ep in captured_endpoints:
            print(f"- URL: {ep['url']}")
            print(f"  File: {ep['file']}")
            print(f"  Preview: {ep['preview']}\n")

if __name__ == "__main__":
    capture_network_exact()
