#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAMT.053 → YNAB CSV converter

Reads a CAMT.053.001.04 XML file and writes a YNAB-compatible CSV:
  Columns: Date, Payee, Category, Memo, Outflow, Inflow
  Date format: DD/MM/YYYY
  Outflow for DBIT, Inflow for CRDT

Usage:
  python camt053_to_ynab.py <input_file.xml>

If no argument is provided, INPUT_FILE is used.
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# Default input file (can be overridden by CLI)
INPUT_FILE = ""

# CAMT.053.001.04 namespace
NS = {"c": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.04"}


def _text(el):
    return el.text.strip() if el is not None and el.text else ""


def find_text(parent, path):
    el = parent.find(path, NS)
    return _text(el)


def findall(parent, path):
    return parent.findall(path, NS)


def parse_date_iso_to_ynab(iso_date: str) -> str:
    # Expect YYYY-MM-DD
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        # Try datetime with time (YYYY-MM-DDTHH:MM:SS)
        try:
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return "01/01/2000"


def clean_text(s: str) -> str:
    s = " ".join(str(s).split())
    return s.strip(" /-,")


def is_placeholder_or_self(name: str, owner: str) -> bool:
    n = (name or "").strip().lower()
    o = (owner or "").strip().lower()
    return n in {"", "notprovided", "not provided"} or n == o


def first_nonempty(seq):
    for s in seq:
        if s and str(s).strip():
            return s
    return ""


def collect_memo_parts(ntry) -> list:
    parts = []

    # Entry-level additional info
    addtl_ntry = find_text(ntry, "./c:AddtlNtryInf")
    if addtl_ntry:
        parts.append(clean_text(addtl_ntry))

    # Iterate all TxDtls and collect remittance and additional info
    for tx in findall(ntry, "./c:NtryDtls/c:TxDtls"):
        # Unstructured remittance info
        for u in findall(tx, "./c:RmtInf/c:Ustrd"):
            txt = clean_text(_text(u))
            if txt:
                parts.append(txt)
        # Additional transaction info
        addtl_tx = find_text(tx, "./c:AddtlTxInf")
        if addtl_tx:
            parts.append(clean_text(addtl_tx))
        # Useful refs
        acct_ref = find_text(tx, "./c:Refs/c:AcctSvcrRef")
        if acct_ref:
            parts.append(f"Ref: {acct_ref}")
        instr_id = find_text(tx, "./c:Refs/c:InstrId")
        if instr_id and instr_id.upper() != "NOTPROVIDED":
            parts.append(f"InstrId: {instr_id}")
        e2e = find_text(tx, "./c:Refs/c:EndToEndId")
        if e2e and e2e.upper() != "NOTPROVIDED":
            parts.append(f"E2E: {e2e}")

    # If nothing else, include a compact BkTxCd semantic
    dom = find_text(ntry, "./c:BkTxCd/c:Domn/c:Cd")
    fam = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:Cd")
    sub = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:SubFmlyCd")
    if any([dom, fam, sub]):
        parts.append("TxCode: " + " ".join(x for x in [dom, fam, sub] if x))

    # Unique while preserving order
    seen = set()
    uniq = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def extract_payee(ntry, owner_name: str, cdt_dbt: str) -> str:
    """
    Heuristics:
      - For credits: prefer debtor (originator), then creditor, then AddtlNtryInf/Ustrd.
      - For debits: prefer creditor (beneficiary), then debtor, then AddtlNtryInf/Ustrd.
      - Ignore placeholders and account owner name.
    """
    names = []

    # Walk through TxDtls if present (often where names live)
    tx_list = findall(ntry, "./c:NtryDtls/c:TxDtls")
    if tx_list:
        for tx in tx_list:
            dbtr = clean_text(find_text(tx, "./c:RltdPties/c:Dbtr/c:Nm"))
            cdtr = clean_text(find_text(tx, "./c:RltdPties/c:Cdtr/c:Nm"))
            if cdt_dbt == "CRDT":
                names.extend([dbtr, cdtr])
            else:
                names.extend([cdtr, dbtr])

    # Fallbacks from entry-level text
    addtl = clean_text(find_text(ntry, "./c:AddtlNtryInf"))
    # First unstructured remittance text
    ustrd = ""
    if tx_list:
        for tx in tx_list:
            u = findall(tx, "./c:RmtInf/c:Ustrd")
            if u:
                ustrd = clean_text(_text(u[0]))
                if ustrd:
                    break

    # Filter out placeholders/self and choose first sensible
    for cand in names:
        if not is_placeholder_or_self(cand, owner_name):
            return cand

    if addtl and not is_placeholder_or_self(addtl, owner_name):
        return addtl
    if ustrd and not is_placeholder_or_self(ustrd, owner_name):
        return ustrd

    # Last resort: compact description from BkTxCd or generic labels
    dom = find_text(ntry, "./c:BkTxCd/c:Domn/c:Cd")
    fam = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:Cd")
    sub = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:SubFmlyCd")
    txcode = " ".join(x for x in [dom, fam, sub] if x)
    if txcode:
        return txcode
    return "Transaction"


def parse_entries(root) -> list:
    stmt = root.find(".//c:BkToCstmrStmt/c:Stmt", NS)
    if stmt is None:
        return []

    owner_name = clean_text(find_text(stmt, "./c:Acct/c:Ownr/c:Nm"))

    entries = []
    for ntry in findall(stmt, "./c:Ntry"):
        # Default direction at entry level
        ntry_cdt_dbt = find_text(ntry, "./c:CdtDbtInd")  # CRDT or DBIT

        # Date preference: Booking date, fallback to Value date
        date_iso = find_text(ntry, "./c:BookgDt/c:Dt") or find_text(ntry, "./c:ValDt/c:Dt")
        date_str = parse_date_iso_to_ynab(date_iso) if date_iso else "01/01/2000"

        tx_list = findall(ntry, "./c:NtryDtls/c:TxDtls")
        if tx_list:
            # Create one CSV row per TxDtls
            for tx in tx_list:
                # Amount: prefer tx-level amount, fallback to detailed nodes, then zero
                amt_tx_str = (
                    find_text(tx, "./c:Amt")
                    or find_text(tx, "./c:AmtDtls/c:TxAmt/c:Amt")
                    or find_text(tx, "./c:AmtDtls/c:InstdAmt/c:Amt")
                )
                try:
                    amount = float(amt_tx_str.replace("'", "").replace(" ", "")) if amt_tx_str else 0.0
                except ValueError:
                    amount = 0.0

                cdt_dbt = find_text(tx, "./c:CdtDbtInd") or ntry_cdt_dbt

                # Payee from tx-level related parties
                dbtr_nm = clean_text(find_text(tx, "./c:RltdPties/c:Dbtr/c:Nm"))
                cdtr_nm = clean_text(find_text(tx, "./c:RltdPties/c:Cdtr/c:Nm"))
                payee = ""
                if cdt_dbt == "CRDT":
                    # Incoming → sender
                    for cand in (dbtr_nm, cdtr_nm):
                        if not is_placeholder_or_self(cand, owner_name):
                            payee = cand
                            break
                else:
                    # Outgoing → beneficiary
                    for cand in (cdtr_nm, dbtr_nm):
                        if not is_placeholder_or_self(cand, owner_name):
                            payee = cand
                            break

                # Fallbacks for payee
                if not payee:
                    addtl_ntry = clean_text(find_text(ntry, "./c:AddtlNtryInf"))
                    if addtl_ntry and not is_placeholder_or_self(addtl_ntry, owner_name):
                        payee = addtl_ntry
                if not payee:
                    u_first = ""
                    u_nodes = findall(tx, "./c:RmtInf/c:Ustrd")
                    if u_nodes:
                        u_first = clean_text(_text(u_nodes[0]))
                    if u_first and not is_placeholder_or_self(u_first, owner_name):
                        payee = u_first
                if not payee:
                    # Last resort from tx code
                    dom = find_text(ntry, "./c:BkTxCd/c:Domn/c:Cd")
                    fam = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:Cd")
                    sub = find_text(ntry, "./c:BkTxCd/c:Domn/c:Fmly/c:SubFmlyCd")
                    payee = " ".join(x for x in [dom, fam, sub] if x) or "Transaction"

                # Build memo per tx
                memo_parts = []
                # Entry-level additional info
                addtl_ntry = find_text(ntry, "./c:AddtlNtryInf")
                if addtl_ntry:
                    memo_parts.append(clean_text(addtl_ntry))
                # Unstructured remittance
                for u in findall(tx, "./c:RmtInf/c:Ustrd"):
                    ut = clean_text(_text(u))
                    if ut:
                        memo_parts.append(ut)
                # Structured remittance
                s_ref = find_text(tx, "./c:RmtInf/c:Strd/c:CdtrRefInf/c:Ref")
                if s_ref:
                    memo_parts.append(f"Ref: {s_ref}")
                addtl_rmt = find_text(tx, "./c:RmtInf/c:Strd/c:AddtlRmtInf")
                if addtl_rmt:
                    memo_parts.append(clean_text(addtl_rmt))
                # Additional tx info
                addtl_tx = find_text(tx, "./c:AddtlTxInf")
                if addtl_tx:
                    memo_parts.append(clean_text(addtl_tx))
                # Refs
                acct_ref = find_text(tx, "./c:Refs/c:AcctSvcrRef")
                if acct_ref:
                    memo_parts.append(f"Ref: {acct_ref}")
                instr_id = find_text(tx, "./c:Refs/c:InstrId")
                if instr_id and instr_id.upper() != "NOTPROVIDED":
                    memo_parts.append(f"InstrId: {instr_id}")
                e2e = find_text(tx, "./c:Refs/c:EndToEndId")
                if e2e and e2e.upper() != "NOTPROVIDED":
                    memo_parts.append(f"E2E: {e2e}")
                # Counterparty bank/account hints (help distinguish split payments)
                if cdt_dbt == "CRDT":
                    # Show debtor agent for incoming
                    dbtr_bic = find_text(tx, "./c:RltdAgts/c:DbtrAgt/c:FinInstnId/c:BICFI")
                    dbtr_bank = find_text(tx, "./c:RltdAgts/c:DbtrAgt/c:FinInstnId/c:Nm")
                    if dbtr_bic or dbtr_bank:
                        memo_parts.append("From bank: " + " ".join(x for x in [dbtr_bank, dbtr_bic] if x))
                else:
                    # Show creditor account/agent for outgoing
                    cdtr_iban = find_text(tx, "./c:RltdPties/c:CdtrAcct/c:Id/c:IBAN") or find_text(
                        tx, "./c:RltdPties/c:CdtrAcct/c:Id/c:Othr/c:Id"
                    )
                    if cdtr_iban:
                        memo_parts.append(f"To acct: {cdtr_iban}")
                    cdtr_bic = find_text(tx, "./c:RltdAgts/c:CdtrAgt/c:FinInstnId/c:BICFI")
                    cdtr_bank = find_text(tx, "./c:RltdAgts/c:CdtrAgt/c:FinInstnId/c:Nm")
                    if cdtr_bic or cdtr_bank:
                        memo_parts.append("To bank: " + " ".join(x for x in [cdtr_bank, cdtr_bic] if x))

                # Deduplicate while preserving order
                seen = set()
                uniq = []
                for p in memo_parts:
                    if p and p not in seen:
                        seen.add(p)
                        uniq.append(p)
                memo = " | ".join(uniq)[:512]

                # Outflow/Inflow according to CdtDbtInd
                if cdt_dbt == "CRDT":
                    outflow = 0.0
                    inflow = amount
                else:
                    outflow = amount
                    inflow = 0.0

                entries.append({
                    "Date": date_str,
                    "Payee": payee[:100],
                    "Category": "",
                    "Memo": memo,
                    "Outflow": outflow,
                    "Inflow": inflow,
                })
        else:
            # Fallback: no TxDtls → treat entry as a single transaction
            amt_str = find_text(ntry, "./c:Amt")
            try:
                amount = float(amt_str.replace("'", "").replace(" ", "")) if amt_str else 0.0
            except ValueError:
                amount = 0.0

            payee = extract_payee(ntry, owner_name, ntry_cdt_dbt)
            memo_parts = collect_memo_parts(ntry)
            memo = " | ".join(memo_parts)[:512]

            if ntry_cdt_dbt == "CRDT":
                outflow = 0.0
                inflow = amount
            else:
                outflow = amount
                inflow = 0.0

            entries.append({
                "Date": date_str,
                "Payee": payee[:100],
                "Category": "",
                "Memo": memo,
                "Outflow": outflow,
                "Inflow": inflow,
            })

    return entries


def write_ynab_csv(rows: list, out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])
        for r in rows:
            w.writerow([r["Date"], r["Payee"], r["Category"], r["Memo"], r["Outflow"], r["Inflow"]])


def main():
    if len(sys.argv) > 1:
        in_file = Path(sys.argv[1])
    else:
        in_file = Path(INPUT_FILE)

    if not in_file.exists():
        print(f"Input file not found: {in_file}")
        sys.exit(2)

    try:
        tree = ET.parse(str(in_file))
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        sys.exit(3)

    rows = parse_entries(root)
    out_file = in_file.with_name(in_file.name + " conv.csv")
    write_ynab_csv(rows, out_file)

    print(f"Converted {len(rows)} transactions → {out_file}")


if __name__ == "__main__":
    main()
