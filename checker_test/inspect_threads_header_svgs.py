import time
from playwright.sync_api import sync_playwright
import config

def inspect_threads():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Look for the profile card container (the one containing "ece25051" and "Follow")
        card = page.locator("div:has-text('ece25051'):has-text('Follow')").last
        print("Profile Card Found:", card.count())
        
        # Dump all SVGs in card
        svgs = card.locator("svg").all()
        print(f"SVGs in Profile Card: {len(svgs)}")
        for idx, s in enumerate(svgs):
            parent = s.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
            print(f"Card SVG {idx}: aria={s.get_attribute('aria-label')}, parent_html={parent.evaluate('el => el.outerHTML')[:120] if parent.count() else 'None'}")
            
            # Click it and see what opens
            if parent.count() and parent.is_visible():
                print(f"  Clicking SVG #{idx} parent...")
                parent.click()
                time.sleep(2)
                page.screenshot(path=str(config.DEBUG_DIR / f"threads_card_svg_click_{idx}.png"))
                
                # Check for menu or dialog
                menus = page.locator("div[role='menu'], div[role='dialog'], div[data-pressable-container='true']").all()
                for m in menus:
                    if m.is_visible():
                        print(f"    Container visible text:\n{m.inner_text()}")
                page.keyboard.press("Escape")
                time.sleep(1)
                
        context.close()

if __name__ == "__main__":
    inspect_threads()
