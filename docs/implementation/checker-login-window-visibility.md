# Checker login window visibility diagnostic

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.

The user reported that Setup Checker Account opened no browser from
`python main.py`. Their screenshot showed the setup/start controls disabled
and the login instruction still displayed.

Live process inspection found Python PID 4144 running `main.py`, Playwright's
driver PID 14344, and its Chromium child PID 13212 using this workspace's
`browser_profile`. Chromium had no headless flag and had a real window titled
`Instagram - Google Chrome for Testing`, handle 67942. This establishes that
the browser launched; it does not establish successful account login.

Restored that existing window with Windows `ShowWindowAsync(handle, 9)` and
requested foreground activation with `SetForegroundWindow`. The actual output
was `ForegroundRequest: True`, `ForegroundMatches: True` (checked using
`GetForegroundWindow`). No application source was changed.

Restoring the existing window was chosen because it was already open and
owned by the app's login driver. Opening another persistent browser would risk
a profile-lock conflict. Reinstalling Chromium or rewriting setup was rejected
because the live browser process and window demonstrate successful launch.
No processes were terminated or browser profiles modified by this diagnostic.

The user must still complete login and close the browser. Successful login,
transparency extraction and NFR-1 remain unverified by this diagnostic.
