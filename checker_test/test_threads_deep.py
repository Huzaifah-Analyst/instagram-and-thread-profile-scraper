import time
from playwright.sync_api import sync_playwright
import config

def test_threads_deep():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for acc in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n================= THREADS: @{acc} =================")
            page.goto(f"https://www.threads.net/@{acc}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Screenshot page
            page.screenshot(path=str(config.DEBUG_DIR / f"threads_{acc}_page.png"))
            
            # Check if page is unavailable
            body = page.inner_text("body")
            if "This page isn't available" in body or "Sorry, this page" in body:
                print(f"Threads @{acc}: Not Found / Doesn't exist")
                continue
                
            # Find all clickable SVG buttons on the page
            # Look for 3-dots circle SVG or menu triggers
            print("Searching for 3-dots on Threads...")
            all_svgs = page.locator("svg").all()
            print(f"Total SVGs: {len(all_svgs)}")
            
            clicked = False
            for idx, s in enumerate(all_svgs):
                try:
                    # Check if SVG is inside main / header
                    box = s.bounding_box()
                    if box and box["y"] < 350 and box["x"] > 500: # profile header region
                        print(f"Candidate SVG {idx} at ({box['x']}, {box['y']}): outerHTML={s.evaluate('el => el.outerHTML')[:80]}")
                        s.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]").click()
                        time.sleep(2)
                        
                        # Look for menu
                        menu = page.locator("div[role='menu'], div[data-pressable-container='true']").all()
                        for m in menu:
                            if m.is_visible():
                                print("--> FOUND MENU! Content:\n", m.inner_text())
                                page.screenshot(path=str(config.DEBUG_DIR / f"threads_{acc}_menu_success.png"))
                                clicked = True
                                
                                # Click About this profile
                                about_btn = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                                if about_btn.count() and about_btn.is_visible():
                                    print("Found 'About this profile'! Clicking...")
                                    about_btn.click()
                                    time.sleep(3)
                                    page.screenshot(path=str(config.DEBUG_DIR / f"threads_{acc}_about_dialog.png"))
                                    diag = page.locator("div[role='dialog']").first
                                    if diag.count():
                                        print(f"--> THREADS @{acc} ABOUT DIALOG:\n", diag.inner_text())
                                break
                        if clicked:
                            break
                except Exception as e:
                    pass
            page.keyboard.press("Escape")
            time.sleep(1)
            
        context.close()

if __name__ == "__main__":
    test_threads_deep()
