import time
from playwright.sync_api import sync_playwright
import config

def verify_threads_fix():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n--- Testing Threads @{u} ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find all SVGs on page
            card = page.locator("div[aria-label='Column body'], div[role='main']").first
            svgs = card.locator("svg").all()
            print(f"Total SVGs found in card: {len(svgs)}")
            
            # In Threads profile card, the action buttons are at y between 100 and 350, x > 600
            for idx, s in enumerate(svgs):
                box = s.bounding_box()
                if box and 100 < box["y"] < 350 and box["x"] > 600:
                    aria = s.get_attribute("aria-label") or ""
                    if "Instagram" not in aria and "search" not in aria.lower():
                        # This is the 3 dots button!
                        print(f"Found 3-dots SVG #{idx} at {box} (aria={aria})")
                        parent = s.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
                        if parent.count():
                            parent.click()
                        else:
                            s.click()
                        time.sleep(1.5)
                        
                        # Click About this profile
                        about_btn = page.locator("div:has-text('About this profile'), span:has-text('About this profile')").last
                        if about_btn.count() and about_btn.is_visible():
                            print("Clicking 'About this profile'...")
                            about_btn.click()
                            time.sleep(3)
                            
                            # Extract modal data
                            for el in page.locator("div:has-text('Based in')").all():
                                t = el.inner_text()
                                if "Name" in t and "Joined" in t and len(t) < 400:
                                    print(f"SUCCESS EXTRACTED:\n{t}\n")
                                    break
                            page.keyboard.press("Escape")
                            break
            page.keyboard.press("Escape")
            time.sleep(1)
            
        context.close()

if __name__ == "__main__":
    verify_threads_fix()
