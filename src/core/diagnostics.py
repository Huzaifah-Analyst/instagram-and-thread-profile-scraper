"""Opt-in page evidence and persistent per-run records, without cookie dumps."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from src.core.paths import DEBUG_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)


async def capture_page(page: Page, platform: str, username: str, stage: str) -> str:
    """Save visible text, screenshot and stage metadata without full HTML."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", username)
    prefix = DEBUG_DIR / f"{platform}_{safe_name}_{stage}_{stamp}"
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        Path(str(prefix) + ".txt").write_text(
            await page.inner_text("body", timeout=1500), encoding="utf-8"
        )
        await page.screenshot(path=str(prefix) + ".png", timeout=3000)
        Path(str(prefix) + ".json").write_text(json.dumps({
            "platform": platform, "username": username, "stage": stage,
            "url": page.url, "captured_utc": stamp,
        }, indent=2), encoding="utf-8")
        return str(prefix) + ".json"
    except (OSError, PlaywrightError) as exc:
        logger.warning("Cannot capture %s/%s at %s: %s", platform, username, stage, exc)
        return ""


class RunJournal:
    """Persist each completed row immediately so a failed run remains reviewable."""

    def __init__(self, directory: Path = RESULTS_DIR) -> None:
        """Reserve a unique local journal path; no account secrets are stored."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        self.path = directory / f"run_{stamp}.jsonl"

    def append(self, record: dict) -> None:
        """Append a JSON event or raise an actionable persistence failure."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
