"""Unit tests for browser-free helpers in the core engine."""

import pytest

from src.core.extractors import (
    detect_session_challenge,
    is_not_found_page,
    is_private_profile,
    parse_about_dialog,
    split_threads_joined,
)
from src.core.resource_blocker import should_block
from src.core.scraper import build_record, chunk_usernames, clean_usernames, empty_platform_result


# ---- resource blocker (TSK-101) ------------------------------------------- #

@pytest.mark.parametrize("resource_type, url", [
    ("image", "https://scontent.cdninstagram.com/v/t51/abc"),
    ("media", "https://video.cdninstagram.com/clip"),
    ("font", "https://static.cdninstagram.com/font"),
    ("other", "https://cdn.example.com/a/photo.JPG?stp=1"),
    ("other", "https://cdn.example.com/f.woff2"),
])
def test_blocks_heavy_assets(resource_type: str, url: str) -> None:
    assert should_block(resource_type, url)


@pytest.mark.parametrize("resource_type, url", [
    ("document", "https://www.instagram.com/someuser/"),
    ("script", "https://static.cdninstagram.com/rsrc.php/app.js"),
    ("xhr", "https://www.instagram.com/api/graphql"),
    ("fetch", "https://www.threads.com/graphql/query"),
    ("stylesheet", "https://static.cdninstagram.com/styles.css"),
])
def test_allows_essential_requests(resource_type: str, url: str) -> None:
    assert not should_block(resource_type, url)


# ---- extractors parsing (TSK-102 / TSK-103) ------------------------------- #

def test_parse_instagram_about_english() -> None:
    text = "About this account\nusername\nDate joined\nMarch 2015\nAccount based in\nTurkey\nClose"
    assert parse_about_dialog(text) == {"date_joined": "March 2015", "join_badge": None, "country": "Turkey"}


def test_parse_instagram_about_turkish() -> None:
    text = "Bu hesap hakkında\nKatılma tarihi\nEylül 2019\nHesabın bulunduğu konum\nTürkiye"
    parsed = parse_about_dialog(text)
    assert parsed["date_joined"] == "Eylül 2019"
    assert parsed["country"] == "Türkiye"


def test_parse_threads_about_with_badge() -> None:
    text = "Name\nSome User (@someuser)\nJoined\nSeptember 2023 · 100M+\nBased in\nPakistan"
    assert parse_about_dialog(text) == {"date_joined": "September 2023", "join_badge": "100M+", "country": "Pakistan"}


def test_parse_ignores_label_words_inside_values() -> None:
    """A bio line mentioning 'location' must not be treated as a label."""
    text = "Name\nTravel blogger, location independent\nJoined\nJuly 2023"
    assert parse_about_dialog(text)["country"] is None


@pytest.mark.parametrize("raw, expected", [
    ("September 2023 · 100M+", ("September 2023", "100M+")),
    ("#2,345,678 · July 2023", ("July 2023", "#2,345,678")),
    ("July 2023", ("July 2023", None)),
])
def test_split_threads_joined(raw: str, expected: tuple) -> None:
    assert split_threads_joined(raw) == expected


def test_detect_login_redirect() -> None:
    assert detect_session_challenge("https://www.instagram.com/accounts/login/?next=/x/", "")


def test_detect_challenge_text() -> None:
    assert detect_session_challenge("https://www.instagram.com/x/", "Please wait a few minutes before you try again.")


def test_username_containing_login_is_not_a_challenge() -> None:
    """The prototype flagged any URL containing 'login'; a username must not trigger it."""
    assert detect_session_challenge("https://www.instagram.com/loginking/", "loginking 120 posts") is None


def test_not_found_and_private_markers() -> None:
    assert is_not_found_page("Sorry, this page isn't available. The link you followed may be broken.")
    # Current (2026) logged-out Instagram wording.
    assert is_not_found_page("Log in\nProfile isn't available\nThe link may be broken, or the profile may have been removed.")
    assert is_private_profile("This account is private\nFollow to see their photos")
    assert not is_not_found_page("someuser 10 posts")


# ---- dispatcher helpers (TSK-105) ----------------------------------------- #

def test_chunks_100_accounts_into_5_by_20() -> None:
    users = [f"u{i}" for i in range(100)]
    chunks = chunk_usernames(users, 5)
    assert [len(c) for c in chunks] == [20, 20, 20, 20, 20]
    assert sum(chunks, []) == users


def test_chunks_are_balanced_and_never_empty() -> None:
    assert [len(c) for c in chunk_usernames([f"u{i}" for i in range(12)], 5)] == [3, 3, 2, 2, 2]
    assert chunk_usernames(["a", "b"], 5) == [["a"], ["b"]]
    assert chunk_usernames([], 5) == []


def test_chunk_rejects_zero_workers() -> None:
    with pytest.raises(ValueError):
        chunk_usernames(["a"], 0)


def test_clean_usernames() -> None:
    assert clean_usernames([" @Alice ", "bob", "", "alice", "bob\n"]) == ["Alice", "bob"]


def test_scraper_defaults_match_extractor_timeouts(tmp_path) -> None:
    """Defaults stay the current extractor budgets; see ISSUE_concurrent_session_detection.md."""
    from src.core import extractors
    from src.core.scraper import MultiWorkerScraper

    scraper = MultiWorkerScraper(profile_dir=tmp_path)
    assert scraper.page_ready_timeout_s == extractors.PAGE_READY_TIMEOUT_S
    assert scraper.dialog_timeout_s == extractors.DIALOG_TIMEOUT_S
    assert scraper.menu_click_timeout_s == extractors.MENU_CLICK_TIMEOUT_S


def test_scraper_timeouts_are_configurable_without_a_code_change(tmp_path) -> None:
    """Huzaifah must be able to widen timeouts for a concurrent-load test via a constructor arg."""
    from src.core.scraper import MultiWorkerScraper

    scraper = MultiWorkerScraper(profile_dir=tmp_path, page_ready_timeout_s=16.0,
                                 dialog_timeout_s=16.0, menu_click_timeout_s=8.0)
    assert (scraper.page_ready_timeout_s, scraper.dialog_timeout_s, scraper.menu_click_timeout_s) == (16.0, 16.0, 8.0)


def test_build_record_links_ban_and_joins_errors() -> None:
    ig = {**empty_platform_result(), "status": "active", "country": "Turkey"}
    threads = {**empty_platform_result(), "status": "suspended", "error": "x"}
    record = build_record("someuser", ig, threads, 3.14159)
    assert record["composite_status"] == "BANNED"
    assert record["ig_status"] == record["threads_status"] == "banned"
    assert record["ig_country"] == "Turkey"
    assert record["error_message"] == "x"
    assert record["seconds"] == 3.14
