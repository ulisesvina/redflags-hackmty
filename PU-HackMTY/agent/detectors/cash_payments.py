"""detect_cash_payments: suppliers paid in cash (forma_pago == "01").

Cash is a weak signal, not proof. In Mexico cash expenses are deductible only up to MXN 2,000
per transaction (LISR Art. 27-III), so any cash invoice over the cap is a legitimate audit flag
— but paying small amounts in cash is ordinary commerce. The decoy here is a supplier whose cash
invoices all stay *under* the cap: the agent should record it as \u201clooked, all under the
deductibility cap, benign\u201d rather than accuse it. The lead carries ``n_over_cap`` /
``all_under_cap`` so whether the cap is crossed is explicit and the detector never decides.

Rules:

- ``ds.invoices`` rows with ``tipo == \"recibida\"`` and ``forma_pago == \"01\"``.
- One lead per supplier, ``cap_mxn`` defaults to 2000.0 (LISR Art. 27-III).

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``. Output is deterministic:
one dict per supplier, sorted by ``entity_id``.
"""
from __future__ import annotations

DEFAULT_CAP_MXN = 2000.0  # LISR Art. 27-III cash deductibility ceiling, per transaction.


def detect_cash_payments(ds, *, cap_mxn: float = DEFAULT_CAP_MXN, **params) -> list[dict]:
    """Return one lead per supplier that received cash invoices.

    One dict per supplier, sorted by ``entity_id``:

        entity_id · name · n_cash_invoices · cash_total_mxn · max_cash_invoice_mxn ·
        n_over_cap · all_under_cap · n_with_receipt · evidence
    """
    cash = ds.invoices[
        (ds.invoices["tipo"] == "recibida") & (ds.invoices["forma_pago"] == "01")
    ] if len(ds.invoices) else ds.invoices

    receipt_set = set(ds.goods_receipts["invoice_uuid"]) if len(ds.goods_receipts) else set()

    names = dict(zip(ds.suppliers["supplier_id"], ds.suppliers["name"]))

    # txn_ids by invoice_uuid (any bank transaction referencing a cash invoice).
    txn_by_invoice: dict[str, list[str]] = {}
    if len(ds.bank_transactions):
        bt = ds.bank_transactions[ds.bank_transactions["invoice_uuid"] != ""]
        for t in bt.itertuples(index=False):
            txn_by_invoice.setdefault(str(t.invoice_uuid), []).append(str(t.txn_id))

    rows: list[dict] = []
    for supplier_id, sub in cash.groupby("counterparty_id") if len(cash) else []:
        invoice_uuids = sorted(str(u) for u in sub["uuid"])
        cash_total = float(sub["total"].sum())
        max_cash = float(sub["total"].max())
        n_over_cap = int((sub["total"] > cap_mxn).sum())
        n_with_receipt = sum(1 for u in invoice_uuids if u in receipt_set)

        txn_ids = sorted({tid for u in invoice_uuids for tid in txn_by_invoice.get(u, [])})

        rows.append(
            {
                "entity_id": str(supplier_id),
                "name": str(names.get(str(supplier_id), "")),
                "n_cash_invoices": int(len(sub)),
                "cash_total_mxn": cash_total,
                "max_cash_invoice_mxn": max_cash,
                "n_over_cap": n_over_cap,
                "all_under_cap": bool(n_over_cap == 0),
                "n_with_receipt": int(n_with_receipt),
                "evidence": invoice_uuids + txn_ids,
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
