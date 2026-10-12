"""Sequential account setup; completed profiles can subsequently check in parallel."""

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
    """Try every account independently and return a credential-free summary.

    Failed setup windows close so later accounts are not held indefinitely.
    ``keep_manual_open`` is retained for caller compatibility; manual recovery
    is available through each checker's separate Login IG + Threads action.
    """
    if len(accounts) != len(checkers) or not accounts or any(
        account.username != checker.username for account, checker in zip(accounts, checkers)
    ):
        return "Account/profile bindings do not match. Import the file again."
    completed = 0
    verified = {"ig": 0, "threads": 0}
    summaries: list[str] = []
    try:
        async with async_playwright() as pw:
            for account, checker in zip(accounts, checkers):
                if cancel.is_set():
                    break
                progress(f"{checker.checker_id}: opening login browser...")
                context = None
                outcomes: list[str] = []
                ready_platforms: list[str] = []
                try:
                    checker.profile_dir.mkdir(parents=True, exist_ok=True)
                    context = await pw.chromium.launch_persistent_context(
                        str(checker.profile_dir), channel="chromium", headless=headless,
                        viewport={"width": 1280, "height": 800}, locale="en-US",
                    )
                    page = context.pages[0] if context.pages else await context.new_page()
                    for platform in ("ig", "threads"):
                        if cancel.is_set():
                            outcomes.append(f"{platform}: not attempted (cancelled)")
                            continue
                        progress(f"{checker.checker_id}: signing into {platform}...")
                        try:
                            outcome = await login_platform(page, platform, account, cancel)
                        except Exception as exc:
                            outcomes.append(f"{platform}: login failed ({type(exc).__name__})")
                            continue
                        if not outcome.ready:
                            outcomes.append(f"{platform}: {outcome.message}")
                        else:
                            verified[platform] += 1
                            ready_platforms.append(platform)
                        progress(f"{checker.checker_id} {platform}: {outcome.message}")
                    if not outcomes:
                        completed += 1
                except Exception as exc:
                    # Exception messages can contain filled secrets; expose type only.
                    outcomes.append(f"browser setup failed ({type(exc).__name__})")
                finally:
                    if context is not None:
                        try:
                            await context.close()
                        except Exception as exc:
                            progress(f"{checker.checker_id}: browser close failed ({type(exc).__name__}).")
                summary = f"{checker.checker_id}: " + ("; ".join(outcomes) or "IG + Threads verified")
                if outcomes and ready_platforms:
                    summary += "; verified: " + ", ".join(ready_platforms)
                summaries.append(summary)
                progress(summary)
    except Exception as exc:
        summaries.append(f"Browser service unavailable ({type(exc).__name__}).")
    prefix = f"{completed}/{len(accounts)} verified."
    if completed == len(accounts):
        prefix = f"All {completed} accounts verified on Instagram and Threads."
    if cancel.is_set():
        prefix = "Login cancelled. " + prefix
    return (prefix + f" IG {verified['ig']}/{len(accounts)}; "
            f"Threads {verified['threads']}/{len(accounts)}.\n" + "\n".join(summaries))
