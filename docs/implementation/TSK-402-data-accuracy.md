# TSK-402: data accuracy investigation blocked by unauthenticated live page

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`,
created from the up-to-date `fix/live-test-findings` branch.

## Exact commands and observed evidence

Local preflight:

```text
python -c "from pathlib import Path; from src.core.session import check_session; print(check_session(Path('browser_profile')))"
('connected', 'Instagram session found')
```

This function checks cookie names and expiration metadata, not server acceptance.

Controlled batch (10 unique entries from the existing local 95-account list):

```text
python -m src.core.scraper --file debug/round2_control_usernames.txt --mode combined --workers 1 --debug-dump
```

First sandbox attempt encountered `net::ERR_NETWORK_ACCESS_DENIED` and was
interrupted. Approved unrestricted retry completed all 10 records and printed:

```text
10 accounts in 193.8s | assets blocked: 641
```

The redirected PowerShell invocation reported exit 1 and wrapped the initial
stderr logging record as `NativeCommandError`; its captured output nonetheless
contains all 10 JSON records and the completion summary, without a traceback.
This is the CLI's displayed precision, not a higher-precision elapsed measurement.

Observed record breakdown:

| Outcome | Count |
| --- | ---: |
| Country and joined date for both platforms | 0 |
| Any country or joined date | 0 |
| All four fields null, with explanatory errors | 10 |
| Composite ACTIVE | 10 |
| NOT_FOUND | 0 |
| PRIVATE platform status | 0 |
| BLOCKED | 0 |
| IG options (...) button not found | 10 |
| Threads 'About this profile' option not found | 9 |
| Threads profile menu not found | 1 |

No `ig_*.txt` or `threads_*.txt` dialog captures were produced. The existing
dump implementation only writes when dialog text was read; enabling debug dump
does not guarantee a file when failure occurs before dialog polling.

A subsequent one-profile diagnostic, `python -m debug.round2_session_health`,
used the same persistent profile, saved visible body text and a full-page
screenshot without the resource blocker, and exited 0. The inspected screenshot
shows **Log In / Sign Up**, a public profile, and no Options control. Saved
metadata has `header_count: 1`, `options_count: 0`, `challenge: null`.
The detector did not flag this public unauthenticated page as session-blocked.

Local evidence (intentionally ignored, containing client identifiers):

- [Controlled CLI output](../../debug/round2_control_cli_unrestricted.txt)
- [Visible page text](../../debug/round2_session_health_body.txt)
- [Inspected screenshot](../../debug/round2_session_health.png)
- [Page metadata](../../debug/round2_session_health.json)
- [Diagnostic script](../../debug/round2_session_health.py)

## Conclusion and changes

The saved cookie preflight is insufficient: this observed browser page is
unauthenticated. A working checker session was not available for transparency
verification. Live testing stopped at this prerequisite failure; manual checker
re-authentication through Setup Checker Account is needed. No credentials were
requested or edited, and no login was performed by this session.

Neither the parsing-bug hypothesis nor the Meta-served repeated-date hypothesis
is confirmed. There is **no raw transparency text** from this run with which to
answer the October 2025 question. No parser, selectors, timeout settings, session
code, or other application source was changed. No speculative fixture was added.

## Alternatives considered and rejected

- Altering DATE_KEYS or label matching: rejected because no captured dialog
  demonstrates an incorrect label match; it could break tested Threads formats.
- Two consecutive confirmations: would repeat an unauthenticated request and
  cannot establish that a repeated server value is correct.
- Cross-checking a known-good account: useful after login is restored, but a
  known historical date does not make this unauthenticated browser usable.
- Continuing the 100-account benchmark: rejected by the directive's accuracy
  and working-session gates.
- Automatically repairing cookie state: not attempted; the reason the server
  rejects or fails to use the saved login was not established by this diagnostic.

All attempts are recorded in [the running test log](../test_log.md).
