# Round 3 Task 4: missing targets and error isolation

12 October 2026. Two different cases must remain distinct.

The supplied 95-target screenshot explicitly reports **27 returned**, then a
checker challenge stop. The other **68 have no returned rows**. The screenshot
alone cannot reconstruct every in-flight assignment, because no journal/debug
capture was enabled. It is consistent with stopping before finishing the queue;
it is not evidence that 95 targets were attempted or that 68 completed results
vanished. Historical single-context concurrent pages also explain why some
already in-flight rows arrived after a BLOCKED row.

A separate source defect was reproduced: `_consume` claimed a target, awaited
`_check_account` without a general exception boundary, and used `gather` whose
cleanup cancelled sibling tasks after an exception. A non-Playwright exception
could therefore lose a claimed target and interrupt unrelated workers. Also,
the single try block around both extractors skipped Threads after an IG exception.

The shared queue now emits an explicit ERROR row for an unexpected target error
or absent result status and continues. Each platform has its own extraction
boundary. A journal write failure is visible but does not suppress UI/memory
results. Results retain input order, checker attribution and the original
exception class without secret-bearing exception messages.

`unstarted_usernames` is tracked separately from returned/attempted rows and
saved in the finished journal event. The GUI distinguishes checked and unstarted
counts and exposes checker-health/storage warnings. It does not fabricate
successful or failed extraction rows for targets never assigned.

Tests exercise twenty targets with target_2 raising ValueError: all twenty
records return in order, exactly one error row, no stop. The challenge regression
has thirty queued, five in flight/returned and twenty-five explicitly unstarted;
no new target is assigned after BLOCKED. A platform exception regression confirms
Threads still returns its date after IG errors. Existing chunk tests cover
balanced no-loss splitting; the live pool uses a shared queue, not static chunks.
Input normalization deliberately removes blank and duplicate handles and rejects
invalid input visibly; those are not lost attempted targets.

Rejected: counting never-started targets as failures to make progress show 100%,
retrying challenged targets on another checker, or claiming the source defect
caused the historical screenshot without an assignment journal. Shared process
termination can still interrupt work; already written rows survive in the journal.
