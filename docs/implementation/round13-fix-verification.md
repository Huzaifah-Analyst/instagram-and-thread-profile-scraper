# Round 13 (Claude) - verifying the three fixes and the packaged build at scale

15 October 2026. Reviewing commits `8e4b066` (defect fixes) and `46d0234`
(packaging) on `feature/targeted-check-modes`. Codex verified the exe with
two accounts per mode and stated plainly that no 95-target benchmark was run,
so that measurement is this round's work.

## The three defects are fixed, confirmed at 95-account scale

| | Round 11 (defective) | **Round 13 (fixed)** |
| --- | ---: | ---: |
| Smart `data_quality` | Complete 0, Partial 89 | **Complete 80**, Not available 8, Partial 7 |
| Smart rows carrying error text | 89 / 95 | **7 / 95** |
| Status Only rows carrying error text | 95 / 95 | **0 / 95** |
| Status Only `unknown` results | 9 | **0** |
| Status Only agreement with logged-in run | 86 / 95 | **95 / 95** (see below) |

D3's one-line change (`followers?`) was checked for over-reach: "1 follower"
and "1 Follower" now classify active, while "123 following" and a bare
"followers" with no number still return unknown.

## Combined mode was not disturbed

The D1 fix touches completeness logic, so the risk was that it leaked into
the default mode. All 95 saved Combined rows from `RUN_20261014_000708` were
replayed through the new `build_record`:

```text
saved  : {'Complete': 30, 'Partial': 59, 'Not available': 6}
replay : {'Complete': 30, 'Partial': 59, 'Not available': 6}
rows whose quality changed: 0
```

The guard is correctly narrow: `smart_skip` requires both
`mode == combined_smart` and the `skipped_ig_sufficient` marker.

## Timings on the fixed code, same 95-account list

| Mode | Round 11 | Round 13 |
| --- | ---: | ---: |
| `combined_smart` | 225.2s | **263.5s** |
| `ig_status_only` | 62.4s | **44.4s** |

Both are single runs on a live site and move in opposite directions, which is
the run-to-run variance already documented, not an effect of the fixes. The
honest summary remains: Smart Combined lands in the 3.5 to 4.5 minute range
against Combined's 10 minutes, and is comfortably inside the client's
accepted 6 to 7 minutes.

## A finding that looked like a defect and was not

Three accounts disagreed with the 14 October Combined baseline, and two of
them (`na.sh8217`, `saylor4631`) came back `not_found` from the logged-out
mode where the baseline said `active`. Reported at face value that would be
two fabricated wrong verdicts, which is exactly what this mode is designed
never to produce.

Checking the logged-in run from the same day settles it:

| Account | Baseline 14 Oct (logged in) | Smart 15 Oct (logged in) | Anonymous 15 Oct |
| --- | --- | --- | --- |
| `na.sh8217` | active | **not_found** | not_found |
| `saylor4631` | active | **not_found** | not_found |
| `ri.ley2435` | active | error (1000ms locator timeout) | active |

The logged-in run agrees with the logged-out one, so **those two accounts were
genuinely removed between 14 and 15 October**. The anonymous classifier was
right and the baseline was stale. Corrected reading: **95 of 95 correct, zero
wrong verdicts, zero unknowns.**

`ri.ley2435` is a real but transient extraction error on the Instagram path,
reported as an error rather than guessed. Smart mode then fell through to
Threads, as designed when Instagram yields no country, and still returned the
country. That is Codex's own IG-exception fallback working on live data.

Country coverage accounts for exactly:

```text
lost country  : ['na.sh8217', 'saylor4631']
gained country: []
net: 85 - 2 + 0 = 83
```

**No country was lost to the code.** The drop from 85 to 83 is two accounts
that no longer exist.

This is worth telling the client: these lists decay. Two of 95 disappeared in
a single day, so a re-run is expected to differ from a previous one, and that
is a real change rather than a tool inconsistency.

## Packaging and suite

- Rebuilt exe present at `dist/MetaInspectorDesktop.exe`, 325,044,156 bytes,
  dated 15 October 11:10. Not committed to git; `git ls-files dist/ build/`
  is empty.
- Full suite **279 passed**, matching Codex's report.
- The previously flaky real-Tk test (P84) ran green three times in a row in
  isolation after being restructured onto a shared module-scoped root.
- No em dash or en dash anywhere under `docs/`, `src/` or `tests/`. Codex also
  cleared the pre-existing ones it found while editing.
- Documents were updated as instructed although the delivery message did not
  mention them: `PRD.md` NFR-1 and NFR-3, `QUICK_START.md` rewritten for five
  modes, `tasks.md` ticks. TSK-502 and TSK-501 are correctly left unticked
  with reasons.

Codex's PRD edit improved on my instruction: it notes that 410.5s was a
100-target run and 596.3s a 95-target run, so the pair is not a controlled
comparison. That is correct and I had not flagged it.

## What remains unverified

The 95-target runs above exercise the **code**, through the CLI. The packaged
exe was exercised at two accounts per mode. The logic is identical and the
packaging-specific paths (bundled Chromium resolution under `sys._MEIPASS`,
and `ig_status_only`'s `chromium.launch()` which no packaged build had run
before) were confirmed working, so the residual risk is low but not zero.

**BL-02 is still the real gate**: a bare Windows machine with no Python. The
operator checklist exists at `implementation/bl02-clean-machine-checklist.md`.
