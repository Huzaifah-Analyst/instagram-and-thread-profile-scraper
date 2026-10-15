# Manual verification: five checker accounts

Run from the project folder:

```powershell
python main.py
```

Close an older running app first; it keeps the old imported Python code until
restarted. The existing `dist` executable has not been rebuilt with these changes.

## Setup

1. Click **Setup Checker Account**. There are five independent slots.
2. Click **Login IG + Threads** for Checker 1. Complete official login/2FA in
   both browser tabs. Confirm Instagram and Threads feeds load, then close the
   entire setup browser. If it is behind the app, select Chromium with Alt+Tab.
3. Repeat for Checkers 2–5 with a different real account in each slot. The login
   windows are set up one at a time; all saved sessions can run concurrently.
4. Tick the slots to use and **Save selection**. This manual method does not
   require a credential file.

## Automatic setup from the supplied account file

1. Restart with `python main.py`, open **Setup Checker Account**, then click
   **Import accounts & auto-login** and select `docs/accounts.txt`.
2. The file must contain one `username|password|2FA secret` row per checker, up to
   five accounts. The current file has no separate email column. Codes are
   generated locally from the authenticator secrets; keep Windows time correct.
3. Watch the status bar and visible browser. Each account signs into Instagram
   then Threads in its own profile. Password/2FA values are not shown in app logs.
   Browser setup is sequential; target checks can later run across five profiles.
   On **Go to your authentication app**, the **Code** field and Continue button
   are handled automatically by the import flow. The separate **Login IG +
   Threads** button opens the manual-login flow and does not load file credentials.
4. If Meta asks for a checkpoint, CAPTCHA, email/SMS code or an unfamiliar step,
   automatic setup records the failure, closes that browser and tries later
   accounts. After the summary appears, reopen the affected slot with **Login IG
   + Threads**, complete the official manual steps and close its browser.
5. Only the message **All 5 accounts verified on Instagram and Threads** confirms
   all five completed setup. The summary also shows separate IG/Threads counts
   and each account's outcome. Healthy subsets can be used without waiting for five.
6. Open Setup again: check that the expected username appears beside each slot.
   Select the ready slots, save, set **Checker limit 5**, and run a small Combined
   batch using the accuracy checks below. Start performs a new live login check.

The app preserves old manual profiles and keeps imported profiles tied to their
username even if the file order changes. The supplied text file still contains
credentials on your disk; the app does not delete it or make a second copy.

## Verify accuracy before a batch

1. First enable one verified healthy checker, choose **Instagram Only**, **Checker limit 1**,
   and turn **Save debug captures** on. Check `brenda_1074`.
2. Compare the exact same username in Instagram's About dialog. The user-supplied
   reference showed **October 2025 / China**. `brenna1074` is a different account.
3. Choose **Threads Only** and a target whose About information you can manually
   see in Threads. Compare its exact raw displayed fields. An absent country is
   missing data, not a country to infer from the profile's name or language.
4. Then use Combined on a small set. Double-click each row: inspect stages,
   errors, source URLs and evidence. ACTIVE with Failed/Partial is not a complete
   extraction. If login is required, return to the named checker slot's Setup.
5. Enable the healthy logged-in slots, set **Checker limit 5**, and use at least five
   targets. The **Checker** column identifies assignment. Each target should
   appear once; a challenge stops new work rather than reassigning it invisibly.

Latest live findings (12 October): checker_5 alone passed IG; none passed Threads.
Start recovery with checker_5's Threads setup. Checker_2 has an actual suspension
notice; checker_1/3 need their own verification. See the
[per-checker findings](implementation/round3-live-checker-logins.md). Do not begin
the Combined benchmark until a real Threads feed/profile login is working.

Results are retained in `results/run_*.jsonl`; screenshots/text/metadata are in
`debug/`. In the frozen build their planned location is
`%LOCALAPPDATA%/MetaInspector`; frozen restart behavior still needs a release test.

## Automated checks if agent-side permission review is unavailable

From a normal PowerShell terminal in this project, with the setup browser closed:

```powershell
python -m pytest -q -rs > docs/implementation/evidence/checker-pool-pytest-manual.txt 2>&1
python -m src.core.scraper brenda_1074 --mode combined --workers 1 --debug-dump > debug/combined-manual.txt 2>&1
```

The agent can inspect these saved outputs locally. Do not send passwords or 2FA
codes. Review and record outcomes in `docs/test_log.md`, including failures.
The 100-account / under-five-minute benchmark remains unverified; do not use a
batch of failed/partial rows to claim that performance requirement is met.
