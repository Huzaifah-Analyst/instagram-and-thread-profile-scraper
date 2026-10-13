"""Playwright network resource blocker (TSK-101).

Aborts heavy media and font downloads so each profile page loads with only
HTML, JavaScript, CSS and XHR/Fetch/GraphQL traffic. CSS is kept on purpose:
the Threads extractor relies on real element positions (bounding boxes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import Page, Request
from playwright.async_api import Error as PlaywrightError

logger = logging.getLogger(__name__)

BLOCKED_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".ico",
    ".mp4", ".webm", ".m4s", ".mp3",
    ".woff", ".woff2", ".ttf", ".otf",
)
BLOCKED_RESOURCE_TYPES = frozenset({"image", "media", "font"})


@dataclass
class BlockerStats:
    """Counters for verifying the blocker (TSK-101 acceptance check)."""

    blocked: int = 0
    allowed: int = 0


def should_block(resource_type: str, url: str) -> bool:
    """Decides whether a request is a heavy asset that should be aborted.

    Args:
        resource_type: Playwright ``request.resource_type`` (e.g. ``image``, ``xhr``).
        url: Full request URL.

    Returns:
        ``True`` if the request should be aborted.
    """
    if resource_type in BLOCKED_RESOURCE_TYPES:
        return True
    path = urlparse(url).path.lower()
    return path.endswith(BLOCKED_EXTENSIONS)


async def attach_resource_blocker(target: Page) -> BlockerStats:
    """Block heavy Chromium resources without routing critical requests.

    Playwright's wildcard page routing disables HTTP cache and intercepts every
    document/script/API request. CDP Fetch patterns instead pause only heavy
    resource types and Other requests needing the extension fallback. They leave
    document, stylesheet, script, XHR and Fetch traffic on the native path.
    """
    stats = BlockerStats()
    session = await target.context.new_cdp_session(target)
    intercepted = {"Image", "Media", "Font", "Other"}

    async def paused(event: dict) -> None:
        """Abort selected heavy assets and release other paused requests."""
        resource_type = event.get("resourceType", "Other").lower()
        blocked = should_block(resource_type, event["request"]["url"])
        try:
            if blocked:
                await session.send("Fetch.failRequest", {
                    "requestId": event["requestId"], "errorReason": "Aborted",
                })
                stats.blocked += 1
            else:
                await session.send("Fetch.continueRequest", {
                    "requestId": event["requestId"],
                })
        except PlaywrightError as exc:
            logger.debug("Resource request ended before handling: %s", exc)

    def observed(request: Request) -> None:
        """Count allowed requests without intercepting critical traffic."""
        if (request.resource_type.capitalize() not in intercepted
                or not should_block(request.resource_type, request.url)):
            stats.allowed += 1

    session.on("Fetch.requestPaused", paused)
    await session.send("Fetch.enable", {"patterns": [
        {"resourceType": resource_type, "requestStage": "Request"}
        for resource_type in sorted(intercepted)
    ]})
    target.on("request", observed)
    logger.debug("Selective Chromium resource blocker attached to page")
    return stats
