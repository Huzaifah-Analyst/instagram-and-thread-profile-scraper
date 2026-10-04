import time
from playwright.sync_api import sync_playwright
import config

def test_zeynep():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://www.threads.net/@zeynep607196", wait_until="domcontentloaded")
        time.sleep(3)
        
        svgs = page.locator("div[aria-label='Column body'] svg").all()
        if len(svgs) >= 3:
            svgs[2].locator("xpath=ancestor::div[@role='button' or @tabindex='0' or @aria-haspopup][1]").click()
            time.sleep(1.5)
            about = page.locator(":text('About this profile')").first
            if about.count():
                about.click()
                time.sleep(3)
                page.screenshot(path=str(config.DEBUG_DIR / "zeynep_threads_dialog.png"))
                diag = page.locator("div[role='dialog']").first
                if diag.count():
                    print("ZEYNEP DIALOG TEXT:\n", diag.inner_text())
                else:
                    print("Body text snippet:\n", page.inner_text("body")[:500])
                    
        context.close()

if __name__ == "__main__":
    test_zeynep()
