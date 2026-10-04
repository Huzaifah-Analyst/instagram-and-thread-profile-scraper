import time
from playwright.sync_api import sync_playwright
import config

def click_and_inspect():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Inspect Threads @ece25051
        print("Navigating to Threads...")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Find all divs with aria-haspopup="menu" or SVG circles
        menu_triggers = page.locator("div[aria-haspopup='menu'], div[aria-haspopup='dialog'], svg circle").all()
        print(f"Found {len(menu_triggers)} menu triggers on Threads")
        
        # Find the 3 dots button right inside profile header
        # In Threads, the profile header has the 3 dots button right next to the bell icon
        # Let's locate by coordinates or parent structure
        # Or locate all SVGs with 3 dots (circle elements)
        three_dots_svg = page.locator("svg:has(circle + circle + circle)").all()
        print(f"Found {len(three_dots_svg)} 3-dots SVG on Threads")
        
        for i, s in enumerate(three_dots_svg):
            try:
                if s.is_visible():
                    print(f"Clicking 3-dots SVG #{i}...")
                    # Click parent clickable container
                    parent = s.locator("xpath=ancestor::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
                    if parent.count():
                        parent.click()
                    else:
                        s.click()
                    time.sleep(1.5)
                    page.screenshot(path=str(config.DEBUG_DIR / f"threads_menu_clicked_{i}.png"))
                    
                    # Dump all visible menu/dialog text
                    dialogs = page.locator("div[role='menu'], div[role='dialog'], div[data-pressable-container='true']").all()
                    for d in dialogs:
                        if d.is_visible():
                            print(f"  Visible container text:\n{d.inner_text()}")
            except Exception as e:
                print(f"Error on 3-dots #{i}: {e}")

        # 2. Inspect Instagram @ece25051
        print("\nNavigating to Instagram...")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded")
        time.sleep(4)
        
        # Take full page screenshot
        page.screenshot(path=str(config.DEBUG_DIR / "ig_full_page.png"))
        print("IG Body text preview:", repr(page.inner_text("body")[:300]))
        
        # Look for 3-dots on IG
        ig_dots = page.locator("svg[aria-label*='Options'], svg[aria-label*='options'], svg:has(circle + circle + circle)").all()
        print(f"Found {len(ig_dots)} 3-dots on IG")
        for i, s in enumerate(ig_dots):
            try:
                if s.is_visible():
                    print(f"Clicking IG 3-dots #{i} (aria={s.get_attribute('aria-label')})...")
                    s.click()
                    time.sleep(1.5)
                    page.screenshot(path=str(config.DEBUG_DIR / f"ig_menu_clicked_{i}.png"))
                    dialogs = page.locator("div[role='dialog']").all()
                    for d in dialogs:
                        if d.is_visible():
                            print(f"  IG Dialog text:\n{d.inner_text()}")
            except Exception as e:
                print(f"Error on IG 3-dots #{i}: {e}")
                
        context.close()

if __name__ == "__main__":
    click_and_inspect()
