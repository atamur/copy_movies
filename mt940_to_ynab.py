INPUT_FILE = r"EN_MT940_240825.sta"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT940 → YNAB4 CSV converter (Python 3.7 compatible)

This version balances ORDP vs BENM extraction:
  • For debits (D) → prefer BENM if present, UNLESS ORDP clearly looks like a corporate
    (AG/SA/GmbH/etc.) and BENM looks like a person/title (Mr/Mrs/Herr/Frau). This preserves
    cases like Viseca while fixing "Mr/Mrs ... /BENM/ACME AG" where ACME AG should win.
  • For credits (C) → prefer ORDP (sender) as before.

Usage (CLI):
  python mt940_to_ynab_py37_v4.py <input_file.mt940>

Or set:
  INPUT_FILE = r"path"
then run without args.

Output: "<input_file> conv.csv" (Date, Payee, Category, Memo, Outflow, Inflow)
Date format: DD/MM/YYYY
"""
import sys
import re
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def parse_amount(raw: str) -> float:
    """Convert MT940 amount strings to float (EU, US, apostrophes)."""
    if raw is None:
        return 0.0
    s = raw.strip()
    s = s.replace("\u00A0", "").replace(" ", "").replace("'", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_valdate(yyMMdd: str) -> str:
    """Convert YYMMDD → DD/MM/YYYY (assumes 2000–2099)."""
    try:
        yy = int(yyMMdd[:2])
        year = 2000 + yy
        month = int(yyMMdd[2:4])
        day = int(yyMMdd[4:6])
        dt = datetime(year, month, day)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return "01/01/2000"


# ---------- Payee extraction helpers ----------
_CORP_PAT = re.compile(
    r"\b(AG|SA|GmbH|S\.?à\.?r\.?l|SARL|BV|NV|Ltd|Limited|LLC|Inc\.?|PLC|SAS|S\.?p\.?A\.?|SpA|Co\.|Company|Bank|Versicherung|Insurance|Stiftung|Foundation|Services?|Holding)\b",
    re.IGNORECASE,
)
_TITLE_PAT = re.compile(r"\b(Mr|Mrs|Ms|Miss|Herr|Frau|Dr|Prof)\b", re.IGNORECASE)


def _cleanup_name(s: str) -> str:
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip(" /-,")


def _ordp_name(t: str) -> str:
    """Extract the token after the first comma in ORDP segments."""
    # ORDP//C/<code>, <Name> ...
    m = re.search(r"ORDP//C/[^,]*,\s*([^/,]+)", t, flags=re.IGNORECASE)
    if not m:
        # ORDP/<code>, <Name> ...
        m = re.search(r"ORDP/[^,]*,\s*([^/,]+)", t, flags=re.IGNORECASE)
    return _cleanup_name(m.group(1)) if m else ""


def _benm_name(t: str) -> str:
    """Extract the first name token in BENM/… (up to comma or slash)."""
    m = re.search(r"BENM/([^/,]+)", t, flags=re.IGNORECASE)
    return _cleanup_name(m.group(1)) if m else ""


def _name_score(name: str) -> int:
    """Rough score: >0 means corporate-ish, <0 means person-ish, 0 unknown."""
    if not name:
        return 0
    if _CORP_PAT.search(name):
        return 2
    if _TITLE_PAT.search(name):
        return -2
    # Heuristic: many words in ALL CAPS looks corporate-ish
    words = name.split()
    capsish = sum(1 for w in words if len(w) > 1 and w.isupper())
    if capsish >= 2:
        return 1
    # Short 2-word capitalized combos look person-ish
    if len(words) <= 3 and all(w and w[0].isupper() for w in words):
        return -1
    return 0


def extract_payee_from_86(text: str, dc: str) -> str:
    """
    Extract a human-friendly counterparty name from :86: with smarter selection.

    • Debits (D): prefer BENM, unless ORDP is clearly corporate and BENM looks like a person.
    • Credits (C): prefer ORDP; if missing, fall back to BENM.
    • Fallbacks: NAME/, REMI/, short slice of the whole :86: text.
    """
    if not text:
        return ""
    t = " ".join(text.split())

    ordp = _ordp_name(t)
    benm = _benm_name(t)

    if dc == "D":
        # Decide using simple scoring
        if benm:
            if ordp:
                if _name_score(ordp) > 0 and _name_score(benm) < 0:
                    return ordp
            return benm
        if ordp:
            return ordp
    else:  # Credits
        if ordp:
            return ordp
        if benm:
            return benm

    # NAME/
    m = re.search(r"NAME/([^/]+)", t, flags=re.IGNORECASE)
    if m:
        return _cleanup_name(m.group(1))

    # REMI/
    m = re.search(r"REMI/([^/]+)", t, flags=re.IGNORECASE)
    if m:
        return _cleanup_name(m.group(1))[:80]

    return t[:80]


# ---------- MT940 parsing & CSV ----------

def build_memo_86(text: str, extras: List[str]) -> str:
    parts: List[str] = []
    if extras:
        parts.extend([x.strip() for x in extras if x and x.strip()])
    if text:
        parts.append(" ".join(text.split()))
    memo = " | ".join(parts)
    return memo[:512]


def parse_mt940_lines(lines: List[str]) -> List[Dict[str, Any]]:
    txns: List[Dict[str, Any]] = []
    currency = None

    current: Dict[str, Any] = None  # type: ignore
    in_86 = False

    for raw in lines:
        line = raw.rstrip("\r\n")

        if line.startswith(":60F:"):
            m = re.search(r":60F:.*?[DC]\s*(\d{6})?([A-Z]{3})", line)
            if m:
                currency = m.group(2)

        if line.startswith(":61:"):
            if current:
                current["memo"] = build_memo_86(current.get("_86", ""), current.get("_free", []))
                current["payee"] = extract_payee_from_86(current.get("_86", ""), current["dc"]) or current["memo"][:64]
                txns.append(current)

            in_86 = False
            current = {"_86": "", "_free": [], "currency": currency}

            body = line[4:].strip()
            m = re.match(r"(?P<valdate>\d{6})(?P<entrydate>\d{4})?(?P<dc>[DC])(?P<rest>.*)", body)
            if not m:
                current["valdate"] = "000101"
                current["dc"] = "D"
                current["amount"] = 0.0
                current["_free"].append(body)
            else:
                current["valdate"] = m.group("valdate")
                current["dc"] = m.group("dc")
                rest = m.group("rest")
                am = re.search(r"([\d.,']+)", rest)
                amount = parse_amount(am.group(1)) if am else 0.0
                current["amount"] = amount

        elif line.startswith(":86:"):
            in_86 = True
            if current is not None:
                current["_86"] = line[4:].strip()
        elif line.startswith(":") and not line.startswith(":86:"):
            in_86 = False
        else:
            if current is None:
                continue
            if in_86:
                if line:
                    current["_86"] += " " + line.strip()
            else:
                if line.strip():
                    current["_free"].append(line.strip())

    if current:
        current["memo"] = build_memo_86(current.get("_86", ""), current.get("_free", []))
        current["payee"] = extract_payee_from_86(current.get("_86", ""), current["dc"]) or current["memo"][:64]
        txns.append(current)

    return txns


def write_ynab_csv(txns: List[Dict[str, Any]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])
        for t in txns:
            date_str = parse_valdate(t.get("valdate", "000101"))
            amt = float(t.get("amount", 0.0))
            dc = t.get("dc", "D")
            outflow = amt if dc == "D" else 0.0
            inflow = amt if dc == "C" else 0.0
            payee = t.get("payee", "")[:100]
            memo = t.get("memo", "")
            writer.writerow([date_str, payee, "", memo, outflow, inflow])


def main() -> None:
    chosen = INPUT_FILE.strip()
    if chosen:
        in_file = Path(chosen)
    else:
        if len(sys.argv) < 2:
            print("Usage: python mt940_to_ynab_py37_v4.py <input_file.mt940>\nOr set INPUT_FILE inside the script.")
            sys.exit(1)
        in_file = Path(sys.argv[1])

    if not in_file.exists():
        print(f"Input file not found: {in_file}")
        sys.exit(2)

    try:
        content = in_file.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        content = in_file.read_text(encoding="cp1252", errors="replace")

    lines = content.splitlines()
    txns = parse_mt940_lines(lines)

    out_file = in_file.with_name(in_file.name + " conv.csv")
    write_ynab_csv(txns, out_file)

    print(f"Converted {len(txns)} transactions → {out_file}")


if __name__ == "__main__":
    main()
