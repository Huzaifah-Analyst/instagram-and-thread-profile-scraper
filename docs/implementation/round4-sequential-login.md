# Round 4 Task 1 - sequential manual login

13 October 2026. Branch: `fix/single-account-worker-concurrency`.

The default Setup action for exactly one selected checker now opens one headed
Chromium window containing the Instagram login page. After the user closes it,
the application launches a second window containing only the Threads login page.
After that closes, a headless context runs the existing combined live preflight
and expected-username check. The result names each platform and its specific
failure, or explicitly says both logins verified. CLI login prints this summary.

The same persistent **profile directory** is reused sequentially. A context that
closed with its browser cannot itself be reused, so the implementation relaunches
the context after each closure. There is no overlap or copying of credentials.
This manual flow does not read the account import file, generate TOTP, submit
passwords, or click profile-creation controls. App closure cancels the flow before
another window opens. Existing multi-account import remains under Manage checkers.

Alternatives considered: keep two simultaneous tabs (does not match the request),
reuse a closed context (not possible), infer success from window closure or a
saved cookie (does not verify the requested identity/platform). These were rejected.

## Tests

- Controlled closure tests assert IG close precedes Threads launch and both close
  before preflight; incomplete Threads results remain explicit.
- A real Chromium regression launches two headed windows then headless preflight,
  each on the same isolated profile. A persistent fixture cookie survives the
  relaunches. All traffic is locally fulfilled and authentication results are
  fixture values: this proves lifecycle, not real Meta authentication.
- Real Tk Setup-button regression directly selects the single checker; manager
  and import regressions continue to pass. Cancellation prevents Threads launch.
- Complete suite: **182 passed in 62.85s**, zero skips.
  [Output](evidence/round4-maximized.txt), [all runs](../test_log.md).

## Live result and operator

The agent selected only checker_5 and invoked the actual app's Setup button.
**The user performed the manual login interactions**, then reported both windows
complete and closed. App-driven post-close verification reported:

- Instagram: Logged in (live verified).
- Threads: home page unavailable; platform returned its broken-link page.

A separate read-only headed inspection subsequently showed public Threads posts
with a visible **Log in or sign up for Threads** prompt. Own-profile identity was
false. This does not prove successful Threads login or establish why login did
not survive/complete. No benchmark was started from this unauthenticated state.

Local ignored evidence: [app summary](../../debug/round4-manual-status.json),
[read-only diagnostic](../../debug/round4-readonly-health.json),
[Threads home screenshot](../../debug/threads_checker_5_round4_home_20261013_093052_000149.png).
Checkers 1/2/3 were not opened or logged into; the original browser_profile fallback
and checker_4 were not opened either. Existing account bindings were preserved;
only enabled selection changed to checker_5 for this round.


## Resolved live setup after window sizing correction

The user clarified that the first Threads window remained on onboarding:
Continue was inaccessible and scrolling did not work. Manual windows now use
`no_viewport=True` and `--start-maximized`, allowing native resizing instead of
forcing the 1280x800 viewport. Extraction/preflight viewport settings are unchanged.
Both controlled and real Chromium tests assert this window configuration.

The actual app setup was reopened for checker_5. The user completed onboarding
manually and closed the windows. Post-close live preflight now reports **Both
logins verified**, including both expected platform identities. This supersedes
the earlier failed attempt above. [Sanitized final summary](evidence/round4-live-setup.json).
The following 95-target run independently passed both platform preflights again.
Only checker_5 was used; checkers 1/2/3 were not touched.
