"""Checker-session detection for the persistent browser profile.

Reads Chromium's cookie database (names and expiry only; values stay
encrypted and are never read) to tell whether the profile holds a
non-expired Instagram ``sessionid`` cookie.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

SESSION_CONNECTED = "connected"
SESSION_DISCONNECTED = "disconnected"
SESSION_UNKNOWN = "unknown"

COOKIE_DB_CANDIDATES = (Path("Default") / "Network" / "Cookies", Path("Default") / "Cookies")
_CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _now_chrome_micros() -> int:
    """Current time as Chromium's ``expires_utc`` (microseconds since 1601)."""
    return int((datetime.now(timezone.utc) - _CHROME_EPOCH).total_seconds() * 1_000_000)


def find_cookie_db(profile_dir: Union[str, Path]) -> Optional[Path]:
    """Returns the cookie database path inside a Chromium profile, if present."""
    for candidate in COOKIE_DB_CANDIDATES:
        path = Path(profile_dir) / candidate
        if path.is_file():
            return path
    return None


def check_session(profile_dir: Union[str, Path]) -> tuple[str, Optional[str]]:
    """Checks whether the profile has a live Instagram login.

    Args:
        profile_dir: Chromium user-data dir used by the scraper.

    Returns:
        ``(state, detail)`` where state is ``connected``, ``disconnected`` or
        ``unknown`` (database locked/unreadable, e.g. while a run is active).
    """
    db_path = find_cookie_db(profile_dir)
    if db_path is None:
        return SESSION_DISCONNECTED, "No browser profile yet"

    # Chromium may hold the file open; query a copy so we never lock it.
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "Cookies"
        try:
            shutil.copyfile(db_path, copy)
            conn = sqlite3.connect(copy)
            try:
                row = conn.execute(
                    "SELECT MAX(expires_utc) FROM cookies "
                    "WHERE name = 'sessionid' AND host_key LIKE '%instagram.com'"
                ).fetchone()
            finally:
                conn.close()
        except (OSError, sqlite3.Error) as exc:
            logger.warning("Could not read cookie database %s: %s", db_path, exc)
            return SESSION_UNKNOWN, "Session status unavailable"

    expires = row[0] if row else None
    if expires is None:
        return SESSION_DISCONNECTED, "Not logged in"
    if expires != 0 and expires < _now_chrome_micros():
        return SESSION_DISCONNECTED, "Session expired"
    return SESSION_CONNECTED, "Instagram session found"
