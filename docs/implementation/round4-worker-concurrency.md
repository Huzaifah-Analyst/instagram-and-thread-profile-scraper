# Round 4 Task 2 - worker pages on a single account

13 October 2026. Branch: `fix/single-account-worker-concurrency`.

Confirmed from the pre-change `run_pool`: it added one page per healthy checker
and exhausted the checker loop when only one checker existed. Workers=5 with one
healthy checker therefore produced **one worker**, not five. The older scraper's
`_open_pages` method and git revision `609a302` show the original multiple-pages
inside-one-context implementation. That method remained in the source but was
not called by the current pool. This concurrency regression is P50.

The pool now verifies available checker contexts as before, then distributes
spare worker slots over those healthy contexts in round-robin order. Each added
page has its own resource blocker and consumes the same shared target queue.
One checker can supply all five pages; two or three checkers share five pages.
Active checker IDs remain unique, so the UI does not report five healthy accounts
when five pages use one account. Result checker attribution is retained.

Failed setup/preflight accounts receive no pages or targets. Failure to allocate
an extra page records a warning and leaves existing workers usable, with bounded
allocation attempts. Context cleanup occurs once per context. Active-session
challenge still stops new queue assignments globally; in-flight targets may finish.

Alternatives considered: require five accounts (leaves the requested slots idle),
launch concurrent contexts against one profile directory (profile-lock conflict),
or reuse the old static chunk scheduler (loses current shared-queue resilience).
Allocating pages on verified existing contexts preserves the Round 3 design.

## Evidence

- Parameterized scheduler test with one, two and three healthy checkers requires
  **five distinct pages to enter extraction before any may finish**. Each case
  returns all 15 targets once; barriers prevent sequential execution passing.
- Actual Chromium test creates **one persistent context, five pages, five blocker
  instances and 20 fixture target results**. A concurrency barrier plus separate
  DOM assertions establish page isolation and simultaneous processing. Health
  and extraction are fixtures; this is not a live Meta throughput measurement.
- Existing mixed-health, target-exception and active-challenge regressions pass.
  Extra-page allocation failure also preserves the initial worker and its queue.
- Complete suite: **182 passed in 62.85s**, zero skips.
  [Output](evidence/round4-maximized.txt), tests in `tests/test_checker_pool.py` and
  `tests/test_round4_browser.py`.

Five concurrent pages increase concurrency on the same authenticated account;
they do not fix authentication or establish a measured speedup. Pacing and the
resource-blocker policy were not weakened. Live authentication subsequently succeeded. The actual 95-target Combined run
observed five distinct worker pages, one context, five blockers and only checker_5.
All 95 rows returned without unstarted targets, but extraction quality/speed
failed acceptance; see [Task 3](TSK-401-nfr1-benchmark.md).
