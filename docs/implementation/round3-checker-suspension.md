# Round 3 Task 5: actual checker suspension

12 October 2026. **Case (a) is now directly observed for checker_2**: its own
saved profile opens Instagram's `/accounts/suspended/` page. This is not a target
row returned as composite BANNED. The notice and screenshot were read directly:

- `We suspended your account`
- `Suspended on October 9, 2026`
- Meta describes the reason as its Community Standards on **account integrity**.
- The account is unusable and a **Request review** control is displayed.

[Raw text](../../debug/ig_checker_2_round3_health_20261012_172422_427169.txt),
[screenshot](../../debug/ig_checker_2_round3_health_20261012_172422_427169.png),
[route/identity metadata](../../debug/round3-health.json).
This is the profile currently bound to checker_2; the screenshot's display name
was not used to guess a username. No appeal/review was submitted by this task.

The displayed date predates this Round 3 execution on 12 October and the recorded
account-import implementation/live attempts on 10 October. It therefore does
not support blaming today's TOTP or login pacing for this suspension. It also
does not prove that older automation had no role: no account activity history,
prior ownership history or detailed Meta enforcement explanation is available.
The only observed reason is Meta's account-integrity notice; further causation
cannot be established from a stored cookie or our application logs.

Checker_1/3 also reached the suspended route but displayed verification controls;
their captures do not establish the same final notice or reason as checker_2.
Historical @howard.8991 screenshots show **BLOCKED**, meaning a checker-session
challenge, not FR-3 target BANNED. That older single-session evidence does not
identify which of today's imported checker slots was involved. These events
must not be conflated.

New handling classifies the suspended route before form entry/preflight success,
even with a stale session cookie or unhydrated body. At setup it skips that slot;
during an active check it remains a session-blocked global fail-safe. Regression
tests distinguish BLOCKED from target BANNED. Rejected: assigning a speculative
rate-limit cause, resetting profiles to hide the notice, or weakening TSK-403.
