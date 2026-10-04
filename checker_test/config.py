import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.resolve()
USERNAMES_FILE = BASE_DIR / "usernames.txt"
RESULTS_DIR = BASE_DIR / "results"
DEBUG_DIR = BASE_DIR / "debug"
DEBUG_NETWORK_DIR = DEBUG_DIR / "network"
BROWSER_PROFILE_DIR = BASE_DIR / "browser_profile"

RESULTS_XLSX = RESULTS_DIR / "results.xlsx"
RESULTS_CSV = RESULTS_DIR / "results.csv"

# Delays & Timeouts
MIN_DELAY = 3.0  # seconds
MAX_DELAY = 7.0  # seconds
PAGE_TIMEOUT = 30000  # ms (30s)
NAVIGATION_TIMEOUT = 30000  # ms (30s)

# Create required directories
for d in [RESULTS_DIR, DEBUG_DIR, DEBUG_NETWORK_DIR, BROWSER_PROFILE_DIR]:
    d.mkdir(parents=True, exist_ok=True)
