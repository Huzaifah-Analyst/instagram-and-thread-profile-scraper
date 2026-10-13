# Round 5 Task 1 - resource blocker isolation

13 October 2026. Branch: `fix/extraction-root-cause-isolation`.

Protocol: same eight targets previously returning both IG fields in Round 4,
selected in their original input order; same checker_5 persistent profile,
Instagram-only, headless, workers=1, debug captures enabled, existing timeout
budgets, fixed six-second inter-target pacing in both conditions. Raw usernames,
field values and per-account timings remain local. No other checker is opened.
Runs are sequential; no browser tests or concurrent live runs run beside them.

The constructor now accepts `resource_blocker_enabled=True`; CLI supports
`--no-resource-blocker`. Initial and extra worker pages honor the switch. Default
behavior and GUI default remain enabled. This is diagnostic instrumentation,
not an assumed hydration fix.

Current blocker aborts image/media/font resource types and URLs ending in listed
media/font extensions. It otherwise continues document, script, stylesheet and
XHR/fetch requests. The extension check is independent of the resource type.
Network response/failure counts are recorded without response bodies or cookies.

Alternatives: temporarily comment out route attachment (hard to reproduce and
could accidentally ship disabled), change timing simultaneously (confounds the
comparison), or use unrelated targets (cannot separate target availability).
Each was rejected. Browser cache/session/server conditions may still change over
sequential runs; a difference alone does not identify a particular bad request.

Live measurements will be recorded after each completed condition. No root-cause
conclusion or extraction-policy change is claimed before those results.


## Completed comparison

| Condition | IG country + date | Loading-logo-stuck outcomes | Whole run seconds |
| --- | --- | --- | --- |
| Blocker ON, 1 worker | 8/8 | 0 | 93.82900000000154 |
| Blocker OFF, 1 worker | 8/8 | 0 | 74.96799999999712 |

Both produced Complete rows without errors; the identical ordered target-list
hash is retained with both local records. OFF was faster in this ordered pair,
but did not repair a failed extraction: ON already succeeded 8/8. Thus these
conditions do not reproduce a hydration-breaking blocker defect. Default ON is
retained for Task 2. This does not rule out a blocker/concurrency interaction or
identify why the earlier large Combined run had loading failures.

[ON raw timings/captures](../../debug/round5-t1-on.json),
[OFF raw timings/captures](../../debug/round5-t1-off.json).


## Interaction and routing-mechanism controls

At five pages, original blocker ON returned 3/8 complete in 42.89099999999962s;
OFF returned 8/8 in 30.01599999999962s. An additional **wildcard-route pass-through**
control attached the old handler but continued every request: **zero resources
were policy-aborted**, yet only 3/8 completed in 41.93800000000192s. Therefore the
failed condition does not require a misclassified/stripped asset.

Installed Playwright `Page.route` documentation states that enabling routing
turns off HTTP cache. The new local HTTP regression independently proves the
old blocker requests a cacheable script twice across two navigations; the fixed
blocker requests it once. Old-handler negative control intentionally fails that
assertion. These establish a routing/cache defect; the live experiment does not
separate every millisecond of cache loss from Python round-trip overhead.

The repair uses Chromium CDP Fetch patterns for Image/Media/Font/Other only.
Critical documents, scripts, CSS, XHR and Fetch are not intercepted. Other uses
the existing extension fallback. No wildcard Page.route hook is installed and
HTTP cache remains available. Media/font blocking stays enabled by default.
A live five-page recheck with the corrected blocker returned **8/8 in
28.1720000000023 seconds**, with images still blocked. No country/date parser,
identity requirement or timeout budget was weakened.

[Pass-through raw](../../debug/round5-t3-route-pass.json),
[corrected raw](../../debug/round5-t3-selective.json),
[old-handler negative control](evidence/round5-negative-cache.txt).
The requested single larger Combined recheck is reported separately in Task 3.
