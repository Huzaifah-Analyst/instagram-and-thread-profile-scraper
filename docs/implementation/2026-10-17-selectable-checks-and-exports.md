# Selectable checks and exports: shared implementation report

Date: **17 October 2026**. Branch: `feature/selectable-checks-and-exports`,
based on `85dd8ec`. This file is the shared Codex/Claude handover in the
repository. No merge into dev, branch deletion or remote push was performed.

## What was requested and implemented

The reference picture called for independent checks instead of choosing an
entire fixed workflow. The user also confirmed both meanings of live export:
export Alive accounts only and export completed results during an active run.

| Check | Work performed |
| --- | --- |
| IG Alive | IG status; alone it uses the existing anonymous checker with no login. |
| Threads Alive | Threads profile status/identity, stopping before About. |
| IG + Threads Alive | Shortcut controlling both Alive boxes; no duplicate requests. |
| IG Country | IG identity plus the transparency panel's country field. |
| Threads Country | Threads identity plus the transparency panel's country field. |
| IG Age (joined date) | IG identity plus reported joined month/year. |
| Threads Age (joined date) | Threads identity plus reported joined month/year; badge retained when available. |

Age is the reported joined date, not an invented exact account age. Country
and date share a panel, so the page can render both, but only requested
metadata is retained. Profile status must still be read to validate a
country/date request. Fields excluded by custom scope display Not checked.

All 63 nonempty combinations of the six independent flags are covered by
tests. Empty or unknown selections are rejected before a run can clear prior
results. Run controls freeze the checkboxes during active work. The Alive
shortcut and individual boxes stay synchronized.

Existing five modes remain presets. Combined remains the startup default.
Selecting a preset resets the field boxes; a checkbox edit requests explicit
custom scope. Smart Combined's conditional Threads skip is preserved when
that preset is used, whereas custom scope visits each selected platform.
Only IG Alive alone needs no login. Other choices retain existing session
verification, pacing, worker limits and challenge-stop behavior. The picture's
Turbo/0.01-second/10-worker settings were not introduced as new defaults.

## Export behavior

- Select Output has Full export, Alive/status only, Country only,
  Age/joined only and Checked fields presets. Individual columns remain
  optional except existing identity/fallback rules. OK saves; Cancel discards
  the draft. Column preferences continue to persist after restart.
- Checked fields uses the results' recorded selection, falling back to the
  panel if no results exist. Full export means all supported columns of data
  already collected; it does not perform extra scraping.
- Copy/export rows offers All results, IG Alive only, Threads Alive only
  and Both Alive only. Explicit active/private qualifies; Unknown, skipped,
  error and not-found states do not. A Smart skip cannot establish Threads
  Alive. Filters use per-platform status, not the overall ACTIVE label.
- Copy, CSV and Excel use the same column selection and row filter. With no
  matching rows, the GUI explains why and does not create an empty file.
- Once a finished row exists, these actions work during a run. Each action
  takes an independent snapshot of completed rows and leaves the batch
  running. Later arrivals are not appended to an already saved file. This is
  live snapshot export, not continuous file streaming.
- History retains full records, including requested checks, and has its own
  Alive row filter. Existing raw export values and formula protection remain.

The checking selection remains for the current app session; mode presets are
restored on a fresh launch. Export column preferences retain their existing
persistence. User Manual and Quick Start describe both selection steps.

## Implementation map for the next reviewer

| File | Responsibility |
| --- | --- |
| `src/core/check_plan.py` | Canonical flags, validation, session mode, metadata scope and requested-data quality. |
| `src/core/selected_checks.py` | Dispatch selected platforms with exact required fields; preserve explicit failures. |
| `src/core/scraper.py` | Optional `checks` API and CLI forwarding; legacy behavior when absent. |
| `src/core/extractors.py`, `dialogs.py` | Status-only early return; wait only for requested transparency fields. |
| `src/gui/components/check_selection.py`, `left_panel.py`, `app.py` | Screenshot-inspired cards, preset synchronization, validation and factory wiring. |
| `src/core/export_selection.py` | Export field presets and snapshot/Alive row filtering. |
| GUI output dialog/actions/status bar/history | Real controls for the shared export behavior. |
| `data_table.py` | Explain metadata intentionally excluded by custom scope. |

Records add `requested_checks` for explicit selections. Unselected metadata
stays None, with country availability `not_requested`. Quality is graded
against requested fields; withheld requested country stays Partial and real
read failures retain Error. Existing presets without explicit checks retain
their original record builder and grading.

CLI example using the same selection planner:

```text
python -m src.core.scraper --file targets.txt --checks ig_alive,ig_country
```

Supported IDs: `ig_alive`, `threads_alive`, `ig_country`, `threads_country`,
`ig_age`, `threads_age`. No new browser concurrency or pacing defaults.

## Verification performed

- Complete suite: **427 passed in 101.57s, zero skips**. This includes the
  earlier 339 cases plus 88 new cases, with existing assertions retained.
- Tests cover all combinations, exact platform/field dispatch, masking
  incidental panel data, no About work for status-only requests, incomplete
  withheld/failing fields, and correct metadata display.
- A real Chromium fixture verifies a joined-date-only request returns
  without waiting for an unrequested country. It serves local fixture
  content, not a live Meta profile or speed benchmark.
- Actual Tk tests verify checkbox/factory wiring, disabled controls,
  empty-selection preservation of earlier results, Alive shortcuts, preset
  application/cancel, clipboard output, filtered history, and no empty file
  when no rows match.
- A real GUI bridge test holds its second fixture target, then copies and
  exports the first completed row to CSV and XLSX while state stays RUNNING.
  Generated files are read back. This validates live export UI behavior with
  fixture results, not a claim of live scraping accuracy.
- First two focused attempts were interrupted after partial progress while
  investigating a new sleep mock that also affected Playwright transport.
  The final spy delegates to the original sleep and is scoped to the panel
  read. The next focused run completed: 99 passed, 1 failed in 17.02s.
  That test needed the shared GUI fixture to reset the new checkbox state
  along with its preset. After correcting fixture isolation, the full suite
  passed as above. Failed/interrupted attempts remain recorded.
- Final style-only edits were checked against the tested source/test ASTs,
  excluding docstrings: zero semantic differences.

Evidence outputs and final artifact details are stored alongside this report
under `evidence/selectable-checks-*`. Raw build/preview logs remain local in
ignored `debug/`. [Full suite](evidence/selectable-checks-full.txt),
[focused failure](evidence/selectable-checks-focused-failure.txt), and
[aggregate audit/build evidence](evidence/selectable-checks-summary.json).

## Build, visual check and audit

PyInstaller rebuilt `dist/MetaInspectorDesktop.exe` successfully. Its exact
size and SHA256 are in the aggregate evidence linked above. The bundled
Chromium build remains above the project's original 150 MB size target.

Opened the actual rebuilt EXE with an isolated app-data folder, confirmed a
responsive window and visually inspected a 1900 by 1040 app-only capture.
All six field cards, the both-Alive shortcut, export-row filter and live
snapshot caption were visible. No checker session or target was used.
Closed only this preview window after inspection.

![Actual rebuilt EXE showing the new controls](images/selectable-checks-exe-2026-10-17.png)

The local capture helper initially needed a corrected 64-bit Windows HDC
declaration. A native window-message click did not visibly toggle a checkbox;
it is not counted as a successful packaged interaction. Functional control
and file assertions above come from real Tk tests. Actual EXE export dialogs
and a live check run were not newly exercised in this task.

Targeted audit: 47 production files, largest 460 lines. New modules' functions
have type annotations/docstrings and no over-79-character lines. Changed
text files remain below 500 lines, added text contains no prohibited dash
characters, and candidate files contain no supplied password/2FA matches.
This is a targeted audit rather than a comprehensive security assessment.

## Not verified in this task

No new live IG/Threads extraction benchmark, account login, full-list
country/date audit, under-five-minute acceptance or clean Windows-machine
test was performed. Automated timing is test duration, not scraping speed.
No existing client timing is presented as a new measurement here. A failed or
withheld live read still cannot be turned into a guaranteed country/date.

## Operator steps

1. Open the updated app. In What to Check, choose the wanted fields, using
   the left panel's scrollbar when needed. A mode preset can restore its set.
2. Enter targets and Start. For IG Alive plus IG Country, keep only those two
   independent boxes. Age returns a joined date when selected.
3. Select Output, choose Checked fields or another preset, adjust columns and
   press OK. Choose the desired Copy/export rows filter separately.
4. Copy or export after the first finished result, or wait for completion.
   Repeat the export to include later arrivals. History can reopen final runs.

Codex and Claude should use this dated report and the current branch rather
than treating the older Round 4/8 status report as the latest implementation.
