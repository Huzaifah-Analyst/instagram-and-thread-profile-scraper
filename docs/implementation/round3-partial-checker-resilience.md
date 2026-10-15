# Round 3 Task 1: partial checker health

12 October 2026, `fix/resilience-and-root-cause`.

Setup and preflight now isolate failures by account. A failed browser launch,
platform login or preflight records a reason and allows later accounts to run.
The pool selects up to the worker limit from healthy selected profiles, rather
than consuming that limit with failed launches. Unhealthy preflight contexts
close before checking begins. Both requested platforms receive their own health
entry, including when one preflight raises unexpectedly.

Automatic setup attempts all five supplied accounts sequentially. It reports
both-platform and per-platform verified counts plus each account's failure.
Failed windows close; the prior indefinite manual-completion wait no longer
blocks later accounts. The separate **Login IG + Threads** action remains the
manual recovery path. A scrollable setup-results window keeps the complete
summary readable rather than truncating five outcomes into one status line.

Method: retain one persistent context/page per checker and the shared queue.
Rejected: five pages sharing one account, automatic reassignment of a challenged
target, or weakening the mid-run global stop. A requested Combined checker still
must pass both platform preflights; an IG-only run can use an IG-only healthy slot.

Regression proof in `tests/test_checker_pool.py`:

- Three healthy plus two unhealthy contexts complete twelve targets using only
  checker_1, checker_3 and checker_5; no global stop and no unstarted targets.
- A first browser launch failure with one worker still uses checker_2.
- Zero healthy contexts produce no fabricated target rows and an explicit reason.
- A live-session BLOCKED result stops further assignment; five in-flight results
  remain, and twenty-five never-started targets are explicitly listed.

`tests/test_auto_login.py` proves account 2 failure still attempts accounts 3–5
on both platforms. The real five-account setup also attempted all ten platform
logins, though it did not establish any healthy Combined checker. See
[Task 2](round3-live-checker-logins.md) and [all test executions](../test_log.md).

## Cross-cutting hard-stop audit

| Boundary | Result |
| --- | --- |
| Individual launch/preflight/login failure | Record and continue with later slots. |
| One platform extraction exception | Record its error; still check the other requested platform. |
| Unexpected target-processing exception/missing status | Persist an ERROR row for that claimed target; continue queue. |
| Journal I/O/serialization failure | Log and expose storage warning; preserve memory/UI results and continue. |
| GUI callback failure | Existing logged isolation retained. |
| Active mid-run checker challenge | Global TSK-403 stop retained, including prevention of next platform. |
| User cancellation/Stop/app close | Explicit operator action retained. |
| No healthy checker, invalid configuration/input, unavailable shared Playwright service | No usable work can be assigned; actionable failure retained. These are not one-account failures. |

Credential-file validation still rejects a malformed file before any secret is
submitted: an invalid or ambiguous profile binding must not partially alter
stored checker identities. The GUI bridge retains its final crash boundary for
shared service failure; already emitted rows remain visible and journalled when
storage is available. Process termination cannot guarantee an in-flight result.
