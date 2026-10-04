import json
import time
from playwright.sync_api import sync_playwright
import config

def extract_both():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Instagram
        print("\n" + "="*50)
        print("INSTAGRAM EXTRACTION TEST: ece25051")
        print("="*50)
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        page.wait_for_selector("header", timeout=20000)
        time.sleep(3)
        
        # Click Options button (div with aria-haspopup="dialog" in header)
        dots = page.locator("header div[aria-haspopup='dialog']").first
        if dots.count() and dots.is_visible():
            print("Clicking IG 3 dots...")
            dots.click()
            time.sleep(2)
            page.screenshot(path=str(config.DEBUG_DIR / "ig_ece_menu_opened.png"))
            
            # Print all buttons in the opened modal
            modal_btns = page.locator("div[role='dialog'] button").all()
            print(f"IG Modal buttons count: {len(modal_btns)}")
            for b in modal_btns:
                print("  IG Modal button:", repr(b.inner_text()))
                
            # Click "About this account"
            about_btn = page.locator("div[role='dialog'] button:has-text('About this account'), div[role='dialog'] button:has-text('Bu hesap hakkında')").first
            if about_btn.count():
                print("Clicking 'About this account'...")
                about_btn.click()
                time.sleep(2.5)
                page.screenshot(path=str(config.DEBUG_DIR / "ig_ece_about_final.png"))
                dialog = page.locator("div[role='dialog']").first
                if dialog.count():
                    print("\n>>> INSTAGRAM EXTRACTED DATA <<<\n")
                    print(dialog.inner_text())
                    print(">>> END INSTAGRAM DATA <<<\n")
            else:
                print("'About this account' NOT in list of buttons.")

        # 2. Threads
        print("\n" + "="*50)
        print("THREADS EXTRACTION TEST: ece25051")
        print("="*50)
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        page.wait_for_selector("div[role='main']", timeout=20000)
        time.sleep(3)
        
        # Find 3 dots popup next to Follow / Notification bell on profile
        # In Threads, the 3 dots popup container in profile header is div[aria-haspopup='menu'] or svg with 3 dots
        thr_dots = page.locator("div[role='main'] div[aria-haspopup='menu']:not(:has-text('More'))").first
        if not thr_dots.count():
            thr_dots = page.locator("div[role='main'] svg circle").first.locator("xpath=ancestor::div[@role='button' or @aria-haspopup][1]")
            
        if thr_dots.count() and thr_dots.is_visible():
            print("Clicking Threads 3 dots...")
            thr_dots.click()
            time.sleep(2.5)
            page.screenshot(path=str(config.DEBUG_DIR / "threads_ece_menu_opened.png"))
            
            # Print all items in opened menu
            menu_items = page.locator("div[role='menu'] *, div[data-pressable-container='true'] *").all()
            menu_container = page.locator("div[role='menu'], div[data-pressable-container='true']").first
            if menu_container.count():
                print("Threads Menu Full Text:\n", repr(menu_container.inner_text()))
                
            about_thr = page.locator(":has-text('About this profile'), :has-text('Bu profil hakkında')").first
            if about_thr.count() and about_thr.is_visible():
                print("Clicking 'About this profile' on Threads...")
                about_thr.click()
                time.sleep(2.5)
                page.screenshot(path=str(config.DEBUG_DIR / "threads_ece_about_final.png"))
                d_thr = page.locator("div[role='dialog']").first
                if d_thr.count():
                    print("\n>>> THREADS EXTRACTED DATA <<<\n")
                    print(d_thr.inner_text())
                    print(">>> END THREADS DATA <<<\n")
            else:
                print("'About this profile' button not found in Threads menu.")
                
        context.close()

if __name__ == "__main__":
    extract_both()
