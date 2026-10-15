"""Field-level and failure-level analysis of a benchmark output file.

Reads the production CLI's stdout (one JSON record per line plus a final
summary line) and reports, per data field, how many targets produced a real
value, how many did not, and the reason each missing value had -- grouped by
extraction stage, error text and the platform's own disclosure state. Nothing
is inferred: every count comes from the record fields the extractor wrote.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = (
    ("ig_country", "ig"), ("ig_date_joined", "ig"),
    ("threads_country", "threads"), ("threads_date_joined", "threads"),
    ("threads_badge", "threads"),
)


def load(path: Path) -> tuple[list[dict], float | None]:
    """Return parsed records and the CLI's reported elapsed seconds, if present."""
    records: list[dict] = []
    elapsed: float | None = None
    raw = path.read_bytes()
    text = raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8-sig")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                logging.warning("Ignoring malformed JSON output line: %s", exc)
                continue
            if "username" in row:
                records.append(row)
        else:
            found = re.search(r"accounts in ([\d.]+)s", line)
            if found:
                elapsed = float(found.group(1))
    return records, elapsed


def field_state(row: dict, field: str, platform: str) -> str:
    """Classify a field, treating literal Not shared as withheld, not present."""
    value = row.get(field)
    country = field.endswith("_country")
    if value and not (country and str(value).strip().casefold() == "not shared"):
        return "present"
    status = row.get(f"{platform}_status")
    if status == "not_found":
        return "account-does-not-exist"
    if status in (None, "skipped", "skipped_ig_sufficient"):
        return "not-checked"
    if row.get("checking_mode") == "ig_status_only":
        return "unavailable-in-mode"
    if country and (row.get(f"{platform}_country_availability") in ("not_shared", "not_disclosed")
                    or (value and str(value).strip().casefold() == "not shared")):
        return "platform-withheld"
    return "extraction-failed"


def aggregate(records: list[dict], elapsed: float | None) -> dict:
    """Return shareable counts without usernames, source URLs or field values."""
    fields = {field: dict(Counter(field_state(row, field, platform) for row in records))
              for field, platform in FIELDS}
    return {
        "elapsed_seconds": elapsed, "rows": len(records),
        "unique_rows": len({row["username"].casefold() for row in records}),
        "meets_300_seconds": elapsed is not None and elapsed <= 300 and len(records) == 100,
        "fields": fields,
        "quality": dict(Counter(row.get("data_quality") for row in records)),
        "status": dict(Counter(row.get("composite_status") for row in records)),
        "checkers": dict(Counter(row.get("checker_id") for row in records)),
    }


def main() -> None:
    """Print the full breakdown for the given output file."""
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "debug/round7_benchmark100_output.txt")
    records, elapsed = load(path)
    if "--aggregate" in sys.argv:
        print(json.dumps(aggregate(records, elapsed), indent=2))
        return
    total = len(records)
    print(f"=== RUN: {path} ===")
    print(f"rows returned: {total}")
    print(f"CLI elapsed seconds: {elapsed}")
    if elapsed and total:
        print(f"seconds per target: {elapsed / total:.2f}")
        print(f"5-minute (300s) target: {'MET' if elapsed <= 300 else 'NOT MET'}")
    print()

    print("=== COMPOSITE STATUS ===")
    for key, count in Counter(r.get("composite_status") for r in records).most_common():
        print(f"  {key}: {count}")
    print()

    print("=== DATA QUALITY ===")
    for key, count in Counter(r.get("data_quality") for r in records).most_common():
        print(f"  {key}: {count}")
    print()

    print("=== STAGE REACHED (per platform) ===")
    for platform in ("ig", "threads"):
        counts = Counter(r.get(f"{platform}_stage") for r in records)
        print(f"  {platform}: {dict(counts.most_common())}")
    print()

    print("=== FIELD-LEVEL COMPLETENESS ===")
    for field, platform in FIELDS:
        got = [r for r in records if field_state(r, field, platform) == "present"]
        missing = [r for r in records if field_state(r, field, platform) != "present"]
        print(f"\n  {field}: {len(got)}/{total} present, {len(missing)} missing")
        reasons: dict[str, list[str]] = defaultdict(list)
        for row in missing:
            reason = field_state(row, field, platform)
            reasons[reason].append(row["username"])
        for reason, names in sorted(reasons.items(), key=lambda kv: -len(kv[1])):
            print(f"      - {len(names):>3}  {reason}")
            print(f"             e.g. {', '.join(names[:4])}")

    print("\n\n=== ERROR MESSAGES (verbatim, grouped) ===")
    errors = Counter(r.get("error_message") for r in records if r.get("error_message"))
    print(f"  rows with any error text: {sum(errors.values())}/{total}")
    print(f"  rows with no error text:  {total - sum(errors.values())}/{total}")
    for message, count in errors.most_common():
        print(f"\n  [{count}x] {message}")
        samples = [r["username"] for r in records if r.get("error_message") == message][:4]
        print(f"        e.g. {', '.join(samples)}")

    print("\n\n=== TIMING ===")
    times = sorted(float(r.get("seconds") or 0) for r in records)
    if times:
        print(f"  mean {sum(times) / len(times):.2f}s | median {times[len(times) // 2]:.2f}s"
              f" | min {times[0]:.2f}s | max {times[-1]:.2f}s")
        slowest = sorted(records, key=lambda r: -float(r.get("seconds") or 0))[:5]
        for row in slowest:
            print(f"    {row['seconds']:>7}s  {row['username']:<22}"
                  f" ig={row.get('ig_stage')} threads={row.get('threads_stage')}")

    print("\n=== RETRY EVIDENCE (round 6 menu/dialog retry) ===")
    retried = [r for r in records
               if any(re.search(r"(profile_menu_open|about_clicked)_2_", str(step))
                      for step in (r.get("threads_evidence_steps") or [])
                      + (r.get("ig_evidence_steps") or []))]
    print(f"  targets where a second menu attempt was captured: {len(retried)}")
    for row in retried[:10]:
        print(f"    {row['username']:<22} threads_stage={row.get('threads_stage')}"
              f" date={row.get('threads_date_joined')} country={row.get('threads_country')}")

    print("\n=== CHECKERS USED ===")
    print(f"  {dict(Counter(r.get('checker_id') for r in records))}")


if __name__ == "__main__":
    main()
