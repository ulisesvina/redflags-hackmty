"""detect_clabe_not_on_master: money sent to a bank account that is not on record.

Payment diversion: an outgoing transfer that references a real supplier invoice but
lands in a CLABE that is different from the supplier's *master* CLABE (the account
of record in ``suppliers.clabe``). This is not an accusation against the supplier —
the supplier (here) is honest — it is a tell that the payment went somewhere else,
into an account the books never declared.

The report is one dict per offending transfer, sorted by ``txn_id``.

The original (correct) payment to the master CLABE is deliberately excluded: those
transactions carry the master CLABE, so ``counterparty_clabe == master_clabe`` and
they are dropped by the comparison. Payroll rows (``invoice_uuid == ""``) are excluded
up front. CLABEs are compared as strings: they are exactly 18 digits (the loader
guarantees this and preserves leading zeros).

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic: sorted by ``txn_id``.
"""
from __future__ import annotations


def detect_clabe_not_on_master(ds, **params) -> list[dict]:
    """List outgoing invoice payments whose CLABE differs from the supplier master.

    Steps:
    1. ``ds.bank_transactions`` rows with ``direction == "out"`` and
       ``invoice_uuid != ""`` (payroll rows have an empty ``invoice_uuid`` and are
       excluded by construction).
    2. Join ``ds.invoices`` on ``uuid`` -> ``counterparty_id`` (the supplier), then
       ``ds.suppliers`` on ``supplier_id`` -> the master ``clabe``.
    3. Keep rows where ``counterparty_clabe != master_clabe`` (string comparison).
    4. One dict per transaction, sorted by ``txn_id``.
    """
    out = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out") & (ds.bank_transactions["invoice_uuid"] != "")
    ]

    # supplier id per invoice, then master clabe per supplier (safe: every
    # invoice references a known counterparty and every supplier has a CLABE).
    inv_cp = ds.invoices.set_index("uuid")["counterparty_id"]
    sup_clabe = ds.suppliers.set_index("supplier_id")["clabe"]

    rows: list[dict] = []
    for t in out.itertuples(index=False):
        supplier_id = inv_cp.get(t.invoice_uuid)
        if supplier_id is None:
            continue
        master_clabe = sup_clabe.get(supplier_id)
        if master_clabe is None:
            continue

        paid_clabe = str(t.counterparty_clabe)
        if paid_clabe == str(master_clabe):
            continue

        rows.append(
            {
                "entity_id": str(supplier_id),
                "txn_id": str(t.txn_id),
                "invoice_uuid": str(t.invoice_uuid),
                "fecha": t.fecha.date().isoformat(),
                "amount_mxn": float(t.amount),
                "paid_clabe": paid_clabe,
                "master_clabe": str(master_clabe),
                "counterparty_name": str(t.counterparty_name),
                "evidence": [str(t.txn_id), str(t.invoice_uuid)],
            }
        )

    rows.sort(key=lambda x: x["txn_id"])
    return rows
