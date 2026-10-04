import time
import json
import pandas as pd
from playwright.sync_api import sync_playwright
import config

def run_fast_checker():
    print("\n=======================================================")
    print("TEST D: FAST API-DIRECT METHOD (NO UI CLICKS)")
    print("=======================================================")
    
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Navigate to instagram home once to ensure session & tokens are fresh
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        time.sleep(2)
        
        # Extract fb_dtsg and lsd from page context
        tokens = page.evaluate("""() => {
            return {
                fb_dtsg: window._sharedData?.raw_csrf_token || document.querySelector('[name="csrf_token"]')?.value || '',
                cookies: document.cookie
            };
        }""")
        print("Session context verified. Running fast request test...")
        
        test_accounts = [l.strip() for l in open("usernames.txt").readlines() if l.strip()][:20]
        
        fast_results = []
        t_start = time.time()
        
        for idx, u in enumerate(test_accounts, 1):
            t0 = time.time()
            res = {"username": u, "fast_status": "unknown", "date_joined": None, "country": None, "seconds": 0.0}
            
            try:
                # In Web API, fetching Instagram web profile info directly via web request
                resp = page.request.get(
                    f"https://www.instagram.com/api/v1/users/web_profile_info/?username={u}",
                    headers={
                        "x-ig-app-id": "936619743392459",
                        "x-requested-with": "XMLHttpRequest",
                        "referer": f"https://www.instagram.com/{u}/"
                    }
                )
                
                status_code = resp.status
                if status_code == 200:
                    data = resp.json()
                    user = data.get("data", {}).get("user", {})
                    res["fast_status"] = "exists"
                    
                    # Check transparency / about fields in user object
                    # Some accounts have about_this_account or transparency details in user dictionary
                    trans = user.get("show_account_transparency_details")
                    res["transparency_enabled"] = trans
                    # Check if joined date or location exists in web_profile_info
                    # In web_profile_info, date_joined is not public without the transparency modal query
                elif status_code == 404:
                    res["fast_status"] = "not_found"
                elif status_code == 429:
                    res["fast_status"] = "rate_limit"
                else:
                    res["fast_status"] = f"http_{status_code}"
                    
            except Exception as e:
                res["fast_status"] = "error"
                res["error"] = str(e)
                
            res["seconds"] = round(time.time() - t0, 2)
            fast_results.append(res)
            print(f"[{idx}/20] Fast check @{u}: status={res['fast_status']} ({res['seconds']}s)")
            time.sleep(2.5) # 2 to 4s delay as instructed
            
        context.close()
        
        total_time = time.time() - t_start
        df = pd.DataFrame(fast_results)
        df.to_csv(config.RESULTS_DIR / "test_d_fast_results.csv", index=False)
        
        print("\n" + "="*60)
        print("FAST CHECKER SUMMARY:")
        print(f"Total processed: {len(df)}")
        print(f"Total runtime: {total_time:.1f}s")
        print(f"Average time per account: {df['seconds'].mean():.2f}s")
        est_per_hour = (3600 / (df['seconds'].mean() + 2.5))
        print(f"Estimated accounts per hour: ~{est_per_hour:.0f} accounts/hour")
        print("="*60)

if __name__ == "__main__":
    run_fast_checker()
