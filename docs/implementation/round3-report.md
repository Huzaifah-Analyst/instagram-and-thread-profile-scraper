# Round 3 implementation and observed acceptance

Follow-up on 13 October: the agent opened the actual desktop app and operated its
Setup controls. Checker_5 IG feed/identity verified; selecting its Threads Meta
account continuation reached the real **Privacy Public/Private** onboarding step.
User chose Private; later continuation returned Something went wrong and setup remains incomplete; see [GUI follow-up](round3-live-checker-logins.md).
This refines the earlier login blocker without claiming completed Threads setup.

12 October 2026. Branch `fix/resilience-and-root-cause`, based on the pulled,
up-to-date `fix/data-accuracy-and-nfr1-verification` at `3615193`. No merge or branch
deletion is part of this task. The unrelated IDE report for another project was
not modified.

**Latest automated acceptance: 172 passed in 29.19s, zero skips**, complete pytest suite, including the current Meta-account card follow-up. [Latest output](evidence/meta-card-final.txt). Earlier Round 3 acceptance: 170 passed in 40.00s.
[Output](evidence/round3-full-acceptance.txt). Earlier 60-test subset and the first
full run's three failures remain in [test_log.md](../test_log.md), with reasons.
The new fixture redirect escaped initial routing; replacing it with a local
history update kept the account-health tests synthetic. The error-boundary mock
also exposed an absent-URL assumption, which was hardened before the passing run.

| Task | Result | Evidence/report |
| --- | --- | --- |
| 1: tolerate unhealthy checkers | Implemented. 3 healthy + 2 unhealthy finish all twelve targets; setup account 2 failure still attempts 3–5; active challenge stop retained. | [Partial-checker resilience](round3-partial-checker-resilience.md) |
| 2: real independent logins | All five attempted. IG **1/5**, Threads **0/5**, both platforms **0/5**. Each failure recorded; no count inferred from cookies. | [Live checker results](round3-live-checker-logins.md) |
| 3: Threads cause | Actual compound continuation mismatch fixed; remaining login/onboarding/broken-home states captured. No healthy current session for target-menu diagnosis; SVG and hydration hypotheses remain unproven. | [Threads diagnosis](round3-threads-root-cause.md) |
| 4: missing targets | Real unexpected-exception drop path fixed and tested. Stopped/unstarted targets tracked separately; historical 27/95 screenshot is not proof that 95 were attempted. | [Missing targets](round3-missing-targets.md) |
| 5: checker ban | **(a)** confirmed for checker_2: real suspension notice, October 9, account integrity. Exact automation contribution is unknown. Historical target BLOCKED is a different observation. | [Suspension investigation](round3-checker-suspension.md) |
| 6: NFR-1 | **Not run; not accepted.** No healthy Combined checker and only 95 supplied unique targets. No benchmark elapsed number exists. | [TSK-401](TSK-401-nfr1-benchmark.md) |

Carried-over work completes the late/sibling authenticator Continue control
handling and CLI imported-profile selection. The current user account-health
blockers are reported rather than repeatedly resubmitting secrets. Per-account
setup summaries are readable in a separate scrollable window; batch completion
surfaces failed checker health, unstarted targets and journal warnings.

No successful live five-checker extraction, 100-target accuracy, sub-300-second
throughput, new packaged build or clean-machine acceptance is claimed. The
resource blocker, per-checker pacing and target date/country values were not
changed to manufacture a faster result. Recover at least one real IG+Threads
session using [the manual steps](round3-live-checker-logins.md), then supply the
remaining five targets or an agreed 100-target file for the gated benchmark.
