# Round 9 (Claude) - clean IG-only re-run, and two corrections

13 October 2026. Branch `feature/output-selection-and-export` (Codex's Round 8
delivery, commit `e2b9bba`). This round is review + one re-measurement; no
application code was changed.

## Why a re-run was needed

Round 8 reported Instagram Only at **584.6s with 41 extraction failures**,
versus Round 7's Combined run where Instagram had **0** extraction failures.
Codex reported this honestly and stated the cause was unisolated. Reviewing
the saved records found the cause:

- 10 rows carried hard network errors (`ERR_INTERNET_DISCONNECTED`,
  `ERR_NETWORK_CHANGED`, `ERR_CONNECTION_CLOSED`).
- Their evidence-capture timestamps cluster inside a **16-second window,
  17:00:48 to 17:01:04** - a transient loss of internet connectivity on this
  machine, not a site or code behaviour.

The Round 8 code changes were also ruled out as a cause: the only extraction
change was stable-panel polling in `src/core/dialogs.py`, and `_poll_dialog`
runs *after* `profile_matches()`. The 20 identity failures happen before it
is ever called, so it cannot have produced them.

## The clean measurement

Same list (`debug/round7_benchmark100.txt`, 100 unique targets), same
production CLI, same conditions, run after confirming the network was stable
(ping 0% loss, 61ms average):

```text
python -m src.core.scraper --file debug/round7_benchmark100.txt \
  --mode ig_only --workers 5 --checkers 5 --debug-dump
```

| | Round 8 (contaminated) | **Round 9 (clean)** |
| --- | ---: | ---: |
| Elapsed | 584.6s | **426.1s** |
| Rows returned | 100 | 100 |
| IG stage complete | 52 | **93** |
| IG extraction failures | 41 | **0** |
| Real IG countries (excluding literal `Not shared`) | 49 | **86** |
| IG join dates | 52 | **93** |
| IG NOT_FOUND (genuine) | 7 | 7 |

The clean run's field counts are **identical** to Round 7's Combined run for
Instagram (86 real countries, 93 dates, 7 NOT_FOUND, 0 failures). Two
independent runs agreeing exactly is strong evidence the extraction path is
stable and repeatable; the Round 8 numbers were an artefact of the outage.

**Instagram Only still does not meet NFR-1: 426.1s vs the 300s target.**

## Correction 1: my Round 7 country counts were overstated

Codex found, and I independently confirmed, that my Round 7 analyser counted
the literal string `"Not shared"` as a present country, because it tested
only truthiness:

- IG country: I reported **91 present**; actually **86 real + 5 literal
  `Not shared`**.
- Threads country: I reported **44 present**; actually **40 real + 4 literal
  `Not shared`**.

Extraction-failure counts (IG 0, Threads 1) and all date/badge counts were
unaffected. Codex's corrected analyser and its accounting regression test are
the right fix; `round7-benchmark100.md` carries a correction notice rather
than being silently rewritten.

## Correction 2: my advice that "IG-only is the free speed win" was wrong

After Round 7 I told Huzaifah that choosing Instagram Only would be a
significant, zero-risk speed win, reasoning that Threads was ~30% of total
work time. **The measurement disproves it.**

| | Combined (Round 7) | IG-only (Round 9 clean) |
| --- | ---: | ---: |
| Measured elapsed | 410.5s | **426.1s** |
| Work per worker | 271.3s | **289.1s** |
| Pacing per worker | 114.0s | **114.0s** |
| Mean row time | 13.56s | 14.46s |

Dropping Threads entirely produced **no speedup at all** (+15.6s, well inside
the +/-36% run-to-run variance measured in Round 7). Two reasons, both
visible in the numbers:

1. **The 4-8s pacing is per *target*, not per *platform*.** It stays at
   ~114s per worker no matter how many platforms are checked, so it cannot
   shrink by dropping one.
2. **Threads contributed little work to begin with**, because 44 of the 100
   targets have no Threads profile at all and resolve as fast 404s.

Threads Only (359.9s, Codex's Round 8 measurement) *is* faster than both -
for the same reason in reverse: 44 of its 100 targets are instant 404s.

### Current honest position on NFR-1

| Mode | Measured | Meets 300s? |
| --- | ---: | --- |
| Combined | 410.5s | No |
| Instagram Only | 426.1s | No |
| Threads Only | 359.9s | No |

No mode meets the target. Mode choice is a **feature** (the user picks what
data they want) but it is **not** a route to NFR-1. The only remaining levers
are still the two ban-risk ones: pacing and worker count.

## Verification performed on Codex's Round 8 delivery

- Full suite re-run independently: **222 passed in 107.83s**, zero skips
  (Codex reported 222; confirmed).
- `EXPORT_COLUMNS` extended exactly as directed - `Data Quality`,
  `IG Country Availability`, `Threads Country Availability` added to file
  exports, while `SHEET_COLUMNS` (the Google Sheets clipboard copy) was
  correctly left clean at 6 columns.
- Output settings behaviour verified directly against the real API, not the
  report: unticking every column leaves `('Username', 'Status')`; a custom
  selection persists across reload; a corrupted settings file falls back to
  the defaults and logs the reason instead of crashing.
- Stable-panel polling reviewed: it only returns early when a panel carrying
  at least one parsed field has been byte-identical for 4 consecutive poll
  cycles, and a still-changing panel keeps the full deadline. The paired live
  sample Codex ran (156.9s before / 213.6s after) did not demonstrate a
  saving, which is consistent with the variance already measured - the change
  is sound in principle but its real-world benefit remains unproven.

## Still open

- NFR-1 unmet in all three modes (P65).
- `lyricnixon292`'s empty-profile menu failure (P64).
- Whether reduced pacing or more workers can be done safely - unchanged, and
  still a decision for Huzaifah rather than a silent code change.

## Artifacts

- [Clean run output](../../debug/round9_ig100_clean.txt) (local only)
- Round 8 reports: [mode benchmarks](round8-mode-benchmarks.md),
  [export port](round8-export-port.md),
  [output selection](round8-output-selection.md),
  [stable dialog](round8-stable-dialog.md)
