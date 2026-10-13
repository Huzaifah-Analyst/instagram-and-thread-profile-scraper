# Round 3 Task 3: Threads evidence and limits

12 October 2026. There is no single proven cause covering every historical
Threads error. This round found concrete authentication/setup failures before
target extraction could be attempted with a healthy checker.

## Observed causes of these attempts

1. Checker_1 had an IG session cookie but **no Threads session cookie**. Its
   visible continuation button's concatenated DOM text was
   `Continue with InstagramLog in`. The previous anchored expression accepted
   only `Continue with Instagram`. That DOM text alone does not establish the
   browser's full accessible name; the recorded fixture proves compatibility
   with that variant, not a live successful click on this account.
   The exact compound form is now recognized and exercised in local Chromium.
   Live continuation and whether the restricted IG account could ultimately
   authenticate Threads were not established for checker_1.
2. Checker_2/3 remained on a Threads password form without a Threads cookie after
   one submission. Saved metadata contains no invalid-code/password rejection
   marker. We cannot distinguish a server refusal from another UI/network
   progression failure from this capture; no root cause is invented.
3. Checker_4/5 reached `/onboarding/` with a cookie and no verified profile
   identity. Read-only navigation to Threads home then returned the actual page
   text `Not all who wander are lost, but this page is`, followed by a broken-link
   explanation. Both screenshots were saved; checker_5's screenshot was directly
   inspected. Neither page contains a target profile or its More/About controls.
   Cookie presence was insufficient; the home-error screen is now rejected in
   preflight and onboarding is reported as requiring manual completion.

Evidence, all local and ignored:

- [Login/control observations](../../debug/round3-login.json).
- [Checker 4 page text](../../debug/threads_checker_4_round3_health_20261012_172436_360089.txt).
- [Checker 5 page text](../../debug/threads_checker_5_round3_health_20261012_172448_197103.txt)
  and [screenshot](../../debug/threads_checker_5_round3_health_20261012_172448_197103.png).
- [Capture URLs and identity results](../../debug/round3-health.json).

No working dual-platform session remained, so the directive's gate prevented a
fresh target-menu experiment. The current More SVG/coordinate selector was
**not** demonstrated wrong on an authenticated current target DOM. Nor does a
loaded broken-page screen prove that a longer hydration timeout would fix it.
An earlier actual Threads capture read October 2025 / Not shared; another earlier
failure showed only a loading logo. Those are distinct observed states, not a
general conclusion that every Threads failure is a selector or timeout bug.

Method: inspect actual page text, path, visible controls and platform-specific
cookie/identity state. Rejected: guessing a new SVG coordinate, increasing all
timeouts, or treating an IG login as Threads authentication. Remaining work is a
fresh authenticated target capture after manual setup restores at least one
checker; server-side reason for the onboarding/broken-page response is unknown.

## Actual app follow-up, 13 October 2026

The agent drove the actual Setup and checker_5 Login controls. Its IG feed passed
identity verification; Threads offered the distinct `Join using your Meta Account`
button. Selecting the real visible control by its text and expected username
reached **Privacy: Public profile / Private profile** at `/onboarding/`. This is
direct evidence of incomplete profile setup. The prior generic home-error screen
did not establish that this setup could not be completed through its login flow.

The user subsequently authorized Private. A fresh saved-account continuation returned the visible Something went wrong alert; setup remains incomplete. No final
profile creation or successful Threads identity check is claimed yet. See
[actual GUI follow-up and raw evidence](round3-live-checker-logins.md).
