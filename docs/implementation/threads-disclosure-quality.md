# Threads country disclosure is not a country value

2026-10-10, P32. Found while verifying the newly authenticated live session.

The exact About panel contained this structure (identity anonymized):

```text
Name
Example (@target)
Joined
October 2025 · 100M+
Based in
Not shared
```

The parser correctly copied the values. However, `build_record` counted every
nonempty country string as Complete, including **Not shared**. That overstated
the amount of disclosed data.

The fix preserves the source text **Not shared** for display, records explicit
`country_availability=not_shared`, explains the disclosure in the result, and
marks the row Partial when a date is available but the country is not disclosed.
No country is inferred or copied from Instagram. The date and badge are retained.

Rejected alternatives: replacing the value with China from Instagram (different
platform field), hiding the disclosure as a generic N/A, or reporting Complete
just because reading the panel succeeded. Data quality describes available
requested data, while the `complete` extraction stage describes the UI workflow.

Added an anonymized regression using the exact captured label/value structure.
Also check the smallest eligible Threads fallback container before larger page
ancestors, so a short profile's bio cannot override the nested About fields;
this is covered by an actual Chromium synthetic DOM fixture. Fresh live and full
suite outcomes are recorded in [test_log.md](../test_log.md).

Final suite: **113 passed in 13.51s**, zero skips. The fresh live recheck failed
before either transparency panel loaded (62.0s total / 43.41s row). Thus the exact
captured-value regression passes, but a successful live post-fix classification
has not been observed. No fresh field values are claimed for that failed run.
