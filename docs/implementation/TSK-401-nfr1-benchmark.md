# TSK-401: live Combined benchmark - Round 4

## Round 5: 50-account Combined recheck (Claude continuation), 13 October 2026

Branch `fix/extraction-root-cause-isolation`. Codex ran this 50-target
Combined recheck as Task 3 of its Round 5 directive, after fixing the
resource-blocker routing/cache defect (P55/P56), then hit a usage limit
before writing it up. This section reports Codex's own already-captured
result (`debug/round5-t3-combined50.json`); no new live run was started to
produce these numbers.

**Elapsed: 281.9220000000023 seconds** (~4m 42s), workers=5, one checker
(checker_5), blocker ON (selective/corrected), debug_dump on. This is a
**50-target** recheck, not the 100-target NFR-1 benchmark, and not directly
comparable to Round 4's 95-target 1047.66s run (different target count,
and Round 4 predates the resource-blocker fix) -- it is reported to show
the blocker fix's effect on a larger, more realistic Combined batch than
the 8-target Task 1/2 samples.

| Metric | Round 4 (95 targets, pre-fix) | Round 5 (50 targets, post-fix) |
| --- | ---: | ---: |
| Elapsed | 1047.66s | 281.92s |
| Elapsed per target | ~11.0s | ~5.6s |
| Data quality | Complete 0, Partial 14, Failed 81 | Complete 15, Partial 31, Failed 4 |
| IG both fields | 12/95 dates, 11/95 countries | 45/50 |
| Threads both fields | 2/95 | 17/50 (pre P57/P58; see below) |
| Unstarted / dropped | 0 / 0 | 0 / 0 |
| Stop reason | none | none |

Per-target elapsed time roughly halved and IG's both-fields rate went from
~12% to 90% -- consistent with the resource-blocker routing/cache fix
(P55/P56) being a genuine, substantial improvement, not just an 8-target
artifact. **This is still not a 100-target run and NFR-1 (100 accounts
under 5 minutes) remains unverified** -- 50 targets in 281.9s does not
linearly imply 100 targets in under 300s, and no such extrapolation is
claimed here.

Threads' own result (17/50 both-fields before P57/P58) undersells what was
actually happening: of the 33 non-complete Threads records, `threads_stage`
breakdown was `identity` 24, `about_dialog` 6, `navigate` 2 (a transient
`net::ERR_NETWORK_CHANGED`), `about_menu` 1. Reading the raw evidence behind
each of these (see `round5-threads-404.md` and
`round5-threads-country-absent.md`) found that **all 24 `identity` failures
and 5 of the 6 `about_dialog` failures were not extraction bugs**: the 24
were genuine "this account has no Threads profile" pages (Threads' 404
wording was simply unrecognized, so `NOT_FOUND` was misreported as an
identity-verification failure), and the 5 were panels that Threads rendered
with no country row at all (not a timing/hydration problem -- confirmed
stable for the entire poll budget). Both are now fixed (P57, P58) and
covered by regression tests, but **not yet re-verified by a fresh live
run against this same 50-target list** -- the next live batch should show
the Threads `NOT_FOUND` count rise and the `identity`/`about_dialog`
failure counts drop accordingly, which is the next thing to confirm before
attempting the actual 100-target NFR-1 benchmark.

[Raw 50-target result](../../debug/round5-t3-combined50.json) (local only,
contains target usernames).

---


13 October 2026. Branch: `fix/single-account-worker-concurrency`.
User changed the immediate request to **95 unique targets**. This result is for
that actual list; it is not a completed 100-target NFR-1 benchmark.

## Measured result

**Elapsed: 1047.6569999999992 seconds**, measured without rounding with
`time.monotonic()` around the full production `run_async` call, including
startup/preflight and shutdown. Five-minute usable-results goal: **NOT MET**.
No extrapolation to 100 targets, no comparison to a controlled earlier baseline.

| Metric | Actual result |
| --- | --- |
| Unique targets / returned rows | 95 / 95 |
| Unstarted / duplicate rows | 0 / 0 |
| Checker / contexts / observed worker pages | checker_5 / 1 / 5 |
| Independent resource blockers | 5 |
| Live preflight | IG and Threads expected identity verified |
| Composite status | ACTIVE 53, ERROR 42, BLOCKED 0 |
| Data quality | Complete 0, Partial 14, Failed 81 |
| Rows with extraction errors / error-free rows | 95 / 0 |
| IG extracted dates / countries | 12 / 11 |
| Threads extracted dates / countries | 2 / 2 |
| Stop reason / journal error | none / none |

ACTIVE describes detected account existence, not successful transparency extraction.
No row has a complete usable Combined result. All returned rows and unrounded
platform durations are retained locally. Only aggregate metrics are committed;
per-account field values and individual timing rows are excluded from the push.

Settings: Combined, workers=5, headless=True, debug_dump=True; per-worker pacing
4-8 seconds; page-ready/dialog/menu budgets 10/10/8 seconds. Evidence capture costs
are included in runtime. No stripped-debug equivalent was measured.

## Observed bottlenecks and next work

| Terminal extraction stage | IG calls | Threads calls |
| --- | --- | --- |
| identity verification failed | 49 | 60 |
| About menu unavailable | 14 | 33 |
| About dialog missing requested fields | 18 | 0 |
| complete | 11 | 2 |
| navigation / profile not found | 3 | 0 |

Per-row recorded seconds: mean 47.24494736842105, maximum 84.86. Whole extractor
calls ending at identity failure total 1238.5439999999962 seconds for IG and
1288.6589999999978 for Threads across parallel workers. Threads calls ending at
About-menu failure total 782.9839999999967 seconds. These overlapping call totals
include navigation, waits, debug capture and dismissal; they are **not isolated
stage timers** and must not be added to elapsed wall time.

Directly inspected evidence (exact capture paths remain in the
[local result's evidence fields](../../debug/round4-benchmark95.json)):

- One IG identity-failure screenshot shows only the Instagram loading splash.
  Of identity-failure captures, 31 IG and 26 Threads have empty visible body text.
  This supports readiness problems for those captures, not a proven
  identity-selector defect on all targets.
- One Threads About-failure screenshot shows the correct target profile with its
  menu open but a spinner instead of loaded items. A wrong SVG click is not
  established for this case.
- One IG About-failure screenshot shows the target profile/loading content without
  an About dialog. Menu-open and About-click captures remain in its evidence chain.
- One successful Threads extraction screenshot explicitly shows the target
  identity, date and country matching the row. This validates that example,
  not the other 94 targets. Individual account field values remain local.

Next diagnostic priorities: measure navigation/header readiness and menu hydration
separately under concurrency, inspect failed/pending document/script/API requests,
and compare a small controlled one-page/five-page sample. Do not merely raise
all timeouts or assert rate limiting, resource blocking, CPU saturation or a
particular Meta server cause without that evidence. Five Threads final capture
references are empty, so not every failure has complete screenshot evidence.

## Reproduction and artifacts

The agent ran the production scraper after the **user** manually completed login
and onboarding in the actual app. Only checker_5 was selected. No checker 1/2/3
login, account-file import, TOTP submission or profile reset occurred this round.

- [Sanitized aggregate evidence](evidence/round4-benchmark95-summary.json).
- [All 95 local rows](../../debug/round4-benchmark95.json) and
  [190 local whole-platform call timings](../../debug/round4-benchmark95.json).
- [Local full result](../../debug/round4-benchmark95.json),
  [append-only journal](../../results/run_20261013_101042_427210.jsonl),
  [local runner](../../debug/round4_benchmark95.py).
- [Manual login proof](evidence/round4-live-setup.json),
  [task report](round4-report.md), [test log](../test_log.md).

Method: real saved profile, real Meta responses, production shared queue, wrappers
that observe extractor durations and page/context identities without changing
responses. Rejected: fabricating five additional targets, counting fast failure
rows as success, bypassing identity verification, or extrapolating timings.

Earlier rounds below are historical and superseded by the completed 95-target run.

## Round 3 decision, 12 October 2026

Branch: `fix/resilience-and-root-cause`. **100-account Combined benchmark not
attempted; elapsed time and row breakdown do not exist. NFR-1 is unverified and
has not met acceptance.** No rounded sample, estimate, extrapolation or simulated
run is presented as a measured 100-account result.

Task 1 now permits any healthy subset. Task 2 actually attempted all five imported
checkers: **IG 1/5, Threads 0/5, both platforms 0/5**. Task 3's captures show
authentication/onboarding/broken-page failures before any usable Threads target
session. Task 5 confirms a real checker suspension. The directive explicitly
requires stopping live work without a working checker; there is no healthy subset
with which to run Combined. This is the blocker, not waiting for all five logins.

[Task 2 counts](round3-live-checker-logins.md),
[Threads raw evidence](round3-threads-root-cause.md),
[suspension notice](round3-checker-suspension.md).

The supplied target list also contains **95 unique targets**, not 100. An earlier
request for the remaining five or a 100-target file is unanswered. Duplicating
targets or silently inventing five client targets was rejected. After at least
one real Combined checker works, use an agreed list of 100 unique targets,
measure the entire `run_async` call including startup/preflight with
`time.monotonic`, retain its unrounded numeric duration and every row, and report
the actual participating checker IDs, field completeness, disclosure-only
partials, extraction errors, BLOCKED rows and never-started count separately.
Pass requires the requested usable results under 300 seconds, not merely fast
empty/error rows. No timing/pacing or resource-blocker change was justified by
the failed authentication prerequisite in this round.

## Earlier attempts (historical)

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.

The required 100-account Combined-mode, 5-worker benchmark was **not run**.
There is no benchmark elapsed number or benchmark success/error breakdown.
NFR-1 remains **unverified**.

The preceding 10-account, 1-worker controlled diagnostic printed `193.8s` and
returned zero transparency fields across all 10 records. A directly inspected
live screenshot showed an unauthenticated Instagram page despite a saved
session cookie. See [TSK-402 evidence](TSK-402-data-accuracy.md). That diagnostic
is not the NFR-1 benchmark and its timing must not be extrapolated to 100 accounts.

No performance changes were implemented. Benchmarking an unauthenticated
session or raising concurrency to improve empty-result throughput was rejected
because the directive requires the accuracy question to be resolved first.

After manual re-authentication, repeat the 10–15 account Combined diagnostic
with one worker and raw captures. Only once raw dialogs resolve the accuracy
question should the 100-account benchmark proceed with 5 workers and default
menu/dialog/page-ready budgets of 8.0/10.0/10.0 seconds. The reused source list
has 95 unique entries, so it alone does not satisfy the 100-account requirement.

The live failures occurred before transparency polling: all 10 IG rows lacked
the Options control; nine Threads rows lacked the About option and one lacked
the profile menu. These are observed failure locations, not proof of a timing
bottleneck. No five-worker benchmark bottleneck or invasive fix is claimed.


## Follow-up implementation status

The later user request authorized five independent checker profiles and a shared
queue. That implementation is regression-tested with five simulated contexts,
not benchmarked with five authenticated live accounts. A single Combined target
was read in 17.1s total (8.36s row) after re-login; a later target attempt took
62.0s and failed during loading. Neither is a 100-account benchmark. Controlled
10-target launches were also prevented by approval-review timeouts.

**NFR-1 remains unverified, not met by evidence.** No throughput estimate or success
rate is extrapolated from the one successful target. Fresh baseline stability and
working Combined logins are required before the 100-account benchmark. Round 3
supersedes the earlier requirement to wait for five: any healthy subset suffices.
