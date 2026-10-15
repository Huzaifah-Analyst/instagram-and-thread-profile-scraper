# Result quality, retained evidence and durable paths

2026-10-10. Implements P10, P17, P23 and the path fix for P24; corrects P26 docs.

## Implementation and reason

Results keep account status separate from Data quality: Complete, Partial,
Failed, or Not available. ACTIVE only indicates a positively identified profile;
an incomplete ACTIVE row is amber. Complete in Combined requires both platforms.
The table adds checker ID, and double-click opens the entire record, including
full error, per-platform stage, final URL and evidence paths.

GUI and CLI persist completed rows immediately to ignored `results/run_*.jsonl`,
plus run-start settings and final checker-health/stop information. A completed
row therefore survives a later process failure. Persistence errors fail visibly;
the UI does not silently pretend a save succeeded.

With debug enabled, page text, screenshots and stage metadata are saved locally
even on early login/menu failures. Raw dialog dumps remain available. Cookies,
passwords and full HTML are not deliberately dumped. Captures may contain the
logged-in person's visible account name and stay ignored/local.

Source runs use the project directory regardless of shell working directory.
Frozen runs use `%LOCALAPPDATA%/MetaInspector`, outside `_MEIPASS`. The current
development checker profile is retained as checker 1. Both headed and headless
production contexts explicitly select full Chromium, the browser variant the
existing build spec bundles.

## Alternatives and limits

Rejected: calling every ACTIVE row a successful extraction, inventing values
for absent fields, keeping only truncated errors, and storing login sessions in
temporary onefile extraction directories. JSONL was chosen as a small durable
diagnostic record format; this does not implement the previously advertised
SQLite history viewer or clipboard/Sheets export.

The executable has not been rebuilt or tested across restarts. The build spec's
cached-revision selection/dependency pinning (P25), prior 309.9 MB size finding
and clean-machine requirement (P27) remain open. README now describes implemented
capabilities and identifies the benchmark as unverified.

`test_health_and_validation.py` covers journal retention, Unicode fields,
quality semantics and frozen data-root selection. GUI bridge tests exercise
the real widgets. All exact execution results, including environment failures,
are in [test_log.md](../test_log.md).
