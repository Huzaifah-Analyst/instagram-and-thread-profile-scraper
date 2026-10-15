"""Regression tests for per-field benchmark disclosure accounting."""

import importlib.util
from pathlib import Path


def test_withheld_country_does_not_hide_missing_date_or_badge() -> None:
    """Literal Not shared is withheld; date/badge failures stay failures."""
    script = Path(__file__).resolve().parents[1] / "debug" / "round7_analyze.py"
    spec = importlib.util.spec_from_file_location("benchmark_analysis", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    row = {"username": "fixture", "threads_status": "active",
           "threads_country": "Not shared", "threads_country_availability": "not_shared"}
    result = module.aggregate([row], 10)
    assert result["fields"]["threads_country"] == {"platform-withheld": 1}
    assert result["fields"]["threads_date_joined"] == {"extraction-failed": 1}
    assert result["fields"]["threads_badge"] == {"extraction-failed": 1}
    assert result["fields"]["ig_country"] == {"not-checked": 1}
    assert not result["meets_300_seconds"]  # A smaller sample is not acceptance.


def test_intentionally_unrequested_fields_are_not_extraction_failures() -> None:
    """Mode omissions must remain distinguishable in offline benchmark analysis."""
    script = Path(__file__).resolve().parents[1] / "debug" / "round7_analyze.py"
    spec = importlib.util.spec_from_file_location("benchmark_analysis_modes", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    smart = {"threads_status": "skipped_ig_sufficient"}
    assert module.field_state(smart, "threads_country", "threads") == "not-checked"
    anonymous = {"checking_mode": "ig_status_only", "ig_status": "active"}
    assert module.field_state(anonymous, "ig_country", "ig") == "unavailable-in-mode"
