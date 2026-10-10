"""Stable writable application data paths for source and frozen builds."""

import os
import sys
from pathlib import Path


def data_root() -> Path:
    """Keep frozen login state outside PyInstaller's temporary extraction."""
    if getattr(sys, "frozen", False):
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MetaInspector"
    return Path(__file__).resolve().parents[2]


DEFAULT_PROFILE_DIR = data_root() / "browser_profile"
DEBUG_DIR = data_root() / "debug"
RESULTS_DIR = data_root() / "results"
