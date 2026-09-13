"""detect_kickback_outflow: money leaving a supplier's account to an employee's personal CLABE.

The proof of the kickback scheme, not just its tell. ``detect_employee_address_match`` (#7) says a
supplier is registered at an employee's home — a coincidence a defence lawyer can explain. What closes
the case is the supplier's own bank statement (``counterparty_bank``) showing money flowing from the
supplier's CLABE to that same employee's *personal* CLABE. ``data_estate/README.md`` calls this the
proof: "same-approver + counterparty statement outflows to employee CLABE".

This detector hands it over as a lead with the ``CP*`` record IDs attached. It is deliberately
threshold-free: a single peso leaving a supplier's account for an employee's personal account is a lead
worth investigating. It never decides — the loop (#13) and the guard (#14) weigh it.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``. Output is deterministic: one
dict per (supplier, employee) pair, sorted by ``(entity_id, employee_id)``.
"""
from __future__ import annotations


def detect_kickback_outflow(ds, **params) -> list[dict]:
    """Return one lead per (supplier, employee) pair whose supplier statement pays the employee.

    Steps:
    1. Take ``ds.counterparty_bank`` rows with ``direction == "out"``.
    2. Join ``entity_clabe`` to ``ds.suppliers.clabe`` (exact string) to find the supplier whose
       statement it is; rows whose ``entity_clabe`` is not a supplier CLABE are dropped.
    3. Join ``counterparty_clabe`` to ``ds.employees.personal_clabe``; keep only rows that land on an
       employee's personal account.
    4. Group by ``(supplier_id, employee_id)``; one lead per pair.

    ``evidence`` is the matched ``CP*`` record IDs only — the supplier's invoices and *our* payments
    are already the evidence of #7, and the loop unions evidence per entity.
    """
    # Map every supplier CLABE back to its supplier_id; drop duplicate CLABEs defensively.
    supplier_by_clabe: dict[str, str] = {}
    for s in ds.suppliers.itertuples(index=False):
        if str(s.clabe) and str(s.clabe) not in supplier_by_clabe:
            supplier_by_clabe[str(s.clabe)] = str(s.supplier_id)

    # Map every employee personal CLABE back to its employee_id.
    employee_by_clabe: dict[str, str] = {}
    for e in ds.employees.itertuples(index=False):
        if str(e.personal_clabe) and str(e.personal_clabe) not in employee_by_clabe:
            employee_by_clabe[str(e.personal_clabe)] = str(e.employee_id)

    # supplier_id -> approved_by (the person who signed off on the vendor).
    supplier_dir = {
        str(s.supplier_id): {
            "name": str(s.name),
            "approved_by": str(s.approved_by),
        }
        for s in ds.suppliers.itertuples(index=False)
    }
    employee_dir = {
        str(e.employee_id): {"name": str(e.name), "role": str(e.role)}
        for e in ds.employees.itertuples(index=False)
    }

    out = ds.counterparty_bank[ds.counterparty_bank["direction"] == "out"]
    if len(out) == 0:
        return []

    rows: list[dict] = []
    for r in out.itertuples(index=False):
        supplier_id = supplier_by_clabe.get(str(r.entity_clabe))
        if supplier_id is None:
            continue  # customer statements are not this detector's business
        employee_id = employee_by_clabe.get(str(r.counterparty_clabe))
        if employee_id is None:
            continue  # outflow did not land on an employee personal account

        rows.append(
            {
                "supplier_id": supplier_id,
                "employee_id": employee_id,
                "record_id": str(r.record_id),
                "amount": float(r.amount),
                "fecha": r.fecha,
            }
        )

    if not rows:
        return []

    # Group by (supplier_id, employee_id).
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["supplier_id"], row["employee_id"]), []).append(row)

    # Sum of recibida invoices per supplier, for the outflow ratio denominator.
    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"]
    supplier_invoice_total: dict[str, float] = {}
    if len(recibida):
        sub = recibida[["counterparty_id", "total"]].copy()
        sub["counterparty_id"] = sub["counterparty_id"].astype(str)
        supplier_invoice_total = sub.groupby("counterparty_id")["total"].sum().to_dict()

    leads: list[dict] = []
    for (supplier_id, employee_id), items in grouped.items():
        items_sorted = sorted(items, key=lambda x: (x["record_id"], x["fecha"]))
        outflow_total = sum(i["amount"] for i in items_sorted)
        first_outflow = min(i["fecha"] for i in items_sorted)
        last_outflow = max(i["fecha"] for i in items_sorted)

        supplier_invoice_total_mxn = float(supplier_invoice_total.get(supplier_id, 0.0))
        outflow_ratio = round(outflow_total / supplier_invoice_total_mxn, 4) if supplier_invoice_total_mxn else 0.0

        sup_info = supplier_dir.get(supplier_id, {"name": "", "approved_by": ""})
        emp_info = employee_dir.get(employee_id, {"name": "", "role": ""})

        leads.append(
            {
                "entity_id": supplier_id,
                "supplier_name": sup_info["name"],
                "employee_id": employee_id,
                "employee_name": emp_info["name"],
                "employee_role": emp_info["role"],
                "same_approver": sup_info["approved_by"] == employee_id,
                # Judge-shape (#84): the supplier's approver == the employee who
                # receives the money is the strong link; a shared address is only
                # corroboration.
                "approver_link": sup_info["approved_by"] == employee_id,
                # This detector only fires on a real statement outflow to an
                # employee personal CLABE, so it is never the weak same-institution
                # decoy pattern (that check lives in agent/clear.py, #94).
                "same_bank_only": False,
                "n_outflows": int(len(items_sorted)),
                "outflow_total_mxn": outflow_total,
                "first_outflow": first_outflow.strftime("%Y-%m-%d"),
                "last_outflow": last_outflow.strftime("%Y-%m-%d"),
                "supplier_invoice_total_mxn": supplier_invoice_total_mxn,
                "outflow_ratio": outflow_ratio,
                "evidence": sorted(i["record_id"] for i in items_sorted),
            }
        )

    leads.sort(key=lambda x: (x["entity_id"], x["employee_id"]))
    return leads
