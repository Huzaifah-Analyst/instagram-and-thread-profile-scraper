"""Tests for the concurrency-investigation knobs in the extractors."""

from typing import Iterator

import pytest

from src.core import extractors


@pytest.fixture(autouse=True)
def reset_diagnostics() -> Iterator[None]:
    """Restores default settings so other tests are unaffected."""
    yield
    extractors.DIAGNOSTICS.timeout_scale = 1.0
    extractors.DIAGNOSTICS.debug_dir = None


def test_default_budgets_unchanged() -> None:
    assert extractors._budget(extractors.PAGE_READY_TIMEOUT_S) == 8.0
    assert extractors._budget(extractors.MENU_TIMEOUT_S) == 4.0
    assert extractors._budget(extractors.DIALOG_TIMEOUT_S) == 8.0


def test_timeout_scale_doubles_every_budget() -> None:
    extractors.DIAGNOSTICS.timeout_scale = 2.0
    assert extractors._budget(extractors.PAGE_READY_TIMEOUT_S) == 16.0
    assert extractors._budget(extractors.MENU_TIMEOUT_S) == 8.0
    assert extractors._budget(extractors.DIALOG_TIMEOUT_S) == 16.0
