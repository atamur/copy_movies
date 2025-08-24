#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker "Releases Report.csv" → YNAB4 CSV (Python 3.7 compatible)

v3 — Aggregates **all shares first per date**, then converts once using that date's FX,
so you get exactly **one YNAB row per day** with a single memo.

Changes vs v2:
  • Group by Vest Date, sum Net Share Proceeds (shares), sum USD value (Price×Shares).
  • Compute VWAP (weighted avg price) = USD_sum / shares_sum for the memo.
  • Fetch USD→CHF once per date; CHF inflow = USD_sum × FX.
  • Payee is fixed to "Google stocks".

Requires: requests
  pip install requests

Usage:
  python releases_to_ynab_py37_v3.py                # reads "Releases Report.csv" in current folder
  python releases_to_ynab_py37_v3.py path/to/Report.csv

Output:
  Creates "<input_filename> conv.csv" next to the input file.
"""
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests

# ---- Config ----
INPUT_FILE = r""  # optional hardcoded path; leave empty to use CLI/default
DEFAULT_NAME = "Releases Report.csv"
BASE = "USD"
TARGET = "CHF"
TIMEOUT = 10
PAYEE = "Google stocks"


# ---------- Utilities ----------
def parse_money(s: str) -> float:
    """Parse money/share strings like "$1,234.56" or "1'234.56" → 1234.56."""
    if s is None:
        return 0.0
    t = str(s).strip()
    t = t.replace("$", "").replace("€", "").replace("£", "")
    t = t.replace("\u00A0", " ").strip()
    t = t.replace(",", "").replace("'", "")
    try:
        return float(t)
    except ValueError:
        t2 = t.replace(".", "").replace(",", ".")
        try:
            return float(t2)
        except ValueError:
            return 0.0


def parse_vest_date(d: str) -> datetime:
    return datetime.strptime(d.strip(), "%d-%b-%Y")


def ynab_date(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y")


# ---------- FX ----------
_rate_cache: Dict[str, float] = {}


def fetch_usd_chf(iso_date: str) -> Tuple[float, str]:
    """Fetch USD→CHF rate from api.frankfurter.app for the given ISO date (YYYY-MM-DD).
    Returns (rate, api_effective_date). Frankfurter returns the previous business day if needed.
    """
    if iso_date in _rate_cache:
        return _rate_cache[iso_date], iso_date
    url = f"https://api.frankfurter.app/{iso_date}"
    params = {"from": BASE, "to": TARGET}
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    effective = data.get("date", iso_date)
    rate = float(data["rates"][TARGET])
    _rate_cache[iso_date] = rate
    return rate, effective


# ---------- Core ----------

def collect_items(in_file: Path) -> Dict[str, Dict[str, Any]]:
    """Return a dict keyed by ISO date with aggregated shares & USD.
    Only includes rows with Type=Release and Status=Complete.
    Each group has: {'dt': datetime, 'shares_sum': float, 'usd_sum': float}
    """
    groups: Dict[str, Dict[str, Any]] = {}

    with in_file.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            typ = (row.get("Type") or "").strip().lower()
            status = (row.get("Status") or "").strip().lower()
            if typ != "release" or status != "complete":
                continue

            vest_dt = parse_vest_date(row["Vest Date"])  # e.g., 25-Jul-2025
            date_iso = vest_dt.strftime("%Y-%m-%d")

            price = parse_money(row.get("Price", "0"))                # USD/share
            net_shares = parse_money(row.get("Net Share Proceeds", "0"))  # shares

            g = groups.setdefault(date_iso, {"dt": vest_dt, "shares_sum": 0.0, "usd_sum": 0.0})
            g["shares_sum"] += net_shares
            g["usd_sum"] += price * net_shares

    return groups


def write_ynab(groups: Dict[str, Dict[str, Any]], out_path: Path) -> None:
    # Build rows sorted by date
    rows: List[List[str]] = []
    for date_iso in sorted(groups.keys()):
        g = groups[date_iso]
        dt: datetime = g["dt"]
        shares_sum: float = g["shares_sum"]
        usd_sum: float = g["usd_sum"]

        # FX once per date
        rate, _ = fetch_usd_chf(date_iso)
        chf_value = usd_sum * rate

        # VWAP for memo (avoid div-by-zero)
        vwap = (usd_sum / shares_sum) if shares_sum else 0.0
        memo = f"{shares_sum:g} x {vwap:.2f} @ {rate:.3f}"

        rows.append([
            ynab_date(dt),        # Date
            PAYEE,                # Payee
            "",                   # Category
            memo,                 # Memo
            "0.00",              # Outflow
            f"{chf_value:.2f}",  # Inflow
        ])

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])
        w.writerows(rows)


def main() -> None:
    # Choose input path
    if INPUT_FILE.strip():
        in_file = Path(INPUT_FILE)
    else:
        in_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_NAME)

    if not in_file.exists():
        print(f"Input file not found: {in_file}")
        sys.exit(2)

    groups = collect_items(in_file)

    out_file = in_file.with_name(in_file.name + " conv.csv")
    write_ynab(groups, out_file)
    print(f"Wrote {len(groups)} transactions → {out_file}")


if __name__ == "__main__":
    main()
