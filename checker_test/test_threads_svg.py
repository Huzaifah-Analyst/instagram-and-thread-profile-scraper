import time
from playwright.sync_api import sync_playwright
import config

def test_svg():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n--- Checking Threads @{u} ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find the 3 dots button on the profile card (circle SVGs)
            circles = page.locator("svg circle + circle + circle").all()
            print(f"Found {len(circles)} 3-dots SVG on Threads")
            
            for c in circles:
                try:
                    box = c.bounding_box()
                    # Only the one on the profile card (y > 100)
                    if box and box["y"] > 100:
                        btn = c.locator("xpath=ancestor::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
                        if btn.count() and btn.is_visible():
                            print(f"Clicking profile 3-dots at {box}...")
                            btn.click()
                            time.sleep(1.5)
                            
                            # Click About this profile
                            about_btn = page.locator("span:has-text('About this profile'), div:has-text('About this profile')").last
                            if about_btn.count():
                                print("Clicking 'About this profile'...")
                                about_btn.click()
                                time.sleep(3)
                                
                                # Check all text on page containing Joined or Based in
                                for el in page.locator("div:has-text('Based in'):has-text('Joined')").all():
                                    t = el.inner_text()
                                    if len(t) < 300:
                                        print(f"EXTRACTED THREADS MODAL:\n{t}\n---")
                                        break
                            page.keyboard.press("Escape")
                            break
                except Exception as e:
                    print(f"Error: {e}")
                    
        context.close()

if __name__ == "__main__":
    test_svg()
