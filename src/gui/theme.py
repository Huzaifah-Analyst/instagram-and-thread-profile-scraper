"""Cyber Dark design tokens from ``docs/design.md`` plus display helpers."""

from __future__ import annotations

from typing import Optional

from src.core import records

BG_DARK = "#121214"
BG_SURFACE = "#1A1A1E"
BG_ELEVATED = "#24242A"
BORDER_COLOR = "#33333A"
TEXT_PRIMARY = "#F3F4F6"
TEXT_MUTED = "#9CA3AF"
ACCENT_BLUE = "#3B82F6"
ACCENT_HOVER = "#2563EB"
STATUS_ACTIVE = "#10B981"
STATUS_BANNED = "#EF4444"
STATUS_WARN = "#F59E0B"
STATUS_EMPTY = "#6B7280"

FONT_FAMILY = "Segoe UI"
# CustomTkinter treats sizes as pixels; these approximate the pt scale in design.md.
FONT_H1 = (FONT_FAMILY, 20, "bold")
FONT_SECTION = (FONT_FAMILY, 15, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BADGE = (FONT_FAMILY, 12, "bold")
FONT_CAPTION = (FONT_FAMILY, 11)
# ttk widgets treat positive sizes as points; negative sizes are pixels, matching CTk.
TTK_FONT_BODY = (FONT_FAMILY, -13)
TTK_FONT_HEADING = (FONT_FAMILY, -12, "bold")

MODE_LABELS = {"combined": "Combined", "ig_only": "Instagram Only", "threads_only": "Threads Only"}

WINDOW_SIZE = (1150, 750)
WINDOW_MIN_SIZE = (950, 600)
LEFT_PANEL_WIDTH = 320

# Display status -> (text colour, background colour) for table rows.
STATUS_COLORS: dict[str, tuple[str, str]] = {
    "ACTIVE": ("#34D399", "#064E3B"),
    "BANNED": ("#F87171", "#7F1D1D"),
    "PRIVATE": (STATUS_WARN, "#78350F"),
    "BLOCKED": (STATUS_WARN, "#78350F"),
    "NOT_FOUND": (TEXT_MUTED, BG_ELEVATED),
    "ERROR": (STATUS_EMPTY, BG_ELEVATED),
}


# Kept as GUI-facing names; the logic is shared with the exporters in src/core/records.py.
display_status = records.display_status
cell = records.text_or_missing


def format_duration(seconds: float) -> str:
    """Formats seconds as ``1m 05s`` / ``42s`` for the status bar."""
    seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{secs}s"


def estimate_eta(elapsed: float, done: int, total: int) -> Optional[float]:
    """Estimates remaining seconds from the average time per finished account.

    Returns:
        Remaining seconds, or ``None`` before the first account finishes.
    """
    if done <= 0 or total <= 0:
        return None
    return elapsed / done * max(0, total - done)
