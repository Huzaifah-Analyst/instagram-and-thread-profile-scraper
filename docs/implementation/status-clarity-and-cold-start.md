# Status clarity and anonymous cold-start fixes

15 October 2026. Branch `fix/status-clarity-and-cold-start`, created from
`dev` at `0e555b1`. No merge into dev and no branch deletion.

The two fixes are implemented and the full suite passes. Two real 50-target
CLI runs completed, but the client's packaged cold-start Unknown pattern was
not reproduced. This does not establish that the packaged defect is closed.

## Anonymous mode

- Named `ANONYMOUS_PAGE_READY_TIMEOUT_S = 30.0` in `anonymous_status.py`.
  Anonymous checks use the larger of this floor and an explicit configured
  budget. The shared 10-second default and logged-in mode budgets are unchanged.
- Complete the entire main pass before retrying only Unknown targets once.
  Reuse the same anonymous context and worker pages, with the warm cache.
  Known verdicts are not retried. Persistent Unknown retains its read reason.
- Emit one final record, journal row and progress increment per attempted
  target. Retry durations include both attempts. Pause/stop and cleanup remain
  supported, including preserving attempted Unknowns when stopped early.
- Journal aggregate main-pass Unknown and retry counts for diagnosis. No
  account, persistent context or logged-in pacing is introduced.

## Display explanations

Both platforms' country/date cells now use their existing structured state:
Not checked, Skipped (IG country), Unavailable (status only), No account,
Not shown by platform, or a short failed-stage label. Literal Not shared and
actual values are preserved. Truly unexplained missing values remain N/A.
Country disclosure alone cannot explain an absent joined date.

Stage labels are Page not loaded, Identity unverified, Menu not found,
About unavailable and Panel incomplete, with Check failed as the fallback.
The full error remains in Error. No error-prose matching is used.

This changes table rendering only, including reopened history. Stored values,
raw clipboard/CSV/Excel fields, composite verdicts and quality grading are
unchanged. Combined remains the default; its extraction path and record
builder were not changed. Existing regression tests remain in the full suite.

USER_MANUAL sections 7/8 and QUICK_START describe these labels and automatic
retry. Contradictory manual claims about fixed clipboard/export columns were
also corrected to the existing Select Output behavior.

## Actual before/after measurements

The first 50 unique targets from the existing Round 7 target file were used.
No accounts were invented or duplicated. Target-file SHA256:
`9e722287031e782332a132e0378379e0ee91bfcaa6a649c9441747b234ef0a5f`.

| Run | Returned / unique | Active | Not found | Unknown | Read errors | Elapsed |
| --- | --- | --- | --- | --- | --- | --- |
| Before, untouched `0e555b1` | 50 / 50 | 45 | 5 | 0 | 0 | 37.1s |
| After, fixed source | 50 / 50 | 45 | 5 | 0 | 0 | 125.7s |

For each run, exact case-insensitive returned-target equality was checked.
Both used the production CLI, `--mode ig_status_only --workers 5`, headless,
default blocker enabled, no debug captures, fresh nonpersistent browser
contexts and no checker accounts. The baseline ran in a detached worktree at
`0e555b1`. Runs were sequential, without tests or another live batch alongside
them; network/site conditions were not controlled or proven identical.

After-run journal: first-pass Unknown 0, retry attempts 0, final Unknown 0,
zero unstarted targets, no stop reason and no active checkers. There was no
live warm-retry recovery to measure. The after run had 24 target reads over
10 seconds, maximum 24.41s; baseline maximum was 6.61s. These measurements
show slower after-run rendering, not its cause. Do not infer how those same
pages would have behaved in a separate run with the shorter budget.

**No speed improvement is established.** The client's earlier 26 Unknown out
of 95 was reported from an EXE run, not measured anew here. A preliminary EXE
attempt loaded the list but never started checking, so it is not counted.
An earlier CLI attempt ended after five records without a finished journal;
its termination cause is unconfirmed and it is not counted as a complete run.
The complete baseline was then rerun as shown above.

## Test and build evidence

- First focused run: 1 failed, 60 passed in 2.21s. A new test incorrectly
  assumed the first journal event was an aggregate; actual record events
  correctly preceded it. The test now selects the aggregate event by type.
- Corrected focused run, including retry-exception coverage: 62 passed in
  0.92s. Initial full suite: 339 passed in 79.61s.
- Final suite after style cleanup and stronger exact-once journal assertions:
  **339 passed in 78.08s, zero skips**. No retry plugin or skipped coverage.
- New tests cover main-pass-before-retry ordering, exactly one retry,
  persistent Unknown reasons, recovered clean status, summed attempt time,
  no account pacing, stop during either pass, unique progress/journal rows,
  unchanged Combined budget, every requested cell state on both platforms
  and dates, no invented country-to-date reason, and unchanged CSV/records.
- Targeted source audit: 43 production files, largest 434 lines; no supplied
  password/2FA matches in candidate files. New anonymous/test functions have
  annotations/docstrings; these files obey the 79-character line limit.
  This is a targeted check, not a comprehensive security audit.
- Rebuilt `dist/MetaInspectorDesktop.exe` successfully with PyInstaller:
  **325,048,557 bytes**, SHA256
  `65a2d5f09a3249e97ed0c1bd639bf625d88426727429f4f89faaee5313d5b392`.
  The artifact is local and ignored by Git. This rebuilt EXE was not runtime
  retested; the earlier packaged acceptance report describes an older build.

Full outputs and aggregate evidence: [final suite](evidence/status-cold-full-final.txt),
[initial full suite](evidence/status-cold-full.txt),
[initial focused failure](evidence/status-cold-targeted-initial.txt),
[corrected focused run](evidence/status-cold-targeted-corrected.txt), and
[live/build summary](evidence/status-cold-live-summary.json).

Raw target results, journals, interrupted attempts and build log remain under
ignored `debug/` and `results/`. Only aggregate live evidence is included.

## Verification still needed

No fresh packaged 50/95-target run, slower-client cold-start reproduction,
live warm-retry recovery, Combined/Smart/Threads benchmark or new login was
performed. A separate clean Windows machine was not available. The new
display labels were covered through the actual rendering functions and
record/export invariance tests, not a new manual EXE screenshot for each
label. Persistent Unknown still requires an honest reason and later review.
