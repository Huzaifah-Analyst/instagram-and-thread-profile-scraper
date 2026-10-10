"""Pure, exact-label transparency parsing and page classification."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

# Label lines in the transparency dialogs (compared lower-cased, exact line).
DATE_KEYS = ("date joined", "joined", "date of creation", "katılma tarihi")
COUNTRY_KEYS = (
    "account based in", "based in", "account location", "location",
    "hesabın bulunduğu konum", "konum",
)

ABOUT_IG_TEXTS = ("About this account", "About this profile", "Bu hesap hakkında")
ABOUT_THREADS_TEXTS = ("About this profile", "Bu profil hakkında")

NOT_FOUND_MARKERS = (
    "sorry, this page isn't available",
    "this page isn't available",
    "profile isn't available",
    "the profile may have been removed",
    "üzgünüz, bu sayfaya ulaşılamıyor",
    "profil kullanılamıyor",
    "sayfa bulunamadı",
    "sayfa kullanılamıyor",
)
PRIVATE_MARKERS = ("this account is private", "bu hesap gizli")
CHALLENGE_PATH_PREFIXES = ("/accounts/login", "/login", "/challenge", "/checkpoint", "/auth_platform")
CHALLENGE_MARKERS = (
    "suspicious activity",
    "please wait a few minutes before you try again",
    "we restrict certain activity",
    "help us confirm it's you",
    "confirm you're a human",
    "hesabın geçici olarak kilitlendi",
    "olağan dışı hareket",
)

_BADGE_RE = re.compile(r"^(#\s?[\d.,]+|[\d.,]+\s?[KMB]\+?)$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Pure parsing helpers
# --------------------------------------------------------------------------- #

def detect_session_challenge(url: str, body_text: str) -> Optional[str]:
    """Detects a login wall, checkpoint or rate-limit page on the checker session.

    Args:
        url: Current page URL.
        body_text: Visible body text of the page.

    Returns:
        A reason string if a challenge was detected, otherwise ``None``.
    """
    path = urlparse(url).path.lower().rstrip("/")
    # Match whole path segments so a username like "loginking" is not a login page.
    if any(path == p or path.startswith(p + "/") for p in CHALLENGE_PATH_PREFIXES):
        return f"Redirected to {url}"
    lowered = body_text.lower()
    lines = {line.strip().casefold() for line in body_text.splitlines()}
    if "log in or sign up for threads" in lines:
        return "Threads login required"
    if {"log in", "sign up"}.issubset(lines):
        return "Instagram login required"
    for marker in CHALLENGE_MARKERS:
        if marker in lowered:
            return f"Challenge text detected: '{marker}'"
    return None


def is_not_found_page(body_text: str) -> bool:
    """Returns ``True`` if the body shows Meta's "page isn't available" error."""
    lowered = body_text.lower()
    return any(marker in lowered for marker in NOT_FOUND_MARKERS)


def is_private_profile(body_text: str) -> bool:
    """Returns ``True`` if the Instagram body shows the private-account notice."""
    lowered = body_text.lower()
    return any(marker in lowered for marker in PRIVATE_MARKERS)


def _value_after_label(lines: list[str], keys: tuple[str, ...]) -> Optional[str]:
    """Finds the first line equal to one of ``keys`` and returns the next line."""
    for idx, line in enumerate(lines[:-1]):
        if line.lower() in keys:
            value = lines[idx + 1]
            if value.lower() not in DATE_KEYS + COUNTRY_KEYS + ("close", "name"):
                return value
    return None


def split_threads_joined(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Splits a Threads "Joined" value like ``September 2023 · 100M+``.

    Args:
        raw: Raw value text below the "Joined" label.

    Returns:
        Tuple of ``(date_joined, join_badge)``; either may be ``None``.
    """
    parts = [p.strip() for p in raw.split("·") if p.strip()]
    date_joined: Optional[str] = None
    badge: Optional[str] = None
    for part in parts:
        if badge is None and _BADGE_RE.match(part):
            badge = part
        elif date_joined is None:
            date_joined = part
    return date_joined, badge


def parse_about_dialog(text: str) -> dict:
    """Parses transparency dialog text into joined date, badge and country.

    Works for both the Instagram "About this account" dialog and the Threads
    "About this profile" panel, in English and Turkish.

    Args:
        text: ``inner_text`` of the dialog.

    Returns:
        Dict with ``date_joined``, ``join_badge`` and ``country`` (``None`` if missing).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    raw_date = _value_after_label(lines, DATE_KEYS)
    country = _value_after_label(lines, COUNTRY_KEYS)
    date_joined, badge = split_threads_joined(raw_date) if raw_date else (None, None)
    return {"date_joined": date_joined, "join_badge": badge, "country": country}


def has_username(text: str, username: str) -> bool:
    """Match a complete identity line or an explicit parenthesized handle."""
    wanted = username.casefold().lstrip("@")
    return any(
        line.strip().casefold().lstrip("@") == wanted
        or f"(@{wanted})" in line.casefold()
        for line in text.splitlines()
    )


def country_is_disclosed(value: Optional[str]) -> bool:
    """Separate the live-observed 'Not shared' disclosure from a country value."""
    return bool(value and value.strip().casefold() != "not shared")
