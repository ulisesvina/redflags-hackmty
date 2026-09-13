"""detect_threshold_splitting: purchase invoices clustered just under an approval limit.

The judges' ``threshold_splitting`` type: a vendor's purchases split into several
invoices (and POs), each just below an approver's limit, so no single approver ever
sees the total. The goods are real — the fraud is against the company's own approval
control, not the vendor. A single small invoice is not a violation; the *cluster* is:
several invoices from one supplier in the same two-day window, every one just under
the limit, that in aggregate blow straight past it.

Every returned dict is a *lead*, not an accusation. It names the supplier, the
approver whose gate was dodged, the limit, and the invoice / payment / receipt records
that form the cluster. A cluster alone does not prove intent — it just says "here is a
gate someone should have had to approve separately."

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic, sorted by ``(entity_id, first_date)``.

The approval limits live in ``agent.rules.APPROVAL_LIMIT_SUBTOTAL`` (mirrored from
``data_estate/generate.py``). An invoice's limit is the limit of the *role* of its
``approved_by`` employee; an unknown role gets the smallest finite limit so nothing
slips through by having no rule at all.
"""
from __future__ import annotations


def _iso(ts) -> str:
    """ISO date for a timestamp; the detectors never assume a pandas dtype."""
    return ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)


def _limit_for_role(role: str, limits: dict[str, float]) -> float:
    """The approval limit for ``role``; unknown role -> the smallest finite limit."""
    if role in limits:
        limit = limits[role]
        if limit != float("inf"):
            return float(limit)
        return float("inf")
    finite = [float(v) for v in limits.values() if v != float("inf")]
    return min(finite) if finite else 0.0


def detect_threshold_splitting(ds, *, window_days=2, min_cluster=3, min_ratio=0.80) -> list[dict]:
    """Clusters of ``recibida`` invoices from one supplier, one approver, just under a limit.

    Per supplier, the ``recibida`` invoices are sorted by date and split into clusters
    where consecutive invoices are ``<= window_days`` apart. A cluster survives when it
    has ``>= min_cluster`` invoices, every invoice's ``subtotal`` is in
    ``[min_ratio * limit, limit)``, and the cluster's summed subtotal meets the limit.
    """
    from agent.rules import APPROVAL_LIMIT_SUBTOTAL

    rec = ds.invoices[ds.invoices["tipo"] == "recibida"] if len(ds.invoices) else ds.invoices
    if not len(rec):
        return []

    rec = rec.copy()
    rec["approved_by"] = rec["approved_by"].fillna("")

    role_of: dict[str, str] = {}
    if len(ds.employees):
        role_of = {str(e.employee_id): str(e.role) for e in ds.employees.itertuples(index=False)}

    rows: list[dict] = []
    # A cluster is a single approver dodging *their own* gate, so group by supplier
    # and approver (the limit is uniform within a cluster).
    for (supplier, approver), grp in rec[rec["approved_by"] != ""].groupby(
        ["counterparty_id", "approved_by"], sort=False
    ):
        grp = grp.sort_values("fecha").reset_index(drop=True)
        # Split into date clusters on the same axis as a business-day window.
        bounds: list[tuple[int, int]] = []
        start = 0
        for i in range(1, len(grp)):
            if (grp.loc[i, "fecha"] - grp.loc[i - 1, "fecha"]).days > window_days:
                bounds.append((start, i))
                start = i
        bounds.append((start, len(grp)))

        role = role_of.get(str(approver), "")
        limit = _limit_for_role(role, APPROVAL_LIMIT_SUBTOTAL)

        for a, b in bounds:
            cl = grp.iloc[a:b]
            subtotals = [float(x) for x in cl["subtotal"]]
            if len(subtotals) < min_cluster:
                continue
            # Every invoice sits under the limit, but close enough that splitting is
            # obviously deliberate; a Director General's "infinite" limit never passes.
            if any(s < min_ratio * limit or s >= limit for s in subtotals):
                continue
            if sum(subtotals) < limit:
                continue

            uuids = [str(u) for u in cl["uuid"]]
            evidence = list(uuids)
            if len(ds.bank_transactions):
                paid = ds.bank_transactions[
                    (ds.bank_transactions["direction"] == "out")
                    & (ds.bank_transactions["invoice_uuid"].isin(uuids))
                ]
                evidence.extend(str(t) for t in paid["txn_id"])
            if len(ds.goods_receipts):
                goods = ds.goods_receipts[ds.goods_receipts["invoice_uuid"].isin(uuids)]
                evidence.extend(str(r) for r in goods["receipt_id"])
            evidence = list(dict.fromkeys(evidence))

            rows.append(
                {
                    "entity_id": str(supplier),
                    "approver_id": str(approver),
                    # The approver is the co-actor whose gate was dodged — carry them as
                    # the lead's employee so the loop's dossier lists them as related and
                    # the finding accuses [vendor, buyer] (kickback does the same).
                    "employee_id": str(approver),
                    "approver_role": role,
                    "limit": limit,
                    "n_invoices": len(subtotals),
                    "first_date": _iso(cl["fecha"].min()),
                    "last_date": _iso(cl["fecha"].max()),
                    "cluster_subtotal": round(sum(subtotals), 2),
                    "cluster_total_mxn": round(float(cl["total"].sum()), 2),
                    "invoice_uuids": uuids,
                    "evidence": evidence,
                }
            )

    rows.sort(key=lambda r: (r["entity_id"], r["first_date"]))
    return rows
