"""detect_shared_supplier_address: two suppliers registered at one address.

A genuine (if weak) tip for a related-party arrangement: two separate legal entities sharing a
single registered address. Legitimate for an honest supplier and its neighbour in a shared
commercial building; that is exactly the decoy this detector exists to surface so the loop can
record \u201cwe looked and it is benign\u201d. It is a deliberately **weak signal** — the lead carries
whether the address also happens to be an *employee's home* (which ``detect_employee_address_match``
#7 covers), so nothing here is decided by the detector.

Rules:

- Group ``ds.suppliers`` by ``(street.strip(), city.strip())``; keep groups with \u2265 2 suppliers.
- One lead per supplier in such a group. ``shares_with`` lists the other group members.
- ``employee_home_match`` is True only when the same address equals some employee's
  ``(home_street, home_city)``. On company_42 it is False for every lead because #7 owns that case.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``. Output is deterministic:
one dict per supplier, sorted by ``entity_id``.
"""
from __future__ import annotations


def detect_shared_supplier_address(ds, **params) -> list[dict]:
    """Return one lead per supplier that shares its registered address with another supplier.

    Steps:
    1. Strip ``street``/``city`` and group ``ds.suppliers``; keep groups with \u2265 2 members.
    2. For each supplier in such a group emit one dict with ``shares_with`` (the other member
       ids, sorted) and ``employee_home_match`` (whether the address is also an employee's home).
    """
    sup = ds.suppliers[["supplier_id", "name", "street", "city"]].copy()
    sup["street"] = sup["street"].str.strip()
    sup["city"] = sup["city"].str.strip()

    # Group members per address, for groups with >= 2 suppliers.
    address_members: dict[tuple[str, str], list[str]] = {}
    for row in sup.itertuples(index=False):
        address_members.setdefault((str(row.street), str(row.city)), []).append(str(row.supplier_id))
    shared_addresses = {
        addr: sorted(members)
        for addr, members in address_members.items()
        if len(members) >= 2
    }

    # Employee home addresses, for the employee_home_match flag.
    if len(ds.employees):
        homes = {
            (str(s), str(c))
            for s, c in zip(ds.employees["home_street"].str.strip(), ds.employees["home_city"].str.strip())
        }
    else:
        homes = set()

    receipt_set = set(ds.goods_receipts["invoice_uuid"]) if len(ds.goods_receipts) else set()
    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"] if len(ds.invoices) else ds.invoices

    rows: list[dict] = []
    for row in sup.itertuples(index=False):
        addr = (str(row.street), str(row.city))
        members = shared_addresses.get(addr)
        if members is None:
            continue

        sub = recibida[recibida["counterparty_id"] == str(row.supplier_id)]
        invoice_uuids = sorted(str(u) for u in sub["uuid"])
        n_with_receipt = sum(1 for u in invoice_uuids if u in receipt_set)

        rows.append(
            {
                "entity_id": str(row.supplier_id),
                "name": str(row.name),
                "street": str(row.street),
                "city": str(row.city),
                "shares_with": [m for m in members if m != str(row.supplier_id)],
                "employee_home_match": bool(addr in homes),
                "n_invoices": int(len(sub)),
                "total_mxn": float(sub["total"].sum()) if len(sub) else 0.0,
                "n_with_receipt": int(n_with_receipt),
                "evidence": invoice_uuids,
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
