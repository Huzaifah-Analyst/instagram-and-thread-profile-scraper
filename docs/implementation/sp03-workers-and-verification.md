# SP-03 and targeted mode verification

14 October 2026. Renamed the visible "Checker limit" label to
"Parallel workers". The `workers` variables, values, range and forwarded
argument remain unchanged. No checker account selection is implied by this
control. The expanded radio list uses a scrollable section and wrapped labels
so the longer mode names fit the existing left panel.

## Tests actually run

| Run | Result |
| --- | --- |
| Unmodified f07fc72 baseline | 222 passed in 64.32s |
| First new-test run | 34 passed, 1 failed in 7.31s |
| Corrected new-test run | 35 passed in 4.86s |
| Final complete suite | 260 passed in 53.71s |

The first failure occurred while creating a second real Tk root: Tk reported
it could not load `ttk/scale.tcl`. The new GUI tests were changed to use the
existing module-scoped single-interpreter pattern, rather than skipping or
mocking GUI coverage. The underlying local Tk installation issue was not
independently repaired or root-caused. The corrected tests and full suite
passed, with no skips. Final coverage adds 38 collected cases to the baseline.

The suite includes real Chromium hydration/deadline fixtures, real Tk mode
forwarding, the unchanged prior tests, anonymous lifecycle/pacing assertions,
Smart Combined routing and analyzer classification of intentional omissions.
No existing assertion was weakened or removed. Test-suite runtimes above are
test measurements, not scraping performance measurements.

Evidence:

- `evidence/targeted-modes-before.txt`
- `evidence/targeted-modes-new.txt` (initial failure retained)
- `evidence/targeted-modes-new2.txt`
- `evidence/targeted-modes-full.txt`

All new source functions have annotations and docstrings. Production files
remain below 500 lines. Added lines and new source/documents were checked for
forbidden en/em dash characters. No new such characters were written.

## What was not verified

No live target run or checker login was performed in this task. Checkers
1/2/3/4 and checker_5 were not opened. Smart mode savings, anonymous-mode
100-target timing and live status accuracy remain unmeasured. The historical
164-second projection and 119.4-second prototype timing are attributed in
the respective task reports. No packaged EXE was built or tested, and there
was no merge into dev or branch deletion.

## Try the changes

Restart `python main.py`. Combined is still selected by default. Choose
Smart Combined to collect Threads only when IG does not disclose a country,
or IG Status Only to check status without Setup or a checker login. The
status-only country/date limitation is shown before the run and in the table.

CLI examples, using the already existing local target list:

```text
python -m src.core.scraper --file debug/round7_benchmark100.txt --mode combined_smart --checkers 5
python -m src.core.scraper --file debug/round7_benchmark100.txt --mode ig_status_only
```

These commands are usage instructions, not claims that those benchmarks were
run. See [Smart Combined](sp01-smart-combined.md) and
[anonymous status](sp02-anonymous-status.md) for semantics and limitations.
