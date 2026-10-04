import os
import sys
import time
import random
import traceback
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

import config

def load_usernames(filepath: Path) -> list[str]:
    """Reads usernames from file, strips spaces, removes duplicates, maintains order."""
    if not filepath.exists():
        print(f"[Error] Usernames file not found: {filepath}")
        return []
    
    seen = set()
    ordered_users = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if u and u not in seen:
                seen.add(u)
                ordered_users.append(u)
    return ordered_users

def load_existing_results() -> tuple[pd.DataFrame, set[str]]:
    """Loads existing results for resume support."""
    columns = [
        "username",
        "ig_status",
        "ig_date_joined",
        "ig_country",
        "ig_seconds",
        "threads_status",
        "threads_date_joined",
        "threads_join_badge",
        "threads_country",
        "threads_seconds",
        "seconds_taken",
        "error"
    ]
    
    if config.RESULTS_CSV.exists():
        try:
            df = pd.read_csv(config.RESULTS_CSV)
            # Ensure all columns exist
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            done_users = set(df["username"].dropna().astype(str))
            return df, done_users
        except Exception as e:
            print(f"[Warning] Could not read existing results.csv: {e}")
            
    df = pd.DataFrame(columns=columns)
    return df, set()

def save_results(df: pd.DataFrame):
    """Saves DataFrame to both CSV and Excel."""
    try:
        df.to_csv(config.RESULTS_CSV, index=False, encoding="utf-8-sig")
        df.to_excel(config.RESULTS_XLSX, index=False, engine="openpyxl")
    except Exception as e:
        print(f"[Error] Failed to save results: {e}")

def check_safety_challenge(page: Page, platform: str) -> tuple[bool, str]:
    """
    Checks if Instagram or Threads showed a login prompt, checkpoint, challenge,
    rate limit, or CAPTCHA.
    """
    url = page.url.lower()
    if "checkpoint" in url or "challenge" in url or "accounts/login" in url or "login" in url:
        return True, f"Redirected to {page.url}"
    
    try:
        body_text = page.inner_text("body").lower()
        triggers = [
            "suspicious activity",
            "please wait a few minutes before you try again",
            "try again later",
            "we restrict certain activity",
            "help us confirm it's you",
            "confirm you're a human",
            "security check",
            "rate limit",
            "hesabın geçici olarak kilitlendi",
            "daha sonra tekrar dene",
            "olağan dışı hareket"
        ]
        for trigger in triggers:
            if trigger in body_text:
                return True, f"Trigger keyword detected: '{trigger}'"
    except Exception:
        pass
        
    return False, ""

def extract_instagram_profile(page: Page, username: str) -> dict:
    """Extracts Date Joined and Country from Instagram profile with dynamic polling."""
    t0 = time.time()
    res = {
        "status": "unknown",
        "date_joined": None,
        "country": None,
        "seconds": 0.0,
        "error": None
    }
    
    url = f"https://www.instagram.com/{username}/"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
    except PlaywrightTimeoutError:
        pass
    time.sleep(2.5)
    
    # Check challenge
    is_challenge, reason = check_safety_challenge(page, "Instagram")
    if is_challenge:
        res["status"] = "checkpoint"
        res["error"] = f"SAFETY TRIGGER: {reason}"
        res["seconds"] = round(time.time() - t0, 2)
        return res
        
    body_text = page.inner_text("body")
    if "Sorry, this page isn't available" in body_text or "Sayfa Bulunamadı" in body_text:
        res["status"] = "not_found"
        res["seconds"] = round(time.time() - t0, 2)
        return res
        
    if "This account is private" in body_text or "Bu hesap gizli" in body_text:
        res["status"] = "private"
    else:
        res["status"] = "exists"
        
    # Open "About this account"
    try:
        dots_btn = page.locator("header div[aria-haspopup='dialog'], header button:has(svg), header svg[aria-label*='Options'], header svg[aria-label*='Seçenekler']").first
        if not dots_btn.count() or not dots_btn.is_visible():
            dots_btn = page.locator("header [role='button']:has(svg)").first
            
        if dots_btn.count() and dots_btn.is_visible():
            dots_btn.click()
            time.sleep(1.5)
            
            about_opt = page.locator(":text('About this account'), :text('About this profile'), :text('Bu hesap hakkında')").first
            if about_opt.count() and about_opt.is_visible():
                about_opt.click()
                
                # Dynamic polling up to 10s for dialog content
                t_end = time.time() + 10.0
                while time.time() < t_end:
                    dialog = page.locator("div[role='dialog']").first
                    if dialog.count() and dialog.is_visible():
                        dialog_text = dialog.inner_text()
                        if "Date joined" in dialog_text or "Katılma tarihi" in dialog_text:
                            lines = [l.strip() for l in dialog_text.splitlines() if l.strip()]
                            for idx, line in enumerate(lines):
                                if any(k in line for k in ["Date joined", "Katılma tarihi"]):
                                    if idx + 1 < len(lines):
                                        res["date_joined"] = lines[idx + 1]
                                if any(k in line for k in ["Account based in", "Hesabın bulunduğu konum", "Account location"]):
                                    if idx + 1 < len(lines):
                                        res["country"] = lines[idx + 1]
                            break
                    time.sleep(0.5)
                    
                page.keyboard.press("Escape")
                time.sleep(0.5)
                page.keyboard.press("Escape")
            else:
                page.keyboard.press("Escape")
        else:
            page.keyboard.press("Escape")
    except Exception as e:
        res["error"] = f"IG parse error: {str(e)}"
        
    res["seconds"] = round(time.time() - t0, 2)
    return res

def extract_threads_profile(page: Page, username: str) -> dict:
    """Extracts Date Joined, Join Badge, and Country from Threads profile with robust selector."""
    t0 = time.time()
    res = {
        "status": "unknown",
        "date_joined": None,
        "join_badge": None,
        "country": None,
        "seconds": 0.0,
        "error": None
    }
    
    url = f"https://www.threads.net/@{username}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
    except PlaywrightTimeoutError:
        pass
    time.sleep(2.5)
    
    is_challenge, reason = check_safety_challenge(page, "Threads")
    if is_challenge:
        res["status"] = "checkpoint"
        res["error"] = f"SAFETY TRIGGER: {reason}"
        res["seconds"] = round(time.time() - t0, 2)
        return res
        
    body_text = page.inner_text("body")
    if "This page isn't available" in body_text or "Sayfa kullanılamıyor" in body_text:
        res["status"] = "not_found"
        res["seconds"] = round(time.time() - t0, 2)
        return res
        
    res["status"] = "exists"
    
    # Open "About this profile"
    try:
        card = page.locator("div[aria-label='Column body'], div[role='main']").first
        action_svgs = [s for s in card.locator("svg").all() if s.bounding_box() and 100 < s.bounding_box()["y"] < 350 and s.bounding_box()["x"] > 600]
        
        if action_svgs:
            dots_svg = action_svgs[-1] # Rightmost icon is the 3-dots
            parent = dots_svg.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
            if parent.count():
                parent.click()
            else:
                dots_svg.click()
            time.sleep(1.5)
            
            about_opt = page.locator(":text('About this profile'), :text('Bu profil hakkında')").last
            if about_opt.count() and about_opt.is_visible():
                about_opt.click()
                
                t_end = time.time() + 8.0
                while time.time() < t_end:
                    for el in page.locator("div:has-text('Based in')").all():
                        try:
                            t = el.inner_text()
                            if "Name" in t and ("Joined" in t or "Based in" in t) and len(t) < 400:
                                lines = [l.strip() for l in t.splitlines() if l.strip()]
                                for idx, line in enumerate(lines):
                                    if line in ["Joined", "Katılma tarihi"]:
                                        if idx + 1 < len(lines):
                                            raw = lines[idx + 1]
                                            if "·" in raw:
                                                parts = raw.split("·")
                                                res["date_joined"] = parts[0].strip()
                                                res["join_badge"] = parts[1].strip()
                                            else:
                                                res["date_joined"] = raw.strip()
                                                res["join_badge"] = ""
                                    if line in ["Based in", "Account based in", "Location", "Konum"]:
                                        if idx + 1 < len(lines):
                                            res["country"] = lines[idx + 1]
                                break
                        except Exception:
                            pass
                    if res["date_joined"] or res["country"]:
                        break
                    time.sleep(0.5)
                    
                page.keyboard.press("Escape")
            else:
                page.keyboard.press("Escape")
        else:
            page.keyboard.press("Escape")
    except Exception as e:
        res["error"] = f"Threads parse error: {str(e)}"
        
    res["seconds"] = round(time.time() - t0, 2)
    return res

def process_username(page: Page, username: str) -> dict:
    """Processes a single account with retry on timeout and per-platform timing."""
    start_time = time.time()
    
    ig_data = None
    threads_data = None
    errors = []
    
    # 1. Instagram Attempt (with 1 retry on timeout)
    for attempt in range(2):
        try:
            ig_data = extract_instagram_profile(page, username)
            if ig_data.get("error"):
                errors.append(ig_data["error"])
            break
        except PlaywrightTimeoutError:
            if attempt == 0:
                print(f"  [Retry] Timeout on Instagram @{username}, retrying once...")
                time.sleep(2)
            else:
                errors.append("IG Timeout")
                ig_data = {"status": "timeout", "date_joined": None, "country": None, "seconds": 20.0}
        except Exception as e:
            errors.append(f"IG Exception: {str(e)}")
            ig_data = {"status": "error", "date_joined": None, "country": None, "seconds": 0.0}
            break

    # If safety checkpoint hit on IG, return immediately
    if ig_data and ig_data.get("status") == "checkpoint":
        ss_path = config.DEBUG_DIR / f"checkpoint_ig_{username}.png"
        page.screenshot(path=str(ss_path))
        elapsed = round(time.time() - start_time, 2)
        return {
            "username": username,
            "ig_status": "checkpoint",
            "ig_date_joined": None,
            "ig_country": None,
            "ig_seconds": ig_data.get("seconds", 0.0),
            "threads_status": "skipped",
            "threads_date_joined": None,
            "threads_join_badge": None,
            "threads_country": None,
            "threads_seconds": 0.0,
            "seconds_taken": elapsed,
            "error": "CRITICAL: Checkpoint / Challenge triggered on Instagram",
            "stop_run": True
        }

    # 2. Threads Attempt (with 1 retry on timeout)
    for attempt in range(2):
        try:
            threads_data = extract_threads_profile(page, username)
            if threads_data.get("error"):
                errors.append(threads_data["error"])
            break
        except PlaywrightTimeoutError:
            if attempt == 0:
                print(f"  [Retry] Timeout on Threads @{username}, retrying once...")
                time.sleep(2)
            else:
                errors.append("Threads Timeout")
                threads_data = {"status": "timeout", "date_joined": None, "join_badge": None, "country": None, "seconds": 20.0}
        except Exception as e:
            errors.append(f"Threads Exception: {str(e)}")
            threads_data = {"status": "error", "date_joined": None, "join_badge": None, "country": None, "seconds": 0.0}
            break

    # If safety checkpoint hit on Threads, return immediately
    if threads_data and threads_data.get("status") == "checkpoint":
        ss_path = config.DEBUG_DIR / f"checkpoint_threads_{username}.png"
        page.screenshot(path=str(ss_path))
        elapsed = round(time.time() - start_time, 2)
        return {
            "username": username,
            "ig_status": ig_data.get("status"),
            "ig_date_joined": ig_data.get("date_joined"),
            "ig_country": ig_data.get("country"),
            "ig_seconds": ig_data.get("seconds", 0.0),
            "threads_status": "checkpoint",
            "threads_date_joined": None,
            "threads_join_badge": None,
            "threads_country": None,
            "threads_seconds": threads_data.get("seconds", 0.0),
            "seconds_taken": elapsed,
            "error": "CRITICAL: Checkpoint / Challenge triggered on Threads",
            "stop_run": True
        }

    elapsed = round(time.time() - start_time, 2)
    return {
        "username": username,
        "ig_status": ig_data.get("status") if ig_data else "error",
        "ig_date_joined": ig_data.get("date_joined") if ig_data else None,
        "ig_country": ig_data.get("country") if ig_data else None,
        "ig_seconds": ig_data.get("seconds") if ig_data else 0.0,
        "threads_status": threads_data.get("status") if threads_data else "error",
        "threads_date_joined": threads_data.get("date_joined") if threads_data else None,
        "threads_join_badge": threads_data.get("join_badge") if threads_data else None,
        "threads_country": threads_data.get("country") if threads_data else None,
        "threads_seconds": threads_data.get("seconds") if threads_data else 0.0,
        "seconds_taken": elapsed,
        "error": "; ".join(errors) if errors else "",
        "stop_run": False
    }

def print_summary(df: pd.DataFrame, total_runtime_sec: float):
    total = len(df)
    if total == 0:
        print("\nNo accounts were processed.")
        return
        
    ig_success = len(df[df["ig_date_joined"].notna() | (df["ig_country"].notna())])
    threads_success = len(df[df["threads_date_joined"].notna() | (df["threads_country"].notna())])
    
    avg_total_sec = df["seconds_taken"].mean() if total > 0 else 0
    avg_ig_sec = df["ig_seconds"].mean() if "ig_seconds" in df.columns and total > 0 else 0
    avg_threads_sec = df["threads_seconds"].mean() if "threads_seconds" in df.columns and total > 0 else 0
    
    est_both_per_hour = (3600 / avg_total_sec) if avg_total_sec > 0 else 0
    est_ig_only_per_hour = (3600 / (avg_ig_sec + 4.0)) if avg_ig_sec > 0 else 0 # +4s avg delay
    est_threads_only_per_hour = (3600 / (avg_threads_sec + 4.0)) if avg_threads_sec > 0 else 0
    
    print("\n" + "="*70)
    print("                      EXECUTION & SPEED SUMMARY")
    print("="*70)
    print(f"Total Accounts Processed:     {total}")
    print(f"Instagram Success Rate:       {ig_success}/{total} ({(ig_success/total)*100:.1f}%)")
    print(f"Threads Success Rate:         {threads_success}/{total} ({(threads_success/total)*100:.1f}%)")
    print(f"Total Run Time:               {total_runtime_sec/60:.2f} min ({total_runtime_sec:.1f}s)")
    print(f"Average Speed Per Account:    {avg_total_sec:.2f}s (IG: {avg_ig_sec:.2f}s | Threads: {avg_threads_sec:.2f}s)")
    print("-" * 70)
    print("ESTIMATED CAPACITY (ACCOUNTS / HOUR - SINGLE SESSION):")
    print(f"  • Both Instagram + Threads: ~{est_both_per_hour:.0f} accounts / hour")
    print(f"  • Instagram Only (with delay): ~{est_ig_only_per_hour:.0f} accounts / hour")
    print(f"  • Threads Only (with delay):   ~{est_threads_only_per_hour:.0f} accounts / hour")
    
    checkpoints = df[df["ig_status"] == "checkpoint"]
    if not checkpoints.empty:
        print(f"\n[ALERT] Encounted {len(checkpoints)} safety checkpoints/challenges.")
    else:
        print("\nSafety status: Clean run (No checkpoints, captchas, or blocks encountered).")
    print("="*70 + "\n")

def run_batch(max_accounts: int = None):
    usernames = load_usernames(config.USERNAMES_FILE)
    print(f"Loaded {len(usernames)} unique usernames from {config.USERNAMES_FILE.name}")
    
    results_df, done_users = load_existing_results()
    if done_users:
        print(f"Found {len(done_users)} already processed accounts in results. Resuming...")
        
    pending_users = [u for u in usernames if u not in done_users]
    if max_accounts:
        pending_users = pending_users[:max_accounts]
        
    print(f"Accounts to process in this run: {len(pending_users)}")
    
    if not pending_users:
        print("All usernames have already been processed!")
        print_summary(results_df, results_df["seconds_taken"].sum())
        return

    start_run_time = time.time()
    
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        for idx, username in enumerate(pending_users, 1):
            print(f"\n[{idx}/{len(pending_users)}] Processing @{username}...")
            
            result = process_username(page, username)
            stop_run = result.pop("stop_run", False)
            
            # Append result and save immediately
            results_df = pd.concat([results_df, pd.DataFrame([result])], ignore_index=True)
            save_results(results_df)
            
            print(f"  -> Extracted in {result['seconds_taken']}s (IG: {result['ig_seconds']}s, Thr: {result['threads_seconds']}s)")
            print(f"     IG: {result['ig_status']} [{result['ig_date_joined']}, {result['ig_country']}]")
            print(f"     Threads: {result['threads_status']} [{result['threads_date_joined']}, {result['threads_country']}]")
            
            if stop_run:
                print("\n[SAFETY STOP] Checkpoint or rate-limit encountered. Halting execution immediately.")
                break
                
            # Random delay between accounts
            if idx < len(pending_users):
                delay = round(random.uniform(config.MIN_DELAY, config.MAX_DELAY), 2)
                print(f"  Waiting {delay}s before next account...")
                time.sleep(delay)
                
        context.close()
        
    total_time = time.time() - start_run_time
    print_summary(results_df, total_time)

if __name__ == "__main__":
    max_acc = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_batch(max_acc)
