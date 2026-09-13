"""detect_new_vendor_round_amounts: recently onboarded suppliers with suspiciously round invoices.

Classic EFOS smell. A supplier that was just onboarded and whose invoices are all
clean multiples of 1,000 MXN subtotal is the paper-trail signature of a shell
invoicing nothing real. The 16% IVA is the tell: a round *subtotal* of 85,000 is a
98,600 *total*, so the roundness is only visible on ``subtotal``. On ``total`` the
kickback shell's share drops to 0.0 and this detector misses it; on ``subtotal``
it is 1.0.

By design this also flags the **new-vendor decoy** (S00009, a real supplier
onboarded 2025-06-02 whose invoices are all round): it is an *expected lead*, not
an accusation. Every one of its invoices has a warehouse-signed goods receipt, so
the investigation loop (#13) clears it. A lead is never a finding by itself.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic (sorted by ``entity_id``).
"""
from __future__ import annotations

import pandas as pd


def detect_new_vendor_round_amounts(ds, *, since="2024-07-01", min_share=0.6) -> list[dict]:
    """List suppliers onboarded on/after ``since`` whose ``recibida`` invoices are round thousands.

    For every supplier with ``onboarded >= since`` and at least one ``recibida``
    invoice:
      1. ``round_share`` = share of its ``recibida`` invoices whose ``subtotal``
         is a multiple of 1,000 (``subtotal % 1000 == 0`` within a tolerance of
         0.005 after rounding to 2 decimals).
      2. Keep suppliers with ``round_share >= min_share``.

    One dict per supplier, sorted by ``entity_id``:

        entity_id · name · category · onboarded (ISO) · first_invoice (ISO) ·
        n_invoices · n_round · round_share · total_mxn · evidence (invoice UUIDs)

    ``total_mxn`` is the sum of that supplier's ``recibida`` ``subtotal`` (the
    base amount whose roundness is being measured, net of IVA).

    The ``since`` cutoff is a six-month look-back before the fiscal year starts
    (2024-07-01 here), so long-standing honest suppliers — even one with a single
    round 380,000 invoice, like the law-firm decoy — are never candidates.
    """
    since_ts = pd.Timestamp(since)

    suppliers = ds.suppliers
    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"].copy()
    recibida["subtotal"] = recibida["subtotal"].astype("float64")

    candidates = suppliers[suppliers["onboarded"] >= since_ts]

    rows: list[dict] = []
    for s in candidates.itertuples(index=False):
        sid = str(s.supplier_id)
        sub = recibida[recibida["counterparty_id"] == sid]
        if sub.empty:
            continue

        subt = sub["subtotal"].round(2)
        is_round = (subt % 1000).abs() <= 0.005
        n_inv = int(len(sub))
        n_round = int(is_round.sum())
        share = n_round / n_inv if n_inv else 0.0
        if share < min_share:
            continue

        uuids = sub["uuid"].astype(str).tolist()
        first_inv = sub["fecha"].min()

        rows.append(
            {
                "entity_id": sid,
                "name": str(s.name),
                "category": str(s.category),
                "onboarded": s.onboarded.date().isoformat(),
                "first_invoice": first_inv.date().isoformat(),
                "n_invoices": n_inv,
                "n_round": n_round,
                "round_share": float(share),
                "total_mxn": float(subt.sum()),
                "evidence": sorted(uuids),
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
