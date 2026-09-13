"""detect_employee_address_match: supplier registered at an employee's home.

An undisclosed related party: a supplier whose registered street/city exactly
matches an employee's home address. Combined with that same employee approving
the supplier (``same_approver``), it is the classic tell for the kickback shell
— a shell vendor the insider sets up at their own address and signs off on.

This is a **lead list, not an accusation list**: a single address coincidence is
not proof of fraud on its own (some vendors genuinely register at their owner's
home). The investigation loop (#13) weighs ``same_approver`` and the payment/i
invoice trail before pursuing. The "shared office" decoy — two suppliers at the
same address as *each other* — is deliberately excluded: we only compare
suppliers to employee homes, never supplier to supplier.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``.
Output is deterministic: one dict per (supplier, employee) match, sorted by
``(entity_id, employee_id)``.
"""
from __future__ import annotations


def detect_employee_address_match(ds, **params) -> list[dict]:
    """Return one lead per (supplier, employee) whose addresses exactly match.

    Steps:
    1. Inner-join ``ds.suppliers`` (street, city) to ``ds.employees``
       (home_street, home_city) on an exact match after ``.str.strip()`` on both
       sides. No fuzzy matching; no supplier-to-supplier comparisons.
    2. ``same_approver`` = ``suppliers.approved_by == employees.employee_id``.
    3. Emit one dict per pair with the supplier's ``recibida`` invoice count and
       total, and evidence = those invoice UUIDs + the ``out`` transaction ids
       that reference them.
    """
    sup = ds.suppliers[
        ["supplier_id", "name", "street", "city", "approved_by"]
    ].copy()
    emp = ds.employees[
        ["employee_id", "name", "role", "home_street", "home_city"]
    ].copy()

    # Normalize strings on both sides before comparing (never fuzzy, never
    # supplier-vs-supplier).
    for col in ("street", "city"):
        sup[col] = sup[col].str.strip()
    for col in ("home_street", "home_city"):
        emp[col] = emp[col].str.strip()

    matches = sup.merge(
        emp,
        left_on=["street", "city"],
        right_on=["home_street", "home_city"],
        how="inner",
    )

    # Outgoing bank transactions keyed by invoice_uuid, so we can attach the
    # money trail to each matched supplier's invoices.
    out_txns_by_invoice: dict[str, list[str]] = {}
    if len(ds.bank_transactions):
        out = ds.bank_transactions[
            (ds.bank_transactions["direction"] == "out")
            & (ds.bank_transactions["invoice_uuid"] != "")
        ]
        for t in out.itertuples(index=False):
            out_txns_by_invoice.setdefault(str(t.invoice_uuid), []).append(str(t.txn_id))

    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"] if len(ds.invoices) else ds.invoices

    rows: list[dict] = []
    for m in matches.itertuples(index=False):
        supplier_id = str(m.supplier_id)
        supplier_inv = recibida[recibida["counterparty_id"] == supplier_id]
        invoice_uuids = sorted(str(u) for u in supplier_inv["uuid"])
        total_mxn = float(supplier_inv["total"].sum()) if len(supplier_inv) else 0.0

        txn_ids = sorted(
            {
                tid
                for uuid in invoice_uuids
                for tid in out_txns_by_invoice.get(uuid, [])
            }
        )

        rows.append(
            {
                "entity_id": supplier_id,
                "supplier_name": str(m.name_x),
                "employee_id": str(m.employee_id),
                "employee_name": str(m.name_y),
                "employee_role": str(m.role),
                "same_approver": bool(m.approved_by == m.employee_id),
                "street": str(m.street),
                "city": str(m.city),
                "n_invoices": int(len(supplier_inv)),
                "total_mxn": total_mxn,
                "evidence": invoice_uuids + txn_ids,
            }
        )

    rows.sort(key=lambda x: (x["entity_id"], x["employee_id"]))
    return rows
