# Five independent checker sessions

2026-10-10. Implements P15, P16 and the configuration part of P20.

The latest user request authorizes implementation and accepts explicit manual
verification where agent-side live checks are unavailable. Earlier audit
reports describe the old single-session architecture, not this implementation.

## Implementation

- Five named slots, each with its own persistent Chromium directory. Checker 1
  reuses `browser_profile`; slots 2–5 use `checker_profiles/checker_N`.
- Setup opens an account manager. Each login opens official Instagram and
  Threads tabs. The operator completes passwords and 2FA in those tabs, then
  closes the browser. The application stores only slot selection, not passwords.
- Selected contexts remain open concurrently. One page per checker consumes
  a shared queue, with per-checker pacing. The worker setting caps active slots;
  selecting five workers with one enabled slot still uses one account.
- All active slots pass mode-specific live preflight before target assignment.
  A failed slot names the checker/platform and stops startup without target rows.
- Each result includes `checker_id`. Input order is retained in returned results;
  the live table displays completion order. A challenge stops new work globally;
  existing platform requests may finish, but no next platform/target is started.
- Exceptions cancel sibling tasks before contexts close. Duplicate profile
  paths are rejected. Operators must use a different real account in each slot;
  separate directories do not themselves prove distinct account identities.

## Why this method

A shared queue prevents duplicate targets and balances slow/fast profiles.
Independent browser contexts isolate cookies. Manual official login supports
email/2FA flows without collecting or scripting secrets.

Rejected: five pages in one context (still one checker account), copying one
session into five slots (no independent logins), and moving challenged work to
another account automatically (would mask the failure and violate the existing
global-stop behavior). This is workload distribution across healthy sessions,
not a promise of increased platform allowance or a measured speedup.

## Verification

`tests/test_checker_pool.py` runs the actual scheduler with fake browser/health
boundaries: five independent contexts handle 21 targets exactly once, all five
participate, records retain input order, and contexts close. It also checks
preflight failure, challenge stopping, settings corruption and duplicate paths.
The real Tk widgets are exercised in `tests/test_gui_bridge.py`.

Final suite: **113 passed in 13.51s**, zero skips. See [test log](../test_log.md)
for every execution, including earlier Tcl/environment failures. Five
authenticated live accounts have **not** yet been demonstrated.
No 100-account Combined benchmark or throughput claim is supported.

Use [manual verification](../manual_verification.md) for account setup and live checks.
