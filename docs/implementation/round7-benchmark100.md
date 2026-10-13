# Round 7 (Claude) - the 100-account Combined benchmark, measured

13 October 2026. Branch `fix/extraction-root-cause-isolation`, after the
Round 5 resource-blocker fix (P55), Round 5 continuation classification fixes
(P57/P58) and the Round 6 menu/dialog retry (P61).

## Target list (100 unique, none invented)

The supplied client list has 95 unique usernames. The remaining 5 were taken
from the project's own pre-existing lists (`checker_test/usernames.txt`,
`docs/testinusername.txt`): `zeynep607196`, `elif70566`, `ece25051`,
`ayse517258`, `fatma868612`. No username was fabricated and no target was
duplicated -- the assembled list was asserted to be 100 distinct entries
before the run (`debug/round7_benchmark100.txt`).

## Command and conditions

```text
python -m src.core.scraper --file debug/round7_benchmark100.txt \
  --mode combined --workers 5 --checkers 5 --debug-dump
```

Production CLI, no custom wrapper. checker_5 only (checkers 1-4 never
opened). Combined mode, 5 worker pages on one checker context, resource
blocker ON (selective CDP), debug captures ON, pacing 4-8s per worker
between targets, budgets page-ready/dialog/menu = 10/10/8s.

## Headline result

**100 accounts in 410.5 seconds (6m 50s).** The 5-minute (300s) NFR-1
target is **NOT MET**. For comparison, Round 4's pre-fix run took 1047.66s
for 95 targets: per-target time improved from ~11.0s to ~4.1s (2.7x), and
usable-data rates improved far more (below).

| Metric | Round 4 (95, pre-fix) | Round 7 (100, post-fix) |
| --- | ---: | ---: |
| Elapsed | 1047.66s | **410.5s** |
| Rows returned / queued | 95 / 95 | **100 / 100** |
| Unstarted / dropped / duplicated | 0 / 0 / 0 | **0 / 0 / 0** |
| BLOCKED (session challenge) | 0 | **0** |
| Data quality Complete | 0 | **36** |
| Data quality Partial | 14 | 58 |
| Data quality Failed | 81 | **0** |
| Not available (genuinely no account) | - | 6 |
| Rows carrying any error text | 95 / 95 | **21 / 100** |

## Field-level completeness, and the reason for every missing value

Five requested data fields x 100 targets. Every "missing" below is
categorized from the record's own `*_status`, `*_stage` and
`*_country_availability` fields -- not inferred.

| Field | Present | Missing: account doesn't exist | Missing: platform withheld it | Missing: extraction failed |
| --- | ---: | ---: | ---: | ---: |
| `ig_country` | **91/100** | 7 | 2 | **0** |
| `ig_date_joined` | **93/100** | 7 | 0 | **0** |
| `threads_country` | 44/100 | 44 | 11 | **1** |
| `threads_date_joined` | 55/100 | 44 | 0 | **1** |
| `threads_badge` | 55/100 | 44 | 0 | **1** |

The same result stated per platform, excluding accounts that genuinely do
not exist on that platform (which are correct results, not failures):

- **Instagram: 93 of 100 targets have an account. 91 returned both country
  and join date. 2 had the country withheld by Instagram itself. 0
  extraction failures.**
- **Threads: 56 of 100 targets have an account. 44 returned both country and
  join date. 15 had the country withheld by Threads itself. 1 extraction
  failure.**

That is **1 genuine extraction failure in 149 platform checks against
existing accounts (99.3% success)**. Round 4's equivalent was 81 Failed
rows out of 95.

## Verification of the classifications (not taken on trust)

- **All 44 Threads `NOT_FOUND` rows were re-checked against their own saved
  page capture**: 44/44 contain Threads' real 404 text. Zero
  misclassifications. (This is the P57 fix validated at scale -- in Round 5
  these same 404s were being reported as identity-verification failures.)
- **All 7 Instagram `NOT_FOUND` rows likewise verified** against their
  captures: 7/7 show a real unavailable-profile page.
- **The 15 withheld countries** are split between the platform printing the
  literal text `"Not shared"` (`country_availability="not_shared"`) and the
  platform rendering no country row at all
  (`country_availability="not_disclosed"`, the P58 fix). Both are reported
  with the reason visible in `error_message`, so an operator can tell
  "platform won't say" apart from "we failed to read it".

## The one genuine failure

`lyricnixon292`: Threads account exists and is active, but `_options()`
could not find the profile "More" control across **both** attempts
(`threads_stage="about_menu"`, "Threads profile menu not found", 32.0s).
Its final-state capture shows a real but completely empty profile ("0
followers", "No threads yet"). This matches the long-standing documented
quirk in `docs/memory.md` section 4 item 1: inactive Threads profiles with
zero posts often do not render the About control at all. **Not fixed**, and
probably not fixable in code if the control genuinely does not exist for
empty profiles -- the honest output for such an account is exactly what it
produced: active, no transparency data, reason stated.

## The Round 6 retry, observed firing live

The retry (P61) fired on exactly **2 targets** (`damaris_9759`,
`me_redith6621` -- identified by their `profile_menu_open_2_*` /
`about_clicked_2_*` captures) and **both recovered fully**, returning real
date and country (October 2025 / China for both). `me_redith6621` was one of
the accounts that failed with both fields missing before this fix existed.
This is the first direct live evidence of the retry rescuing a result rather
than just passing a synthetic test.

Cost of the retry when it does not help: `lyricnixon292` spent 32.0s partly
because the menu search ran twice. That is the accepted, documented
trade-off.

## Why 410.5s and not under 300s

The wall time is explained almost entirely by a validated arithmetic model,
not speculation:

| Component | Seconds |
| --- | ---: |
| Sum of per-row work across all 5 workers | 1356.3 |
| Work per worker (1356.3 / 5) | 271.3 |
| Deliberate pacing per worker ((20-1) x 6.0s avg) | 114.0 |
| **Predicted elapsed** | **385.3** + startup/preflight |
| **Measured elapsed** | **410.5** |

**The deliberate 4-8s pacing between targets accounts for ~114s, about 28%
of the entire run.** It exists specifically to avoid the rate-limit and
challenge behaviour that caused this project's earlier incidents, and this
run hit **zero** blocks with it in place.

Projections from the same validated model (not measured):
- pacing reduced to 2-4s (mean 3s): ~328s + startup -- still over 300s.
- 8 workers at current pacing: ~238s -- under 300s, but more concurrent
  pages per account is exactly the variable that triggered the original
  Incident 5 detection, and all 5 accounts' suspension history makes that a
  risk decision for Huzaifah, not a silent code change.

### A measured hypothesis that turned out wrong

I expected the debug captures (499 screenshot/text/json files written during
the benchmark) to be a significant cost, and tested it rather than assuming:
the same 15 full-path targets ran in **87.9s with captures ON** and
**119.9s with captures OFF**. Captures-off was *slower*, i.e. the live
site's own run-to-run variance (±36% on this sample) completely dominates
any capture overhead. **Conclusion: turning captures off is not a route to
300s, and single runs of ~15 targets cannot reliably measure anything
smaller than roughly a 40% effect.** Recorded because the hypothesis was
disproved, not quietly dropped.

## Timing distribution

mean 13.56s per target, median 12.53s, min 2.86s, max 35.53s. Slowest five:
`giannafrazier18` 35.53s (both platforms complete), `lyricnixon292` 32.0s
(the one failure, retry spent), `braxtonmayo25` 30.94s, `me_redith6621`
27.42s (retry, recovered), `jackyates293` 25.48s.

## What this run does and does not establish

**Does:** the extraction engine now reads essentially everything the
platforms actually expose (99.3% of reachable platform checks); nothing is
dropped or duplicated; no fabricated data; every missing value has a
recorded, verifiable reason; no session block at 5 workers across 100
targets.

**Does not:** meet NFR-1's 5-minute target (410.5s). Does not establish
that reduced pacing or more workers would be safe. Does not re-test the
one inactive-profile failure mode. Single run -- the ±36% variance measured
above applies to this 410.5s number too, so a repeat run could land
meaningfully higher or lower.

## Artifacts

- [100 target list](../../debug/round7_benchmark100.txt)
- [Full run output, all 100 rows](../../debug/round7_benchmark100_output.txt)
- [Analysis script used for every number above](../../debug/round7_analyze.py)
- [A/B targets](../../debug/round7_ab_targets.txt)
- Per-target stage captures: `debug/ig_*`, `debug/threads_*` (local only)
