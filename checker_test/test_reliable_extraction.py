import sys
import time
from playwright.sync_api import sync_playwright
import config

sys.stdout.reconfigure(encoding='utf-8')

def extract_profile_reliable(page, username):
    res = {
        "username": username,
        "ig_date_joined": None,
        "ig_country": None,
        "threads_date_joined": None,
        "threads_join_badge": None,
        "threads_country": None
    }
    
    # 1. Instagram
    page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded")
    time.sleep(2.5)
    
    dots = page.locator("header div[aria-haspopup='dialog'], header button:has(svg), header svg[aria-label='Options']").first
    if dots.count() and dots.is_visible():
        dots.click()
        time.sleep(1.5)
        
        about_btn = page.locator(":text('About this account'), :text('About this profile'), :text('Bu hesap hakkında')").first
        if about_btn.count() and about_btn.is_visible():
            about_btn.click()
            
            # Wait up to 7s for "Date joined" text to appear in dialog
            t_end = time.time() + 7.0
            while time.time() < t_end:
                dialog = page.locator("div[role='dialog']").first
                if dialog.count() and dialog.is_visible():
                    txt = dialog.inner_text()
                    if "Date joined" in txt or "Katılma tarihi" in txt:
                        lines = [l.strip() for l in txt.splitlines() if l.strip()]
                        for idx, l in enumerate(lines):
                            if "Date joined" in l or "Katılma tarihi" in l:
                                if idx + 1 < len(lines):
                                    res["ig_date_joined"] = lines[idx + 1]
                            if any(k in l for k in ["Account based in", "Hesabın bulunduğu konum"]):
                                if idx + 1 < len(lines):
                                    res["ig_country"] = lines[idx + 1]
                        break
                time.sleep(0.5)
            page.keyboard.press("Escape")
            time.sleep(0.5)
            page.keyboard.press("Escape")

    # 2. Threads
    page.goto(f"https://www.threads.net/@{username}", wait_until="domcontentloaded")
    time.sleep(2.5)
    
    body = page.inner_text("body")
    if not ("This page isn't available" in body or "Sayfa kullanılamıyor" in body):
        # Locate the 3-dots on the profile card (it's the 3rd icon in header actions)
        card = page.locator(f"div:has-text('{username}'):has-text('Follow')").last
        if not card.count():
            card = page.locator("div[role='main']").first
            
        thr_dots = card.locator("div[aria-haspopup='dialog']").first
        if thr_dots.count() and thr_dots.is_visible():
            thr_dots.click()
            time.sleep(1.5)
            
            about_thr = page.locator(":text('About this profile'), :text('Bu profil hakkında')").first
            if about_thr.count() and about_thr.is_visible():
                about_thr.click()
                
                t_end = time.time() + 7.0
                while time.time() < t_end:
                    dialog = page.locator("div[role='dialog']").first
                    if dialog.count() and dialog.is_visible():
                        txt = dialog.inner_text()
                        if "Joined" in txt or "Katılma" in txt or "Based in" in txt:
                            lines = [l.strip() for l in txt.splitlines() if l.strip()]
                            for idx, l in enumerate(lines):
                                if l in ["Joined", "Katılma tarihi"]:
                                    if idx + 1 < len(lines):
                                        raw_j = lines[idx + 1]
                                        if "·" in raw_j:
                                            p = raw_j.split("·")
                                            res["threads_date_joined"] = p[0].strip()
                                            res["threads_join_badge"] = p[1].strip()
                                        else:
                                            res["threads_date_joined"] = raw_j.strip()
                                if l in ["Based in", "Account based in", "Location", "Konum"]:
                                    if idx + 1 < len(lines):
                                        res["threads_country"] = lines[idx + 1]
                            break
                    time.sleep(0.5)
                page.keyboard.press("Escape")

    return res

def test_reliable():
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        sample = ["zeynep607196", "elif70566", "ece25051", "ayse517258", "fatma868612"]
        for s in sample:
            r = extract_profile_reliable(page, s)
            print(f"Result for @{s}:")
            print(f"  IG: {r['ig_date_joined']} | {r['ig_country']}")
            print(f"  Threads: {r['threads_date_joined']} [{r['threads_join_badge']}] | {r['threads_country']}\n")
            
        context.close()

if __name__ == "__main__":
    test_reliable()
