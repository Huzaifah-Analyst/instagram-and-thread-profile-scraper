import time
from playwright.sync_api import sync_playwright
import config

def test_circle():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n--- Testing Threads @{u} with circle selector ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find SVG with circle
            circle_svgs = page.locator("svg:has(circle)").all()
            print(f"Found {len(circle_svgs)} svg:has(circle)")
            
            for idx, s in enumerate(circle_svgs):
                box = s.bounding_box()
                print(f"  SVG {idx} at {box}")
                if box and box["y"] < 350: # In profile header
                    btn = s.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
                    btn.click()
                    time.sleep(1.5)
                    
                    about = page.locator(":text('About this profile')").first
                    if about.count():
                        print("Found 'About this profile'! Clicking...")
                        about.click()
                        time.sleep(3)
                        
                        # Get text
                        modal = page.locator("div:has-text('Based in')").last
                        print("MODAL TEXT:\n", modal.inner_text())
                        page.screenshot(path=str(config.DEBUG_DIR / f"circle_success_{u}.png"))
                        page.keyboard.press("Escape")
                        break
            page.keyboard.press("Escape")
            time.sleep(1)
            
        context.close()

if __name__ == "__main__":
    test_circle()
