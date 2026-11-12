"""Track layoffs in the US: every layoff by company, state, industry and date, from state layoff notices,
SEC filings and news reports, saved to CSV with a summary of the companies with the most workers affected.

    python layoffs_tracker.py --state CA --since 2026-01-01
    python layoffs_tracker.py --company intel
    python layoffs_tracker.py --top --days 90

Needs a DataPorium API key in the DATAPORIUM_API_KEY environment variable.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from dataporium import DataPorium

EVENT_COLUMNS = ["announced_date", "effective_date", "company", "ticker", "state", "county", "city", "industry",
                 "naics", "workers", "workforce_pct", "layoff_type", "status", "source_types", "event_id"]
COMPANY_COLUMNS = ["company", "ticker", "events", "confirmed_events", "workers", "latest_date", "states", "industry"]
PAGE = 200


def flat(value):
    """Lists become 'a; b' so they fit in one CSV cell."""
    if isinstance(value, list):
        return "; ".join(str(v.get("name") or v.get("url") or v) if isinstance(v, dict) else str(v) for v in value)
    return value


def fetch_events(dp: DataPorium, filters: dict, max_rows: int) -> list[dict]:
    rows: list[dict] = []
    while len(rows) < max_rows:
        answer = dp.layoffs_events(**filters, limit=min(PAGE, max_rows - len(rows)), offset=len(rows))
        page = answer.get("rows") or []
        rows.extend(page)
        if not page or len(rows) >= int(answer.get("total") or 0):
            break
    return rows


def by_company(events: list[dict]) -> list[dict]:
    """Events and stated workers per company, most workers first."""
    totals: dict[str, dict] = defaultdict(lambda: {"events": 0, "workers": 0, "states": set()})
    for e in events:
        t = totals[e.get("company") or "?"]
        t["events"] += 1
        t["workers"] += int(e.get("workers") or 0)
        if e.get("state"):
            t["states"].add(e["state"])
    ranked = [{"company": c, "events": t["events"], "workers": t["workers"], "states": ", ".join(sorted(t["states"]))}
              for c, t in totals.items()]
    return sorted(ranked, key=lambda r: (r["workers"], r["events"]), reverse=True)


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: flat(row.get(k)) for k in columns})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download US layoffs to CSV.")
    parser.add_argument("--state", help="2-letter state codes, comma-separated, e.g. CA,TX")
    parser.add_argument("--company", help="Words in the company name, e.g. intel")
    parser.add_argument("--ticker", help="Tickers, comma-separated")
    parser.add_argument("--naics", help="Industry code prefix, e.g. 51 (information) or 31-33 (manufacturing)")
    parser.add_argument("--since", help="Announced on or after (YYYY, YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--until", help="Announced on or before")
    parser.add_argument("--min-workers", type=int, help="Only layoffs of at least this many workers")
    parser.add_argument("--status", choices=["confirmed", "reported", "all"], default="confirmed",
                        help="confirmed (an official notice or filing exists, default), reported (news only) or all")
    parser.add_argument("--max", type=int, default=1000, help="Most layoffs to download (default 1000)")
    parser.add_argument("--top", action="store_true", help="Rank companies instead of listing layoffs")
    parser.add_argument("--days", type=int, default=90, choices=[30, 90, 365, 0], help="With --top: 30, 90, 365 or 0 (all time)")
    parser.add_argument("--out", default="output", help="Folder for the CSV files (default output)")
    args = parser.parse_args(argv)

    dp = DataPorium()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    status = None if args.status == "all" else args.status

    if args.top:
        answer = dp.layoffs_companies(days=args.days, state=args.state, naics=args.naics, status=status,
                                      sort="workers", limit=min(args.max, 500))
        rows = answer.get("rows") or []
        write_csv(out / "top_companies.csv", rows, COMPANY_COLUMNS)
        period = "all time" if args.days == 0 else f"the last {args.days} days"
        print(f"Companies with the most workers laid off, {period}:")
        for r in rows[:15]:
            print(f"  {str(r.get('company'))[:40]:40} {int(r.get('workers') or 0):>8,} workers  {r.get('events')} layoffs")
        print(f"Saved {len(rows)} companies to {out / 'top_companies.csv'}")
        return 0 if rows else 1

    filters = {"state": args.state, "company": args.company, "ticker": args.ticker, "naics": args.naics,
               "date_from": args.since, "date_to": args.until, "min_workers": args.min_workers, "status": status}
    events = fetch_events(dp, filters, args.max)
    write_csv(out / "layoffs.csv", events, EVENT_COLUMNS)
    print(f"{len(events)} layoffs saved to {out / 'layoffs.csv'}")
    if events:
        workers = sum(int(e.get("workers") or 0) for e in events)
        print(f"Workers stated: {workers:,}. Companies with the most:")
        for r in by_company(events)[:10]:
            print(f"  {r['company'][:40]:40} {r['workers']:>8,} workers  {r['events']} layoffs  {r['states']}")
    return 0 if events else 1


if __name__ == "__main__":
    sys.exit(main())
