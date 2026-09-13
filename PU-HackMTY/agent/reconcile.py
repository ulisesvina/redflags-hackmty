"""Peso reconciliation, the way the judges do it (#87).

``student-materials/forensic-auditor/README.md``:

    An accusation must validate before it is printed. Every cited ``record_id`` must
    exist in the estate, and ``peso_amount`` must reconcile to the sum of cited exhibit
    amounts within 2%. Amounts reconcile **per table**: an invoice and the bank transfer
    that settled it are the same pesos seen twice, so citing a complete money trail is
    not penalised.

Their ``validate_format.py`` implements that by summing every cited exhibit's amount
column per source table, taking the table whose sum is closest to the claim, and
requiring the two to agree within 2%. This module is the single implementation of that
arithmetic on our side, so the evidence guard (which decides whether a finding may
exist) and the submission writer (which prints it) can never disagree about whether a
number reconciles.

Pure, deterministic, no I/O, no LLM, never reads ``hidden/``.
"""
from __future__ import annotations

import pandas as pd

from .data import Dataset

# The judges' tolerance. A judge will ask to see this constant, so it lives in code
# with its source named, never in a prompt.
PESO_TOLERANCE = 0.02

# Judges' table -> the column their validator sums. Tables absent here carry no amount
# and therefore can never be the table a claim reconciles against.
AMOUNT_COLUMN = {
    "invoices": "total",
    "bank_txns": "amount",
    "purchase_orders": "amount",
    "contracts": "value",
}

# Legacy record-id prefixes -> the judges' table that record would live in.
_LEGACY_PREFIX_TABLE = {"TX": "bank_txns", "CP": "bank_txns", "GR": "purchase_orders", "GL": "ledger"}


def source_table(record_id: str, ds: Dataset) -> str:
    """The judges' table a record id belongs to, or ``""`` when it resolves to none.

    On a judges' estate ``ds.record_table`` (#79) already knows. On our legacy CSV
    layout the id's shape decides: an invoice uuid is in ``invoices``, ``TX``/``CP`` are
    both bank rows, ``GR`` stands in for a purchase order, ``GL`` is a ledger entry.
    """
    if ds.record_table:
        table = ds.record_table.get(record_id)
        if table:
            return table
    if len(ds.invoices) and record_id in set(ds.invoices["uuid"]):
        return "invoices"
    return _LEGACY_PREFIX_TABLE.get(record_id[:2], "")


def _row(frame: pd.DataFrame, column: str, value: str):
    if len(frame) == 0 or column not in frame.columns:
        return None
    hit = frame[frame[column] == value]
    return hit.iloc[0] if len(hit) else None


def amount_of(record_id: str, table: str, ds: Dataset) -> float:
    """The amount the judges' validator reads off this record, or ``0.0``."""
    if table == "invoices":
        row = _row(ds.invoices, "uuid", record_id)
        return float(row["total"]) if row is not None else 0.0
    if table == "bank_txns":
        row = _row(ds.bank_transactions, "txn_id", record_id)
        if row is None:
            row = _row(ds.counterparty_bank, "record_id", record_id)
        return float(row["amount"]) if row is not None else 0.0
    if table == "purchase_orders":
        row = _row(ds.purchase_orders, "po_id", record_id)
        if row is None:
            # Legacy estates have no purchase_orders; a GR receipt stands in for one and
            # carries no amount of its own, so it never anchors a reconciliation.
            return 0.0
        return float(row["amount"]) if row is not None else 0.0
    if table == "contracts":
        row = _row(ds.contracts, "contract_id", record_id)
        return float(row["value"]) if row is not None else 0.0
    return 0.0


def per_table_sums(record_ids, ds: Dataset) -> dict[str, float]:
    """``{judges' table: summed amount}`` over the given records, ignoring duplicates.

    Only tables that carry an amount appear. A record cited twice is counted once, the
    way a set of exhibit ids would be.
    """
    sums: dict[str, float] = {}
    for record_id in dict.fromkeys(str(r) for r in record_ids):
        table = source_table(record_id, ds)
        if table not in AMOUNT_COLUMN:
            continue
        value = amount_of(record_id, table, ds)
        if value:
            sums[table] = sums.get(table, 0.0) + value
    return {table: round(total, 2) for table, total in sums.items()}


def reconciles(total: float, claimed: float) -> bool:
    """Do a table's summed exhibits and a claimed amount agree within 2%?"""
    return abs(float(claimed) - float(total)) <= PESO_TOLERANCE * max(float(total), 1.0)


def best_table(sums: dict[str, float], claimed: float) -> tuple[str, float]:
    """The table whose sum is closest to the claim, as the judges' validator picks it."""
    if not sums:
        return "", 0.0
    table = min(sums, key=lambda t: abs(float(claimed) - sums[t]))
    return table, sums[table]
