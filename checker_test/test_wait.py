import time
from playwright.sync_api import sync_playwright
import config

def test_wait():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Test IG
        print("Opening IG ece25051...")
        page.goto("https://www.instagram.com/ece25051/")
        page.wait_for_selector("header", timeout=15000)
        time.sleep(2)
        
        print("IG Title:", page.title())
        
        # Find 3 dots in header
        # In IG, the 3 dots is inside header: div[role='button'], button, or div with aria-haspopup="dialog"
        header_btns = page.locator("header [role='button'], header button, header div[aria-haspopup='dialog']").all()
        print(f"Header buttons found: {len(header_btns)}")
        for idx, b in enumerate(header_btns):
            print(f"  Btn {idx}: aria={b.get_attribute('aria-label')}, aria-popup={b.get_attribute('aria-haspopup')}, text={b.inner_text()}")
            if b.get_attribute("aria-haspopup") == "dialog" or (not b.inner_text() and b.is_visible()):
                print(f"  Clicking Btn {idx}...")
                b.click()
                time.sleep(1.5)
                dialog = page.locator("div[role='dialog']").first
                if dialog.count() and dialog.is_visible():
                    print("  Dialog text:\n", dialog.inner_text())
                    page.screenshot(path=str(config.DEBUG_DIR / "ig_ece_dialog.png"))
                    
                    # Click About this account
                    about_btn = page.locator("button:has-text('About this account'), button:has-text('Bu hesap hakkında')").first
                    if about_btn.count() and about_btn.is_visible():
                        print("  Clicking 'About this account'...")
                        about_btn.click()
                        time.sleep(2)
                        page.screenshot(path=str(config.DEBUG_DIR / "ig_ece_about_result.png"))
                        d2 = page.locator("div[role='dialog']").first
                        if d2.count():
                            print("  >>> IG ABOUT TEXT <<<\n", d2.inner_text())
                    break
        
        # Test Threads
        print("\nOpening Threads ece25051...")
        page.goto("https://www.threads.net/@ece25051")
        page.wait_for_selector("text=ece25051", timeout=15000)
        time.sleep(2)
        
        print("Threads Title:", page.title())
        # In Threads, locate all buttons/divs with aria-haspopup="menu"
        thr_popups = page.locator("div[aria-haspopup='menu'], div[aria-haspopup='dialog'], button[aria-haspopup='menu']").all()
        print(f"Threads popups found: {len(thr_popups)}")
        for idx, b in enumerate(thr_popups):
            print(f"  Thr popup {idx}: aria={b.get_attribute('aria-label')}, text={b.inner_text()}")
            # We want the one near header / profile, not the sidebar More button
            if b.is_visible() and "more" not in (b.inner_text().lower()):
                print(f"  Clicking Thr popup {idx}...")
                b.click()
                time.sleep(1.5)
                menu = page.locator("div[role='menu'], div[role='dialog']").first
                if menu.count() and menu.is_visible():
                    print("  Threads Menu text:\n", repr(menu.inner_text()))
                    page.screenshot(path=str(config.DEBUG_DIR / "thr_ece_menu.png"))
                    
                    about_thr = page.locator(":has-text('About this profile'), :has-text('Bu profil hakkında')").first
                    if about_thr.count() and about_thr.is_visible():
                        print("  Clicking 'About this profile'...")
                        about_thr.click()
                        time.sleep(2)
                        page.screenshot(path=str(config.DEBUG_DIR / "thr_ece_about_result.png"))
                        d2 = page.locator("div[role='dialog']").first
                        if d2.count():
                            print("  >>> THREADS ABOUT TEXT <<<\n", d2.inner_text())
                    break
                    
        context.close()

if __name__ == "__main__":
    test_wait()
