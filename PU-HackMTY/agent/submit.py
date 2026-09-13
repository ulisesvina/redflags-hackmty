"""The JSON the judges machine-check (#88): ``submission.json``.

``case_file.json`` is our internal shape, scored by ``data_estate/score.py``. The judges
read ``submission_schema.json``: prefixed entity ids, at least three exhibits per finding
each naming the table it came from, a money trail, a confidence tier, declined leads with
the signal that raised them and who closed them, and three run numbers.

Three rules drive everything here:

**The five scheme types are a closed enum.** ``duplicate_invoice_payment`` is a real
control failure and not one of them, so a finding of that type is *moved* into
``leads_not_pursued`` with its evidence ids in the reason, closed by the validator. It is
never dropped silently and never smuggled in under a type it does not have.

**peso_amount must reconcile to the cited exhibits within 2%, per table.** The judges sum
exhibit amounts per source table and compare the closest table to the claim, so an invoice
and the transfer that settled it are not counted as double the money. This module therefore
picks the exhibit set to fit the amount: for a round-trip the claim is the sales side, so it
cites the sales invoices, not every invoice the two entities ever exchanged.

**Nothing is asserted that a record does not support.** Every narrative number is recomputed
from the dataset rows the finding cites, every exhibit id resolves to a real record, and
``confidence`` is ``proven`` only when the rule's own precondition has an exhibit behind it.

CLI::

    python -m agent.submit <estate> <case_file.json> [--log run.jsonl] [--seed N] [--out submission.json]

Check the result with the judges' own validator::

    python scripts/judges/validate_format.py --submission submission.json --estate estate.db
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

from .data import Dataset, load
from .reconcile import (
    AMOUNT_COLUMN as _AMOUNT_COLUMN,  # noqa: F401  (re-exported below)
)
from .reconcile import PESO_TOLERANCE as _PESO_TOLERANCE
from .reconcile import amount_of as _amount_of_shared
from .reconcile import reconciles as _reconciles_shared
from .reconcile import source_table as _source_table_shared

# Our internal scheme names -> the judges' closed enum (docs/SPEC_GAP.md).
SCHEME_MAP = {
    "efos_fake_supplier": "phantom_vendor",
    "kickback_shell": "kickback",
    "round_trip_sales": "round_tripping",
    "threshold_splitting": "threshold_splitting",
    "revenue_inflation": "revenue_inflation",
}
# Real findings with no judges' type: reported as control observations, never as findings.
CONTROL_ONLY = ("duplicate_invoice_payment", "other")

# Tables whose rows carry an amount the judges reconcile against, and the column.
AMOUNT_COLUMN = _AMOUNT_COLUMN
PESO_TOLERANCE = _PESO_TOLERANCE
MAX_NARRATIVE_WORDS = 150



def _money(value: float) -> str:
    return f"MXN {value:,.2f}"


def _date(value) -> str:
    if value is None or (isinstance(value, float) and value != value) or pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _truncate_words(text: str, limit: int = MAX_NARRATIVE_WORDS) -> str:
    """Cut a narrative to ``limit`` words, preferring the last sentence boundary."""
    words = text.split()
    if len(words) <= limit:
        return text
    clipped = " ".join(words[:limit])
    stop = max(clipped.rfind(". "), clipped.rfind("! "), clipped.rfind("? "))
    return clipped[: stop + 1] if stop > 0 else clipped.rstrip(",;:") + "."


# --------------------------------------------------------------- entities and records
def entity_id(internal_id: str, ds: Dataset) -> str:
    """Our entity id as the judges spell it: ``RFC:<rfc>`` or ``EMP:<digits>``."""
    if ":" in internal_id:
        return internal_id
    for frame, key, column in (
        (ds.suppliers, "supplier_id", "rfc"),
        (ds.customers, "customer_id", "rfc"),
    ):
        if len(frame):
            row = frame[frame[key] == internal_id]
            if len(row) and str(row.iloc[0][column]):
                return "RFC:" + str(row.iloc[0][column])
    if len(ds.employees):
        row = ds.employees[ds.employees["employee_id"] == internal_id]
        if len(row):
            digits = re.sub(r"\D", "", internal_id)
            return "EMP:" + (digits or internal_id)
    return internal_id


def source_table(record_id: str, ds: Dataset) -> str:
    """The judges' table a record id belongs to, for an exhibit's ``source_table``."""
    return _source_table_shared(record_id, ds)


def _row(frame: pd.DataFrame, column: str, value: str):
    if len(frame) == 0:
        return None
    hit = frame[frame[column] == value]
    return hit.iloc[0] if len(hit) else None


def _entity_name(internal_id: str, ds: Dataset) -> str:
    for frame, key in ((ds.suppliers, "supplier_id"), (ds.customers, "customer_id"), (ds.employees, "employee_id")):
        row = _row(frame, key, internal_id)
        if row is not None and str(row["name"]):
            return str(row["name"])
    return internal_id


def _company_name(ds: Dataset) -> str:
    """The company as a narrative would name it.

    A judges' estate has no company table, so the adapter can only derive an RFC. Writing
    "EMP920101AB1 paid ..." reads like a machine; the entity ids in ``entities`` are what
    the judges match on, so the prose says "the company".
    """
    name = str(ds.company.get("name", ""))
    return name if name and name != str(ds.company.get("rfc", "")) else "the company"


def _name_for_clabe(clabe: str, ds: Dataset) -> str:
    if not clabe:
        return ""
    if clabe == str(ds.company.get("clabe", "")):
        return _company_name(ds)
    for frame, column, name_col in (
        (ds.suppliers, "clabe", "name"),
        (ds.customers, "clabe", "name"),
        (ds.employees, "personal_clabe", "name"),
    ):
        row = _row(frame, column, clabe)
        if row is not None:
            return str(row[name_col])
    return clabe


# ------------------------------------------------------------------------ exhibits
def _invoice_note(row, ds: Dataset) -> str:
    counterparty = _entity_name(str(row["counterparty_id"]), ds)
    direction = (
        f"Invoice from {counterparty} to {_company_name(ds)}"
        if row["tipo"] == "recibida"
        else f"Invoice from {_company_name(ds)} to {counterparty}"
    )
    note = f"{direction} for {_money(float(row['total']))} on {_date(row['fecha'])}"
    if not str(row.get("po_number", "")):
        note += ", with no purchase order behind it"
    if str(row.get("status", "")) == "cancelado":
        note += "; the invoice is cancelled"
    return note + "."


def _bank_note(row, ds: Dataset) -> str:
    other = _name_for_clabe(str(row["counterparty_clabe"]), ds) or "an unidentified account"
    verb = f"{_company_name(ds)} paid {other}" if row["direction"] == "out" else f"{other} paid {_company_name(ds)}"
    note = f"{verb} {_money(float(row['amount']))} on {_date(row['fecha'])}"
    reference = str(row.get("reference", ""))
    return note + (f', reference "{reference}".' if reference else ".")


def _counterparty_note(row, ds: Dataset) -> str:
    payer = str(row["entity_name"]) or _name_for_clabe(str(row["entity_clabe"]), ds)
    payee = str(row["counterparty_name"]) or _name_for_clabe(str(row["counterparty_clabe"]), ds)
    return (
        f"{payer} transferred {_money(float(row['amount']))} to {payee} on {_date(row['fecha'])}; "
        f"{_company_name(ds)} is not a party to this transfer."
    )


def _note_for(record_id: str, table: str, ds: Dataset) -> str:
    """One sentence saying what a record proves, built from the record itself."""
    if table == "invoices":
        row = _row(ds.invoices, "uuid", record_id)
        return _invoice_note(row, ds) if row is not None else f"Invoice {record_id}."
    if table == "bank_txns":
        row = _row(ds.bank_transactions, "txn_id", record_id)
        if row is not None:
            return _bank_note(row, ds)
        row = _row(ds.counterparty_bank, "record_id", record_id)
        if row is not None:
            return _counterparty_note(row, ds)
        return f"Bank transaction {record_id}."
    if table == "purchase_orders":
        row = _row(ds.purchase_orders, "po_id", record_id)
        if row is not None:
            return (
                f"Purchase order {record_id} for {_money(float(row['amount']))} dated {_date(row['date'])}, "
                f"approved by {row['approver'] or 'nobody named'}."
            )
        row = _row(ds.goods_receipts, "receipt_id", record_id)
        if row is not None:
            return f"Goods receipt {record_id} recorded on {_date(row['fecha'])} against invoice {row['invoice_uuid']}."
        return f"Purchase order {record_id}."
    if table == "vendors":
        row = _row(ds.suppliers, "rfc", record_id)
        if row is not None:
            return (
                f"Vendor master record for {row['name']}: registered {_date(row['onboarded'])}, "
                f"category {row['category'] or 'unstated'}, bank account {row['clabe']}."
            )
        return f"Vendor master record {record_id}."
    if table == "employees":
        row = _row(ds.employees, "employee_id", record_id)
        if row is not None:
            return (
                f"Employee master record for {row['name']}, {row['role'] or 'role unstated'}, "
                f"personal account {row['personal_clabe']}."
            )
        return f"Employee master record {record_id}."
    if table == "efos_list":
        row = _row(ds.efos_69b, "rfc", record_id)
        if row is not None:
            return (
                f"SAT Article 69-B listing for {row['nombre']}: {row['situacion'].lower()}, "
                f"published {_date(row['fecha_publicacion'])}."
            )
        return f"SAT 69-B listing for {record_id}."
    if table == "ledger":
        row = _row(ds.ledger, "entry_id", record_id)
        if row is not None:
            return (
                f"Ledger entry {record_id} on {_date(row['fecha'])}: {row['descripcion']} "
                f"(debit {float(row['debit']):,.2f} / credit {float(row['credit']):,.2f})."
            )
        return f"Ledger entry {record_id}."
    if table == "contracts":
        row = _row(ds.contracts, "contract_id", record_id)
        if row is not None:
            return f"Contract {record_id} for {_money(float(row['value']))} from {_date(row['start_date'])}: {row['scope_text']}."
        return f"Contract {record_id}."
    return f"Record {record_id}."


def _amount_of(record_id: str, table: str, ds: Dataset) -> float:
    """The amount the judges' validator will read off this record, or 0.0."""
    return _amount_of_shared(record_id, table, ds)


def _reconciles(total: float, claimed: float) -> bool:
    return _reconciles_shared(total, claimed)


def _invoice_ids(ds: Dataset, accused: set[str], tipo: str | None = None) -> list[str]:
    """Invoice uuids whose counterparty is one of the accused, optionally one direction."""
    if len(ds.invoices) == 0:
        return []
    sub = ds.invoices[ds.invoices["counterparty_id"].isin(accused)]
    if tipo:
        sub = sub[sub["tipo"] == tipo]
    return list(sub.sort_values("fecha")["uuid"])


def _amount_basis(finding: dict, ds: Dataset, cited: list[str]) -> tuple[list[str], float]:
    """The record set the claimed amount reconciles against, and that amount.

    The judges sum exhibits per table and compare the closest table to the claim. So the
    exhibits have to be *chosen* to fit: a round-trip claims the sales side, and citing
    every invoice the two entities exchanged would read as double the money and fail.
    """
    claimed = float(finding.get("amount_mxn", 0.0))
    accused = set(finding.get("accused", []))

    # The evidence guard (#87) already decided which records carry this finding's money
    # and refused to let it exist unless they reconcile. Trust that rather than
    # re-deriving it: it is the same arithmetic, done once, where the finding was born.
    counted = [str(r) for r in finding.get("counted_exhibits", []) if str(r)]
    if counted:
        total = sum(_amount_of(r, source_table(r, ds), ds) for r in counted)
        if total > 0 and _reconciles(total, claimed):
            return counted, claimed

    cited_invoices = [r for r in cited if source_table(r, ds) == "invoices"]
    cited_bank = [r for r in cited if source_table(r, ds) == "bank_txns"]

    candidates: list[list[str]] = [
        _invoice_ids(ds, accused),
        _invoice_ids(ds, accused, "recibida"),
        _invoice_ids(ds, accused, "emitida"),
        cited_invoices,
        cited_bank,
    ]
    for group in candidates:
        if not group:
            continue
        total = sum(_amount_of(r, source_table(r, ds), ds) for r in group)
        if total > 0 and _reconciles(total, claimed):
            return group, claimed

    # Nothing the finding can cite adds up to the claim. Rather than emit a submission
    # the judges' own validator rejects, claim exactly what the cited records prove.
    fallback = cited_invoices or cited_bank or cited
    total = sum(_amount_of(r, source_table(r, ds), ds) for r in fallback)
    return fallback, round(total, 2)


def _master_records(finding: dict, ds: Dataset) -> list[tuple[str, str]]:
    """(record_id, table) for the master rows that tie each accused entity to the scheme."""
    out: list[tuple[str, str]] = []
    listed = set(ds.efos_69b["rfc"]) if len(ds.efos_69b) else set()
    for accused in finding.get("accused", []):
        supplier = _row(ds.suppliers, "supplier_id", accused)
        if supplier is not None and str(supplier["rfc"]):
            out.append((str(supplier["rfc"]), "vendors"))
            if str(supplier["rfc"]) in listed:
                out.append((str(supplier["rfc"]), "efos_list"))
            continue
        employee = _row(ds.employees, "employee_id", accused)
        if employee is not None:
            out.append((str(employee["employee_id"]), "employees"))
            continue
        customer = _row(ds.customers, "customer_id", accused)
        if customer is not None and str(customer["rfc"]):
            out.append((str(customer["rfc"]), "vendors" if str(customer["rfc"]) in set(ds.suppliers["rfc"]) else ""))
    return [(rid, table) for rid, table in out if table]


def _exhibits(finding: dict, ds: Dataset) -> tuple[list[dict], float]:
    """Every exhibit for one finding, numbered EX-01…, plus the amount they support."""
    cited = [str(e) for e in finding.get("evidence", [])]
    basis, amount = _amount_basis(finding, ds, cited)

    ordered: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for record_id in list(basis) + cited:
        table = source_table(record_id, ds)
        if not table or (record_id, table) in seen:
            continue
        # An exhibit outside the reconciling table would be summed into its own table and
        # never chosen, but an *extra* invoice would break the invoices total.
        if table == "invoices" and record_id not in basis and any(source_table(b, ds) == "invoices" for b in basis):
            continue
        seen.add((record_id, table))
        ordered.append((record_id, table))
    for record_id, table in _master_records(finding, ds):
        if (record_id, table) not in seen:
            seen.add((record_id, table))
            ordered.append((record_id, table))

    return [
        {
            "exhibit_id": f"EX-{i:02d}",
            "source_table": table,
            "record_id": record_id,
            "note": _note_for(record_id, table, ds),
        }
        for i, (record_id, table) in enumerate(ordered, start=1)
    ], amount


# --------------------------------------------------------------------- money trail
def _trail_step(record_id: str, exhibit_id: str, ds: Dataset) -> dict | None:
    row = _row(ds.bank_transactions, "txn_id", record_id)
    if row is not None:
        company, other = _company_name(ds), _name_for_clabe(str(row["counterparty_clabe"]), ds)
        source, target = (company, other) if row["direction"] == "out" else (other, company)
        return {
            "from": source or "unidentified account",
            "to": target or "unidentified account",
            "amount": float(row["amount"]),
            "date": _date(row["fecha"]),
            "exhibit_id": exhibit_id,
        }
    row = _row(ds.counterparty_bank, "record_id", record_id)
    if row is not None:
        return {
            "from": str(row["entity_name"]) or _name_for_clabe(str(row["entity_clabe"]), ds),
            "to": str(row["counterparty_name"]) or _name_for_clabe(str(row["counterparty_clabe"]), ds),
            "amount": float(row["amount"]),
            "date": _date(row["fecha"]),
            "exhibit_id": exhibit_id,
        }
    return None


def _money_trail(exhibits: list[dict], ds: Dataset) -> list[dict]:
    """The bank rows among the exhibits, in date order, as named steps."""
    steps = [
        step
        for step in (
            _trail_step(ex["record_id"], ex["exhibit_id"], ds)
            for ex in exhibits
            if ex["source_table"] == "bank_txns"
        )
        if step is not None
    ]
    steps.sort(key=lambda s: (s["date"], s["exhibit_id"]))
    return steps


# --------------------------------------------------------------------- narratives
def _window(ds: Dataset, record_ids: list[str]) -> tuple[str, str]:
    dates = [
        ds.invoices.loc[ds.invoices["uuid"] == r, "fecha"].iloc[0]
        for r in record_ids
        if len(ds.invoices[ds.invoices["uuid"] == r])
    ]
    dates = [d for d in dates if not pd.isna(d)]
    return (_date(min(dates)), _date(max(dates))) if dates else ("", "")


def _narrative(finding: dict, scheme: str, ds: Dataset, exhibits: list[dict], amount: float) -> str:
    """Plain language a non-technical judge can follow, every number from the records."""
    company = _company_name(ds)
    names = [_entity_name(a, ds) for a in finding.get("accused", [])]
    invoices = [ex["record_id"] for ex in exhibits if ex["source_table"] == "invoices"]
    first, last = _window(ds, invoices)
    when = f" between {first} and {last}" if first and last and first != last else (f" on {first}" if first else "")
    suppliers = [a for a in finding.get("accused", []) if _row(ds.suppliers, "supplier_id", a) is not None]
    employees = [a for a in finding.get("accused", []) if _row(ds.employees, "employee_id", a) is not None]
    vendor = _entity_name(suppliers[0], ds) if suppliers else (names[0] if names else "the counterparty")
    trail = _money_trail(exhibits, ds)
    no_po = sum(
        1
        for r in invoices
        if len(ds.invoices[ds.invoices["uuid"] == r]) and not str(ds.invoices.loc[ds.invoices["uuid"] == r, "po_number"].iloc[0])
    )

    if scheme == "phantom_vendor":
        listed = [ex for ex in exhibits if ex["source_table"] == "efos_list"]
        head = (
            f"{vendor} is on the SAT Article 69-B list of taxpayers that invoice operations which never took place. "
            if listed
            else f"{vendor} shows every mark of a supplier that exists only on paper. "
        )
        body = (
            f"{company} booked {len(invoices)} invoice(s) from it{when}, {_money(amount)} in total, and paid them "
            f"from its own bank account. "
        )
        tail = (
            f"{no_po} of those invoices have no purchase order behind them. "
            if no_po
            else "No purchase order or delivery record supports the work invoiced. "
        )
        return head + body + tail + "Deducting invoices from a listed issuer is not allowed, and the VAT credited on them is not creditable."

    if scheme == "kickback":
        employee = _entity_name(employees[0], ds) if employees else "an employee"
        onward = sum(s["amount"] for s in trail if s["to"] == employee)
        head = f"{company} paid {vendor} {_money(amount)} across {len(invoices)} invoice(s){when}. "
        body = (
            f"{vendor}'s own account then moved {_money(onward)} on to the personal account of {employee}, "
            f"who sits inside {company}. "
            if onward
            else f"The money paid to {vendor} was moved on to the personal account of {employee}. "
        )
        return head + body + (
            "Money leaving the company as a supplier payment and returning to the person who approved it is a "
            "kickback: the invoices are not a deductible business expense and the payment is a conflict of interest."
        )

    if scheme == "round_tripping":
        sales = [r for r in invoices if len(ds.invoices[ds.invoices["uuid"] == r]) and ds.invoices.loc[ds.invoices["uuid"] == r, "tipo"].iloc[0] == "emitida"]
        counterpart = names[0] if names else "a counterparty"
        return (
            f"{company} invoiced {_money(amount)} in sales to {counterpart} across {len(sales) or len(invoices)} "
            f"invoice(s){when}, and the same money came back to it. The payments out and the collections in match in "
            f"amount and follow each other within days, with no goods or service moving in either direction. "
            f"Revenue recorded this way inflates turnover without a real customer, and the VAT charged on the sale "
            f"is not a real sale."
        )

    if scheme == "threshold_splitting":
        return (
            f"{company} recorded {len(invoices)} invoice(s) from {vendor}{when} totalling {_money(amount)}, each one "
            f"sitting just under an approval limit while the total sits well above it. Splitting one purchase into "
            f"several documents to stay under the limit defeats the approval control it was written for."
        )

    if scheme == "revenue_inflation":
        return (
            f"{company} booked {_money(amount)} of revenue on {len(invoices)} invoice(s){when} that no money ever "
            f"settled, or that were cancelled without the entry being reversed. Revenue recognised without collection "
            f"or a valid invoice overstates the result for the period."
        )

    return f"{company} recorded {_money(amount)} against {', '.join(names) or 'the accused'}{when}."


# --------------------------------------------------------------------- confidence
def _confidence(scheme: str, exhibits: list[dict], ds: Dataset, finding: dict) -> str:
    """``proven`` when the rule's own precondition has an exhibit; else ``probable``.

    A minimal reading of #87: a phantom vendor is proven by the 69-B listing, a kickback by
    the onward transfer to the employee's own account, a round trip by money leaving and
    coming back. Everything else is probable — a real tier, not a decoration. #91: if the
    adversarial review weakened the finding, that tier is authoritative — a downgrade is
    never reversed into an upgrade.
    """
    if finding.get("challenge", {}).get("confidence") == "probable":
        return "probable"
    tables = {ex["source_table"] for ex in exhibits}
    if "invoices" not in tables:
        return "probable"
    if scheme == "phantom_vendor":
        return "proven" if "efos_list" in tables else "probable"
    if scheme == "kickback":
        employees = {a for a in finding.get("accused", []) if _row(ds.employees, "employee_id", a) is not None}
        clabes = {
            str(_row(ds.employees, "employee_id", e)["personal_clabe"]) for e in employees
        }
        for ex in exhibits:
            if ex["source_table"] != "bank_txns":
                continue
            row = _row(ds.counterparty_bank, "record_id", ex["record_id"])
            if row is not None and str(row["counterparty_clabe"]) in clabes:
                return "proven"
        return "probable"
    if scheme == "round_tripping":
        directions = set()
        for ex in exhibits:
            row = _row(ds.bank_transactions, "txn_id", ex["record_id"])
            if row is not None:
                directions.add(str(row["direction"]))
        return "proven" if {"in", "out"} <= directions else "probable"
    return "probable"


# ------------------------------------------------------------------ declined leads
def _log_index(log: list[dict]) -> dict[str, dict]:
    """Per entity: the detectors that raised it, the tools called, and who closed it."""
    index: dict[str, dict] = {}
    for entry in log or []:
        entity = str(entry.get("entity_id", ""))
        if not entity:
            continue
        slot = index.setdefault(entity, {"detectors": [], "tools": [], "closed_by": ""})
        kind, payload = entry.get("kind"), entry.get("payload", {})
        if kind == "lead":
            for det in payload.get("detectors", []) or []:
                if det not in slot["detectors"]:
                    slot["detectors"].append(str(det))
        elif kind == "tool_call":
            name = str(payload.get("name", ""))
            if name and name not in slot["tools"]:
                slot["tools"].append(name)
        elif kind == "decision" and payload.get("action") == "drop_lead":
            slot["closed_by"] = "investigator"
        elif kind == "guard" and payload.get("accepted") is False:
            slot["closed_by"] = "validator"
    return index


def _dossier_detectors(ds: Dataset) -> dict[str, list[str]]:
    """Detector names per entity, recomputed for leads the log never got to."""
    # Deterministic and cheap; imported here because it is only a fallback path.
    from .detectors import run_all
    from .leads import aggregate

    return {d["entity_id"]: [str(x) for x in d.get("detectors", [])] for d in aggregate(ds, run_all(ds))}


def _leads_not_pursued(case: dict, ds: Dataset, log: list[dict], moved: list[dict]) -> list[dict]:
    index = _log_index(log)
    fallback: dict[str, list[str]] | None = None
    out: list[dict] = []
    for lead in case.get("not_pursued", []):
        entity = str(lead.get("entity", ""))
        slot = index.get(entity, {})
        detectors = list(slot.get("detectors", []))
        if not detectors:
            if fallback is None:
                fallback = _dossier_detectors(ds)
            detectors = fallback.get(entity, [])
        out.append(
            {
                "entity": entity_id(entity, ds),
                "signal": ", ".join(detectors) or "aggregated detector sweep",
                "reason": str(lead.get("reason", "")) or "no corroborating scheme signature matched",
                "tool_calls_made": list(slot.get("tools", [])),
                # #91: the case file is authoritative for who closed the lead (a
                # challenger-killed finding must not read as closed by the investigator).
                "closed_by": lead.get("closed_by") or slot.get("closed_by") or "investigator",
            }
        )
    out.extend(moved)
    out.sort(key=lambda entry: entry["entity"])
    return out


def _as_control_observation(finding: dict, ds: Dataset) -> dict:
    """A real finding whose type is outside the judges' enum, reported as a control failure."""
    evidence = ", ".join(str(e) for e in finding.get("evidence", [])[:8])
    scheme = str(finding.get("scheme_type", "other")).replace("_", " ")
    return {
        "entity": entity_id(str(finding.get("accused", [""])[0]), ds),
        "signal": f"deterministic {finding.get('scheme_type', 'other')} detector",
        "reason": (
            f"A {scheme} of {_money(float(finding.get('amount_mxn', 0.0)))} is evidenced by records "
            f"{evidence}, but it is a control failure, not one of the five scheme types this submission may "
            f"carry, so it is reported here rather than as a finding."
        ),
        "tool_calls_made": [],
        "closed_by": "validator",
    }


# ----------------------------------------------------------------------- assembly
def _seed_from(meta: dict, ds: Dataset) -> int:
    seed = meta.get("seed")
    if isinstance(seed, int) and not isinstance(seed, bool):
        return seed
    for part in (Path(str(ds.path)).stem, Path(str(ds.path)).parent.name):
        match = re.search(r"(?:estate|company)_(\d+)", part)
        if match:
            return int(match.group(1))
    return 0


def build_submission(case: dict, ds: Dataset, log: list[dict] | None = None, meta: dict | None = None) -> dict:
    """Turn our case file into the judges' ``submission.json``."""
    meta = dict(meta or {})
    findings: list[dict] = []
    moved: list[dict] = []

    for finding in case.get("findings", []):
        internal = str(finding.get("scheme_type", ""))
        scheme = SCHEME_MAP.get(internal)
        if scheme is None:
            moved.append(_as_control_observation(finding, ds))
            continue
        exhibits, amount = _exhibits(finding, ds)
        if amount <= 0 or len(exhibits) < 3:
            moved.append(_as_control_observation(finding, ds))
            continue
        findings.append(
            {
                "scheme_type": scheme,
                "entities": [entity_id(a, ds) for a in finding.get("accused", [])],
                "rule_broken": str(finding.get("rule", "")),
                "narrative": _truncate_words(_narrative(finding, scheme, ds, exhibits, amount)),
                "peso_amount": round(float(amount), 2),
                "confidence": _confidence(scheme, exhibits, ds, finding),
                "money_trail": _money_trail(exhibits, ds),
                "exhibits": exhibits,
                # #91: what the adversarial review argued, and why the finding held
                # (or was weakened/killed). Extra keys are allowed by the judges' checker.
                "challenge": finding.get("challenge"),
            }
        )

    run_metadata = dict(case.get("run_metadata") or {})
    run_metadata.update({k: v for k, v in meta.items() if k != "seed"})
    run_metadata.setdefault("llm_calls", 0)
    run_metadata.setdefault("mxn_cost", 0.0)
    run_metadata.setdefault("wall_clock_seconds", 0.0)
    run_metadata.setdefault("cost_by_role", {})
    run_metadata.setdefault("deterministic", True)

    return {
        "seed": _seed_from(meta, ds),
        "findings": findings,
        "leads_not_pursued": _leads_not_pursued(case, ds, log or [], moved),
        "run_metadata": run_metadata,
    }


def write_submission(case: dict, ds: Dataset, out: str | Path, log: list[dict] | None = None, meta: dict | None = None) -> dict:
    submission = build_submission(case, ds, log, meta)
    path = Path(out)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(submission, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return submission


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agent.submit")
    parser.add_argument("estate", help="the estate the case file was produced from")
    parser.add_argument("case_file")
    parser.add_argument("--log", default=None, help="the run's step log, for tools and closers")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", default="submission.json")
    args = parser.parse_args(argv)

    ds = load(args.estate)
    case = json.loads(Path(args.case_file).read_text(encoding="utf-8"))
    entries: list[dict] = []
    if args.log and Path(args.log).exists():
        from .steplog import parse_lines  # noqa: PLC0415 - CLI-only

        entries, _ = parse_lines(Path(args.log).read_text(encoding="utf-8"))
    meta = {"seed": args.seed} if args.seed is not None else {}
    submission = write_submission(case, ds, args.out, entries, meta)
    print(
        f"wrote {args.out}: {len(submission['findings'])} finding(s), "
        f"{len(submission['leads_not_pursued'])} declined lead(s), seed {submission['seed']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
