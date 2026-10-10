"""MetaInspector Desktop entry point: ``python main.py`` (or the packaged .exe).

TSK-501: when PyInstaller freezes this into a standalone executable, the
Chromium build Playwright needs is bundled alongside it (see
``config/metainspector.spec``) instead of expecting ``playwright install`` to
have been run on the client's machine. Playwright discovers browsers under
``PLAYWRIGHT_BROWSERS_PATH``, so that variable must be pointed at the bundled
copy before ``playwright`` is imported anywhere (including transitively via
``src.gui.app``) -- hence this runs before that import.
"""

import sys
from pathlib import Path


def _point_playwright_at_bundled_browsers() -> None:
    """Makes the frozen .exe use its bundled Chromium instead of the system cache."""
    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).resolve().parent / "ms-playwright"
        if bundled.is_dir():
            import os

            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)


if __name__ == "__main__":
    _point_playwright_at_bundled_browsers()
    from src.gui.app import main

    main()
