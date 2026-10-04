import json
import time
from playwright.sync_api import sync_playwright
import config

def test_instagram_and_threads():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Capture network
        network_logs = []
        def log_resp(resp):
            try:
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    t = resp.text()
                    low = t.lower()
                    if any(k in low for k in ["joined", "date_joined", "location", "country", "about_this_account", "about_this_profile"]):
                        fn = config.DEBUG_NETWORK_DIR / f"api_resp_{int(time.time()*1000)}.json"
                        with open(fn, "w", encoding="utf-8") as f:
                            f.write(t)
                        network_logs.append((resp.url, fn))
                        print(f"  [SAVED API RESP] {resp.url}")
            except Exception:
                pass
        page.on("response", log_resp)

        # 1. INSTAGRAM TEST
        print("\n" + "="*50)
        print("TESTING INSTAGRAM: ece25051")
        print("="*50)
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Click Options button
        # Selector: header div[aria-haspopup='dialog']
        opt_btn = page.locator("header div[aria-haspopup='dialog']:has(svg[aria-label='Options']), header svg[aria-label='Options']").first
        if opt_btn.count():
            print("Found Instagram options button. Clicking...")
            opt_btn.click()
            time.sleep(2)
            page.screenshot(path=str(config.DEBUG_DIR / "ig_ece25051_modal.png"))
            
            # Find and click "About this account"
            about_btn = page.locator("button:has-text('About this account'), button:has-text('Bu hesap hakkında')").first
            if about_btn.count():
                print("Found 'About this account' button! Clicking...")
                about_btn.click()
                time.sleep(2)
                page.screenshot(path=str(config.DEBUG_DIR / "ig_ece25051_about_dialog.png"))
                
                # Extract text
                dialog = page.locator("div[role='dialog']").first
                if dialog.count():
                    print("\n--- INSTAGRAM 'ABOUT THIS ACCOUNT' TEXT ---")
                    print(dialog.inner_text())
                    print("-------------------------------------------\n")
            else:
                print("'About this account' button not found in modal.")
                print("Modal content:\n", page.locator("div[role='dialog']").inner_text())
        else:
            print("Options button not found on Instagram header.")

        # 2. THREADS TEST
        print("\n" + "="*50)
        print("TESTING THREADS: ece25051")
        print("="*50)
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        # On Threads profile page, find the 3 dots button on the profile header
        # In Threads, the profile header has: Instagram link, Notification bell, and 3-dots button
        # The 3-dots button is div[aria-haspopup='menu']
        thr_dots = page.locator("div[role='main'] div[aria-haspopup='menu']:has(svg)").first
        if not thr_dots.count():
            # Alternative: find 3rd child in the icon group
            thr_dots = page.locator("div[role='main'] svg[aria-label*='More'], div[role='main'] svg[aria-label*='Daha fazla']").locator("..").first
            
        if thr_dots.count():
            print("Found Threads 3-dots button. Clicking...")
            thr_dots.click()
            time.sleep(2)
            page.screenshot(path=str(config.DEBUG_DIR / "threads_ece25051_menu.png"))
            
            # Check menu
            menu = page.locator("div[role='menu'], div[data-pressable-container='true']").first
            if menu.count():
                print("Threads Menu Text:\n", menu.inner_text())
                
                about_thr = page.locator(":has-text('About this profile'), :has-text('Bu profil hakkında')").first
                if about_thr.count():
                    print("Found 'About this profile'! Clicking...")
                    about_thr.click()
                    time.sleep(2)
                    page.screenshot(path=str(config.DEBUG_DIR / "threads_ece25051_about_dialog.png"))
                    d_thr = page.locator("div[role='dialog']").first
                    if d_thr.count():
                        print("\n--- THREADS 'ABOUT THIS PROFILE' TEXT ---")
                        print(d_thr.inner_text())
                        print("-----------------------------------------\n")
                else:
                    print("'About this profile' not found in Threads menu.")
        else:
            print("Threads 3-dots button not found.")
            
        context.close()

if __name__ == "__main__":
    test_instagram_and_threads()
