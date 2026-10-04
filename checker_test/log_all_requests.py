import json
import time
from playwright.sync_api import sync_playwright
import config

def log_all_requests():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        all_reqs = []
        
        def on_response(response):
            try:
                req = response.request
                url = response.url
                if "instagram.com" in url or "threads.net" in url or "threads.com" in url:
                    if not any(ext in url for ext in [".jpg", ".png", ".webp", ".mp4", ".css", ".svg", ".woff"]):
                        ct = response.headers.get("content-type", "")
                        body = ""
                        try:
                            body = response.text()
                        except Exception:
                            pass
                        all_reqs.append({
                            "url": url,
                            "method": req.method,
                            "post_data": req.post_data,
                            "content_type": ct,
                            "status": response.status,
                            "body_snippet": body[:500] if body else ""
                        })
            except Exception:
                pass
                
        page.on("response", on_response)
        
        print("--- Instagram About Navigation ---")
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
                
        print(f"Total Instagram requests logged: {len(all_reqs)}")
        
        with open(config.DEBUG_NETWORK_DIR / "all_ig_requests.json", "w", encoding="utf-8") as f:
            json.dump(all_reqs, f, indent=2)
            
        all_reqs.clear()
        
        print("--- Threads About Navigation ---")
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
                
        print(f"Total Threads requests logged: {len(all_reqs)}")
        with open(config.DEBUG_NETWORK_DIR / "all_threads_requests.json", "w", encoding="utf-8") as f:
            json.dump(all_reqs, f, indent=2)
            
        context.close()

if __name__ == "__main__":
    log_all_requests()
