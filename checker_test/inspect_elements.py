import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import config

def inspect():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        captured_responses = []
        def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "application/json" in ct or "text/javascript" in ct:
                    url = response.url
                    body = response.text()
                    low = body.lower()
                    if any(k in low for k in ["joined", "account", "country", "location", "about"]):
                        captured_responses.append({"url": url, "body": body[:500]})
                        # Save sample
                        fn = config.DEBUG_NETWORK_DIR / f"capture_{int(time.time()*1000)}.json"
                        with open(fn, "w", encoding="utf-8") as f:
                            f.write(body)
            except Exception:
                pass
        
        page.on("response", on_response)
        
        # Test 1: Instagram ece25051
        print("\n================== INSPECTING INSTAGRAM ==================")
        page.goto("https://www.instagram.com/ece25051/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
        # Find all buttons / icons on header
        print("HTML title:", page.title())
        page.screenshot(path=str(config.DEBUG_DIR / "inspect_ig_loaded.png"))
        
        buttons = page.locator("header button, [role='main'] button, header [role='button']").all()
        print(f"Found {len(buttons)} buttons on Instagram profile:")
        for idx, btn in enumerate(buttons):
            try:
                print(f"  Button {idx}: text={repr(btn.inner_text())}, aria-label={repr(btn.get_attribute('aria-label'))}, html={repr(btn.evaluate('el => el.outerHTML'))[:150]}")
            except Exception as e:
                print(f"  Button {idx}: err={e}")
                
        # Try clicking 3 dots button
        # On Instagram desktop, the 3 dots is often an SVG with aria-label="Options" or inside a button
        dots = page.locator("header button:has(svg), header div[role='button']:has(svg), svg[aria-label*='Options'], svg[aria-label*='options'], svg[aria-label*='Seçenekler']").all()
        print(f"Found {len(dots)} candidate dots elements on IG")
        
        for idx, d in enumerate(dots):
            try:
                if d.is_visible():
                    print(f"Clicking IG candidate {idx}...")
                    d.click()
                    time.sleep(2)
                    page.screenshot(path=str(config.DEBUG_DIR / f"inspect_ig_click_{idx}.png"))
                    
                    # Check dialog
                    dialog = page.locator("div[role='dialog']").first
                    if dialog.count() and dialog.is_visible():
                        print("Dialog opened! Text:\n", dialog.inner_text())
                        # Check About this account
                        about_btn = page.locator("button:has-text('About this account'), button:has-text('Bu hesap hakkında')").first
                        if about_btn.count() and about_btn.is_visible():
                            print("Found 'About this account'! Clicking...")
                            about_btn.click()
                            time.sleep(2)
                            page.screenshot(path=str(config.DEBUG_DIR / "inspect_ig_about_dialog.png"))
                            dialog2 = page.locator("div[role='dialog']").first
                            if dialog2.count():
                                print("About Dialog Content:\n", dialog2.inner_text())
                        break
            except Exception as e:
                print(f"Error clicking candidate {idx}: {e}")

        # Test 2: Threads ece25051
        print("\n================== INSPECTING THREADS ==================")
        page.goto("https://www.threads.net/@ece25051", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
        page.screenshot(path=str(config.DEBUG_DIR / "inspect_threads_loaded.png"))
        
        thr_buttons = page.locator("header button, [role='main'] button, div[role='button']").all()
        print(f"Found {len(thr_buttons)} buttons on Threads:")
        for idx, btn in enumerate(thr_buttons):
            try:
                print(f"  Threads Button {idx}: text={repr(btn.inner_text())}, aria-label={repr(btn.get_attribute('aria-label'))}, html={repr(btn.evaluate('el => el.outerHTML'))[:150]}")
            except Exception as e:
                pass
                
        # Find 3 dots icon on Threads
        thr_dots = page.locator("svg[aria-label*='More'], svg[aria-label*='Daha fazla'], div[role='button']:has(svg), button:has(svg)").all()
        print(f"Found {len(thr_dots)} candidate dots elements on Threads")
        for idx, d in enumerate(thr_dots):
            try:
                if d.is_visible():
                    aria = d.get_attribute('aria-label') or ""
                    html = d.evaluate('el => el.outerHTML')[:100]
                    if "more" in aria.lower() or "daha" in aria.lower() or "<svg" in html:
                        print(f"Clicking Threads candidate {idx} (aria={aria})...")
                        d.click()
                        time.sleep(2)
                        page.screenshot(path=str(config.DEBUG_DIR / f"inspect_threads_click_{idx}.png"))
                        
                        # Check menu or dialog
                        menu = page.locator("div[role='menu'], div[role='dialog']").first
                        if menu.count() and menu.is_visible():
                            print("Threads Menu opened! Text:\n", repr(menu.inner_text()))
                            about_btn = page.locator(":has-text('About this profile'), :has-text('Bu profil hakkında')").first
                            if about_btn.count() and about_btn.is_visible():
                                print("Found 'About this profile'! Clicking...")
                                about_btn.click()
                                time.sleep(2)
                                page.screenshot(path=str(config.DEBUG_DIR / "inspect_threads_about_dialog.png"))
                                d_inner = page.locator("div[role='dialog']").first
                                if d_inner.count():
                                    print("Threads About Dialog Content:\n", d_inner.inner_text())
                            break
            except Exception as e:
                print(f"Error on Threads candidate {idx}: {e}")

        context.close()
        print("\nInspection complete!")

if __name__ == "__main__":
    inspect()
