import time
from playwright.sync_api import sync_playwright
import config

def get_threads_about():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Test accounts
        for acc in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n================= EXTRACTING THREADS ABOUT: @{acc} =================")
            page.goto(f"https://www.threads.net/@{acc}", wait_until="domcontentloaded")
            time.sleep(3)
            
            card = page.locator(f"div:has-text('{acc}'):has-text('Follow')").last
            if not card.count():
                card = page.locator("div[role='main']").first
                
            # Click the 3-dots popup on the card (Card SVG 2)
            dots = card.locator("div[aria-haspopup='dialog']").first
            if dots.count() and dots.is_visible():
                print("Clicking Threads profile 3-dots...")
                dots.click()
                time.sleep(1.5)
                
                # Click "About this profile"
                about_opt = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                if about_opt.count() and about_opt.is_visible():
                    print("Clicking 'About this profile'...")
                    about_opt.click()
                    time.sleep(3)
                    
                    ss_path = config.DEBUG_DIR / f"threads_{acc}_about_loaded.png"
                    page.screenshot(path=str(ss_path))
                    print(f"Screenshot saved: {ss_path}")
                    
                    dialog = page.locator("div[role='dialog']").first
                    if dialog.count():
                        print(f"\n--- THREADS @{acc} ABOUT DIALOG CONTENT ---")
                        print(dialog.inner_text())
                        print("-------------------------------------------\n")
                else:
                    print("About this profile not found in menu")
            else:
                print("Threads 3-dots button not found on card")
                
        context.close()

if __name__ == "__main__":
    get_threads_about()
