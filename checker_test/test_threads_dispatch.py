import time
from playwright.sync_api import sync_playwright
import config

def test_dispatch():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\nTesting Threads @{u}...")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find 3 dots icon in header card
            card = page.locator(f"div:has-text('{u}'):has-text('Follow')").last
            if not card.count():
                card = page.locator("div[role='main']").first
            
            dots = card.locator("div[aria-haspopup='dialog']").first
            if dots.count():
                dots.click()
                time.sleep(1)
                
                # Use force click or dispatch click
                about = page.locator("span:has-text('About this profile'), div:has-text('About this profile')").last
                if about.count():
                    about.dispatch_event("click")
                    time.sleep(3)
                    
                    # Search entire page for "Joined" and "Based in"
                    body = page.inner_text("body")
                    if "Based in" in body and "Joined" in body:
                        print(f"SUCCESS! Found About data for @{u} on Threads!")
                        # Extract the exact block
                        for el in page.locator("div:has-text('Based in')").all():
                            txt = el.inner_text()
                            if "Name" in txt and "Joined" in txt and len(txt) < 300:
                                print(f"--- THREADS @{u} MODAL TEXT ---\n{txt}\n-----------------------------")
                                break
                    else:
                        print("Modal text not found in body.")
                page.keyboard.press("Escape")
            else:
                print("Dots not found")
                
        context.close()

if __name__ == "__main__":
    test_dispatch()
