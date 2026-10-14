"""Shared mode identifiers without importing the browser dispatcher."""

MODE_IG_ONLY = "ig_only"
MODE_THREADS_ONLY = "threads_only"
MODE_COMBINED = "combined"
MODE_COMBINED_SMART = "combined_smart"
MODE_IG_STATUS_ONLY = "ig_status_only"
MODES = (
    MODE_IG_ONLY, MODE_THREADS_ONLY, MODE_COMBINED,
    MODE_COMBINED_SMART, MODE_IG_STATUS_ONLY,
)

STATUS_ONLY_NOTICE = (
    "Status only: country and joined dates are unavailable without login; "
    "Threads is not checked."
)
