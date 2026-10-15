# PyInstaller spec for MetaInspector Desktop (TSK-501).
#
# Build from the repo root with:
#   pyinstaller config/metainspector.spec --distpath dist --workpath build
#
# This bundles Playwright's own Chromium build (not "playwright install" run
# on the client's machine) so the packaged .exe works on a bare Windows box.
# See docs/memory.md's Sprint 5 entry for the measured output size against
# the <150MB target in docs/PRD.md NFR-3 -- bundling a full Chromium browser
# makes that target unreachable; this file documents what was tried, it does
# not claim to hit it.

import os
from pathlib import Path

import playwright

block_cipher = None

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))) if "SPEC" in dir() \
    else Path.cwd()

PLAYWRIGHT_DRIVER_DIR = Path(playwright.__file__).resolve().parent / "driver"
# Only chromium: the app never launches ffmpeg, the headless-shell variant or winldd.
MS_PLAYWRIGHT_CACHE = Path(os.path.expanduser(r"~\AppData\Local\ms-playwright"))
CHROMIUM_DIRS = sorted(MS_PLAYWRIGHT_CACHE.glob("chromium-*"))
if not CHROMIUM_DIRS:
    raise SystemExit(
        "No Chromium build found under %s -- run `python -m playwright install chromium` first."
        % MS_PLAYWRIGHT_CACHE
    )
CHROMIUM_DIR = CHROMIUM_DIRS[-1]

datas = [
    (str(PLAYWRIGHT_DRIVER_DIR), "playwright/driver"),
    (str(CHROMIUM_DIR), f"ms-playwright/{CHROMIUM_DIR.name}"),
]

a = Analysis(
    [str(REPO_ROOT / "main.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "playwright.async_api",
        "pandas",
        "openpyxl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MetaInspectorDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
