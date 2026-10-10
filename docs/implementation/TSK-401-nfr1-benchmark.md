# TSK-401: NFR-1 benchmark not run

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
five working logins are required before the 100-account benchmark.
