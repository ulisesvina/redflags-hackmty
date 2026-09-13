"""detect_duplicate_payments: the same purchase invoice paid more than once.

The supplier here is **honest** (a genuine goods vendor); the lead points at the
payment itself — a duplicate outbound transfer of the same invoice — which is a
control failure or embezzlement, not supplier fraud. The report is therefore
one dict per duplicated invoice, never an accusation against the supplier.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic: rows sorted by ``invoice_uuid``, transactions within a
row sorted by ``fecha`` then ``txn_id``.
"""
from __future__ import annotations


def detect_duplicate_payments(ds, **params) -> list[dict]:
    """List purchase invoices paid more than once.

    Group outgoing bank transactions by ``invoice_uuid`` (dropping the payroll
    rows whose ``invoice_uuid`` is ``""``), keep invoices with two or more
    payments, join the invoice to recover the supplier (``counterparty_id``) and
    the invoice total, and emit one lead per duplicated invoice.
    """
    out = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out") & (ds.bank_transactions["invoice_uuid"] != "")
    ]

    grouped: dict[str, list] = {}
    for t in out.itertuples(index=False):
        grouped.setdefault(t.invoice_uuid, []).append(t)

    inv = ds.invoices.set_index("uuid")
    rows: list[dict] = []

    for uuid in sorted(grouped):
        txns = grouped[uuid]
        if len(txns) < 2:
            continue
        if uuid not in inv.index:
            continue
        txns.sort(key=lambda t: (t.fecha, t.txn_id))
        inv_row = inv.loc[uuid]

        amounts = [float(t.amount) for t in txns]
        txn_ids = [str(t.txn_id) for t in txns]
        total = float(inv_row["total"])
        rows.append(
            {
                "entity_id": str(inv_row["counterparty_id"]),
                "invoice_uuid": str(uuid),
                "n_payments": len(txns),
                "txn_ids": txn_ids,
                "fechas": [t.fecha.date().isoformat() for t in txns],
                "clabes": [str(t.counterparty_clabe) for t in txns],
                "amounts": amounts,
                "invoice_total_mxn": total,
                "overpaid_mxn": sum(amounts) - total,
                "evidence": [str(uuid)] + txn_ids,
            }
        )

    rows.sort(key=lambda x: x["invoice_uuid"])
    return rows
