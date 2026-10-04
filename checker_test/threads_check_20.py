import time
import pandas as pd
from playwright.sync_api import sync_playwright
import config

def check_20_on_threads():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        usernames = [l.strip() for l in open("usernames.txt").readlines() if l.strip()][:10]
        
        for u in usernames:
            print(f"\n--- Checking Threads @{u} ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(2.5)
            
            ss_path = config.DEBUG_DIR / f"thr_batch_{u}.png"
            page.screenshot(path=str(ss_path))
            print(f"Saved screenshot: {ss_path.name}")
            
            # Look for 3-dots
            # In Threads web, the 3 dots is a button with aria-label or SVG in header
            # Let's find all buttons and SVGs
            btns = page.locator("header [role='button'], div[role='main'] [role='button']").all()
            print(f"Buttons found: {len(btns)}")
            for idx, b in enumerate(btns):
                if b.is_visible():
                    aria = b.get_attribute("aria-label") or ""
                    txt = b.inner_text()
                    print(f"  Btn {idx}: aria={aria}, text={repr(txt)}")
                    
        context.close()

if __name__ == "__main__":
    check_20_on_threads()
