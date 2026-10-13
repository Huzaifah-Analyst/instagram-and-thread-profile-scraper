# Current Threads Meta-account continuation

13 October 2026. P47/P49; `fix/resilience-and-root-cause`.

The agent opened the actual desktop app and operated its real Setup controls.
Live Threads login showed a saved-account button whose accessible name includes
an image description, the label Join using your Meta Account, the checker
username and Log in. The earlier exact-name expressions cannot recognize that
current layout. Its concatenated DOM text is not its accessible name.

Auto-login now locates the visible saved-account button by the observed label
and requires an exact visible child matching the imported username. It checks
the official HTTPS origin before clicking. A different saved account is ignored.
This path is preferred to re-entering the password; while its result is pending,
the password form is not submitted. An actual visible alert saying Something
went wrong now produces an explicit unsuccessful login outcome.

Alternatives rejected: clicking the first generic Join button (could select the
wrong account or another action), matching the entire accessible name including
image alt text (fragile), submitting credentials again while continuation is
pending, or declaring that IG cookies prove Threads login. No final profile
creation, privacy choice or appeal is automated by this generic login helper.
The user's Private choice applies to checker_5's authorized live setup attempt.

Actual Chromium regressions include the image-alt prefix, separate password
form and competing wrong-account card. They verify both successful identity
and a delayed error alert, with zero password submission. Full suite:
**172 passed in 29.19s**, zero skips.
[Evidence](evidence/meta-card-final.txt), [all attempts](../test_log.md).

The live continuation itself reached Privacy during the earlier GUI diagnostic.
After the user approved Private, subsequent attempts returned login errors;
the final exact capture contains Something went wrong. Private selection/final
setup has not completed, and neither Threads identity nor Combined throughput
is claimed. See [per-checker evidence](round3-live-checker-logins.md).
