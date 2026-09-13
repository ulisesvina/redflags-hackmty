# Vendored verbatim from the judges' pack: student-materials/forensic-auditor/validate_format.py (#88). Do not edit.
"""Validate that a submission conforms to the required output format.

This checks STRUCTURE ONLY. It does not evaluate whether your findings are
correct, does not score recall, and contains no answer key. Its only job is
to confirm that what your system emits is the shape judges can read.

    python3 validate_format.py --submission my_findings.json

Optionally point it at your own estate to confirm every cited exhibit
record_id actually exists in your database, and that peso_amount reconciles
to the cited exhibits:

    python3 validate_format.py --submission my_findings.json --estate my_estate.db

Stdlib only. Exits non-zero if the format is invalid.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCHEME_TYPES = {"phantom_vendor", "kickback", "round_tripping",
                "threshold_splitting", "revenue_inflation"}
SOURCE_TABLES = {"ledger", "invoices", "bank_txns", "vendors",
                 "efos_list", "purchase_orders", "contracts", "employees"}
CONFIDENCE = {"proven", "probable"}
CLOSED_BY = {"investigator", "challenger", "validator"}

ID_COLUMN = {
    "ledger": "entry_id", "invoices": "uuid", "bank_txns": "txn_id",
    "vendors": "rfc", "efos_list": "rfc", "purchase_orders": "po_id",
    "contracts": "contract_id", "employees": "emp_id",
}
AMOUNT_COLUMN = {"invoices": "total", "bank_txns": "amount",
                 "purchase_orders": "amount", "contracts": "value"}

MIN_EXHIBITS = 3
MAX_NARRATIVE_WORDS = 150
PESO_TOLERANCE = 0.02


def validate_structure(sub: dict) -> list[str]:
    errs: list[str] = []

    for key in ("seed", "findings", "leads_not_pursued", "run_metadata"):
        if key not in sub:
            errs.append(f"submission: missing required key {key!r}")

    if not isinstance(sub.get("seed", 0), int):
        errs.append("submission.seed must be an integer")

    findings = sub.get("findings", [])
    if not isinstance(findings, list):
        errs.append("submission.findings must be an array")
        findings = []

    for i, f in enumerate(findings):
        p = f"findings[{i}]"
        for key in ("scheme_type", "entities", "narrative", "rule_broken",
                    "peso_amount", "exhibits", "confidence"):
            if key not in f:
                errs.append(f"{p}: missing required key {key!r}")

        if f.get("scheme_type") not in SCHEME_TYPES:
            errs.append(f"{p}.scheme_type must be one of {sorted(SCHEME_TYPES)}, "
                        f"got {f.get('scheme_type')!r}")

        ents = f.get("entities", [])
        if not isinstance(ents, list) or not ents:
            errs.append(f"{p}.entities must be a non-empty array")
        else:
            for e in ents:
                if ":" not in str(e):
                    errs.append(f"{p}.entities: {e!r} is missing a type prefix "
                                f"(expected e.g. 'RFC:...' or 'EMP:...')")

        words = len(str(f.get("narrative", "")).split())
        if words == 0:
            errs.append(f"{p}.narrative is empty")
        elif words > MAX_NARRATIVE_WORDS:
            errs.append(f"{p}.narrative is {words} words, maximum is {MAX_NARRATIVE_WORDS}")

        if not str(f.get("rule_broken", "")).strip():
            errs.append(f"{p}.rule_broken is empty")

        amt = f.get("peso_amount")
        if not isinstance(amt, (int, float)) or amt <= 0:
            errs.append(f"{p}.peso_amount must be a positive number, got {amt!r}")

        if f.get("confidence") not in CONFIDENCE:
            errs.append(f"{p}.confidence must be one of {sorted(CONFIDENCE)}, "
                        f"got {f.get('confidence')!r}")

        exhibits = f.get("exhibits", [])
        if not isinstance(exhibits, list) or len(exhibits) < MIN_EXHIBITS:
            errs.append(f"{p}.exhibits must have at least {MIN_EXHIBITS} entries, "
                        f"got {len(exhibits) if isinstance(exhibits, list) else 'non-array'}")
        seen_ids = set()
        for j, ex in enumerate(exhibits if isinstance(exhibits, list) else []):
            q = f"{p}.exhibits[{j}]"
            for key in ("exhibit_id", "source_table", "record_id", "note"):
                if key not in ex:
                    errs.append(f"{q}: missing required key {key!r}")
            if ex.get("source_table") not in SOURCE_TABLES:
                errs.append(f"{q}.source_table must be one of {sorted(SOURCE_TABLES)}, "
                            f"got {ex.get('source_table')!r}")
            eid = ex.get("exhibit_id")
            if eid in seen_ids:
                errs.append(f"{q}.exhibit_id {eid!r} is duplicated within this finding")
            seen_ids.add(eid)
            if not str(ex.get("note", "")).strip():
                errs.append(f"{q}.note is empty - state what this record proves")

        trail = f.get("money_trail")
        if trail is None:
            errs.append(f"{p}.money_trail is absent - a rendered money trail is required "
                        f"for full Clarity credit")
        elif not isinstance(trail, list):
            errs.append(f"{p}.money_trail must be an array")
        else:
            for k, step in enumerate(trail):
                r = f"{p}.money_trail[{k}]"
                for key in ("from", "to", "amount", "date", "exhibit_id"):
                    if key not in step:
                        errs.append(f"{r}: missing required key {key!r}")
                if step.get("exhibit_id") and step["exhibit_id"] not in seen_ids:
                    errs.append(f"{r}.exhibit_id {step['exhibit_id']!r} does not match any "
                                f"exhibit in this finding")

    leads = sub.get("leads_not_pursued", [])
    if not isinstance(leads, list):
        errs.append("submission.leads_not_pursued must be an array")
        leads = []
    for i, l in enumerate(leads):
        p = f"leads_not_pursued[{i}]"
        for key in ("entity", "signal", "reason"):
            if key not in l or not str(l.get(key, "")).strip():
                errs.append(f"{p}: {key!r} is missing or empty")
        if "closed_by" in l and l["closed_by"] not in CLOSED_BY:
            errs.append(f"{p}.closed_by must be one of {sorted(CLOSED_BY)}, "
                        f"got {l['closed_by']!r}")

    meta = sub.get("run_metadata", {})
    if not isinstance(meta, dict):
        errs.append("submission.run_metadata must be an object")
    else:
        for key in ("llm_calls", "mxn_cost", "wall_clock_seconds"):
            if key not in meta:
                errs.append(f"run_metadata: missing required key {key!r}")
            elif not isinstance(meta[key], (int, float)):
                errs.append(f"run_metadata.{key} must be a number, got {meta[key]!r}")

    return errs


def validate_against_estate(sub: dict, db_path: str) -> list[str]:
    """Confirm cited records exist and amounts reconcile. Uses YOUR estate."""
    errs: list[str] = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    for i, f in enumerate(sub.get("findings", [])):
        per_table: dict[str, float] = {}
        for j, ex in enumerate(f.get("exhibits", [])):
            table, rid = ex.get("source_table"), str(ex.get("record_id", ""))
            if table not in have:
                errs.append(f"findings[{i}].exhibits[{j}]: table {table!r} "
                            f"is not present in {db_path}")
                continue
            col = ID_COLUMN.get(table)
            row = conn.execute(
                f"SELECT * FROM {table} WHERE {col} = ?", (rid,)).fetchone()
            if row is None:
                errs.append(f"findings[{i}].exhibits[{j}]: {table}.{rid} "
                            f"does not exist in {db_path}")
                continue
            amt_col = AMOUNT_COLUMN.get(table)
            if amt_col and amt_col in row.keys():
                per_table[table] = per_table.get(table, 0.0) + float(row[amt_col] or 0)

        claimed = float(f.get("peso_amount", 0) or 0)
        if per_table:
            # Per-table, not summed across tables: an invoice and the transfer
            # that settled it are the same pesos seen twice.
            best = min(per_table.values(), key=lambda v: abs(claimed - v))
            if abs(claimed - best) > PESO_TOLERANCE * max(best, 1):
                detail = ", ".join(f"{t}={v:,.2f}" for t, v in sorted(per_table.items()))
                errs.append(f"findings[{i}]: peso_amount {claimed:,.2f} does not reconcile "
                            f"to cited exhibits [{detail}]")
        else:
            errs.append(f"findings[{i}]: no exhibit cites an amount-bearing table "
                        f"({sorted(AMOUNT_COLUMN)}), so peso_amount cannot reconcile")

    conn.close()
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--estate", help="your own estate .db, to check exhibits resolve")
    args = ap.parse_args()

    try:
        sub = json.loads(Path(args.submission).read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL  {args.submission} is not valid JSON: {e}")
        return 1

    errs = validate_structure(sub)
    if args.estate:
        errs += validate_against_estate(sub, args.estate)

    print()
    print("=" * 70)
    print("  FORENSIC AUDITOR - SUBMISSION FORMAT CHECK")
    print("=" * 70)
    n_f = len(sub.get("findings", []))
    n_l = len(sub.get("leads_not_pursued", []))
    print(f"  findings: {n_f}   leads_not_pursued: {n_l}   "
          f"estate check: {'yes' if args.estate else 'skipped'}")
    print("-" * 70)

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print("-" * 70)
        print(f"  {len(errs)} format error(s)")
    else:
        print("  PASS  submission conforms to the required format")

    print("""
  This checks FORMAT ONLY. It does not tell you whether your findings are
  correct, and it cannot score recall or false accusations - that requires
  ground truth for the estate, which you generate yourself.
""")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
