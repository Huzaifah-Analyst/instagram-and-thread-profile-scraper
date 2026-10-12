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
