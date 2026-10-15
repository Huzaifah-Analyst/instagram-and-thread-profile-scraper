# Round 4 implementation and acceptance - 13 October 2026

Branch: `fix/single-account-worker-concurrency`, based on Round 3 `061b4b1`.

| Requested item | Actual outcome |
| --- | --- |
| Sequential manual IG then Threads | Implemented in default single-selected-checker Setup and CLI. Same persistent profile, new context after each window closure; post-close live health displayed per platform. Actual app flow operated with manual login by the user. |
| One account, five concurrent worker pages | Implemented. Real Chromium fixture and scheduler barriers prove simultaneous target processing on five separate pages in one context. Round 3 unhealthy-account skipping and active-challenge stop retained. |
| Automated acceptance | **182 passed in 62.85 seconds**, zero skips. Earlier failed fixture runs retained in test log. |
| Live authentication | User clarified onboarding was incomplete because Continue was inaccessible. After maximized/resizable-window fix, the user completed onboarding; IG and Threads expected identities both verified. |
| Timing request | **95/95 targets returned in 1047.6569999999992 seconds**. Complete 0, Partial 14, Failed 81; every row has an extraction error. Five-minute usable-results target not met. Original 100-target acceptance was not run. |
| Suspended accounts | No login/browser attempt against checkers 1/2/3. Only checker_5 used; original-profile fallback not attempted. |
| Delivery | Requested delivery branch: fix/single-account-worker-concurrency. No merge/deletion. |

Task reports: [sequential setup](round4-sequential-login.md),
[concurrent pages](round4-worker-concurrency.md),
[benchmark decision](TSK-401-nfr1-benchmark.md).
[Test output](evidence/round4-maximized.txt), [test log](../test_log.md),
[problem log](../problem_log.md).

Observed remaining defects: profile readiness/identity failed on 49 IG and 60
Threads extractions; 33 Threads checks could not obtain the About menu item;
18 IG checks reached About polling without all requested fields. Actual captures
include loading splash screens and a menu spinner. These are extraction/readiness
failures after verified login, not evidence that five pages were missing.
Underlying server/network/rendering causes remain unproven. See the benchmark
report for counts, timing limitations, raw evidence and next diagnostic priorities.
