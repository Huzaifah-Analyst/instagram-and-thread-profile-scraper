"""Sequential account setup; completed profiles can subsequently check in parallel."""

import asyncio
import threading
from collections.abc import Callable

from playwright.async_api import async_playwright

from src.core.checkers import Checker
from src.core.credentials import AccountCredential
from src.core.login_flow import login_platform


async def login_accounts(
    accounts: list[AccountCredential], checkers: list[Checker],
    cancel: threading.Event, progress: Callable[[str], None],
    headless: bool = False, keep_manual_open: bool = True,
) -> str:
    """Set up both platforms, halt at first failure and never log credentials."""
    if len(accounts) != len(checkers) or not accounts or any(
        account.username != checker.username for account, checker in zip(accounts, checkers)
    ):
        return "Account/profile bindings do not match. Import the file again."
    completed = 0
    try:
        async with async_playwright() as pw:
            for account, checker in zip(accounts, checkers):
                if cancel.is_set():
                    return f"Login cancelled; {completed}/{len(accounts)} accounts verified."
                progress(f"{checker.checker_id}: opening login browser...")
                checker.profile_dir.mkdir(parents=True, exist_ok=True)
                context = await pw.chromium.launch_persistent_context(
                    str(checker.profile_dir), channel="chromium", headless=headless,
                    viewport={"width": 1280, "height": 800}, locale="en-US",
                )
                closed = asyncio.Event()
                context.on("close", lambda _context: closed.set())
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    for platform in ("ig", "threads"):
                        progress(f"{checker.checker_id}: signing into {platform}...")
                        outcome = await login_platform(page, platform, account, cancel)
                        if not outcome.ready:
                            message = f"{checker.checker_id} {platform}: {outcome.message}"
                            progress(message)
                            if keep_manual_open and not headless and not cancel.is_set() and not closed.is_set():
                                progress(message + " Finish manually, close browser, then import again to resume.")
                                while not closed.is_set() and not cancel.is_set():
                                    await asyncio.sleep(.25)
                            return f"{completed}/{len(accounts)} verified. {message} Import again to resume."
                    completed += 1
                    progress(f"{checker.checker_id}: Instagram and Threads verified ({completed}/{len(accounts)}).")
                finally:
                    await context.close()
    except Exception:  # Never return Playwright exception text containing filled secrets.
        return f"Login browser failed or is already open; {completed}/{len(accounts)} verified. Close it and retry Setup."
    return f"All {completed} accounts verified on Instagram and Threads. Ready to check targets."
