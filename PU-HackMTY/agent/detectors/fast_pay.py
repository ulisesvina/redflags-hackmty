"""detect_fast_pay_no_deliverable: service invoices with no deliverable paid unusually fast.

Pattern: honest suppliers are paid on 15-45 day terms, while the planted schemes
are paid within a week. A "service" invoice (servicios / logistica / renta_util)
never carries a goods receipt by construction, so the missing deliverable is not
itself a materiality problem (goods without receipts are #5's business). The carve
here is *speed*: a service invoice with no deliverable that was paid within
``max_days`` of its date.

This is a **lead list, not an accusation list**. It flags the kickback shell, both
EFOS suppliers, the round-trip supplier, and — by design — the law-firm decoy
(a large one-off service invoice paid in 4 days and approved by the director). The
law firm is an *expected lead*: the investigation loop (#13) clears it because its
invoice cites a court case number and was approved by the director, not by
purchasing. A lead is never a finding by itself; the loop decides what to pursue.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic (sorted by entity_id, fecha_invoice, invoice_uuid).
"""
from __future__ import annotations

SERVICE_CATEGORIES = frozenset({"servicios", "logistica", "renta_util"})


def detect_fast_pay_no_deliverable(ds, *, max_days=10) -> list[dict]:
    """List recibida service invoices with no goods receipt paid within ``max_days``.

    One dict per (invoice, payment): entity_id (supplier), invoice_uuid, txn_id,
    category, fecha_invoice (ISO), fecha_paid (ISO), days_to_pay, total_mxn,
    descripcion, approved_by, evidence=[invoice_uuid, txn_id].
    """
    btx = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out")
        & (ds.bank_transactions["invoice_uuid"] != "")
    ][["txn_id", "fecha", "invoice_uuid"]].rename(columns={"fecha": "fecha_paid"})

    inv = ds.invoices[ds.invoices["tipo"] == "recibida"][
        ["uuid", "fecha", "counterparty_id", "total", "descripcion", "approved_by"]
    ].rename(
        columns={
            "uuid": "invoice_uuid",
            "fecha": "fecha_invoice",
            "total": "total_mxn",
        }
    )

    merged = btx.merge(inv, on="invoice_uuid", how="left")
    merged = merged[merged["counterparty_id"].notna()]
    merged = merged.merge(
        ds.suppliers[["supplier_id", "category"]],
        left_on="counterparty_id",
        right_on="supplier_id",
        how="left",
    )

    receipted = set(ds.goods_receipts["invoice_uuid"])
    merged = merged[~merged["invoice_uuid"].isin(receipted)]
    merged = merged[merged["category"].isin(SERVICE_CATEGORIES)]
    merged["days_to_pay"] = (merged["fecha_paid"] - merged["fecha_invoice"]).dt.days
    merged = merged[merged["days_to_pay"] <= max_days]

    rows: list[dict] = []
    for r in merged.itertuples(index=False):
        rows.append(
            {
                "entity_id": str(r.counterparty_id),
                "invoice_uuid": str(r.invoice_uuid),
                "txn_id": str(r.txn_id),
                "category": str(r.category),
                "fecha_invoice": r.fecha_invoice.date().isoformat(),
                "fecha_paid": r.fecha_paid.date().isoformat(),
                "days_to_pay": int(r.days_to_pay),
                "total_mxn": float(r.total_mxn),
                "descripcion": str(r.descripcion),
                "approved_by": str(r.approved_by),
                "evidence": [str(r.invoice_uuid), str(r.txn_id)],
            }
        )
    rows.sort(key=lambda x: (x["entity_id"], x["fecha_invoice"], x["invoice_uuid"]))
    return rows
