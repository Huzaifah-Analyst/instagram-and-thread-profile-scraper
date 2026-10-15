# Round 8 task 4 — measured mode timings and delivery

13 October 2026. Branch `feature/output-selection-and-export`, based on
`bdb2e55`. Output selection/export/history and stable-panel polling are
implemented. **The under-300-second, zero-error live acceptance is not met.**

## Measured timings

| Mode | Targets returned / unique | Actual elapsed | At most 300s? | Context |
| --- | ---: | ---: | --- | --- |
| Combined | 100 / 100 | **410.5s** | **NOT MET** | Historical Round 7 baseline, before stable polling |
| Instagram Only | 100 / 100 | **584.6s** | **NOT MET** | Fresh Round 8 run |
| Threads Only | 100 / 100 | **359.9s** | **NOT MET** | Fresh Round 8 run, after IG finished |

The exact same `debug/round7_benchmark100.txt` was used for both new runs.
Validated 100 distinct case-insensitive usernames and exact set equality
against returned records; no omitted, extra or duplicated target. File SHA256:
`99a9e26ca5b4f0c2c6275643c7a84d666eac972876ce2fccd8b0fff3bfbaf22a`.

Commands used production CLI, with `--mode ig_only` and then
`--mode threads_only`, `--workers 5 --checkers 5 --debug-dump` and the list
above. Default 4–8s pacing, default 10/10/8s page/dialog/menu budgets,
selective blocker ON, headless. No timeout, pacing or worker increase.
Runs were sequential; browser regression tests did not run alongside them.

All four Round 8 live journals (two small and two full runs) ended normally:
zero unstarted targets, no stop reason, active checker list only checker_5.
**Checkers 1/2/3/4 were never opened or logged into.** No new login/onboarding
was needed. All raw records/captures/session material remain local.

## Field-level results

Counts distinguish a real country from literal `Not shared`. Columns in
each table sum to 100. Platforms excluded by the mode are **not checked**,
not classified as extraction failures.

### Combined — historical 410.5s, corrected analysis of saved records

| Field | Present | Account does not exist | Platform withheld | Extraction failed |
| --- | ---: | ---: | ---: | ---: |
| IG country | 86 | 7 | 7 | 0 |
| IG joined | 93 | 7 | 0 | 0 |
| Threads country | 40 | 44 | 15 | 1 |
| Threads joined | 55 | 44 | 0 | 1 |
| Threads badge | 55 | 44 | 0 | 1 |

The prior Round 7 table counted five IG and four Threads literal `Not shared`
values as present countries. The existing analyzer has been extended to
classify them correctly; missing date/badge fields also no longer inherit a
country-disclosure reason. Elapsed time, date/badge counts and the historical
number of extraction failures are unchanged. The old report has a correction
notice rather than silently rewriting the earlier claim.

### Instagram Only — 584.6s

| Field | Present | Account does not exist | Platform withheld | Extraction failed |
| --- | ---: | ---: | ---: | ---: |
| IG country | 49 | 7 | 3 | 41 |
| IG joined | 52 | 7 | 0 | 41 |

All three Threads fields: 100 not checked. Quality: Complete 49, Partial 3,
Failed 41, Not available 7. IG stages: complete 52, navigate 17 (including
seven not-found results), identity 20, about_dialog 11. Logs contain
navigation timeouts and `ERR_NETWORK_CHANGED`. The root cause of this
degradation compared with Round 7 remains unisolated; no claim that these
errors are caused or solved by stable-dialog polling.

### Threads Only — 359.9s

| Field | Present | Account does not exist | Platform withheld | Extraction failed |
| --- | ---: | ---: | ---: | ---: |
| Threads country | 36 | 44 | 11 | 9 |
| Threads joined | 47 | 44 | 0 | 9 |
| Threads badge | 47 | 44 | 0 | 9 |

Both IG fields: 100 not checked. Quality: Complete 36, Partial 11, Failed 9,
Not available 44. Threads stages: complete 47, navigate 44 (not-found),
about_dialog 7, about_menu 2. No navigation timeout marker was found in this
run's output; menu/panel rendering failures remain. Counting every green
ACTIVE row as a successful extraction would hide these nine failures.

## Verification and limits

- Baseline: **190 passed in 45.19s**, zero skips.
- Final complete suite: **222 passed in 70.06s**, zero skips.
- All original tests unchanged; both ported test files byte-identical to
  sprint3. Ported exporter/history collection: 16 + 5 = **21 cases**.
- The final suite includes eight actual-Tk/settings/history cases, two real
  Chromium stable-dialog cases, and one analyzer accounting regression.
- First targeted attempt: 3 failures / 28 passes; retained in evidence.
  Corrected compatibility and test driver: 31 passes. Final full suite also
  covers the later user clarification that diagnostics are optional.
- Production audit: 40 files, largest 466 lines; audited docstring/annotation
  checks and supplied-credential scan found no matches/violations. This is
  a targeted audit, not a comprehensive security assessment.

Real-Tk tests verify selected TSV/CSV/Excel columns, persistence, cancellation,
mandatory Username, diagnostic choices, visible corrupt-settings fallback,
existing platform radios and history reopening. Details:
[export port](round8-export-port.md), [selector](round8-output-selection.md).
Real Chromium tests verify stable date-only early return and changing-panel
late country. The paired live sample **156.9s before / 213.6s after** did not
establish any speed saving: [polling report](round8-stable-dialog.md).

These are single live measurements, not averages or extrapolations. The
Combined baseline predates the new run conditions; a fresh 100-target
Combined run after this change was not requested or performed. No claim of
all-field live accuracy, zero failures, under-five-minute performance,
packaged EXE acceptance or resolution of P64/P65/P71 is made.

Used and extended the existing `debug/round7_analyze.py`, rather than replacing
it. The script's aggregate option emits counts only, and its regression
prevents literal withheld values from being counted as countries. Rejected
averaging modes or projecting 12-target timings because the requested
acceptance requires actual per-mode measurements.

## Evidence and use

- `evidence/round8-before.txt`, `round8-targeted.txt`,
  `round8-targeted2.txt`, `round8-full.txt`.
- `evidence/round8-combined-round7.json`, `round8-ig100.json`,
  `round8-threads100.json`, and both `round8-small-*.json` summaries.
- Local-only: `debug/round8-ig100.txt`, `debug/round8-threads100.txt`, raw
  small-run outputs, `results/run_*.jsonl`, and browser captures.

To use the changes: restart `python main.py`, run/load results, choose
**Select Output**, tick columns and press **OK**, then use **Copy for Google
Sheets**, **Export CSV** or **Export Excel**. **View Run History** reopens
finished GUI runs. This feature does not change which platforms are scraped.

Delivery is on `feature/output-selection-and-export`; no merge into dev and
no branch deletion. Push verification is reported in the final response.
