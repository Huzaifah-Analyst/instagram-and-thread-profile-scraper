import time
from playwright.sync_api import sync_playwright
import config

def test_about_click():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Capture network
        network_data = []
        def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "json" in ct:
                    t = response.text()
                    low = t.lower()
                    if any(k in low for k in ["joined", "date_joined", "location", "country", "about_this_account", "about_this_profile", "about"]):
                        fn = config.DEBUG_NETWORK_DIR / f"net_ig_{int(time.time()*1000)}.json"
                        with open(fn, "w", encoding="utf-8") as f:
                            f.write(t)
                        print(f"  [SAVED API RESP] {response.url[:70]} -> {fn.name}")
                        network_data.append((response.url, str(fn)))
            except Exception:
                pass
        page.on("response", on_response)

        # 1. Instagram ece25051
        print("\nOpening IG ece25051...")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Click 3 dots
        dots = page.locator("header div[aria-haspopup='dialog'], header button:has(svg), header svg[aria-label='Options']").first
        if dots.count():
            dots.click()
            time.sleep(1.5)
            
            # Click "About this account"
            about_item = page.locator(":text('About this account'), :text('Bu hesap hakkında')").first
            if about_item.count():
                print("Found 'About this account'! Clicking...")
                about_item.click()
                time.sleep(3)
                
                ss_path = config.DEBUG_DIR / "ig_ece25051_about_modal.png"
                page.screenshot(path=str(ss_path))
                print(f"Screenshot saved to {ss_path}")
                
                # Get all text inside dialog
                dialog = page.locator("div[role='dialog']").first
                if dialog.count():
                    print("\n========================================")
                    print("INSTAGRAM 'ABOUT THIS ACCOUNT' CONTENT:")
                    print("========================================")
                    print(dialog.inner_text())
                    print("========================================\n")
        
        # 2. Threads ece25051
        print("\nOpening Threads ece25051...")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(4)
        
        # On Threads, let's find the 3 dots button
        # In Threads, the 3 dots popup is div[aria-haspopup='menu']
        thr_dots = page.locator("div[aria-haspopup='menu']").filter(has_not_text="More").first
        if not thr_dots.count():
            thr_dots = page.locator("svg circle").first.locator("xpath=ancestor::div[@role='button' or @aria-haspopup][1]")
            
        if thr_dots.count():
            print("Found Threads 3-dots! Clicking...")
            thr_dots.click()
            time.sleep(2)
            page.screenshot(path=str(config.DEBUG_DIR / "thr_ece25051_menu_clicked.png"))
            
            # Look for "About this profile"
            about_thr = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
            if about_thr.count() and about_thr.is_visible():
                print("Found 'About this profile' on Threads! Clicking...")
                about_thr.click()
                time.sleep(3)
                ss_thr = config.DEBUG_DIR / "thr_ece25051_about_modal.png"
                page.screenshot(path=str(ss_thr))
                d_thr = page.locator("div[role='dialog']").first
                if d_thr.count():
                    print("\n========================================")
                    print("THREADS 'ABOUT THIS PROFILE' CONTENT:")
                    print("========================================")
                    print(d_thr.inner_text())
                    print("========================================\n")
            else:
                print("Visible text in Threads menu:")
                for m in page.locator("div[role='menu'], div[data-pressable-container='true']").all():
                    print(repr(m.inner_text()))

        context.close()

if __name__ == "__main__":
    test_about_click()
