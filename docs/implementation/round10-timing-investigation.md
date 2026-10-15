# Round 10 (Claude) - why a run that took 410s in the afternoon takes 590s at night

14 October 2026. Branch `feature/output-selection-and-export`. Investigation
only; no application code changed in this round.

## What triggered it

Huzaifah ran the client's 95-account list through the **GUI** twice and got
**587.3s and 596.3s** (both ~9m50s). My Round 7 **CLI** benchmark of
essentially the same list reported **410.5s**. That is a 1.45x gap between
what I told him and what his own app does, so the gap had to be explained
rather than attributed to variance.

Both GUI runs are stored in `history.db`
(`RUN_20261013_235623`, `RUN_20261014_000708`) with full per-row records.

## Row-level comparison

| | Round 7 CLI (13 Oct, 14:19) | GUI run 1 (13 Oct, 23:56) | GUI run 2 (14 Oct, 00:07) |
| --- | ---: | ---: | ---: |
| Targets | 100 | 95 | 95 |
| Elapsed | 410.5s | 587.3s | 596.3s |
| Sum of row work | 1356s | 2281s | 2317s |
| Mean row seconds | 13.56 | 24.01 | 24.39 |
| Median row seconds | 12.53 | 24.36 | 25.97 |
| Rows where **Threads profile is live** | 56, mean **16.96s** | 53, mean **32.31s** | 53, mean **31.79s** |
| Rows where **Threads is a 404** | 44, mean **9.24s** | 42, mean **13.53s** | 42, mean **15.05s** |

Restricted to the 95 usernames both runs share, the GUI was **1.80x** slower
per row (13.58s vs 24.39s).

## Isolating the cause

Three candidates: the GUI itself, the Round 8 code changes, or something
outside our code.

**The Round 8 code is ruled out by reading the diff.** The only extraction
change between the 410.5s branch and the current one is the stable-panel
early return in `src/core/dialogs.py`. It adds a `return best` *before* the
deadline and changes nothing else. An added early return cannot make the
function take longer.

**The GUI is ruled out by measurement.** I re-ran the identical 20 targets
(14 with a live Threads profile, 6 without) through the **production CLI**,
at night, same 5 workers, same combined mode:

```text
python -m src.core.scraper --file sub20.txt --mode combined --workers 5 --checkers 5
20 accounts in 162.7s | assets blocked: 1911
```

| Same 20 targets | Mean row seconds |
| --- | ---: |
| CLI, 14 Oct ~00:15 | **26.45s** |
| GUI, 14 Oct 00:07 | **25.33s** |
| CLI, 13 Oct 14:19 | **12.83s** |

The CLI at night is **as slow as the GUI at night**, and both are about
twice the same CLI's afternoon figure. The GUI adds nothing measurable.

## Where the time actually goes

The decisive detail is that the two Threads paths moved in opposite ways:

| Path | Round 7 afternoon | CLI tonight |
| --- | ---: | ---: |
| Threads **404** rows (navigate, read 404, stop) | 9.24s | **8.63s** |
| Threads **live** rows (navigate, open menu, read About panel) | 16.96s | **34.09s** |

Plain navigation is unchanged, so this is **not** a general network problem
on this machine. Only the path that opens the profile menu and waits for the
**About panel to render** has doubled. That is Meta-side rendering latency at
this hour, and our 10s dialog budget plus 8s menu budget absorb it directly.

**Conclusion: the 410.5s figure was a good-conditions number, and I presented
it as the number. The honest statement is that this run takes roughly 7
minutes under afternoon conditions and roughly 10 minutes under the
conditions measured around midnight, with the whole difference sitting in the
Threads About panel.**

## The conditional-Threads idea, quantified

Huzaifah asked whether Threads could be skipped for accounts whose country
Instagram already gave, and checked only for the rest. The saved records say
this is the strongest lever found so far.

Using `m(threads live) - m(threads 404)` as the cost of the Threads
menu-plus-dialog phase:

| | GUI run 2 | GUI run 1 |
| --- | ---: | ---: |
| Threads menu+dialog phase cost | ~16.7s | ~18.8s |
| Live Threads profiles | 53 | 53 |
| of those, **IG already gave a country** (skippable) | **49** | **47** |
| of those, IG gave no country (must still check) | 4 | 6 |
| Accounts where Threads was the **only** source of a country | 2 | 3 |
| Work removed | ~820s | ~882s |
| Off the wall clock (5 workers) | **~164s** | **~176s** |

Two properties make this safe rather than a trade of accuracy for speed:

1. **Country coverage does not drop.** Round 7 showed that where both
   platforms report a country they agree **36 times out of 36**, zero
   disagreements. The accounts Threads rescues are by definition the ones
   where Instagram gave nothing, and those are exactly the ones the rule
   still checks.
2. **It removes the slow path specifically.** The phase it skips is the
   Threads About panel, which is the single component measured above as
   having doubled.

What it does cost: **Threads Joined and Threads Badge are not collected for
the skipped accounts.** So this must ship as a selectable mode, not as a
silent default.

Predicted elapsed from the same arithmetic: about 420s to 440s under
tonight's conditions, against 596.3s measured. Unverified until it is built
and run.

## Corrections this round makes to my earlier reporting

- Round 7's 410.5s was reported without saying it was measured under
  afternoon conditions. It is not a figure the client should be promised.
- In Round 9 I wrote that the Threads half contributes little and that mode
  choice is not a route to NFR-1. The first half stands for *dropping Threads
  wholesale*; it is wrong as a statement about **this** conditional rule,
  which targets the expensive subset instead of the whole platform.

## Artifacts

- Both GUI runs: `history.db`, runs `RUN_20261013_235623` and
  `RUN_20261014_000708` (local only)
- Night CLI control run: 20 targets, 162.7s (local only)
