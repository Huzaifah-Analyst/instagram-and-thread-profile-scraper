"""Input validation shared by CLI, GUI and the dispatcher."""

import math
import re
from urllib.parse import urlparse


def positive_seconds(value: float) -> float:
    """Reject non-finite, nonpositive or excessive user-supplied budgets."""
    number = float(value)
    if not math.isfinite(number) or not 0 < number <= 120:
        raise ValueError("Timeouts must be finite numbers between 0 and 120 seconds.")
    return number


def clean_usernames(raw: list[str]) -> list[str]:
    """Normalize supported profile URLs; reject invalid handles, deduplicate."""
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        name = item.strip().lstrip("\ufeff")
        if not name:
            continue
        if "://" in name:
            url = urlparse(name)
            parts = url.path.strip("/").split("/")
            if url.scheme not in {"http", "https"} or url.hostname not in {
                "instagram.com", "www.instagram.com", "threads.com",
                "www.threads.com", "threads.net", "www.threads.net",
            } or len(parts) != 1:
                raise ValueError("Use an Instagram/Threads profile URL or username.")
            name = parts[0]
        name = name.lstrip("@").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.]{1,30}", name):
            raise ValueError("Usernames must contain 1–30 letters, digits, dots or underscores.")
        if name.casefold() not in seen:
            seen.add(name.casefold())
            result.append(name)
    return result
