# Instagram & Threads Profile Checker (Test Script)

A Python & Playwright automation tool designed to extract **Date Joined** (month + year) and **Account Based In** (country) for Instagram and Threads profiles, measure performance, and export structured data to Excel and CSV.

---

## 📁 Project Structure

```text
checker_test/
├── config.py             # Paths, timeouts, delays, and directory configuration
├── step0_verify.py       # Step 0 verification script for manual login and layout inspection
├── main.py               # Main scraper script with resume support, retries, and safety triggers
├── usernames.txt         # Input list of usernames (one per line)
├── browser_profile/      # Persistent Playwright browser session folder (keeps you logged in)
├── results/              # Output directory for results.xlsx and results.csv
├── debug/                # UI screenshots (desktop/mobile) and error logs
│   └── network/          # Captured JSON network responses (for future fast API version)
└── README.md             # Setup and operational guide
```

---

## ⚙️ Installation & Setup

1. **Prerequisites**: Python 3.10+ installed on your system.

2. **Install Dependencies**:
   ```bash
   pip install playwright pandas openpyxl
   playwright install chromium
   ```

---

## 🚀 How to Run

### Step 0: Initial Verification & Login (Mandatory First Run)
Run the verification script:
```bash
python step0_verify.py
```
- A Chromium browser window will open.
- Log in manually to your **Instagram** and **Threads** checker accounts.
- Return to your terminal and press **Enter**.
- The script will test 3 target usernames, test UI selectors & mobile viewports, capture screenshots into `debug/`, and record any relevant network JSON responses into `debug/network/`.

### Step 1: Running the Full Test
Once Step 0 is verified, run the full pipeline:
```bash
python main.py
```
- Automatically reads usernames from `usernames.txt`.
- Employs human-like random delays (3 to 7s) between accounts.
- Detects account status (`exists`, `not_found`, `private`, `suspended`).
- Saves progress after **every single account** (`results/results.xlsx` and `results/results.csv`).
- **Resume Support**: If interrupted, restarting `main.py` will skip already-completed usernames.
- **Safety Halt**: Automatically aborts and screenshots if a checkpoint, captcha, or rate-limit is triggered.

---

## 📊 Output Schema

`results.xlsx` / `results.csv`:
- `username`: Account handle
- `ig_status`: `exists` | `not_found` | `private` | `suspended` | `checkpoint`
- `ig_date_joined`: Extracted Instagram join date (e.g. `September 2021`)
- `ig_country`: Extracted Instagram location (e.g. `Turkey`)
- `threads_status`: Status on Threads
- `threads_date_joined`: Extracted Threads join date
- `threads_country`: Extracted Threads location
- `seconds_taken`: Total execution time per account
- `error`: Logged errors or timeouts if any
