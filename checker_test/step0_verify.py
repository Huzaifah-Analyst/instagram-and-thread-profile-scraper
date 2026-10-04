import json
import os
import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Page, Response
import config

captured_network_data = []

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def attach_network_listener(page: Page, label_prefix: str):
    def handle_response(response: Response):
        try:
            url = response.url
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type or "text/javascript" in content_type:
                try:
                    text_data = response.text()
                    if not text_data:
                        return
                    # Check for indicators of joined date or country / location
                    lower = text_data.lower()
                    has_joined = any(k in lower for k in ["date_joined", "date joined", "joined_date", "datejoined", "joined_timestamp", "date_formatted"])
                    has_country = any(k in lower for k in ["account_based_in", "account based in", "country_name", "location_name", "primary_country"])
                    has_about = any(k in lower for k in ["about_this_account", "about_this_profile", "user_about_this_account_v2", "aboutthisaccount"])

                    if has_joined or has_country or has_about or "account" in lower and "joined" in lower:
                        filename = f"{sanitize_filename(label_prefix)}_{sanitize_filename(urlparse(url).path[-30:])}_{int(time.time()*1000)}.json"
                        out_path = config.DEBUG_NETWORK_DIR / filename
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(text_data)
                        captured_network_data.append({
                            "label": label_prefix,
                            "url": url,
                            "file": str(out_path),
                            "has_joined": has_joined,
                            "has_country": has_country,
                            "preview": text_data[:300]
                        })
                        print(f"  [Network JSON Saved] {url[:80]}... -> {filename}")
                except Exception:
                    pass
        except Exception:
            pass

    page.on("response", handle_response)

def verify_instagram(page: Page, username: str) -> dict:
    url = f"https://www.instagram.com/{username}/"
    print(f"\n--- Checking Instagram for @{username} ---")
    res = {"platform": "instagram", "username": username, "status": "unknown", "text_fields": {}, "screenshot": None}
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
        time.sleep(2)
        
        # Check if page is not found or broken
        body_text = page.inner_text("body")
        if "Sorry, this page isn't available" in body_text or "Sayfa Bulunamadı" in body_text:
            res["status"] = "not_found"
            print("  Status: Not Found")
            return res
        
        if "checkpoint" in page.url or "challenge" in page.url:
            res["status"] = "checkpoint"
            print("  [ALERT] Checkpoint / Challenge detected!")
            return res

        res["status"] = "exists"
        
        # Check for 3 dots options button
        dots_btn = page.locator("header button:has(svg), header section button:has(svg), [role='main'] header svg[aria-label*='Options'], [role='main'] header svg[aria-label*='Seçenekler']").first
        
        # Alternative selectors for 3 dots
        if not dots_btn.count() or not dots_btn.is_visible():
            # Try finding buttons with 3 dots SVG or aria-label
            dots_btn = page.locator("header button svg[aria-label*='Options'], header button svg[aria-label*='options'], header button svg[aria-label*='Seçenekler'], header div[role='button']:has(svg)").first

        if dots_btn.count() and dots_btn.is_visible():
            print("  Found profile options (3 dots) button. Clicking...")
            dots_btn.click()
            time.sleep(1.5)
            
            # Look for "About this account"
            about_opt = page.locator("button:has-text('About this account'), div[role='dialog'] button:has-text('About this account'), button:has-text('Bu hesap hakkında')").first
            
            if about_opt.count() and about_opt.is_visible():
                print("  Found 'About this account' button! Clicking...")
                about_opt.click()
                time.sleep(2)
                
                # Take screenshot
                ss_path = config.DEBUG_DIR / f"ig_{username}_about.png"
                page.screenshot(path=str(ss_path))
                res["screenshot"] = str(ss_path)
                print(f"  Screenshot saved to {ss_path}")
                
                # Extract dialog text
                dialog = page.locator("div[role='dialog']").first
                if dialog.count():
                    dialog_text = dialog.inner_text()
                    res["dialog_text"] = dialog_text
                    print("  --- Extracted Dialog Text ---")
                    print(dialog_text)
                    print("  ----------------------------")
            else:
                print("  'About this account' option NOT found in desktop menu.")
                ss_path = config.DEBUG_DIR / f"ig_{username}_menu_open.png"
                page.screenshot(path=str(ss_path))
                res["screenshot"] = str(ss_path)
        else:
            print("  3 dots button not found on desktop profile header.")
            ss_path = config.DEBUG_DIR / f"ig_{username}_desktop_header.png"
            page.screenshot(path=str(ss_path))
            res["screenshot"] = str(ss_path)

    except Exception as e:
        res["error"] = str(e)
        print(f"  Error checking Instagram: {e}")

    return res

def verify_threads(page: Page, username: str) -> dict:
    url = f"https://www.threads.net/@{username}"
    print(f"\n--- Checking Threads for @{username} ---")
    res = {"platform": "threads", "username": username, "status": "unknown", "text_fields": {}, "screenshot": None}
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
        time.sleep(2)
        
        body_text = page.inner_text("body")
        if "This page isn't available" in body_text or "Sayfa kullanılamıyor" in body_text:
            res["status"] = "not_found"
            print("  Status: Not Found")
            return res

        res["status"] = "exists"
        
        # Look for 3 dots or more options button on Threads
        # In Threads web UI, options button is often a button near top right or near follow button with 3 dots SVG
        dots_btn = page.locator("button[aria-label*='More'], button[aria-label*='Daha fazla'], div[role='button'][aria-label*='More'], div[role='button'][aria-label*='Daha fazla'], header button:has(svg)").first
        
        # Look for any 3 dots SVG or menu button on profile
        if not dots_btn.count() or not dots_btn.is_visible():
            dots_btn = page.locator("svg[aria-label*='More'], svg[aria-label*='Daha fazla']").locator("..").first

        if dots_btn.count() and dots_btn.is_visible():
            print("  Found Threads profile options (3 dots) button. Clicking...")
            dots_btn.click()
            time.sleep(1.5)
            
            # Look for "About this profile" or similar
            about_opt = page.locator("div[role='menu'] div:has-text('About this profile'), div[role='menuitem']:has-text('About this profile'), div[role='dialog'] :has-text('About this profile'), :has-text('Bu profil hakkında')").first
            
            if about_opt.count() and about_opt.is_visible():
                print("  Found 'About this profile' button! Clicking...")
                about_opt.click()
                time.sleep(2)
                
                ss_path = config.DEBUG_DIR / f"threads_{username}_about.png"
                page.screenshot(path=str(ss_path))
                res["screenshot"] = str(ss_path)
                print(f"  Screenshot saved to {ss_path}")
                
                # Extract dialog or menu content
                dialog = page.locator("div[role='dialog']").first
                if dialog.count():
                    dialog_text = dialog.inner_text()
                    res["dialog_text"] = dialog_text
                    print("  --- Extracted Threads Dialog Text ---")
                    print(dialog_text)
                    print("  -------------------------------------")
            else:
                print("  'About this profile' not visible directly in menu.")
                ss_path = config.DEBUG_DIR / f"threads_{username}_menu_open.png"
                page.screenshot(path=str(ss_path))
                res["screenshot"] = str(ss_path)
                
                # Print all menu options seen
                menu = page.locator("div[role='menu'], div[role='dialog']").first
                if menu.count():
                    print("  Menu items seen:", repr(menu.inner_text()))
        else:
            print("  3 dots button not found on Threads profile header.")
            ss_path = config.DEBUG_DIR / f"threads_{username}_desktop_header.png"
            page.screenshot(path=str(ss_path))
            res["screenshot"] = str(ss_path)

    except Exception as e:
        res["error"] = str(e)
        print(f"  Error checking Threads: {e}")

    return res

def test_mobile_emulation(context, username: str, platform: str) -> dict:
    print(f"\n--- Testing Mobile Viewport Emulation for {platform} @{username} ---")
    mobile_page = context.new_page()
    mobile_page.set_viewport_size({"width": 390, "height": 844})
    
    res = {}
    if platform == "instagram":
        attach_network_listener(mobile_page, f"ig_mobile_{username}")
        url = f"https://www.instagram.com/{username}/"
        try:
            mobile_page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
        except Exception:
            pass
        time.sleep(2)
        ss_path = config.DEBUG_DIR / f"ig_{username}_mobile.png"
        mobile_page.screenshot(path=str(ss_path))
        print(f"  Saved mobile screenshot: {ss_path}")
        
        # Look for 3 dots
        dots = mobile_page.locator("header button:has(svg), header svg[aria-label*='Options'], header svg[aria-label*='Seçenekler']").first
        if dots.count() and dots.is_visible():
            dots.click()
            time.sleep(1.5)
            about_opt = mobile_page.locator("button:has-text('About this account'), :has-text('Bu hesap hakkında')").first
            if about_opt.count() and about_opt.is_visible():
                about_opt.click()
                time.sleep(2)
                ss_about = config.DEBUG_DIR / f"ig_{username}_mobile_about.png"
                mobile_page.screenshot(path=str(ss_about))
                dialog = mobile_page.locator("div[role='dialog']").first
                if dialog.count():
                    res["dialog_text"] = dialog.inner_text()
                    print("  Mobile Dialog text:", res["dialog_text"])
    elif platform == "threads":
        attach_network_listener(mobile_page, f"threads_mobile_{username}")
        url = f"https://www.threads.net/@{username}"
        try:
            mobile_page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
        except Exception:
            pass
        time.sleep(2)
        ss_path = config.DEBUG_DIR / f"threads_{username}_mobile.png"
        mobile_page.screenshot(path=str(ss_path))
        print(f"  Saved mobile screenshot: {ss_path}")
    
    mobile_page.close()
    return res

def main():
    print("==================================================")
    print("STEP 0: MANUAL LOGIN & VERIFICATION")
    print("==================================================")
    
    # Read first 3 usernames
    with open(config.USERNAMES_FILE, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()][:3]
    
    print(f"Test usernames selected: {usernames}")
    
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        print(f"Launching Chromium with persistent profile: {user_data_dir}")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Step 0.1: Check login status / pause for login
        print("\n[STEP 0.1] Checking / performing manual login...")
        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"  Note: Initial load notice: {e}")
        time.sleep(2)
        
        print("\n" + "="*70)
        print(">>> ACTION REQUIRED <<<")
        print("1. In the opened browser window, log in to Instagram and Threads.")
        print("2. Make sure you are logged in on both instagram.com and threads.net.")
        print("3. Once logged in, press ENTER in this terminal to begin Step 0 verification.")
        print("="*70 + "\n")
        
        input("Press ENTER when logged in and ready to proceed...")
        
        attach_network_listener(page, "general")
        
        ig_results = []
        threads_results = []
        
        # Step 0.2: For 3 usernames, open Instagram and Threads
        for u in usernames:
            attach_network_listener(page, f"ig_{u}")
            ig_res = verify_instagram(page, u)
            ig_results.append(ig_res)
            
            # If about this account wasn't accessible or needs mobile check
            if not ig_res.get("dialog_text"):
                mobile_res = test_mobile_emulation(context, u, "instagram")
                ig_res["mobile_res"] = mobile_res
            
            time.sleep(2)
            
            attach_network_listener(page, f"threads_{u}")
            thr_res = verify_threads(page, u)
            threads_results.append(thr_res)
            
            if not thr_res.get("dialog_text"):
                mobile_res = test_mobile_emulation(context, u, "threads")
                thr_res["mobile_res"] = mobile_res
            
            time.sleep(2)
        
        print("\n==================================================")
        print("STEP 0 VERIFICATION RESULTS SUMMARY")
        print("==================================================")
        print("\nInstagram Results:")
        for r in ig_results:
            print(f"Username: {r['username']} | Status: {r['status']}")
            if 'dialog_text' in r:
                print(f"  Dialog Text:\n{r['dialog_text']}")
            if 'error' in r:
                print(f"  Error: {r['error']}")
                
        print("\nThreads Results:")
        for r in threads_results:
            print(f"Username: {r['username']} | Status: {r['status']}")
            if 'dialog_text' in r:
                print(f"  Dialog Text:\n{r['dialog_text']}")
            if 'error' in r:
                print(f"  Error: {r['error']}")
                
        print(f"\nCaptured {len(captured_network_data)} relevant network JSON responses.")
        for item in captured_network_data:
            print(f" - URL: {item['url']}")
            print(f"   Saved to: {item['file']}")
            
        print("\nStep 0 finished. Browser profile saved.")
        context.close()

if __name__ == "__main__":
    main()
