"""Export presets and honest platform-specific Alive filters."""

from src.core.check_plan import ALIVE_STATUSES, checks_for_mode
from src.core.output_settings import OUTPUT_NAMES, normalize_selection

ROW_FILTERS = (
    "All results", "IG Alive only", "Threads Alive only", "Both Alive only",
)
EXPORT_PRESETS = (
    "Custom columns", "Full export", "Alive/status only", "Country only",
    "Age/joined only", "Checked fields",
)


def filter_records(records: list[dict], row_filter: str) -> list[dict]:
    """Snapshot final rows and require an explicit platform Alive status."""
    if row_filter not in ROW_FILTERS:
        raise ValueError("Unknown export row filter")
    snapshot = list(records)
    if row_filter == "All results":
        return snapshot
    platforms = {
        "IG Alive only": ("ig",), "Threads Alive only": ("threads",),
        "Both Alive only": ("ig", "threads"),
    }[row_filter]
    return [record for record in snapshot if all(
        record.get(f"{platform}_status") in ALIVE_STATUSES
        for platform in platforms
    )]


def checked_columns(checks: tuple[str, ...]) -> tuple[str, ...]:
    """Match exported fields to selected checks, always retaining Username."""
    names = ["Username"]
    labels = {
        "ig_alive": "IG Status", "threads_alive": "Threads Status",
        "ig_country": "IG Country", "threads_country": "Threads Country",
        "ig_age": "IG Joined", "threads_age": "Threads Joined",
    }
    names.extend(labels[check] for check in checks if check in labels)
    return normalize_selection(names)


def export_preset(
    name: str, checks: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Return columns for a quick preset without requesting another scrape."""
    presets = {
        "Full export": OUTPUT_NAMES,
        "Alive/status only": (
            "Username", "Status", "IG Status", "Threads Status",
        ),
        "Country only": ("Username", "IG Country", "Threads Country"),
        "Age/joined only": ("Username", "IG Joined", "Threads Joined"),
    }
    if name == "Checked fields":
        return checked_columns(checks if checks is not None else (
            checks_for_mode("combined")
        ))
    if name not in presets:
        raise ValueError("Choose an export preset")
    return normalize_selection(presets[name])
