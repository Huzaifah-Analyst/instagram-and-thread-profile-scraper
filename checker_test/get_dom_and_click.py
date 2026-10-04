import json
import os
import sys
import time
from playwright.sync_api import sync_playwright
import config

sys.stdout.reconfigure(encoding='utf-8')

def test_clicks():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Test 1: Instagram
        print("=== Instagram Test ===")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Find elements containing ece25051
        user_el = page.locator("header :has-text('ece25051'), section :has-text('ece25051')").first
        print("User header element found:", user_el.count())
        
        # The 3-dots button next to username is a button/div inside header
        # Let's find all buttons or clickable SVGs in the header
        header = page.locator("header").first
        if header.count():
            print("Header HTML:\n", header.evaluate("el => el.outerHTML"))
            
            # Click the 3 dots button in header
            dots_btn = header.locator("svg, button, div[role='button']").filter(has_not_text="Follow").filter(has_not_text="Message").all()
            for idx, d in enumerate(dots_btn):
                print(f"Header element {idx}: tag={d.evaluate('el => el.tagName')}, class={d.evaluate('el => el.className')}, outerHTML={d.evaluate('el => el.outerHTML')[:120]}")
                try:
                    d.click()
                    time.sleep(1.5)
                    dialog = page.locator("div[role='dialog']").first
                    if dialog.count() and dialog.is_visible():
                        print(f"--> DIALOG OPENED on clicking element {idx}!")
                        print("Dialog text:\n", dialog.inner_text())
                        ss_path = config.DEBUG_DIR / "ig_ece25051_dialog_open.png"
                        page.screenshot(path=str(ss_path))
                        
                        # Click About this account
                        about = dialog.locator("button:has-text('About this account'), button:has-text('Bu hesap hakkında')").first
                        if about.count() and about.is_visible():
                            print("Clicking 'About this account'...")
                            about.click()
                            time.sleep(2)
                            ss_about = config.DEBUG_DIR / "ig_ece25051_about_open.png"
                            page.screenshot(path=str(ss_about))
                            d2 = page.locator("div[role='dialog']").first
                            if d2.count():
                                print("--> ABOUT THIS ACCOUNT CONTENT:\n", d2.inner_text())
                        break
                except Exception as e:
                    print(f"Click error: {e}")

        # Test 2: Threads
        print("\n=== Threads Test ===")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        # On Threads, let's find the header card
        # Look for svg circle icons or More buttons
        thr_header = page.locator("div[role='main'] header, div[role='main'] > div:first-child").first
        if thr_header.count():
            print("Threads Header HTML snippet:\n", thr_header.evaluate("el => el.outerHTML")[:600])
            
        # Find all SVG or buttons on Threads
        thr_clickable = page.locator("div[role='main'] svg").all()
        for idx, svg in enumerate(thr_clickable):
            try:
                print(f"Threads SVG {idx}: HTML={svg.evaluate('el => el.outerHTML')[:120]}")
                # Click the parent button/div
                svg.locator("xpath=ancestor::div[@role='button' or @tabindex='0'][1]").click()
                time.sleep(1.5)
                menu = page.locator("div[role='menu'], div[role='dialog']").first
                if menu.count() and menu.is_visible():
                    print(f"--> THREADS MENU OPENED on clicking SVG {idx}!")
                    print("Menu text:\n", menu.inner_text())
                    ss_menu = config.DEBUG_DIR / "threads_ece25051_menu_open.png"
                    page.screenshot(path=str(ss_menu))
                    
                    # Check About this profile
                    about_thr = menu.locator(":has-text('About this profile'), :has-text('Bu profil hakkında')").first
                    if about_thr.count() and about_thr.is_visible():
                        print("Clicking 'About this profile' on Threads...")
                        about_thr.click()
                        time.sleep(2)
                        ss_thr_about = config.DEBUG_DIR / "threads_ece25051_about_open.png"
                        page.screenshot(path=str(ss_thr_about))
                        d_thr = page.locator("div[role='dialog']").first
                        if d_thr.count():
                            print("--> THREADS ABOUT THIS PROFILE CONTENT:\n", d_thr.inner_text())
                    break
            except Exception as e:
                print(f"Threads click error {idx}: {e}")

        context.close()

if __name__ == "__main__":
    test_clicks()
