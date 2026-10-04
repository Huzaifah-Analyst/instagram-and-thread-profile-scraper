import time
from playwright.sync_api import sync_playwright
import config

def dump_all_svgs():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Instagram
        print("--- Instagram SVGs ---")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(4)
        svgs = page.locator("header svg, [role='main'] svg, section svg").all()
        for idx, s in enumerate(svgs):
            try:
                print(f"IG SVG {idx}: aria={repr(s.get_attribute('aria-label'))}, role={repr(s.get_attribute('role'))}, html={repr(s.evaluate('el => el.outerHTML'))[:120]}")
            except Exception as e:
                pass

        # 2. Threads
        print("\n--- Threads SVGs ---")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(4)
        thr_svgs = page.locator("div[role='main'] svg, header svg, main svg").all()
        for idx, s in enumerate(thr_svgs):
            try:
                print(f"Threads SVG {idx}: aria={repr(thr_svgs[idx].get_attribute('aria-label'))}, html={repr(thr_svgs[idx].evaluate('el => el.outerHTML'))[:120]}")
            except Exception as e:
                pass
                
        context.close()

if __name__ == "__main__":
    dump_all_svgs()
