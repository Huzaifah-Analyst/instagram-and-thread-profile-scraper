import time
from playwright.sync_api import sync_playwright
import config

def test_threads_profile_menu():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for acc in ["ece25051", "zeynep607196"]:
            print(f"\n================= THREADS PROFILE MENU: @{acc} =================")
            page.goto(f"https://www.threads.net/@{acc}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # The profile card has Instagram icon (SVG with instagram/threads link or aria), Bell icon, and 3-dots icon
            # Let's find the SVG with 3 circles or the div next to bell
            # In Threads DOM, the profile actions row is inside the profile header
            dots = page.locator("div[aria-haspopup='dialog'], div[aria-haspopup='menu']").filter(has_not_text="More").filter(has_not_text="New thread").all()
            print(f"Found {len(dots)} candidate popup divs on Threads profile")
            
            for idx, d in enumerate(dots):
                try:
                    box = d.bounding_box()
                    print(f"Popup #{idx} at {box}: outerHTML={d.evaluate('el => el.outerHTML')[:120]}")
                    d.click()
                    time.sleep(2)
                    
                    page.screenshot(path=str(config.DEBUG_DIR / f"threads_{acc}_menu_open_{idx}.png"))
                    
                    # Print all text in any dialog/menu
                    for el in page.locator("div[role='dialog'], div[role='menu'], div[data-pressable-container='true']").all():
                        if el.is_visible():
                            print(f"  Visible Text in container:\n{el.inner_text()}")
                            
                    page.keyboard.press("Escape")
                    time.sleep(1)
                except Exception as e:
                    print(f"  Error on #{idx}: {e}")
                    
        context.close()

if __name__ == "__main__":
    test_threads_profile_menu()
