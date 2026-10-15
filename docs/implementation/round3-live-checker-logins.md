# Round 3 Task 2: actual checker login outcomes

12 October 2026. All five imported account/profile bindings were attempted,
with IG and Threads checked independently. Secrets stayed in memory; no passwords,
authenticator seeds, OTP values or cookies are included in committed evidence.

**Verified this run: IG 1/5 (checker_5), Threads 0/5, both platforms 0/5.**
Cookie presence alone is not counted as successful authentication. These counts
describe this attempt, not the historical checker_1 success on 10 October.

| Checker | Instagram observation | Threads observation |
| --- | --- | --- |
| checker_1 | `/accounts/suspended/`; telephone field and Send code, session cookie present; identity unverified. No credentials submitted this attempt. | Home/login continuation, no Threads session cookie; compound button `Continue with InstagramLog in` not recognized by old exact selector. |
| checker_2 | `/accounts/suspended/`; actual notice says suspended October 9, 2026 for account integrity; Request review. | Password submitted once; still `/login`, no Threads session cookie. No rejection marker captured; cause of non-completion remains unknown. |
| checker_3 | `/accounts/suspended/`; manual verification marker and Next control. This is not evidence of an identical final suspension notice to checker_2. | Password submitted once; still `/login`, no Threads session cookie; reason not established. |
| checker_4 | Browser error at `/accounts/onetap/`, cookie present but identity unverified. | Browser error at `/onboarding/`, cookie present but identity unverified; fresh read-only home visit returned broken-page screen. |
| checker_5 | Expected imported identity and IG cookie both verified. | Browser error at `/onboarding/`, cookie present but identity unverified; fresh read-only home visit returned broken-page screen. |

Exact per-platform timings, route paths, control metadata and outcomes:
[round3-login.json](../../debug/round3-login.json). Each outcome was written as it
completed. [Summary](../../debug/round3-login-summary.txt) and
[read-only health index](../../debug/round3-health.json) are local ignored files.
No profile was deleted/reset and no suspension appeal or onboarding form was
submitted by the diagnostic.

The observed gaps led to explicit suspension/onboarding outcome messages,
recognition of the exact compound Threads continuation button, and a broken-home
page preflight rejection. Synthetic Chromium regressions cover those changes.
They have **not** been revalidated as successful real login fixes: account-health
and onboarding blockers require operator attention first. Repeated password/OTP
submissions were rejected as an alternative because the captured pages do not
establish that credentials are wrong or that another submission would help.

To recover: restart `python main.py`, open Setup Checker Account and use
checker_5's **Login IG + Threads**. Complete any displayed Threads setup manually;
verify an actual feed and your own Profile link, then close the setup browser.
For checker_2 use the displayed review process if appropriate. Checker_1/3 need
their own verification steps; do not assume checker_2's notice applies to them.
The app can then preflight and use whichever selected checkers are healthy.

## Agent-operated actual desktop follow-up, 12?13 October

The user requested that verification be performed inside the actual application.
The agent instantiated the production MetaInspectorApp with its default scraper,
invoked its rendered Setup button and checker_5's actual Login IG + Threads button.
The normal login_session created the real headed browser. A diagnostic observer
attached to that real context; no page responses or authentication were mocked.
Actual app and Setup window screenshots were inspected. Early screen-region
captures were obscured by another application and were discarded; replacement
captures target the app window directly.

IG loaded its real feed and passed the imported-identity check repeatedly.
Threads displayed a distinct `Join using your Meta Account` continuation for
checker_5. Selecting that visible button, scoped to the same username, navigated
to `/onboarding/`. Although Playwright's click wait timed out during navigation,
subsequent raw text/screenshot capture showed **Privacy: Public profile / Private
profile**, with Public visually selected. This is now a concrete incomplete
Threads setup, rather than only a generic broken-page symptom.

The agent requested the user's privacy preference before completing that choice.
No final registration/profile-creation action or visibility change was submitted.
Both-platform authentication is still unverified; no Combined benchmark follows
until setup completes and the actual Threads identity/feed is verified.

Evidence: [GUI event log](../../debug/gui-self-verify.jsonl),
[final continuation output](../../debug/gui-self-verify-meta-continuation-output.txt),
[Privacy text](../../debug/threads_checker_5_gui_verification_20261012_190247_496073.txt),
[Privacy screenshot](../../debug/threads_checker_5_gui_verification_20261012_190247_496073.png).
The capture filename is UTC October 12; the Privacy observation is October 13
in Asia/Karachi. Full application verification does not require the user to
perform every click; this remaining choice concerns their profile visibility.

## Private choice authorized, 13 October 2026

The user explicitly chose **Private profile**. This preference remains authorized;
no further permission for that choice is required. The resumed actual-app session
verified IG, but Threads initially showed its broken-link page. Navigating the
known onboarding path restored a login screen. A saved-account continuation later
returned an actual **Something went wrong** alert on `/login/`, captured in the
ARIA tree and screenshot. The Private selection and final setup were **not**
submitted in this attempt. Threads identity remains unverified, so a Combined
sample/benchmark was not started. The visible error is evidence of failure,
not a diagnosis of Meta's underlying account/server reason.

[Exact alert capture](../../debug/threads_checker_5_private_setup_20261013_063549_466706.json),
[actual app diagnostic](../../debug/gui-private-control-diagnosis.txt).
An earlier attempt's generic TimeoutError did not establish that the Private
control itself was blocked; that intermediate interpretation is superseded by
this exact capture. No phone/CAPTCHA/privacy step is being delegated back merely
because automation is inconvenient.

The observed saved Meta-account control is now supported by production auto-login,
with exact username scoping and explicit alert reporting. **172 tests passed in
29.19s**. [Implementation and limits](threads-saved-account-card.md). This local
fix does not establish successful live onboarding or resolve the visible Meta error.
