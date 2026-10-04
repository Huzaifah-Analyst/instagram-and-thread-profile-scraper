import time
from playwright.sync_api import sync_playwright
import config

def test_svg_index():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        for u in ["ece25051", "zeynep607196", "elif70566"]:
            print(f"\n--- Checking Threads @{u} ---")
            page.goto(f"https://www.threads.net/@{u}", wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find all SVGs in column body
            svgs = page.locator("div[aria-label='Column body'] svg").all()
            print(f"Total SVGs found in column body: {len(svgs)}")
            if len(svgs) >= 3:
                # 3rd SVG is the 3-dots icon
                dots_btn = svgs[2].locator("xpath=ancestor::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
                print("Clicking 3rd SVG parent...")
                dots_btn.click()
                time.sleep(1.5)
                
                about_opt = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
                if about_opt.count() and about_opt.is_visible():
                    print("Found 'About this profile'! Clicking...")
                    about_opt.click()
                    time.sleep(3.5)
                    
                    for el in page.locator("div:has-text('Based in')").all():
                        t = el.inner_text()
                        if "Name" in t and "Joined" in t and len(t) < 400:
                            print(f"SUCCESS EXTRACTED FOR @{u}:\n{t}\n")
                            break
                    page.keyboard.press("Escape")
                else:
                    print("'About this profile' not visible in menu")
            else:
                print("Not enough SVGs found in column body")
                
        context.close()

if __name__ == "__main__":
    test_svg_index()
