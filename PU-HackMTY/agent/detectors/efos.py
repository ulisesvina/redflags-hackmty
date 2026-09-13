"""detect_efos: suppliers whose RFC is on SAT's Article 69-B blacklist.

The cheapest, strongest lead in the whole case. SAT publishes, under CFF Art.
69-B, the RFCs of taxpayers it believes issue invoices for operations that never
happened (EFOS). A supplier we paid whose RFC is on that list is a documented
paper trail to a company the tax authority says sells invoices.

Two rules keep this honest:

- **Match on RFC, never on name.** Every dataset plants a decoy supplier whose
  *name* is identical to a listed company but whose RFC is different — a real
  business that happens to share a name with a blacklisted one. Matching on name
  would accuse it. The RFC is the identifier; the name is not.
- **``situacion`` decides whether it is still a lead.** ``Presunto`` (presumed)
  and ``Definitivo`` (confirmed) are live. ``Desvirtuado`` (the taxpayer rebutted
  the presumption) and ``Sentencia favorable`` (a court ruled in its favour) mean
  SAT itself cleared them — not a lead, and accusing one is a false positive.

``fecha_publicacion`` is deliberately *not* a filter. A 69-B listing routinely
lands months after the invoices it condemns — in company_42 the ``Definitivo``
supplier was published 2025-11-15 while every one of its invoices is Feb–Aug
2025 — and that lag is exactly how the scheme works. The publication date is
reported as context, never used to drop a row.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic: one dict per matched supplier, sorted by ``entity_id``.
"""
from __future__ import annotations

ACTIVE_SITUACIONES = ("Presunto", "Definitivo")


def detect_efos(ds, **params) -> list[dict]:
    """Return one lead per supplier whose RFC appears on the 69-B list as live.

    Steps:
    1. Inner-join ``ds.suppliers`` to ``ds.efos_69b`` on ``rfc`` (exact,
       case-sensitive string equality — never on ``name``).
    2. Keep rows whose ``situacion`` is ``Presunto`` or ``Definitivo``;
       ``Desvirtuado`` and ``Sentencia favorable`` were cleared by SAT.
    3. No filter on ``fecha_publicacion``: a listing published after the
       invoices still condemns them.

    One dict per matched supplier, sorted by ``entity_id``:

        entity_id · rfc · name · situacion · fecha_publicacion (ISO) ·
        n_invoices · total_mxn · evidence

    ``n_invoices`` / ``total_mxn`` count and sum ``total`` over that supplier's
    ``recibida`` invoices. ``evidence`` is those invoice UUIDs plus the
    ``txn_id`` of every outgoing bank transaction that references one of them.
    """
    matches = ds.suppliers.merge(ds.efos_69b, on="rfc", how="inner")
    matches = matches[matches["situacion"].isin(ACTIVE_SITUACIONES)]

    # Outgoing bank transactions keyed by invoice_uuid, so each matched
    # supplier's invoices carry the money that actually left the account.
    out_txns_by_invoice: dict[str, list[str]] = {}
    if len(ds.bank_transactions):
        out = ds.bank_transactions[
            (ds.bank_transactions["direction"] == "out")
            & (ds.bank_transactions["invoice_uuid"] != "")
        ]
        for t in out.itertuples(index=False):
            out_txns_by_invoice.setdefault(str(t.invoice_uuid), []).append(str(t.txn_id))

    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"]

    rows: list[dict] = []
    for m in matches.itertuples(index=False):
        supplier_id = str(m.supplier_id)
        sub = recibida[recibida["counterparty_id"] == supplier_id]
        invoice_uuids = sorted(str(u) for u in sub["uuid"])

        txn_ids = sorted(
            {tid for uuid in invoice_uuids for tid in out_txns_by_invoice.get(uuid, [])}
        )

        rows.append(
            {
                "entity_id": supplier_id,
                # `name` collides with efos_69b's `nombre` only by meaning, not
                # by column name, so the merge leaves both intact.
                "rfc": str(m.rfc),
                "name": str(m.name),
                "situacion": str(m.situacion),
                "fecha_publicacion": m.fecha_publicacion.date().isoformat(),
                "n_invoices": int(len(sub)),
                "total_mxn": float(sub["total"].sum()) if len(sub) else 0.0,
                "evidence": invoice_uuids + txn_ids,
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
