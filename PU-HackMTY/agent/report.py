"""The case file a judge reads (#23, restructured for the judges' spec in #90).

``case_file.json`` is for the scorer and ``submission.json`` for the machine check.
This module produces the document a human opens: the five sections
``case_file_structure.md`` requires, in order, with the money trail **rendered as a
diagram** — prose-only caps Clarity at 3 — and every claimed peso reconciled to the
exhibits printed beneath it.

Two outputs from one model of the document:

* **Markdown** (``--out``), where the diagram is a ``mermaid`` ``flowchart LR`` block;
* **HTML** (``--html``), self-contained: the same graph drawn as inline SVG by a small
  pure-Python layout, with no external assets, no ``<script>`` and no URL of any kind,
  so it opens from a file path on a laptop with the Wi-Fi off. Judges may ask for that.

Deterministic and offline by construction: every number is recomputed from the dataset
rows the finding cites, nothing is fetched, and no model is called. The narrative,
exhibits, money trail and confidence come from the submission (:mod:`agent.submit`),
which is built when the caller does not supply one, so the document and the JSON the
judges machine-check can never disagree.

CLI::

    python -m agent.report <estate> <case_file.json> [--submission submission.json]
        [--log runs/<ts>.jsonl] [--out report.md] [--html report.html]

Exits 1, printing the errors, when ``agent.contract.validate_case_file`` rejects the
file — an invalid case file is never rendered.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .contract import validate_case_file
from .data import Dataset, load

# LISR Art. 9 corporate income tax rate. Stated as an assumption in the document.
ISR_RATE = 0.30
# IVA / VAT rate on the invoices.
IVA_RATE = 0.16

# Plain-words scheme names for the report.
_PLAIN = {
    "efos_fake_supplier": "Fake supplier on the SAT 69-B list",
    "kickback_shell": "Kickback through a related-party shell",
    "round_trip_sales": "Round-trip sales (fictitious revenue)",
    "duplicate_invoice_payment": "Duplicate payment diverted to an unregistered account",
    "other": "Other",
}

_CLABE_WARN = " ⚠ CLABE not on supplier master"


def _money(x: float) -> str:
    return f"{x:,.2f}"


def _fmt_date(d) -> str:
    if d is None or str(d) == "":
        return ""
    try:
        return pd.Timestamp(d).date().isoformat()
    except Exception:
        return str(d)


# --- name resolution ---------------------------------------------------------
def _entity_name(ds: Dataset, eid: str) -> tuple[str, str]:
    """Resolve an S*/C*/E* id to (name, qualifier); qualifier is category/role/city."""
    if len(ds.suppliers):
        sub = ds.suppliers[ds.suppliers["supplier_id"] == eid]
        if len(sub):
            r = sub.iloc[0]
            return str(r["name"]), str(r.get("category", ""))
    if len(ds.customers):
        sub = ds.customers[ds.customers["customer_id"] == eid]
        if len(sub):
            r = sub.iloc[0]
            return str(r["name"]), str(r.get("city", ""))
    if len(ds.employees):
        sub = ds.employees[ds.employees["employee_id"] == eid]
        if len(sub):
            r = sub.iloc[0]
            return str(r["name"]), str(r.get("role", ""))
    return eid, ""


def _describe(eid: str, ds: Dataset) -> str:
    name, qual = _entity_name(ds, eid)
    return f"{name} ({eid}, {qual})" if qual else f"{name} ({eid})"


def _supplier_name(ds: Dataset, sid: str) -> str:
    name, _ = _entity_name(ds, sid)
    return name


def _employee_name(ds: Dataset, eid: str) -> str:
    name, _ = _entity_name(ds, eid)
    return name


# --- exposure ----------------------------------------------------------------
def _accused_of(ds: Dataset, accused: list[str], kind: str) -> list[str]:
    """Accused ids that are actual suppliers/customers/employees."""
    if kind == "supplier":
        ids = set(ds.suppliers["supplier_id"]) if len(ds.suppliers) else set()
    elif kind == "customer":
        ids = set(ds.customers["customer_id"]) if len(ds.customers) else set()
    else:
        ids = set(ds.employees["employee_id"]) if len(ds.employees) else set()
    return [a for a in accused if a in ids]


def _recibida_subtotal_iva(ds: Dataset, supplier_ids: list[str]) -> tuple[float, float]:
    """(sum subtotal, sum iva) over every recibida invoice of the accused suppliers.

    The scheme amount is the full book of the accused supplier(s): a finding
    represents the whole scheme, so its exposure is the supplier's entire
    recibida book, not a subset of cited invoices. A scheme that spans several
    suppliers aggregates across all of them (e.g. EFOS S00030 + S00020).
    """
    if not supplier_ids or len(ds.invoices) == 0:
        return 0.0, 0.0
    rec = ds.invoices[ds.invoices["tipo"] == "recibida"]
    sub = rec[rec["counterparty_id"].isin(supplier_ids)]
    if len(sub) == 0:
        return 0.0, 0.0
    return float(sub["subtotal"].sum()), float(sub["iva"].sum())


def _paid_to_employee(ds: Dataset, employee_ids: list[str]) -> float:
    """Sum of counterparty-bank outflows to the accused employee's personal CLABE."""
    if not employee_ids or len(ds.counterparty_bank) == 0 or len(ds.employees) == 0:
        return 0.0
    total = 0.0
    cp_out = ds.counterparty_bank[ds.counterparty_bank["direction"] == "out"]
    for eid in employee_ids:
        sub = ds.employees[ds.employees["employee_id"] == eid]
        if len(sub) == 0:
            continue
        clabe = str(sub.iloc[0]["personal_clabe"])
        rows = cp_out[cp_out["counterparty_clabe"] == clabe]
        total += float(rows["amount"].sum()) if len(rows) else 0.0
    return total


def _revenue_overstated(ds: Dataset, customer_ids: list[str]) -> float:
    """Sum of subtotal over every emitida invoice to the accused customer."""
    if not customer_ids or len(ds.invoices) == 0:
        return 0.0
    em = ds.invoices[ds.invoices["tipo"] == "emitida"]
    sub = em[em["counterparty_id"].isin(customer_ids)]
    return float(sub["subtotal"].sum()) if len(sub) else 0.0


def _duplicate_cash_loss(ds: Dataset, supplier_ids: list[str]) -> float:
    """Sum over the accused supplier's invoices paid more than once of (payments − total).

    The scheme: an invoice is paid twice; the second payment is the diverted amount.
    """
    if not supplier_ids or len(ds.invoices) == 0 or len(ds.bank_transactions) == 0:
        return 0.0
    rec = ds.invoices[ds.invoices["tipo"] == "recibida"]
    rec = rec[rec["counterparty_id"].isin(supplier_ids)]
    inv_uuids = set(rec["uuid"])
    if not inv_uuids:
        return 0.0
    out = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out")
        & (ds.bank_transactions["invoice_uuid"].isin(inv_uuids))
    ]
    if len(out) == 0:
        return 0.0
    total = 0.0
    for uuid_, grp in out.groupby("invoice_uuid"):
        inv = rec[rec["uuid"] == uuid_]
        if len(inv) == 0:
            continue
        inv_total = float(inv.iloc[0]["total"])
        paid = float(grp["amount"].sum())
        if len(grp) >= 2:
            total += paid - inv_total
    return total


def exposure(finding: dict, ds: Dataset) -> dict:
    """Compute the scheme's exposure fields (see the table in ISSUES #23)."""
    accused = finding.get("accused", []) or []
    scheme_type = finding.get("scheme_type", "")
    suppliers = _accused_of(ds, accused, "supplier")
    customers = _accused_of(ds, accused, "customer")
    employees = _accused_of(ds, accused, "employee")
    out: dict[str, float] = {}

    if scheme_type in ("efos_fake_supplier", "kickback_shell", "round_trip_sales"):
        subtotal, iva = _recibida_subtotal_iva(ds, suppliers)
        out["isr_deduction_at_risk"] = round(ISR_RATE * subtotal, 2)
        out["iva_credit_at_risk"] = round(iva, 2)

    if scheme_type == "kickback_shell":
        out["paid_to_employee"] = round(_paid_to_employee(ds, employees), 2)

    if scheme_type == "round_trip_sales":
        out["revenue_overstated"] = round(_revenue_overstated(ds, customers), 2)

    if scheme_type == "duplicate_invoice_payment":
        cash = _duplicate_cash_loss(ds, suppliers)
        out["cash_loss"] = round(cash, 2)
        out["isr_deduction_at_risk"] = round(ISR_RATE * cash, 2)

    return out


# --- money trail -------------------------------------------------------------
def _record_kind(record_id: str, ds: Dataset) -> str | None:
    if len(ds.invoices) and (ds.invoices["uuid"] == record_id).any():
        return "invoice"
    if len(ds.bank_transactions) and (ds.bank_transactions["txn_id"] == record_id).any():
        return "txn"
    if len(ds.counterparty_bank) and (ds.counterparty_bank["record_id"] == record_id).any():
        return "cp"
    if len(ds.goods_receipts) and (ds.goods_receipts["receipt_id"] == record_id).any():
        return "receipt"
    return None


def _invoice_row(ds: Dataset, uuid_: str) -> pd.Series | None:
    sub = ds.invoices[ds.invoices["uuid"] == uuid_]
    return sub.iloc[0] if len(sub) else None


def _txn_row(ds: Dataset, txn_id: str) -> pd.Series | None:
    sub = ds.bank_transactions[ds.bank_transactions["txn_id"] == txn_id]
    return sub.iloc[0] if len(sub) else None


def _cp_row(ds: Dataset, record_id: str) -> pd.Series | None:
    sub = ds.counterparty_bank[ds.counterparty_bank["record_id"] == record_id]
    return sub.iloc[0] if len(sub) else None


def _gr_row(ds: Dataset, receipt_id: str) -> pd.Series | None:
    sub = ds.goods_receipts[ds.goods_receipts["receipt_id"] == receipt_id]
    return sub.iloc[0] if len(sub) else None


def _receipt_note(ds: Dataset, invoice_uuid: str) -> str:
    gr = ds.goods_receipts[ds.goods_receipts["invoice_uuid"] == invoice_uuid]
    if len(gr):
        return f"receipt {str(gr.iloc[0]['receipt_id'])}"
    return "no goods receipt"


def _clabe_warning(ds: Dataset, txn) -> str:
    """Append the CLABE warning when the TX pays a clabe other than the supplier's master."""
    inv_uuid = str(txn.get("invoice_uuid", ""))
    if not inv_uuid:
        return ""
    row = _invoice_row(ds, inv_uuid)
    if row is None:
        return ""
    sid = str(row["counterparty_id"])
    if sid not in set(ds.suppliers["supplier_id"]):
        return ""
    seg = ds.suppliers[ds.suppliers["supplier_id"] == sid]
    if len(seg) == 0:
        return ""
    master = str(seg.iloc[0]["clabe"])
    if str(txn.get("counterparty_clabe", "")) != master:
        return _CLABE_WARN
    return ""


def _employee_clabe_note(ds: Dataset, clabe: str) -> str:
    """' = personal CLABE of <name> (<role>)' when a counterparty clabe is an employee's."""
    if not clabe or len(ds.employees) == 0:
        return ""
    sub = ds.employees[ds.employees["personal_clabe"] == clabe]
    if len(sub) == 0:
        return ""
    r = sub.iloc[0]
    return f" = personal CLABE of {r['name']} ({r['role']})"


def _company_name(ds: Dataset) -> str:
    return str(ds.company.get("name", ""))


def _build_trail_row(step: int, fecha, kind: str, record_id: str, _from: str, _to: str, amount: float, note: str) -> dict:
    return {
        "step": step,
        "fecha": _fmt_date(fecha),
        "kind": kind,
        "record_id": record_id,
        "from": _from,
        "to": _to,
        "amount_mxn": round(amount, 2),
        "note": note,
    }


def money_trail(finding: dict, ds: Dataset) -> list[dict]:
    """One row per cited record, sorted by (fecha, record_id)."""
    company = _company_name(ds)
    rows: list[dict] = []
    for record_id in finding.get("evidence", []) or []:
        kind = _record_kind(record_id, ds)
        if kind == "invoice":
            row = _invoice_row(ds, record_id)
            if row is None:
                continue
            tipo = str(row["tipo"])
            if tipo == "recibida":
                sid = str(row["counterparty_id"])
                rows.append(
                    _build_trail_row(
                        0, row["fecha"], "invoice", record_id,
                        _supplier_name(ds, sid), company, float(row["total"]),
                        f"{row['descripcion']} — {_receipt_note(ds, record_id)}",
                    )
                )
            else:  # emitida
                cid = str(row["counterparty_id"])
                cname, _ = _entity_name(ds, cid)
                rows.append(
                    _build_trail_row(
                        0, row["fecha"], "invoice", record_id,
                        company, cname, float(row["total"]), str(row["descripcion"]),
                    )
                )
        elif kind == "txn":
            row = _txn_row(ds, record_id)
            if row is None:
                continue
            direction = str(row["direction"])
            amount = float(row["amount"])
            note = str(row.get("reference", "")) or ""
            note += _clabe_warning(ds, row)
            if direction == "out":
                rows.append(
                    _build_trail_row(
                        0, row["fecha"], "txn", record_id,
                        company, str(row["counterparty_name"]), amount, note,
                    )
                )
            else:
                rows.append(
                    _build_trail_row(
                        0, row["fecha"], "txn", record_id,
                        str(row["counterparty_name"]), company, amount, note,
                    )
                )
        elif kind == "cp":
            row = _cp_row(ds, record_id)
            if row is None:
                continue
            note = str(row.get("reference", "")) or ""
            note += _employee_clabe_note(ds, str(row.get("counterparty_clabe", "")))
            rows.append(
                _build_trail_row(
                    0, row["fecha"], "cp", record_id,
                    str(row["entity_name"]), str(row["counterparty_name"]),
                    float(row["amount"]), note,
                )
            )
        elif kind == "receipt":
            row = _gr_row(ds, record_id)
            if row is None:
                continue
            rows.append(
                _build_trail_row(
                    0, row["fecha"], "receipt", record_id,
                    _supplier_name(ds, str(row["supplier_id"])), str(row["warehouse"]),
                    float(row["cantidad"]) if row.get("cantidad") is not None else 0.0,
                    _employee_name(ds, str(row["received_by"])),
                )
            )

    rows.sort(key=lambda r: (r["fecha"], r["record_id"]))
    for i, r in enumerate(rows, 1):
        r["step"] = i
    return rows


def _trail_table(rows: list[dict]) -> str:
    header = "| # | Date | Kind | Record | From | To | Amount (MXN) | Note |"
    sep = "|---:|---|---|---|---|---:|---|"
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"| {r['step']} | {r['fecha']} | {r['kind']} | {r['record_id']} "
            f"| {r['from']} | {r['to']} | {_money(r['amount_mxn'])} | {r['note']} |"
        )
    return "\n".join(lines)


def _group_evidence(evidence: list[str], ds: Dataset) -> list[tuple[str, list[str]]]:
    """Group evidence by kind (invoices, bank transactions, counterparty records, receipts)."""
    groups: dict[str, list[str]] = {}
    for e in evidence:
        kind = _record_kind(e, ds) or "unknown"
        groups.setdefault(kind, []).append(e)
    order = ["invoice", "txn", "cp", "receipt", "unknown"]
    labels = {
        "invoice": "Invoices",
        "txn": "Bank transactions",
        "cp": "Counterparty records",
        "receipt": "Goods receipts",
        "unknown": "Other",
    }
    out = []
    for kind in order:
        if kind in groups:
            out.append((labels[kind], sorted(groups[kind])))
    return out


# --- render ------------------------------------------------------------------
def _primary_exposure(expo: dict) -> str:
    for key in ("isr_deduction_at_risk", "paid_to_employee", "revenue_overstated", "cash_loss"):
        if key in expo:
            return _money(expo[key])
    return "—"


def _exposure_lines(finding: dict, ds: Dataset, expo: dict) -> list[str]:
    st = finding.get("scheme_type", "")
    lines: list[str] = []
    if "isr_deduction_at_risk" in expo:
        suppliers = _accused_of(ds, finding.get("accused", []), "supplier")
        subtotal, _iva = _recibida_subtotal_iva(ds, suppliers)
        if st == "duplicate_invoice_payment":
            lines.append(
                f"ISR deduction at risk: MXN {_money(expo['isr_deduction_at_risk'])} "
                f"(30% of the MXN {_money(expo['cash_loss'])} duplicated payment)"
            )
        else:
            lines.append(
                f"ISR deduction at risk: MXN {_money(expo['isr_deduction_at_risk'])} "
                f"(30% of MXN {_money(subtotal)} subtotal)"
            )
    if "iva_credit_at_risk" in expo:
        lines.append(f"IVA credit at risk: MXN {_money(expo['iva_credit_at_risk'])} (16% of numerator)")
    if "paid_to_employee" in expo:
        lines.append(f"Paid to employee: MXN {_money(expo['paid_to_employee'])}")
    if "revenue_overstated" in expo:
        lines.append(f"Revenue overstated: MXN {_money(expo['revenue_overstated'])}")
    if "cash_loss" in expo:
        lines.append(f"Cash loss: MXN {_money(expo['cash_loss'])}")
    return lines




# --- the document model -------------------------------------------------------
# One structure, two emitters: everything below builds plain data, and `render`
# (Markdown) and `render_html` turn the same data into their own markup. That is why
# the two documents can never drift apart.

# What this system cannot see, stated plainly because claiming completeness we cannot
# defend scores worse than admitting the edge (case_file_structure.md, section 5).
CANNOT_DETECT = (
    "collusion that never moves money through the books — a favour, a job for a relative, "
    "an off-ledger cash payment",
    "a supplier that is real, delivers, and simply overcharges: the price is not in the records",
    "schemes whose counterparty banks somewhere this estate does not show, since a transfer "
    "is only visible when one of its two legs is in the data",
    "forged source documents that are internally consistent — the books are taken at face value",
    "anything outside the audit period, or entities with no invoice, ledger entry or transfer",
)

OUT_OF_SCOPE = (
    "valuation and transfer-pricing opinions",
    "payroll, tax filings and anything not reachable from the eight tables of the estate",
    "interviews, contracts held outside the system, and physical inspection",
)

_ARCHITECTURE = (
    "Deterministic detectors read every table and raise leads; leads about the same entities are "
    "merged into one docket per suspected scheme. Each docket is investigated — a hypothesis, then "
    "read-only tools that answer it with record ids — and an evidence guard re-derives the peso "
    "amount from the books and rejects any accusation whose rule, records or arithmetic do not hold. "
    "Only what survives the guard is printed here; everything else is listed in section 4 with the "
    "reason it was closed. The same pipeline produces this document and the machine-checked "
    "submission.json, so the two cannot disagree."
)


def _company_display(ds: Dataset) -> str:
    """The company as a header should name it; judge estates only give us an RFC."""
    name = str(ds.company.get("name", ""))
    rfc = str(ds.company.get("rfc", ""))
    if name and name != rfc:
        return f"{name} (RFC {rfc})" if rfc else name
    return f"the company (RFC {rfc})" if rfc else "the company"


def _audit_period(ds: Dataset) -> str:
    if len(ds.invoices) == 0:
        return "no invoices in this estate"
    dates = ds.invoices["fecha"].dropna()
    if len(dates) == 0:
        return "undated"
    return f"{_fmt_date(dates.min())} to {_fmt_date(dates.max())}"


def _deterministic_line(meta: dict) -> str:
    """Judges may run the seed twice; say whether that reproduces this file, and why."""
    if meta.get("deterministic", True):
        note = str(meta.get("deterministic_note") or "")
        if note:
            return f"yes — {note}"
        if int(meta.get("llm_calls", 0) or 0) == 0:
            return "yes — no model was called; detectors, guard and report are pure functions of the books"
        return "yes"
    return "no — the model was called live; re-running replays from the on-disk cache, which is deterministic"


def _header_rows(ds: Dataset, submission: dict, generated_at: str) -> list[tuple[str, str]]:
    meta = submission.get("run_metadata", {}) or {}
    return [
        ("Company", _company_display(ds)),
        ("Audit period", _audit_period(ds)),
        ("Estate seed", str(submission.get("seed", 0))),
        ("LLM calls", str(meta.get("llm_calls", 0))),
        ("Cost", f"MXN {_money(float(meta.get('mxn_cost', 0.0)))}"),
        ("Wall-clock", f"{float(meta.get('wall_clock_seconds', 0.0)):.2f} s"),
        ("Deterministic", _deterministic_line(meta)),
        ("Generated at", generated_at),
    ]


def _confidence_phrase(findings: list[dict]) -> str:
    proven = sum(1 for f in findings if f.get("confidence") == "proven")
    probable = len(findings) - proven
    if not findings:
        return "0"
    parts = []
    if proven:
        parts.append(f"{proven} proven")
    if probable:
        parts.append(f"{probable} probable")
    return f"{len(findings)} ({', '.join(parts)})"


def _summary_rows(submission: dict) -> list[tuple[str, str]]:
    findings = submission.get("findings", [])
    total = sum(float(f.get("peso_amount", 0.0)) for f in findings)
    return [
        ("Findings", _confidence_phrase(findings)),
        ("Total exposure", f"MXN {_money(total)}"),
        ("Leads investigated and closed", str(len(submission.get("leads_not_pursued", [])))),
    ]


def _summary_sentences(case: dict, ds: Dataset, submission: dict) -> str:
    findings = submission.get("findings", [])
    leads = submission.get("leads_not_pursued", [])
    total = sum(float(f.get("peso_amount", 0.0)) for f in findings)
    entities = sorted({e for f in findings for e in f.get("entities", [])})
    kinds = sorted({str(f.get("scheme_type", "")).replace("_", " ") for f in findings})

    first = (
        f"The books of {_company_display(ds)} were examined in full for {_audit_period(ds)}: "
        f"{len(ds.invoices):,} invoices, {len(ds.bank_transactions):,} bank movements and "
        f"{len(ds.ledger):,} ledger entries."
    )
    if not findings:
        return (
            first
            + " No accusation survived the evidence guard, so this case file makes none: on these "
            + f"records there is nothing to report. {len(leads)} lead(s) were opened and closed; "
            + "section 4 names each one and why."
        )
    second = (
        f"{len(findings)} scheme(s) are evidenced — {', '.join(kinds)} — against "
        f"{len(entities)} entit{'y' if len(entities) == 1 else 'ies'}, totalling MXN {_money(total)}."
    )
    third = (
        "Every peso claimed is reconciled below to the records cited beneath it, and every record id "
        "can be looked up in the estate."
    )
    fourth = (
        f"A further {len(leads)} lead(s) were investigated and closed without an accusation; "
        f"section 4 names each one, what raised it, and why it was dropped."
    )
    return " ".join([first, second, third, fourth])


def _tax_exposure_lines(case: dict, ds: Dataset) -> list[str]:
    """Kept from #23 as a bonus estimate; never part of a finding's peso_amount."""
    isr = iva = 0.0
    for finding in case.get("findings", []):
        expo = exposure(finding, ds)
        isr += float(expo.get("isr_deduction_at_risk", 0.0))
        iva += float(expo.get("iva_credit_at_risk", 0.0))
    lines = []
    if isr:
        lines.append(f"ISR deduction at risk: MXN {_money(isr)} (30% of the disallowed subtotals, LISR Art. 9)")
    if iva:
        lines.append(f"IVA credit at risk: MXN {_money(iva)} (16% charged on the same invoices)")
    return lines


# --- the money-trail diagram --------------------------------------------------
def _trail_nodes(trail: list[dict]) -> list[str]:
    """Every party in the trail, in the order the money first touches it."""
    nodes: list[str] = []
    for step in trail:
        for key in ("from", "to"):
            name = str(step.get(key, "")) or "unidentified account"
            if name not in nodes:
                nodes.append(name)
    return nodes


def _edge_label(step: dict) -> str:
    return f"{step.get('exhibit_id', '')} · MXN {_money(float(step.get('amount', 0.0)))} · {step.get('date', '')}"


def mermaid(trail: list[dict]) -> str:
    """The trail as a ``mermaid`` flowchart: one node per party, one edge per step."""
    nodes = _trail_nodes(trail)
    index = {name: f"N{i}" for i, name in enumerate(nodes)}
    lines = ["```mermaid", "flowchart LR"]
    for name in nodes:
        lines.append(f'    {index[name]}["{_mermaid_text(name)}"]')
    for step in trail:
        src = index[str(step.get("from", "")) or "unidentified account"]
        dst = index[str(step.get("to", "")) or "unidentified account"]
        lines.append(f'    {src} -->|"{_mermaid_text(_edge_label(step))}"| {dst}')
    lines.append("```")
    return "\n".join(lines)


def _mermaid_text(text: str) -> str:
    """Quotes and pipes end a mermaid label early; nothing else needs escaping."""
    return text.replace('"', "'").replace("|", "/")


def _xml(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _shorten(text: str, limit: int = 30) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


# Layout constants for the SVG. One column per party, one row per step: a ten-payment
# trail stays readable instead of becoming ten arrows stacked on one line.
_COL_W = 250
_MARGIN_X = 20
_HEAD_Y = 18
_HEAD_H = 40
_ROW_H = 56
_ROW_TOP = 96


def svg(trail: list[dict], *, title: str = "") -> str:
    """The same graph as inline SVG: parties as columns, each step as its own arrow row.

    Pure geometry, no library, no external asset and no URL — an ``xmlns`` would be a URL
    and inline SVG in HTML does not need one, which is also what keeps the file offline.
    """
    nodes = _trail_nodes(trail)
    if not nodes:
        return '<svg role="img" width="320" height="60"><text x="10" y="34" font-size="13">No dated movement to draw.</text></svg>'

    column = {name: _MARGIN_X + i * _COL_W + _COL_W // 2 for i, name in enumerate(nodes)}
    width = _MARGIN_X * 2 + len(nodes) * _COL_W
    height = _ROW_TOP + max(len(trail), 1) * _ROW_H + 16

    out: list[str] = [
        f'<svg role="img" aria-label="{_xml(title or "money trail")}" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" class="trail">',
        '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#333"/></marker></defs>',
    ]
    for name in nodes:
        x = column[name]
        out.append(
            f'<rect x="{x - _COL_W // 2 + 10}" y="{_HEAD_Y}" width="{_COL_W - 20}" height="{_HEAD_H}" '
            f'rx="6" fill="#eef2f7" stroke="#8ea2bd"/>'
        )
        out.append(
            f'<text x="{x}" y="{_HEAD_Y + 25}" text-anchor="middle" font-size="13" '
            f'font-weight="600" fill="#1b2733">{_xml(_shorten(name))}</text>'
        )
        out.append(
            f'<line x1="{x}" y1="{_HEAD_Y + _HEAD_H}" x2="{x}" y2="{height - 10}" '
            f'stroke="#c3cedd" stroke-dasharray="4 4"/>'
        )

    for i, step in enumerate(trail):
        y = _ROW_TOP + i * _ROW_H
        src = column[str(step.get("from", "")) or "unidentified account"]
        dst = column[str(step.get("to", "")) or "unidentified account"]
        label = _xml(_edge_label(step))
        if src == dst:  # money that never left the account it started in
            out.append(
                f'<path d="M{src},{y} q60,-18 0,-30" fill="none" stroke="#333" marker-end="url(#arrow)"/>'
            )
            out.append(f'<text x="{src + 70}" y="{y - 20}" font-size="12" fill="#1b2733">{label}</text>')
            continue
        out.append(f'<line x1="{src}" y1="{y}" x2="{dst}" y2="{y}" stroke="#333" marker-end="url(#arrow)"/>')
        out.append(
            f'<text x="{(src + dst) // 2}" y="{y - 8}" text-anchor="middle" font-size="12" '
            f'fill="#1b2733">{label}</text>'
        )
    out.append("</svg>")
    return "".join(out)


# --- per-finding view ---------------------------------------------------------
def _reconciliation(finding: dict, ds: Dataset) -> str:
    """The arithmetic, in the table the judges will reconcile against.

    They sum exhibit amounts per source table and compare the closest table to the claim,
    so the line has to name the table it is adding up.
    """
    claimed = float(finding.get("peso_amount", 0.0))
    per_table: dict[str, list[tuple[str, float]]] = {}
    for ex in finding.get("exhibits", []):
        table = ex.get("source_table", "")
        column = _AMOUNT_COLUMN.get(table)
        if not column:
            continue
        per_table.setdefault(table, []).append(
            (ex.get("exhibit_id", ""), _exhibit_amount(ex.get("record_id", ""), table, ds))
        )
    if not per_table:
        return "No cited exhibit carries an amount, so this finding claims nothing that can be reconciled."

    table, rows = min(
        per_table.items(), key=lambda kv: abs(claimed - sum(amount for _, amount in kv[1]))
    )
    total = sum(amount for _, amount in rows)
    terms = " + ".join(f"{eid} {_money(amount)}" for eid, amount in rows)
    verdict = "= claimed" if abs(total - claimed) <= 0.01 else f"vs claimed MXN {_money(claimed)}"
    return f"`{table}`: {terms} = **MXN {_money(total)}** {verdict}."


_AMOUNT_COLUMN = {"invoices": "total", "bank_txns": "amount", "purchase_orders": "amount", "contracts": "value"}


def _exhibit_amount(record_id: str, table: str, ds: Dataset) -> float:
    from .submit import _amount_of

    return _amount_of(record_id, table, ds)


def _finding_heading(finding: dict, ds: Dataset) -> str:
    entities = finding.get("entities", []) or []
    names = []
    for entity in entities:
        name, _ = _entity_name(ds, _internal_id(entity, ds))
        names.append(name if name != entity else entity)
    label = " & ".join(names) if names else "unnamed entity"
    return f"{label} ({', '.join(entities)}) — {finding.get('scheme_type', '')}"


def _internal_id(prefixed: str, ds: Dataset) -> str:
    """Map a judges' entity id back to the id the Dataset frames use, for name lookup."""
    if len(ds.suppliers):
        hit = ds.suppliers[ds.suppliers["supplier_id"] == prefixed]
        if len(hit):
            return prefixed
    rfc = prefixed.split(":", 1)[1] if prefixed.startswith("RFC:") else ""
    if rfc:
        for frame, key in ((ds.suppliers, "supplier_id"), (ds.customers, "customer_id")):
            if len(frame):
                hit = frame[frame["rfc"] == rfc]
                if len(hit):
                    return str(hit.iloc[0][key])
    if prefixed.startswith("EMP:") and len(ds.employees):
        digits = prefixed.split(":", 1)[1]
        for candidate in (prefixed, f"E{digits}"):
            hit = ds.employees[ds.employees["employee_id"] == candidate]
            if len(hit):
                return str(hit.iloc[0]["employee_id"])
    return prefixed


def _challenge_text(finding: dict, challenges: dict[str, str] | None = None) -> str:
    """What an adversarial review argued, and why the finding held (#91)."""
    challenges = challenges or {}
    ch = finding.get("challenge") or {}
    if isinstance(ch, dict) and ch.get("arguments"):
        fought = "; ".join(
            f"{a.get('outcome', '')} — {a.get('claim', '')}"
            + (f" [{' '.join(a.get('records', [])[:4])}]" if a.get("records") else "")
            for a in ch["arguments"]
        )
        if ch.get("verdict") == "survived":
            verdict = "The finding survived the adversarial review."
        elif ch.get("verdict") == "killed":
            verdict = "The finding was killed by the adversarial review and is reported as a declined lead."
        else:
            verdict = f"The adversarial review returned '{ch.get('verdict')}'."
        return f"{verdict} Each argument was tested against the records: {fought}."
    key = ",".join(finding.get("entities", []))
    if key in challenges:
        return str(challenges[key])
    return (
        "No adversarial review ran against this finding in this build, so it stands on the guard's "
        "checks alone: the rule, the records and the arithmetic above. A finding nobody has tried to "
        "break is weaker than one that was attacked and held, and this one has not been attacked."
    )


def _lead_view(lead: dict, ds: Dataset) -> dict:
    entity = str(lead.get("entity", ""))
    name, _ = _entity_name(ds, _internal_id(entity, ds))
    tools = lead.get("tool_calls_made", []) or []
    return {
        "title": f"{name} ({entity})" if name != entity else entity,
        "signal": str(lead.get("signal", "")) or "—",
        "reason": str(lead.get("reason", "")) or "—",
        "tools": ", ".join(str(t) for t in tools) if tools else "none — closed on the records alone",
        "closed_by": str(lead.get("closed_by", "")) or "investigator",
    }


def _reproduction_command(ds: Dataset, submission: dict) -> str:
    return (
        f"python -m agent.investigate {ds.path} --no-llm "
        f"--out case_file.json --submission submission.json && "
        f"python -m agent.report {ds.path} case_file.json --submission submission.json "
        f"--out report.md --html report.html"
    )


def _method_items(ds: Dataset, submission: dict) -> list[tuple[str, list[str]]]:
    meta = submission.get("run_metadata", {}) or {}
    replay = (
        "This file was produced with no network call at all."
        if int(meta.get("llm_calls", 0) or 0) == 0
        else "Re-running replays the model's answers from the on-disk cache, so the file can be "
        "regenerated with the network disabled."
    )
    return [
        ("Architecture", [_ARCHITECTURE]),
        ("Out of scope for this run", list(OUT_OF_SCOPE)),
        ("What this system cannot detect", list(CANNOT_DETECT)),
        ("Reproducibility", [f"`{_reproduction_command(ds, submission)}`", replay]),
    ]


def _submission_for(case: dict, ds: Dataset, submission: dict | None, log: list[dict] | None) -> dict:
    if submission is not None:
        return submission
    from .submit import build_submission

    return build_submission(case, ds, log or [], {})


# --- Markdown -----------------------------------------------------------------
def _md_table(rows: list[tuple[str, str]]) -> list[str]:
    out = ["| | |", "|---|---|"]
    out.extend(f"| {key} | {value} |" for key, value in rows)
    return out


def render(
    case: dict,
    ds: Dataset,
    *,
    submission: dict | None = None,
    log: list[dict] | None = None,
    generated_at: str | None = None,
    challenges: dict[str, str] | None = None,
) -> str:
    """The five required sections as Markdown, money trail as a ``mermaid`` diagram."""
    sub = _submission_for(case, ds, submission, log)
    challenges = challenges or {}
    generated_at = generated_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    findings = sub.get("findings", [])

    parts: list[str] = [f"# Forensic case file — {_company_display(ds)}", ""]

    parts += ["## Header", ""] + _md_table(_header_rows(ds, sub, generated_at)) + [""]

    parts += ["## Executive summary", "", _summary_sentences(case, ds, sub), ""]
    parts += _md_table(_summary_rows(sub)) + [""]
    tax = _tax_exposure_lines(case, ds)
    if tax:
        parts.append("**Tax exposure (bonus estimate)** — an estimate of what the tax authority could "
                     "disallow, not part of any finding's claimed amount:")
        parts.append("")
        parts += [f"- {line}" for line in tax]
        parts.append("")

    parts += ["## Findings", ""]
    if not findings:
        parts += ["No accusation survived the evidence guard on these records.", ""]
    for finding in findings:
        parts.append(f"### {_finding_heading(finding, ds)}")
        parts.append("")
        parts.append(f"**Rule broken** — {finding.get('rule_broken', '')}")
        parts.append("")
        parts.append(
            f"**Amount and confidence** — MXN {_money(float(finding.get('peso_amount', 0.0)))}, "
            f"`{finding.get('confidence', '')}`"
        )
        parts.append("")
        parts.append("**What happened**")
        parts.append("")
        parts.append(finding.get("narrative", ""))
        parts.append("")
        parts.append("**Money trail**")
        parts.append("")
        parts.append(mermaid(finding.get("money_trail", []) or []))
        parts.append("")
        parts.append("**Exhibits**")
        parts.append("")
        parts.append("| Exhibit | Source table | Record id | What it proves |")
        parts.append("|---|---|---|---|")
        for ex in finding.get("exhibits", []):
            parts.append(
                f"| {ex.get('exhibit_id', '')} | `{ex.get('source_table', '')}` "
                f"| `{ex.get('record_id', '')}` | {ex.get('note', '')} |"
            )
        parts.append("")
        parts.append("**Reconciliation**")
        parts.append("")
        parts.append(_reconciliation(finding, ds))
        parts.append("")
        parts.append("**Challenge**")
        parts.append("")
        parts.append(_challenge_text(finding, challenges))
        parts.append("")

    parts += ["## Leads not pursued", ""]
    leads = sub.get("leads_not_pursued", [])
    if not leads:
        parts += ["No lead was opened and closed in this run.", ""]
    for lead in leads:
        view = _lead_view(lead, ds)
        parts.append(f"### {view['title']}")
        parts.append("")
        parts.append(f"- **Signal:** {view['signal']}")
        parts.append(f"- **Reason:** {view['reason']}")
        parts.append(f"- **Tools called:** {view['tools']}")
        parts.append(f"- **Closed by:** {view['closed_by']}")
        parts.append("")

    parts += ["## Method and limits", ""]
    for title, items in _method_items(ds, sub):
        parts.append(f"**{title}**")
        parts.append("")
        parts += [f"- {item}" for item in items]
        parts.append("")

    return "\n".join(parts).strip() + "\n"


# --- HTML ---------------------------------------------------------------------
_CSS = """
:root { color-scheme: light; }
body { margin: 0; padding: 28px 20px 64px; background: #fbfcfd; color: #1b2733;
       font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
main { max-width: 940px; margin: 0 auto; }
h1 { font-size: 1.7rem; margin: 0 0 4px; }
h2 { font-size: 1.25rem; margin: 40px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #d8e0ea; }
h3 { font-size: 1.05rem; margin: 28px 0 8px; }
p { margin: 10px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.93rem; }
th, td { border: 1px solid #d8e0ea; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #eef2f7; font-weight: 600; }
code { background: #eef2f7; border-radius: 3px; padding: 1px 4px; font-size: 0.9em; }
ul { margin: 8px 0; padding-left: 22px; }
li { margin: 4px 0; }
.label { font-weight: 600; }
.trail { display: block; max-width: 100%; height: auto; margin: 10px 0 4px; overflow: visible; }
.figure { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 8px; }
.lead { border-left: 3px solid #c3cedd; padding-left: 12px; margin: 16px 0; }
.meta { color: #5b6b7c; font-size: 0.9rem; }
"""


def _html_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"<tr><th>{_xml(k)}</th><td>{_xml(v)}</td></tr>" for k, v in rows)
    return f"<table>{body}</table>"


def render_html(
    case: dict,
    ds: Dataset,
    *,
    submission: dict | None = None,
    log: list[dict] | None = None,
    generated_at: str | None = None,
    challenges: dict[str, str] | None = None,
) -> str:
    """The same five sections as a self-contained HTML file: inline SVG, no assets, no script."""
    sub = _submission_for(case, ds, submission, log)
    challenges = challenges or {}
    generated_at = generated_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    findings = sub.get("findings", [])
    company = _company_display(ds)

    out: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Forensic case file — {_xml(company)}</title>",
        f"<style>{_CSS}</style></head><body><main>",
        f"<h1>Forensic case file — {_xml(company)}</h1>",
        "<h2>Header</h2>",
        _html_table(_header_rows(ds, sub, generated_at)),
        "<h2>Executive summary</h2>",
        f"<p>{_xml(_summary_sentences(case, ds, sub))}</p>",
        _html_table(_summary_rows(sub)),
    ]
    tax = _tax_exposure_lines(case, ds)
    if tax:
        out.append(
            '<p class="meta"><span class="label">Tax exposure (bonus estimate)</span> — an estimate of '
            "what the tax authority could disallow, not part of any finding's claimed amount:</p>"
        )
        out.append("<ul>" + "".join(f"<li>{_xml(line)}</li>" for line in tax) + "</ul>")

    out.append("<h2>Findings</h2>")
    if not findings:
        out.append("<p>No accusation survived the evidence guard on these records.</p>")
    for finding in findings:
        out.append(f"<h3>{_xml(_finding_heading(finding, ds))}</h3>")
        out.append(f'<p><span class="label">Rule broken</span> — {_xml(finding.get("rule_broken", ""))}</p>')
        out.append(
            f'<p><span class="label">Amount and confidence</span> — MXN '
            f'{_money(float(finding.get("peso_amount", 0.0)))}, <code>{_xml(finding.get("confidence", ""))}</code></p>'
        )
        out.append('<p class="label">What happened</p>')
        out.append(f"<p>{_xml(finding.get('narrative', ''))}</p>")
        out.append('<p class="label">Money trail</p>')
        out.append(
            f'<div class="figure">{svg(finding.get("money_trail", []) or [], title=_finding_heading(finding, ds))}</div>'
        )
        out.append('<p class="label">Exhibits</p>')
        rows = "".join(
            f"<tr><td>{_xml(ex.get('exhibit_id', ''))}</td><td><code>{_xml(ex.get('source_table', ''))}</code></td>"
            f"<td><code>{_xml(ex.get('record_id', ''))}</code></td><td>{_xml(ex.get('note', ''))}</td></tr>"
            for ex in finding.get("exhibits", [])
        )
        out.append(
            "<table><tr><th>Exhibit</th><th>Source table</th><th>Record id</th><th>What it proves</th></tr>"
            + rows
            + "</table>"
        )
        out.append('<p class="label">Reconciliation</p>')
        out.append(f"<p>{_md_inline_to_html(_reconciliation(finding, ds))}</p>")
        out.append('<p class="label">Challenge</p>')
        out.append(f"<p>{_xml(_challenge_text(finding, challenges))}</p>")

    out.append("<h2>Leads not pursued</h2>")
    leads = sub.get("leads_not_pursued", [])
    if not leads:
        out.append("<p>No lead was opened and closed in this run.</p>")
    for lead in leads:
        view = _lead_view(lead, ds)
        out.append(
            '<div class="lead">'
            f"<h3>{_xml(view['title'])}</h3><ul>"
            f'<li><span class="label">Signal:</span> {_xml(view["signal"])}</li>'
            f'<li><span class="label">Reason:</span> {_xml(view["reason"])}</li>'
            f'<li><span class="label">Tools called:</span> {_xml(view["tools"])}</li>'
            f'<li><span class="label">Closed by:</span> {_xml(view["closed_by"])}</li>'
            "</ul></div>"
        )

    out.append("<h2>Method and limits</h2>")
    for title, items in _method_items(ds, sub):
        out.append(f'<p class="label">{_xml(title)}</p>')
        out.append("<ul>" + "".join(f"<li>{_md_inline_to_html(item)}</li>" for item in items) + "</ul>")

    out.append("</main></body></html>")
    return "\n".join(out) + "\n"


def _md_inline_to_html(text: str) -> str:
    """Escape, then re-apply the only two inline marks these strings use: `code` and **bold**."""
    escaped = _xml(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


# --- CLI ---------------------------------------------------------------------
def _read_log(path: str | None) -> list[dict] | None:
    if not path or not Path(path).exists():
        return None
    entries: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="python -m agent.report")
    parser.add_argument("dataset_dir", help="the estate the case file was produced from")
    parser.add_argument("case_file")
    parser.add_argument("--submission", default=None, help="submission.json; rebuilt from the case file when absent")
    parser.add_argument("--out", default=None, help="markdown output (default: <case_file>.md)")
    parser.add_argument("--html", default=None, help="self-contained HTML output")
    parser.add_argument("--log", default=None)
    args = parser.parse_args(argv)

    case_path = Path(args.case_file)
    out_path = Path(args.out) if args.out else case_path.with_suffix(".md")

    ds = load(args.dataset_dir)
    try:
        case = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{args.case_file}: invalid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate_case_file(case, ds)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    submission = None
    if args.submission and Path(args.submission).exists():
        submission = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    log = _read_log(args.log)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(case, ds, submission=submission, log=log), encoding="utf-8")
    print(f"wrote {out_path}")
    if args.html:
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(case, ds, submission=submission, log=log), encoding="utf-8")
        print(f"wrote {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
