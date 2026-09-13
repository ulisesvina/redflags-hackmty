"""agent/clear.py — grounds the "why we did NOT accuse" reasons in the records (#69).

The investigation loop drops every lead without a scheme signature. Historically
that produced one canned sentence per detector, written without looking at the
data, so on a judge's hand-edited dataset it could be *false*, and the honest
answer to "how do you know?" was "it is hard-coded". This module replaces those
clauses with pure pandas checks that return a readable reason **with record IDs**
when the innocent explanation actually holds, and ``None`` when it cannot be
confirmed from the books. A ``None`` becomes an honest ``"unverified: ..."``
reason in ``not_pursued`` (and, in #70, an escalation to the model).

``agent.investigate._drop_reason`` drives it: for each detector on a dossier it
calls :func:`clear_reason`; if every call returns a sentence the entity is
*cleared* (all reasons joined with ``"; "``), otherwise the entity is
*unverified*.

Pure and deterministic: no I/O, no LLM, never reads ``hidden/``. Unknown
detector -> ``None`` (never raises).
"""
from __future__ import annotations

from typing import Callable

from .data import Dataset
from .rules import _active_69b_supplier_ids

# Categories that never carry a goods receipt by generator construction.
_SERVICE_CATEGORIES = {"servicios", "logistica", "renta_util"}
# Categories that *should* carry a goods receipt; a missing one is a red flag.
_GOODS_CATEGORIES = {"consumibles", "materia_prima", "refacciones"}

_CATEGORY_LABEL = {
    "servicios": "service",
    "logistica": "logistics",
    "renta_util": "rental",
    "consumibles": "consumables",
    "materia_prima": "raw material",
    "refacciones": "spare parts",
}


# --- formatting helpers -----------------------------------------------------
def _fmt_mxn(value) -> str:
    """Format a peso amount as ``MXN 1,234.56``."""
    try:
        return f"MXN {float(value):,.2f}"
    except (TypeError, ValueError):
        return "MXN 0.00"


def _ids_text(ids: list[str], n: int = 3) -> str:
    """First ``n`` IDs joined with ', '; append ' and N more' when more exist."""
    ids = [str(i) for i in ids]
    if not ids:
        return ""
    if len(ids) <= n:
        return ", ".join(ids)
    return ", ".join(ids[:n]) + f" and {len(ids) - n} more"


def _supplier_row(ds: Dataset, entity_id: str):
    """The suppliers row for ``entity_id`` or ``None`` if it is not a supplier."""
    if len(ds.suppliers) == 0:
        return None
    sub = ds.suppliers[ds.suppliers["supplier_id"].astype(str) == str(entity_id)]
    return sub.iloc[0] if len(sub) else None


def _recibida(ds: Dataset, entity_id: str):
    """``recibida`` invoices of the supplier ``entity_id``."""
    if len(ds.invoices) == 0:
        return ds.invoices
    return ds.invoices[
        (ds.invoices["tipo"] == "recibida")
        & (ds.invoices["counterparty_id"].astype(str) == str(entity_id))
    ]


def _receipt_ids_for(ds: Dataset, invoice_uuids) -> list[str]:
    """goods_receipt ``receipt_id``s for the given invoice UUIDs."""
    uuids = {str(u) for u in invoice_uuids}
    if not uuids or len(ds.goods_receipts) == 0:
        return []
    sub = ds.goods_receipts[ds.goods_receipts["invoice_uuid"].astype(str).isin(uuids)]
    return sorted({str(r) for r in sub["receipt_id"]})


def _largest_invoice(ds: Dataset, entity_id: str):
    """The largest ``total`` recibida invoice of the supplier, or None."""
    invs = _recibida(ds, entity_id)
    if len(invs) == 0:
        return None
    row = invs.sort_values("total", ascending=False).iloc[0]
    return {
        "uuid": str(row["uuid"]),
        "total": float(row["total"]),
        "descripcion": str(row.get("descripcion", "") or ""),
        "approved_by": str(row.get("approved_by", "") or ""),
        "tipo": str(row.get("tipo", "") or ""),
    }


# --- 69-B / bank helpers ------------------------------------------------------
def _rfc_live_69b(ds: Dataset, entity_id: str) -> bool:
    """Is this supplier's RFC on the 69-B list in a live state?"""
    return str(entity_id) in _active_69b_supplier_ids(ds)


def _address_matches_employee_home(ds: Dataset, street, city) -> bool:
    if len(ds.employees) == 0:
        return False
    sub = ds.employees[
        (ds.employees["home_street"].astype(str) == str(street))
        & (ds.employees["home_city"].astype(str) == str(city))
    ]
    return len(sub) > 0


def _outflow_to_employee(ds: Dataset, entity_clabe) -> bool:
    if len(ds.counterparty_bank) == 0 or len(ds.employees) == 0:
        return False
    emp_clabes = {str(c) for c in ds.employees["personal_clabe"]}
    if not emp_clabes:
        return False
    out = ds.counterparty_bank[
        (ds.counterparty_bank["entity_clabe"].astype(str) == str(entity_clabe))
        & (ds.counterparty_bank["direction"].astype(str) == "out")
    ]
    if len(out) == 0:
        return False
    return any(str(c) in emp_clabes for c in out["counterparty_clabe"])


def _has_employee_link(ds: Dataset, supplier_row) -> bool:
    """True when the address matches an employee home OR money flows to an employee."""
    if _address_matches_employee_home(ds, supplier_row["street"], supplier_row["city"]):
        return True
    return _outflow_to_employee(ds, supplier_row["clabe"])


# --- per-detector checks ------------------------------------------------------
def _clear_new_vendor_round_amounts(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    row = _supplier_row(ds, entity_id)
    if row is None:
        return None
    if _rfc_live_69b(ds, entity_id):
        return None
    invs = _recibida(ds, entity_id)
    if len(invs) == 0:
        return None
    uuids = set(invs["uuid"])
    rec_ids = _receipt_ids_for(ds, uuids)
    # Innocent iff every invoice has at least one goods receipt.
    by_uuid = ds.goods_receipts  # count receipts per invoice
    if len(by_uuid) == 0:
        return None
    have = set(by_uuid["invoice_uuid"].astype(str))
    if not all(str(u) in have for u in uuids):
        return None
    rfc = str(row["rfc"])
    return (
        f"new vendor with round amounts, but all {len(invs)} invoices have "
        f"warehouse-signed goods receipts ({_ids_text(rec_ids)}) and RFC {rfc} is not on the 69-B list"
    )


def _clear_name_twin_69b(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    row = _supplier_row(ds, entity_id)
    if row is None:
        return None
    rfc = str(row["rfc"])
    # Reuse the tool's 69-B resolution rather than re-implementing the logic.
    from .tools import Tools

    info = Tools(ds).check_69b(rfc)
    if info.get("listed"):
        return None
    matches = info.get("name_matches", []) or []
    twins = "; ".join(
        f"{m['rfc']} ({m['nombre']}, {m['situacion']})"
        for m in matches
        if m.get("rfc")
    )
    invs = _recibida(ds, entity_id)
    uuids = set(invs["uuid"])
    rec_ids = _receipt_ids_for(ds, uuids)
    receipt_txt = ""
    if rec_ids:
        receipt_txt = f"; {len(rec_ids)} of {len(invs)} invoices have goods receipts"
    if twins:
        return (
            f"the 69-B list is matched on RFC, not on name — the supplier's RFC {rfc} "
            f"is not listed; its name twin on 69-B is {twins}; NOT this supplier{receipt_txt}"
        )
    return (
        f"the 69-B list is matched on RFC, not on name — the supplier's RFC {rfc} "
        f"is not on the list{receipt_txt}"
    )


def _clear_shared_supplier_address(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    row = _supplier_row(ds, entity_id)
    if row is None:
        return None
    if _address_matches_employee_home(ds, row["street"], row["city"]):
        return None
    if _outflow_to_employee(ds, row["clabe"]):
        return None
    street = str(row["street"])
    # The other suppliers sharing this address (the reason it is not a red flag).
    siblings = ds.suppliers[
        (ds.suppliers["street"].astype(str) == street)
        & (ds.suppliers["city"].astype(str) == str(row["city"]))
        & (ds.suppliers["supplier_id"].astype(str) != str(entity_id))
    ]
    sibling_txt = ""
    if len(siblings):
        parts = [f"{s['supplier_id']} ({s['name']})" for _, s in siblings.iterrows()]
        sibling_txt = f" with {_ids_text(parts)}"
    invs = _recibida(ds, entity_id)
    rec_ids = _receipt_ids_for(ds, set(invs["uuid"]))
    rec_txt = ""
    if len(invs):
        rec_txt = f"; {len(rec_ids)} of {len(invs)} invoices have goods receipts"
    if rec_ids:
        rec_txt += f" ({_ids_text(rec_ids)})"
    return (
        f"shares its address ({street}){sibling_txt}; it matches no employee's home "
        f"and its bank statement shows no outflow to an employee account{rec_txt}"
    )


def _services_no_receipt_reason(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    """Shared logic for ``detect_no_receipt`` and ``detect_fast_pay_no_deliverable``."""
    row = _supplier_row(ds, entity_id)
    if row is None:
        return None
    category = str(row["category"])
    # A goods category with missing receipts is a genuine red flag: not innocent.
    if category in _GOODS_CATEGORIES:
        return None
    if category not in _SERVICE_CATEGORIES:
        return None
    if _rfc_live_69b(ds, entity_id):
        return None
    if _has_employee_link(ds, row):
        return None
    invs = _recibida(ds, entity_id)
    if len(invs) == 0:
        return None
    largest = _largest_invoice(ds, entity_id)
    label = _CATEGORY_LABEL.get(category, category)
    noun = f"{len(invs)} {label} invoice{'s' if len(invs) != 1 else ''}"
    if largest:
        noun = (
            f"{noun}, the largest ({largest['uuid']}, {_fmt_mxn(largest['total'])}) "
            f"describing '{largest['descripcion']}', approved by {largest['approved_by']}"
        )
    rfc = str(row["rfc"])
    return (
        f"{noun}; {label} deliveries carry no goods receipt (LISR deductible regardless); "
        f"RFC {rfc} is not on the 69-B list"
    )


def _clear_no_receipt(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    return _services_no_receipt_reason(entity_id, leads, ds)


def _clear_fast_pay_no_deliverable(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    return _services_no_receipt_reason(entity_id, leads, ds)


def _clear_cash_payments(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    row = _supplier_row(ds, entity_id)
    if row is None:
        return None
    invs = _recibida(ds, entity_id)
    if len(invs) == 0:
        return None
    cash = invs[invs["forma_pago"].astype(str) == "01"]
    if len(cash) == 0:
        return None
    if (cash["total"].astype(float) > 2000.0).any():
        return None
    by_uuid = ds.goods_receipts
    if len(by_uuid) == 0:
        return None
    have = set(by_uuid["invoice_uuid"].astype(str))
    if not all(str(u) in have for u in cash["uuid"]):
        return None
    largest = float(cash["total"].astype(float).max())
    rec_ids = _receipt_ids_for(ds, set(cash["uuid"]))
    return (
        f"{len(cash)} cash invoice{'s' if len(cash) != 1 else ''}, the largest "
        f"{_fmt_mxn(largest)}, all under the MXN 2,000 deductibility cap (LISR Art. 27-III), "
        f"goods received ({_ids_text(rec_ids)})"
    )


def _clear_strong(entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    """A strong (scheme-defining) detector with no complete signature is never cleared."""
    return None


# --- dispatch ---------------------------------------------------------------
_DISPATCH: dict[str, Callable[[str, list[dict], Dataset], str | None]] = {
    "detect_new_vendor_round_amounts": _clear_new_vendor_round_amounts,
    "detect_name_twin_69b": _clear_name_twin_69b,
    "detect_shared_supplier_address": _clear_shared_supplier_address,
    "detect_no_receipt": _clear_no_receipt,
    "detect_fast_pay_no_deliverable": _clear_fast_pay_no_deliverable,
    "detect_cash_payments": _clear_cash_payments,
    # Strong detectors never clear a lead without a complete scheme signature.
    "detect_efos": _clear_strong,
    "detect_employee_address_match": _clear_strong,
    "detect_kickback_outflow": _clear_strong,
    "detect_round_trip": _clear_strong,
    "detect_duplicate_payments": _clear_strong,
    "detect_clabe_not_on_master": _clear_strong,
}


def clear_reason(detector: str, entity_id: str, leads: list[dict], ds: Dataset) -> str | None:
    """One grounded innocent explanation for ``entity_id`` under ``detector``, or None.

    Returns a non-engineer-readable sentence ending with record IDs when the
    innocent explanation actually holds, and ``None`` when it cannot be confirmed
    from the data (or the detector is unknown). Never raises.
    """
    fn = _DISPATCH.get(detector)
    if fn is None:
        return None
    try:
        return fn(entity_id, leads or [], ds)
    except Exception:
        return None
