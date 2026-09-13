"""
Integrity checks for a generated data estate.

  python -m data_estate.validate out/company_42

Checks:
  1. Every ID referenced in hidden/ground_truth.json exists in the public tables.
  2. Ledger balances (sum debit == sum credit) and every ledger line with an invoice/txn ref resolves.
  3. Every bank txn with an invoice_uuid points to a real invoice with matching amount.
  4. Every goods receipt points to a real purchase invoice.
  5. Each planted scheme is *findable* by the naive rule it claims (sanity, not the real detector).
  6. No decoy supplier trips the rules that define the schemes (decoys must be honest by construction).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


def load(out: Path):
    def rd(name):
        with (out / name).open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return {
        "suppliers": rd("suppliers.csv"),
        "customers": rd("customers.csv"),
        "employees": rd("employees.csv"),
        "invoices": rd("invoices.csv"),
        "receipts": rd("goods_receipts.csv"),
        "bank": rd("bank_transactions.csv"),
        "cp": rd("counterparty_bank.csv"),
        "ledger": rd("ledger.csv"),
        "efos": rd("efos_69b.csv"),
        "truth": json.loads((out / "hidden" / "ground_truth.json").read_text(encoding="utf-8")),
    }


def check(out: Path) -> list[str]:
    d = load(out)
    errs: list[str] = []
    ids = set()
    ids |= {s["supplier_id"] for s in d["suppliers"]} | {s["rfc"] for s in d["suppliers"]}
    ids |= {c["customer_id"] for c in d["customers"]} | {c["rfc"] for c in d["customers"]}
    ids |= {e["employee_id"] for e in d["employees"]}
    ids |= {i["uuid"] for i in d["invoices"]}
    ids |= {r["receipt_id"] for r in d["receipts"]}
    ids |= {t["txn_id"] for t in d["bank"]}
    ids |= {c["record_id"] for c in d["cp"]}

    # 1. truth references resolve
    def walk(x, path="truth"):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, str):
            if any(x.startswith(p) and x[len(p):].isdigit() for p in ("S", "C", "E", "GR", "TX", "CP")) \
                    or (len(x) == 36 and x.count("-") == 4):
                if x not in ids:
                    errs.append(f"dangling id {x} at {path}")
    walk(d["truth"])

    # 2. ledger balances and refs
    deb = sum(float(g["debit"]) for g in d["ledger"])
    cre = sum(float(g["credit"]) for g in d["ledger"])
    if abs(deb - cre) > 0.05:
        errs.append(f"ledger unbalanced: debit {deb:.2f} credit {cre:.2f}")
    inv_by = {i["uuid"]: i for i in d["invoices"]}
    tx_by = {t["txn_id"]: t for t in d["bank"]}
    for g in d["ledger"]:
        if g["invoice_uuid"] and g["invoice_uuid"] not in inv_by:
            errs.append(f"ledger {g['entry_id']} -> missing invoice")
        if g["txn_id"] and g["txn_id"] not in tx_by:
            errs.append(f"ledger {g['entry_id']} -> missing txn")

    # 3. bank -> invoice
    for t in d["bank"]:
        if t["invoice_uuid"]:
            inv = inv_by.get(t["invoice_uuid"])
            if not inv:
                errs.append(f"txn {t['txn_id']} -> missing invoice")
            elif abs(float(inv["total"]) - float(t["amount"])) > 0.05:
                errs.append(f"txn {t['txn_id']} amount != invoice total")

    # 4. receipts -> invoice
    for r in d["receipts"]:
        if r["invoice_uuid"] not in inv_by:
            errs.append(f"receipt {r['receipt_id']} -> missing invoice")

    # 5/6. naive rules
    efos_rfcs = {e["rfc"] for e in d["efos"] if e["situacion"] in ("Presunto", "Definitivo")}
    receipts_for = defaultdict(int)
    for r in d["receipts"]:
        receipts_for[r["invoice_uuid"]] += 1
    payments_for = defaultdict(list)
    for t in d["bank"]:
        if t["invoice_uuid"]:
            payments_for[t["invoice_uuid"]].append(t)
    emp_addr = {(e["home_street"], e["home_city"]): e["employee_id"] for e in d["employees"]}
    sup_by = {s["supplier_id"]: s for s in d["suppliers"]}

    # Internal purchasing policy; the threshold_splitting scheme is defined against it.
    from .generate import APPROVAL_LIMIT_SUBTOTAL
    limit = APPROVAL_LIMIT_SUBTOTAL["Gerente de Compras"]

    def _clusters(sid: str) -> list[list[dict]]:
        """Purchase invoices of one supplier grouped into runs <= 2 days apart."""
        rows = sorted(
            (i for i in d["invoices"] if i["counterparty_id"] == sid and i["tipo"] == "recibida"),
            key=lambda i: i["fecha"],
        )
        out: list[list[dict]] = []
        for inv in rows:
            day = date.fromisoformat(inv["fecha"])
            if out and (day - date.fromisoformat(out[-1][-1]["fecha"])).days <= 2:
                out[-1].append(inv)
            else:
                out.append([inv])
        return out

    def flags(sid: str) -> set[str]:
        s = sup_by[sid]
        f = set()
        if s["rfc"] in efos_rfcs:
            f.add("efos")
        if (s["street"], s["city"]) in emp_addr:
            f.add("employee_address")
        if any(len(v) > 1 for k, v in payments_for.items() if inv_by[k]["counterparty_id"] == sid):
            f.add("double_paid")
        # >=3 invoices within 2 days, each between 80% and 100% of the approval limit.
        for cluster in _clusters(sid):
            if len(cluster) >= 3 and all(
                0.8 * limit <= float(i["subtotal"]) < limit for i in cluster
            ):
                f.add("threshold_cluster")
                break
        return f

    def customer_flags(cid: str) -> set[str]:
        """A customer whose sales were booked as revenue but never collected."""
        sales = [i for i in d["invoices"] if i["tipo"] == "emitida" and i["counterparty_id"] == cid]
        if sales and not any(payments_for.get(i["uuid"]) for i in sales):
            return {"uncollected_sales"}
        return set()

    for s in d["truth"]["schemes"]:
        for ent in s["entities"]:
            sid = ent.get("supplier_id")
            if s["type"] == "efos_fake_supplier" and "efos" not in flags(sid):
                errs.append(f"efos scheme supplier {sid} not on 69-B")
            if s["type"] == "kickback_shell" and "employee_address" not in flags(sid):
                errs.append(f"kickback shell {sid} not at employee address")
            if s["type"] == "duplicate_invoice_payment" and "double_paid" not in flags(sid):
                errs.append(f"duplicate scheme supplier {sid} has no double payment")
            if s["type"] == "threshold_splitting" and "threshold_cluster" not in flags(sid):
                errs.append(f"threshold scheme supplier {sid} has no sub-limit cluster")
            cid = ent.get("customer_id")
            if s["type"] == "revenue_inflation" and cid and "uncollected_sales" not in customer_flags(cid):
                errs.append(f"revenue scheme customer {cid} has no uncollected sales")
    for dec in d["truth"]["decoys"]:
        f = flags(dec["supplier_id"])
        if f:
            errs.append(f"decoy {dec['supplier_id']} trips scheme rules {f}")
    return errs


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out/company")
    errs = check(out)
    if errs:
        print("\n".join(errs[:50]))
        print(f"FAILED with {len(errs)} problems")
        sys.exit(1)
    d = load(out)
    print(f"OK {out}: {len(d['invoices'])} invoices, {len(d['bank'])} txns, "
          f"{len(d['truth']['schemes'])} schemes, {len(d['truth']['decoys'])} decoys")


if __name__ == "__main__":
    main()
