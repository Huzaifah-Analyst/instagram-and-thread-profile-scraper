import time
from playwright.sync_api import sync_playwright
import config

def get_loaded_about_data():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Test accounts: zeynep607196, elif70566, ece25051
        accounts = ["zeynep607196", "elif70566", "ece25051"]
        
        for acc in accounts:
            print(f"\n==================== CHECKING IG: @{acc} ====================")
            page.goto(f"https://www.instagram.com/{acc}/", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Click 3 dots
            dots = page.locator("header div[aria-haspopup='dialog'], header button:has(svg), header svg[aria-label='Options']").first
            if dots.count() and dots.is_visible():
                dots.click()
                time.sleep(1.5)
                
                about_opt = page.locator(":text('About this account'), :text('Bu hesap hakkında')").first
                if about_opt.count() and about_opt.is_visible():
                    about_opt.click()
                    # Wait up to 10s for the about dialog content to load
                    time.sleep(5)
                    
                    dialog = page.locator("div[role='dialog']").first
                    ss_path = config.DEBUG_DIR / f"ig_{acc}_about_loaded.png"
                    page.screenshot(path=str(ss_path))
                    print(f"Saved: {ss_path}")
                    
                    if dialog.count():
                        print(f"--- IG @{acc} Dialog Text ---")
                        print(dialog.inner_text())
                        print("-----------------------------")
                        
                    # Close dialog
                    page.keyboard.press("Escape")
                    time.sleep(1)
                    page.keyboard.press("Escape")
                else:
                    print("About this account option not found in menu")
                    page.keyboard.press("Escape")
            else:
                print("3 dots button not found on profile")
                
            print(f"\n==================== CHECKING THREADS: @{acc} ====================")
            page.goto(f"https://www.threads.net/@{acc}", wait_until="domcontentloaded")
            time.sleep(4)
            
            # Find 3 dots on Threads
            thr_dots = page.locator("div[role='main'] div[aria-haspopup='menu']:not(:has-text('More')), div[role='main'] svg circle").first
            if thr_dots.count():
                # Click parent
                parent = thr_dots.locator("xpath=ancestor-or-self::div[@role='button' or @aria-haspopup][1]")
                if parent.count():
                    parent.click()
                else:
                    thr_dots.click()
                time.sleep(2)
                
                # Check for "About this profile"
                about_thr = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                if about_thr.count() and about_thr.is_visible():
                    about_thr.click()
                    time.sleep(5)
                    
                    d_thr = page.locator("div[role='dialog']").first
                    ss_thr = config.DEBUG_DIR / f"threads_{acc}_about_loaded.png"
                    page.screenshot(path=str(ss_thr))
                    print(f"Saved Threads screenshot: {ss_thr}")
                    if d_thr.count():
                        print(f"--- Threads @{acc} Dialog Text ---")
                        print(d_thr.inner_text())
                        print("----------------------------------")
                    page.keyboard.press("Escape")
                else:
                    print("Menu items visible on Threads:")
                    for m in page.locator("div[role='menu']").all():
                        print(repr(m.inner_text()))
                    page.keyboard.press("Escape")
            else:
                print("Threads 3-dots not found")
                
        context.close()

if __name__ == "__main__":
    get_loaded_about_data()
