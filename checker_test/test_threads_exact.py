import time
from playwright.sync_api import sync_playwright
import config

def test_threads_exact():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["zeynep607196", "ece25051", "elif70566"]:
            print(f"\n--- Checking Threads @{u} ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            card = page.locator(f"div:has-text('{u}'):has-text('Follow')").last
            if not card.count():
                card = page.locator("div[role='main']").first
                
            # Click 3-dots
            dots = card.locator("div[aria-haspopup='dialog']").first
            if dots.count():
                dots.click()
                time.sleep(1.5)
                
                # Check menu
                about = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                if about.count():
                    print("Found 'About this profile'! Clicking...")
                    about.click()
                    time.sleep(3)
                    
                    dialogs = page.locator("div[role='dialog']").all()
                    print(f"Dialog count: {len(dialogs)}")
                    for d in dialogs:
                        if d.is_visible():
                            txt = d.inner_text()
                            print("RAW DIALOG TEXT:\n", repr(txt))
                            lines = [l.strip() for l in txt.splitlines() if l.strip()]
                            print("LINES:", lines)
                            for idx, line in enumerate(lines):
                                if "Joined" in line:
                                    print("  --> Joined line match:", line, "next:", lines[idx+1] if idx+1 < len(lines) else None)
                                if "Based in" in line or "Location" in line:
                                    print("  --> Based in line match:", line, "next:", lines[idx+1] if idx+1 < len(lines) else None)
                    page.keyboard.press("Escape")
            else:
                print("Dots not found")
                
        context.close()

if __name__ == "__main__":
    test_threads_exact()
