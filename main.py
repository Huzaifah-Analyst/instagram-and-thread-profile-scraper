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
    """Makes the frozen .exe use its bundled Chromium instead of the system cache.

    Bug fixed 2026-10-10 (live test): a **onefile** PyInstaller build (which is
    what ``config/metainspector.spec`` produces) extracts bundled data files
    to a temp directory at ``sys._MEIPASS`` at runtime, not next to the .exe
    itself -- ``Path(sys.executable).parent`` is just the folder the .exe was
    launched from (e.g. ``dist/``), which never contains the bundled
    ``ms-playwright`` folder. The original version only checked that second
    path, so it silently never set ``PLAYWRIGHT_BROWSERS_PATH``, and
    Playwright fell back to its own default (unbundled) browser path,
    producing "Executable doesn't exist at ...\\_MEI.../playwright/driver/
    package/.local-browsers/chromium-1243/...". Checking ``sys._MEIPASS``
    first fixes the onefile case; the ``sys.executable``-parent check stays
    as a fallback in case this is ever built ``--onedir`` instead.
    """
    if not getattr(sys, "frozen", False):
        return
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "ms-playwright")
    candidates.append(Path(sys.executable).resolve().parent / "ms-playwright")
    for bundled in candidates:
        if bundled.is_dir():
            import os

            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)
            return


if __name__ == "__main__":
    _point_playwright_at_bundled_browsers()
    from src.gui.app import main

    main()
