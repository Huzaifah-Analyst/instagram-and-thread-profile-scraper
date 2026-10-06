"""Playwright network resource blocker (TSK-101).

Aborts heavy media and font downloads so each profile page loads with only
HTML, JavaScript, CSS and XHR/Fetch/GraphQL traffic. CSS is kept on purpose:
the Threads extractor relies on real element positions (bounding boxes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page, Route
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


async def attach_resource_blocker(target: Union[Page, BrowserContext]) -> BlockerStats:
    """Registers a route handler that aborts images, media and fonts.

    Args:
        target: A Playwright page or browser context.

    Returns:
        A live ``BlockerStats`` object updated as requests flow.
    """
    stats = BlockerStats()

    async def _handle(route: Route) -> None:
        request = route.request
        try:
            if should_block(request.resource_type, request.url):
                stats.blocked += 1
                await route.abort()
            else:
                stats.allowed += 1
                await route.continue_()
        except PlaywrightError as exc:
            # Happens when the page navigates or closes mid-request.
            logger.debug("Route already handled for %s: %s", request.url, exc)

    await target.route("**/*", _handle)
    logger.debug("Resource blocker attached to %s", type(target).__name__)
    return stats
