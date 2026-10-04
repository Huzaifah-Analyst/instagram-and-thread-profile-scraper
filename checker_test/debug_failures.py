import time
from playwright.sync_api import sync_playwright
import config

def debug_accounts():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        test_users = ["zeynep607196", "ece25051", "ayse517258", "fatma868612"]
        
        for u in test_users:
            print(f"\n================ INSPECTING IG @{u} ================")
            page.goto(f"https://www.instagram.com/{u}/", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Wait for header
            header = page.locator("header").first
            print("IG Header text:\n", repr(header.inner_text()))
            
            # Look for 3-dots
            dots = page.locator("header div[aria-haspopup='dialog'], header svg[aria-label='Options'], header svg[aria-label='Seçenekler']").first
            if dots.count() and dots.is_visible():
                dots.click()
                time.sleep(2)
                page.screenshot(path=str(config.DEBUG_DIR / f"dbg_ig_{u}_menu.png"))
                
                # Check all menu items
                menu = page.locator("div[role='dialog'], div[data-pressable-container='true']").first
                if menu.count():
                    print("IG Menu items:\n", menu.inner_text())
                    about = menu.locator(":text('About this account'), :text('About this profile'), :text('Bu hesap hakkında')").first
                    if about.count():
                        about.click()
                        time.sleep(3)
                        diag = page.locator("div[role='dialog']").first
                        print("IG About Dialog Content:\n", diag.inner_text())
                        page.screenshot(path=str(config.DEBUG_DIR / f"dbg_ig_{u}_about.png"))
                        page.keyboard.press("Escape")
            else:
                print("IG 3-dots not found")
                
            print(f"\n================ INSPECTING THREADS @{u} ================")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            body = page.inner_text("body")
            if "This page isn't available" in body or "Sayfa kullanılamıyor" in body:
                print("Threads status: Page Not Available (No Threads profile)")
                continue
                
            page.screenshot(path=str(config.DEBUG_DIR / f"dbg_thr_{u}_page.png"))
            print("Threads body snippet:\n", repr(body[:300]))
            
            # Find 3 dots
            all_dots = page.locator("div[aria-haspopup='dialog']").all()
            print(f"Threads popups found: {len(all_dots)}")
            for idx, d in enumerate(all_dots):
                try:
                    if d.is_visible():
                        print(f"Clicking Threads popup {idx}...")
                        d.click()
                        time.sleep(2)
                        menu = page.locator("div[role='dialog'], div[data-pressable-container='true'], div[role='menu']").all()
                        for m in menu:
                            if m.is_visible():
                                print(f"  Container {idx} text:\n{m.inner_text()}")
                                about = m.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                                if about.count() and about.is_visible():
                                    about.click()
                                    time.sleep(3)
                                    d_inner = page.locator("div[role='dialog']").first
                                    print(f"  >>> THREADS @{u} ABOUT CONTENT <<<\n", d_inner.inner_text())
                        page.keyboard.press("Escape")
                        time.sleep(1)
                except Exception as e:
                    print(f"  Error on popup {idx}: {e}")
                    
        context.close()

if __name__ == "__main__":
    debug_accounts()
