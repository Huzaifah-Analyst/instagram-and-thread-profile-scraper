import time
from playwright.sync_api import sync_playwright
import config

def find_threads_dialog_tag():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded")
        time.sleep(3)
        
        card = page.locator("div:has-text('ece25051'):has-text('Follow')").last
        card.locator("div[aria-haspopup='dialog']").first.click()
        time.sleep(1.5)
        
        page.locator(":text('About this profile')").first.click()
        time.sleep(3)
        
        # Dump all elements on page containing "Joined" or "Based in"
        elements = page.locator("*:has-text('Based in')").all()
        print(f"Elements matching 'Based in': {len(elements)}")
        for idx, el in enumerate(elements):
            try:
                tag = el.evaluate("e => e.tagName")
                role = el.get_attribute("role")
                aria = el.get_attribute("aria-label")
                txt = el.inner_text()
                print(f"Element {idx}: tag={tag}, role={role}, text=\n{txt}\n---")
            except Exception:
                pass
                
        context.close()

if __name__ == "__main__":
    find_threads_dialog_tag()
