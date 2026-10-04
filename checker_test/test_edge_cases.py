import time
import pandas as pd
from playwright.sync_api import sync_playwright
import config
from main import process_username

def run_test_b():
    edge_cases = [
        # 3 Non-existent accounts
        "nonexistent_user_xyz_998811",
        "fake_user_test_999912344",
        "invalid_acc_not_found_00077",
        
        # 2 Private accounts
        "gizli_hesap_test_123",
        "private_test_user_991",
        
        # 2 IG accounts with no Threads profile
        "instagram_without_threads_1928",
        "no_threads_test_user_771"
    ]
    
    print("\n=======================================================")
    print("TEST B: EDGE CASES ROBUSTNESS TEST")
    print("=======================================================")
    
    with sync_playwright() as p:
        user_data_dir = str(config.BROWSER_PROFILE_DIR)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        results = []
        for idx, u in enumerate(edge_cases, 1):
            print(f"\n[{idx}/{len(edge_cases)}] Testing Edge Case: @{u}")
            res = process_username(page, u)
            res.pop("stop_run", None)
            results.append(res)
            print(f"  Result -> IG: {res['ig_status']} | Threads: {res['threads_status']} | Error: {repr(res['error'])}")
            time.sleep(2)
            
        context.close()
        
    df = pd.DataFrame(results)
    out_csv = config.RESULTS_DIR / "test_b_edge_cases.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved Test B results to: {out_csv}")
    print("\nTest B Results Table:")
    print(df[["username", "ig_status", "threads_status", "error"]])

if __name__ == "__main__":
    run_test_b()
