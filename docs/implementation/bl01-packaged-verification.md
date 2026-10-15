# BL-01 packaged executable verification

15 October 2026. Branch `feature/targeted-check-modes`, following `8e4b066`.
D1/D2/D3 were committed before packaging and their 278-test suite was green.
No merge into dev or branch deletion. No dist/build files are committed.

## Build and fix

Built from the repository root with:

```text
pyinstaller config/metainspector.spec --distpath dist --workpath build
```

The first rebuild launched, but actual inspection at 150 percent Windows
scaling found the username input collapsed and Start clipped below the panel.
Changed the left panel to a scrollable frame with a retained input height.
Rebuilt again and repeated verification against the final artifact. The final
GUI allows entry at the top and scrolling to Start/Pause/Stop at the bottom.
The output popup was moved upward by its title bar equivalent to expose its
bottom buttons; the Quick Start explains this on smaller displays. Windows
taskbar overlap was avoided by resizing the main window into the work area.

Final executable: `dist/MetaInspectorDesktop.exe`.

- Size: **325,044,156 bytes**.
- SHA256: `e7a8c13b7b3c94fcfd79534d13d0e9a92cd86f506b72b74aca2285229cf68247`.
- Final build log reports EXE creation and Build complete. Build logs remain
  local under `debug/packaging-build-final.txt`.
- The command's first approval review timed out before execution. One retry
  succeeded; there was no build failure concealed by that timeout.

## Seven actual EXE checks

| BL-01 check | Result | Observation |
| --- | --- | --- |
| 1. Launch, stay open, checker header | PASS | Actual rebuilt EXE stayed open through setup, two runs and exports, and launched again after restart. Fresh data showed 0/1 saved IG logins; after session setup it showed 1/1 with live check on Start. |
| 2. Setup and bundled Chromium | PASS | Clicked Setup Checker Account, saw a real Instagram Chromium window and feed. Closed it, then saw the sequential Threads window and feed. EXE reported Both logins verified, with each platform live verified. Windows process inspection resolved chrome.exe under the onefile `_MEI.../ms-playwright/chromium-1243/chrome-win64` payload, not the installed development browser cache. |
| 3. Five selectable modes | PASS | Combined was selected by default. Clicked Instagram Only, Threads Only, Smart Combined and IG Status Only. Each radio selected; anonymous mode changed the header to no login needed and disabled setup. All five labels were visible. |
| 4. Anonymous status batch | PASS | Before adding any checker session, ran 2 targets from the EXE: 2 Active / Status only, zero errors, 10.98s saved runtime. No active checker, no country/date, no Threads metadata. This exercises the packaged nonpersistent chromium.launch path. |
| 5. Smart Combined batch | PASS | With the verified Checker 5 session, 2 targets returned in 12.89s: 2 Complete, real IG country and joined date, 2 deliberate Threads skips, zero errors. Raw skipped country/date/badge values were all None and stage was skipped. |
| 6. Copy, CSV, Excel, history, selector | PASS | Used Select all, unticked IG Country, clicked OK, and copied 13 selected headers plus 2 rows. Saved actual CSV and XLSX through native dialogs. TSV/CSV/XLSX contents matched exactly; Error cells were empty and Data Quality was Complete. History opened both runs; selected/re-copied the older anonymous run and verified its 2 Status only rows. After EXE restart, selection persisted and both runs reopened in history. |
| 7. File size | PASS / size recorded | Actual final file is 325,044,156 bytes. This measurement does not meet the original under-150-MB NFR-3 target; that deviation is explicit in PRD and TSK-501 remains open. |

The live samples used default settings: five-worker selection, default
timeouts/pacing, blocker enabled, debug capture checkbox off. Two targets
allow at most two concurrent target pages. Timings come from the actual EXE's
saved GUI history, include its run startup/preflight, and are not projections
to a larger list. No tests or another live batch ran alongside either sample.

Anonymous verification used an initially empty isolated app-data directory.
Only after it finished was Checker 5's existing profile copied locally for
setup and Smart verification. Nonessential cache paths were excluded after
Windows path-length errors interrupted the first copy. No login credentials
were imported, no new passwords/TOTP submitted, and checkers 1-4 were neither
opened nor logged into. Source profiles were not modified by these EXE runs.

Windows input and screenshots drove the actual executable as an external
process. No app code was injected, callbacks replaced or responses mocked.
Raw captures, sessions and result records remain local under the ignored
`debug/packaged-runtime` and `debug/packaged-*` paths.

## Tests, documentation and evidence

- Actual Tk layout/output target: **12 passed in 17.87s**.
  [Output](evidence/packaging-gui-tests.txt).
- Complete suite after layout change: **279 passed in 69.20s**, zero skips.
  [Output](evidence/packaging-full-tests.txt).
- Added a real-Tk minimum-window regression: input retains usable height,
  usernames can be entered and scrolling exposes Start/Pause/Stop completely.
- [Aggregate live/artifact evidence](evidence/packaged-live-summary.json) and
  [actual selected-export parity](evidence/packaged-export-summary.json).
- Rechecked file import through the actual EXE: the selected text file loaded
  two usernames and the count updated to two without starting another batch.
- [Quick Start](../QUICK_START.md) now covers five modes, real Setup versus
  Manage behavior, field omissions, output selection and an actual UI-only
  screenshot. Pause/stop, secret-file import and exceptional troubleshooting
  instructions were cross-checked against source/tests; those paths were not
  newly exercised live in this packaging task.
- PRD now records the client-accepted 6 to 7 minutes, implemented TOTP scope
  and the size deviation. Task statuses cite code/tests or recorded evidence.

Targeted source audit found 43 production files, largest 432 lines, and no
supplied credential matches in candidate files. Changed Python functions have
type annotations/docstrings, changed text has no forbidden dash characters,
and all changed text files are below 500 lines. This is not a full security audit.

## Unverified limits and size deviation

**BL-02 was not run: a second physical Windows machine without Python and
Playwright is unavailable.** This was the development Windows machine, with
an isolated data folder, not a clean-machine simulation. TSK-502 and BL-02
remain unchecked. [Operator checklist](bl02-clean-machine-checklist.md) covers
the actual bare-Windows procedure and first-launch SmartScreen behavior.
SmartScreen was not triggered or bypassed during these tests.

No fresh 95/100-target benchmark ran. The 225.2s Smart, 596.3s Combined and
62.4s anonymous figures in the guide belong to the independent Round 11
95-target review. The older 410.5s afternoon Combined figure was for 100
targets; it must not be labelled a controlled same-list pair with the 95-target
near-midnight run. No runtime guarantee or full-list accuracy claim is made.
The two previously reported anonymous render-deadline misses were not retested.
This sample exercised skips, not the live Smart Threads fallback.

Installed Chromium measured **452,900,525 bytes**, about 432 MiB (historically
described as roughly 433 MB), before driver/Python dependencies. The rebuilt
full-browser bundle exceeds 150 MB. Shipping without a bundled browser and
requiring `playwright install chromium` was rejected because delivery requires
a bare-Windows install. The final artifact remains local and excluded by
`.gitignore` rules for both `dist/` and `build/`.

Clipboard data was inspected locally; an online Google Sheets paste and
opening Excel itself were not performed. Actual generated CSV/XLSX files were
read and compared independently. Other physical display configurations and
Windows versions still require acceptance; TSK-404 remains open for that matrix.
