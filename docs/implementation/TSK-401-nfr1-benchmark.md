# TSK-401: NFR-1 benchmark not run

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
