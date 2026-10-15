"""Smart routing, anonymous classification and mode-specific result contracts."""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page, Route

from src.core.anonymous_status import classify_status, check_status, status_record
from src.core.checker_health import verify_context
from src.core.modes import MODE_COMBINED_SMART, MODE_IG_STATUS_ONLY
from src.core.scraper import MultiWorkerScraper, empty_platform_result
from test_accuracy_regressions import run_browser


@pytest.mark.parametrize("country,skipped", [
    ("Canada", True), ("Not shared", False), (" nOt ShArEd ", False),
    (None, False), ("", False), ("   ", False),
])
def test_smart_uses_disclosed_country_only(country: str | None, skipped: bool,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """Reuse disclosure semantics and never invent skipped Threads fields."""
    ig = AsyncMock(return_value={**empty_platform_result(), "status": "active",
                                 "country": country, "date_joined": "April 2016"})
    threads = AsyncMock(return_value={**empty_platform_result(), "status": "active"})
    monkeypatch.setattr("src.core.scraper.extract_instagram", ig)
    monkeypatch.setattr("src.core.scraper.extract_threads", threads)
    scraper = MultiWorkerScraper(mode=MODE_COMBINED_SMART)
    record = asyncio.run(scraper._check_account(object(), "target"))
    ig.assert_awaited_once()
    if skipped:
        threads.assert_not_awaited()
        assert record["threads_status"] == "skipped_ig_sufficient"
        assert record["threads_stage"] == "skipped"
        assert record["data_quality"] == "Complete"
        assert record["error_message"] is None
        assert all(record[field] is None for field in (
            "threads_country", "threads_date_joined", "threads_badge",
        ))
    else:
        threads.assert_awaited_once()


def test_default_combined_still_checks_both(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adding the conditional mode must not silently change Combined."""
    extract = AsyncMock(return_value={**empty_platform_result(), "status": "active",
                                      "country": "Canada"})
    monkeypatch.setattr("src.core.scraper.extract_instagram", extract)
    monkeypatch.setattr("src.core.scraper.extract_threads", extract)
    scraper = MultiWorkerScraper()
    assert scraper.mode == "combined"
    asyncio.run(scraper._check_account(object(), "target"))
    assert extract.await_count == 2


def test_smart_checks_threads_after_ig_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """An IG failure cannot silently suppress the fallback platform."""
    monkeypatch.setattr("src.core.scraper.extract_instagram", AsyncMock(side_effect=ValueError("fixture")))
    threads = AsyncMock(return_value={**empty_platform_result(), "status": "active",
                                     "country": "Canada"})
    monkeypatch.setattr("src.core.scraper.extract_threads", threads)
    record = asyncio.run(MultiWorkerScraper(mode=MODE_COMBINED_SMART)._check_account(object(), "target"))
    threads.assert_awaited_once()
    assert record["threads_country"] == "Canada"


def test_smart_preflight_requires_both_platforms(monkeypatch: pytest.MonkeyPatch) -> None:
    """Potential fallback needs the same verified platform sessions as Combined."""
    verify = AsyncMock(return_value=None)
    monkeypatch.setattr("src.core.checker_health.verify_platform", verify)
    result = asyncio.run(verify_context(SimpleNamespace(pages=[object()]), MODE_COMBINED_SMART))
    assert result == {"ig": None, "threads": None}
    assert [call.args[1] for call in verify.await_args_list] == ["ig", "threads"]


@pytest.mark.parametrize("text,expected", [
    ("Profile isn't available", "not_found"),
    ("Sorry, this page isn't available", "not_found"),
    ("USER NOT FOUND", "not_found"),
    ("This account has been suspended", "suspended"),
    ("Account suspended", "suspended"),
    ("1,234 followers", "active"), ("12.4K Followers", "active"),
    ("Followers\n0", "active"),
    ("1 follower", "active"), ("1 Follower", "active"),
    ("0 followers", "active"), ("1 following", "unknown"),
    ("Log In Sign Up willie 1 follower 3 following", "active"),
    ("", "unknown"), ("Log in to see more", "unknown"),
    ("Instagram profile Follow", "unknown"), ("followers", "unknown"),
    ("123 following", "unknown"),
])
def test_anonymous_classifier_never_guesses(text: str, expected: str) -> None:
    """Only explicit unavailable/suspended/follower-count markers decide."""
    assert classify_status(text) == expected


@pytest.mark.parametrize("status", ["active", "not_found", "suspended", "unknown"])
def test_status_records_keep_unavailable_fields_empty(status: str) -> None:
    """Suspension remains an IG observation, never a fabricated Threads ban."""
    record = status_record("target", status, "fixture reason", .5)
    assert record["ig_status"] == status
    assert record["composite_status"] == status.upper()
    assert record["threads_status"] == "skipped"
    assert record["checker_id"] is None
    assert record["data_quality"] != "Failed"
    for field in ("ig_country", "ig_date_joined", "threads_country",
                  "threads_date_joined", "threads_badge"):
        assert record[field] is None
    if status == "unknown":
        assert record["error_message"] == "fixture reason"
    else:
        assert record["error_message"] is None


def test_real_page_waits_past_prototype_delay() -> None:
    """A page blank at 1.2 seconds can still yield a known status later."""
    async def check(page: Page) -> None:
        """Hydrate a routed fixture after 1.5 seconds without external traffic."""
        async def serve(route: Route) -> None:
            """Serve an initially blank page with a delayed follower count."""
            await route.fulfill(body='''<html><body><script>
              setTimeout(() => document.body.textContent = '123 followers', 1500);
              </script></body></html>''', content_type="text/html")
        await page.route("**/*", serve)
        record = await check_status(page, "target", 4)
        assert record["ig_status"] == "active"
        assert record["seconds"] >= 1.4
    run_browser(check)


def test_real_page_unknown_at_bounded_deadline() -> None:
    """A login wall without a decision marker stays unknown, never not-found."""
    async def check(page: Page) -> None:
        """Poll a fixed ambiguous page through the entire small test budget."""
        await page.route("**/*", lambda route: route.fulfill(
            body="<html><body>Log in to see more</body></html>", content_type="text/html",
        ))
        record = await check_status(page, "target", .4)
        assert record["ig_status"] == "unknown"
        assert .35 <= record["seconds"] < 2
        assert "No decision marker" in record["error_message"]
    run_browser(check)


@pytest.mark.parametrize("mode", [MODE_IG_STATUS_ONLY, MODE_COMBINED_SMART])
def test_cli_forwards_modes_and_anonymous_ignores_checker_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    """No-login CLI works even with invalid checker settings or a checker flag."""
    import src.core.scraper as module

    if mode == MODE_IG_STATUS_ONLY:
        (tmp_path / "checkers.json").write_text("invalid", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scraper", "target", "--mode", mode,
                                    "--profile", str(tmp_path / "profile"), "--checkers", "5"])
    seen: list[MultiWorkerScraper] = []

    def run(scraper: MultiWorkerScraper, users: list[str]) -> list[dict]:
        """Inspect CLI setup without starting a browser."""
        assert users == ["target"]
        seen.append(scraper)
        return []

    monkeypatch.setattr(MultiWorkerScraper, "run", run)
    module.main()
    assert seen[0].mode == mode
    if mode == MODE_IG_STATUS_ONLY:
        assert seen[0].checkers == []


@pytest.mark.parametrize("option", [["--login"], ["--login-checker", "5"]])
def test_anonymous_cli_rejects_login_flags(option: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """An anonymous invocation cannot accidentally enter persistent setup."""
    from src.core.scraper import main

    login = AsyncMock(side_effect=AssertionError("Must never log in"))
    monkeypatch.setattr("src.core.scraper.login_session", login)
    monkeypatch.setattr(sys, "argv", ["scraper", "--mode", MODE_IG_STATUS_ONLY, *option])
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
    login.assert_not_awaited()
