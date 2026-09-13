"""detect_no_receipt: purchase invoices with no proof of delivery.

This is a **lead list, not an accusation list**. Most rows are honest service
suppliers (servicios, logistica, renta_util) that never carry goods receipts
by construction; ``receipt_required`` marks the goods categories
(materia_prima, refacciones, consumibles) where a missing receipt would be a
materiality problem. The investigation loop (#13) consumes these leads and
decides what to pursue.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic (sorted by entity_id, fecha, invoice_uuid).
"""
from __future__ import annotations

GOODS_CATEGORIES = frozenset({"materia_prima", "refacciones", "consumibles"})


def detect_no_receipt(ds, **params) -> list[dict]:
    """List every purchase (recibida) invoice without a goods receipt.

    One dict per invoice: entity_id (supplier), invoice_uuid, fecha (ISO),
    category, receipt_required (bool), total_mxn, descripcion, approved_by,
    po_number, evidence=[invoice_uuid].
    """
    rec = ds.invoices[ds.invoices["tipo"] == "recibida"][
        ["uuid", "fecha", "counterparty_id", "total", "descripcion", "approved_by", "po_number"]
    ].rename(columns={"uuid": "invoice_uuid", "total": "total_mxn"})

    receipted = set(ds.goods_receipts["invoice_uuid"])
    rec = rec[~rec["invoice_uuid"].isin(receipted)]

    rec = rec.merge(
        ds.suppliers[["supplier_id", "category"]],
        left_on="counterparty_id",
        right_on="supplier_id",
        how="left",
    )

    rows: list[dict] = []
    for r in rec.itertuples(index=False):
        category = str(r.category)
        rows.append(
            {
                "entity_id": str(r.counterparty_id),
                "invoice_uuid": str(r.invoice_uuid),
                "fecha": r.fecha.date().isoformat(),
                "category": category,
                "receipt_required": category in GOODS_CATEGORIES,
                "total_mxn": float(r.total_mxn),
                "descripcion": str(r.descripcion),
                "approved_by": str(r.approved_by),
                "po_number": str(r.po_number),
                "evidence": [str(r.invoice_uuid)],
            }
        )
    rows.sort(key=lambda x: (x["entity_id"], x["fecha"], x["invoice_uuid"]))
    return rows
