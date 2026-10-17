"""Shared mode identifiers without importing the browser dispatcher."""

MODE_IG_ONLY = "ig_only"
MODE_THREADS_ONLY = "threads_only"
MODE_COMBINED = "combined"
MODE_COMBINED_SMART = "combined_smart"
MODE_IG_STATUS_ONLY = "ig_status_only"
MODE_THREADS_STATUS_ONLY = "threads_status_only"
MODE_COMBINED_STATUS_ONLY = "combined_status_only"
ANONYMOUS_MODES = (
    MODE_IG_STATUS_ONLY, MODE_THREADS_STATUS_ONLY, MODE_COMBINED_STATUS_ONLY,
)
MODES = (
    MODE_IG_ONLY, MODE_THREADS_ONLY, MODE_COMBINED,
    MODE_COMBINED_SMART, *ANONYMOUS_MODES,
)

STATUS_ONLY_NOTICE = (
    "Status only: country and joined dates are unavailable without login; "
    "Threads is not checked."
)


def status_notice(mode: str) -> str:
    """Explain public-first status reads and selective saved-login fallback."""
    if mode == MODE_IG_STATUS_ONLY:
        return STATUS_ONLY_NOTICE
    return (
        "Alive checks: public pages first; saved login verifies unclear "
        "results. Country and joined dates are not requested."
    )
