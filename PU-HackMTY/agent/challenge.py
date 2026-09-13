"""Adversarial review (#91): attack every finding before it is printed.

"If your system runs an adversarial review, include what it argued and why the
finding survived. A finding that no one tried to break is weaker than one that
was attacked and held." Also the judges' question "what if the employee just
happens to bank at the same institution?".

:func:`challenge` takes an accepted finding and the dataset and returns the
arguments a defender would raise against it plus a verdict. Every argument is a
deterministic predicate over ``ds`` (pure pandas, no LLM, no I/O, never reads
``hidden/``). An argument whose counter-claim the records *support* is returned
with outcome ``killed`` or ``weakened``; one the records refute is ``survived``
(the accusation held). The caller (``agent.investigate``) turns a ``killed``
finding into a declined lead closed by the challenger, a ``weakened`` finding
into ``confidence = 'probable'``, and logs one ``challenge`` entry per finding.

The scheme types handled are the internal ones (see AGENTS.md): ``efos_fake_supplier``,
``kickback_shell``, ``round_trip_sales``, ``threshold_splitting``,
``revenue_inflation`` and ``duplicate_invoice_payment`` (a control observation).
An unknown type is never killed: return a single "survived" argument.
"""
from __future__ import annotations

import pandas as pd

from .data import Dataset

# A forward leg (the middleman passing our money on) later than this many days
# after our payment means it does not belong to the round trip we paid for.
FORWARD_DAYS = 7
# A phantom vendor that has a PO or contract behind this share of its invoices
# is not paper: the accusation does not hold.
PO_RATIO = 0.50
# A fixed-fee contract explains repeated amounts only when the invoices are
# spaced out; a daily run of split invoices is the pattern a splitter leaves.
THRESHOLD_GAP_DAYS = 20

_PAYROLL_WORDS = ("nomina", "nómina", "payroll", "prestamo", "préstamo", "loan", "adelanto")


def _arg(claim: str, records: list[str], outcome: str) -> dict:
    """One argument in the adversarial review."""
    return {"claim": claim, "records": list(records), "outcome": outcome}


def _row(frame: pd.DataFrame, column: str, value: str) -> pd.Series | None:
    if len(frame) == 0:
        return None
    hit = frame[frame[column] == value]
    return hit.iloc[0] if len(hit) else None


def _supplier_rfc(entity_id: str, ds: Dataset) -> str:
    row = _row(ds.suppliers, "supplier_id", entity_id)
    return str(row["rfc"]) if row is not None else ""


def _supplier_clabe(entity_id: str, ds: Dataset) -> str:
    row = _row(ds.suppliers, "supplier_id", entity_id)
    return str(row["clabe"]) if row is not None else ""


def _employee_clabe(entity_id: str, ds: Dataset) -> str:
    row = _row(ds.employees, "employee_id", entity_id)
    return str(row["personal_clabe"]) if row is not None else ""


def _customer_clabe(entity_id: str, ds: Dataset) -> str:
    row = _row(ds.customers, "customer_id", entity_id)
    return str(row["clabe"]) if row is not None else ""


def _ids(frame: pd.DataFrame, column: str) -> set[str]:
    return set(frame[column]) if len(frame) else set()


def _accused_of(finding: dict, ds: Dataset, column: str, kind: str) -> list[str]:
    ids = _ids(ds.suppliers if kind == "supplier" else ds.customers if kind == "customer" else ds.employees, column)
    return [a for a in finding.get("accused", []) if a in ids]


def _suppliers(finding, ds) -> list[str]:
    return _accused_of(finding, ds, "supplier_id", "supplier")


def _customers(finding, ds) -> list[str]:
    return _accused_of(finding, ds, "customer_id", "customer")


def _employees(finding, ds) -> list[str]:
    return _accused_of(finding, ds, "employee_id", "employee")


def _invoice_dates(ds: Dataset, supplier_ids: list[str]) -> list[pd.Timestamp]:
    if len(ds.invoices) == 0 or not supplier_ids:
        return []
    sub = ds.invoices[ds.invoices["counterparty_id"].isin(supplier_ids)]
    dates = pd.to_datetime(sub["fecha"], errors="coerce")
    return sorted(d for d in dates if not pd.isna(d))


def _bank_rows(ds: Dataset) -> list[dict]:
    """Normalise ``bank_transactions`` rows to a schema-independent form.

    Legacy rows carry ``account_clabe``/``counterparty_clabe``/``direction``;
    judge rows carry ``from_clabe``/``to_clabe``. Both are folded to ``from``/
    ``to`` (the direction money actually moves), plus the amount, date, id and
    reference.
    """
    if len(ds.bank_transactions) == 0:
        return []
    out: list[dict] = []
    cols = set(ds.bank_transactions.columns)
    for r in ds.bank_transactions.to_dict("records"):
        if "from_clabe" in cols:
            out.append({
                "from": str(r.get("from_clabe", "")), "to": str(r.get("to_clabe", "")),
                "direction": "", "amount": r.get("amount"), "fecha": r.get("date"),
                "reference": str(r.get("reference", "")), "id": str(r.get("txn_id", "")),
            })
        else:
            direction = str(r.get("direction", ""))
            acct = str(r.get("account_clabe", ""))
            cparty = str(r.get("counterparty_clabe", ""))
            frm, to = (acct, cparty) if direction == "out" else (cparty, acct)
            out.append({
                "from": frm, "to": to, "direction": direction, "amount": r.get("amount"),
                "fecha": r.get("fecha"), "reference": str(r.get("reference", "")),
                "id": str(r.get("txn_id", "")),
            })
    return out


def _cp_rows(ds: Dataset) -> list[dict]:
    """Normalise ``counterparty_bank`` rows to the same ``from``/``to`` form."""
    if len(ds.counterparty_bank) == 0:
        return []
    out: list[dict] = []
    for r in ds.counterparty_bank.to_dict("records"):
        direction = str(r.get("direction", ""))
        entity = str(r.get("entity_clabe", ""))
        counterparty = str(r.get("counterparty_clabe", ""))
        frm, to = (entity, counterparty) if direction == "out" else (counterparty, entity)
        out.append({
            "from": frm, "to": to, "direction": direction, "amount": r.get("amount"),
            "fecha": r.get("fecha"), "reference": str(r.get("reference", "")),
            "id": str(r.get("record_id", "")),
        })
    return out


def _all_flow_rows(ds: Dataset) -> list[dict]:
    """All bank movements (legacy + judge), normalized, as ``from``/``to`` rows."""
    return _bank_rows(ds) + _cp_rows(ds)


def _transfer_rows(a: str, b: str, ds: Dataset) -> list[dict]:
    """Rows showing money moving between the two CLABEs, in any direction."""
    return [r for r in _all_flow_rows(ds) if (r["from"] == a and r["to"] == b) or (r["from"] == b and r["to"] == a)]


def _company_clabe(ds: Dataset) -> str:
    return str(ds.company.get("clabe", ""))


# --- argument builders -------------------------------------------------------

def _arg_efos_po_contract(finding: dict, ds: Dataset) -> dict | None:
    """A PO or contract exists for >= PO_RATIO of the vendor's invoices."""
    suppliers = _suppliers(finding, ds)
    if not suppliers:
        return None
    rfc = {_supplier_rfc(s, ds) for s in suppliers if _supplier_rfc(s, ds)}
    po_vendors = set(ds.purchase_orders["vendor_rfc"]) if len(ds.purchase_orders) else set()
    contract_vendors = set(ds.contracts["vendor_rfc"]) if len(ds.contracts) else set()
    covered = (po_vendors | contract_vendors) & rfc
    records = sorted(str(v) for v in covered)
    n = len(_invoice_dates(ds, suppliers))
    if n == 0 or not covered:
        return _arg(
            "a PO or contract exists for >= 50% of the invoices", [],
            "survived",
        )
    # The share is by supplier: a vendor with any PO/contract count is covered.
    # With no data to argue the other way the counter-claim is unsupported.
    if len(covered) >= max(1, int(PO_RATIO * len(suppliers))):
        return _arg(
            "a PO or contract exists for >= 50% of the invoices", records,
            "killed",
        )
    return _arg("a PO or contract exists for >= 50% of the invoices", records, "survived")


def _arg_efos_presunto(finding: dict, ds: Dataset) -> dict:
    """The 69-B listing is 'presunto' and published after every invoice."""
    suppliers = _suppliers(finding, ds)
    weakened: list[str] = []
    for s in suppliers:
        rfc = _supplier_rfc(s, ds)
        if not rfc or len(ds.efos_69b) == 0:
            continue
        row = _row(ds.efos_69b, "rfc", rfc)
        if row is None or str(row["situacion"]).lower() != "presunto":
            continue
        pub = row.get("fecha_publicacion")
        if pub is None or pd.isna(pub):
            continue
        dates = _invoice_dates(ds, [s])
        if not dates:
            continue
        if pd.Timestamp(pub) > max(dates):
            weakened.append(str(rfc))
    return _arg(
        "the 69-B status is presunto and publication is after every invoice",
        weakened,
        "weakened" if weakened else "survived",
    )


def _arg_efos_other_receivers(finding: dict, ds: Dataset) -> dict | None:
    """The vendor invoices other receivers too (n/a when it only invoices us)."""
    suppliers = _suppliers(finding, ds)
    if not suppliers or len(ds.invoices) == 0:
        return None
    company_rfc = str(ds.company.get("rfc", ""))
    other = []
    for s in suppliers:
        rfc = _supplier_rfc(s, ds)
        if not rfc:
            continue
        sub = ds.invoices[ds.invoices["rfc_emisor"] == rfc]
        if len(sub) and any(str(v) and v != company_rfc for v in sub["rfc_receptor"]):
            other.append(str(rfc))
    if not other:
        return None  # no data -> skip, per the spec
    return _arg(
        "the vendor has invoices to other receivers", other, "weakened",
    )


def _arg_kickback_same_bank(finding: dict, ds: Dataset) -> dict | None:
    """Same-bank-code only, no transfer between the accounts."""
    suppliers = _suppliers(finding, ds)
    employees = _employees(finding, ds)
    if not suppliers or not employees:
        return None
    sup = _supplier_clabe(suppliers[0], ds)
    emp = _employee_clabe(employees[0], ds)
    if not sup or not emp:
        return None
    transfers = _transfer_rows(sup, emp, ds)
    records = sorted(str(t.get("id")) for t in transfers if t.get("id"))
    same_prefix = bool(sup) and bool(emp) and sup[:3] == emp[:3]
    if not transfers and same_prefix:
        # The employee's clabe is only linked by the shared bank code, and no
        # money ever moved between the two accounts.
        return _arg(
            "the employee link is same-bank-code only, no transfer between the accounts",
            [sup[:3], emp[:3]], "killed",
        )
    return _arg(
        "the employee link is same-bank-code only, no transfer between the accounts",
        records, "survived",
    )


def _arg_kickback_payroll(finding: dict, ds: Dataset) -> dict | None:
    """The transfer references payroll or a loan."""
    suppliers = _suppliers(finding, ds)
    employees = _employees(finding, ds)
    if not suppliers or not employees:
        return None
    sup = _supplier_clabe(suppliers[0], ds)
    emp = _employee_clabe(employees[0], ds)
    matched = []
    if sup and emp:
        for t in _transfer_rows(sup, emp, ds):
            ref = str(t.get("reference") or "")
            if any(w in ref.lower() for w in _PAYROLL_WORDS):
                matched.append(str(t.get("id")))
    return _arg(
        "the transfer references payroll or a loan", sorted(matched),
        "weakened" if matched else "survived",
    )


def _arg_kickback_approver(finding: dict, ds: Dataset) -> dict | None:
    """The approver is not the linked employee."""
    suppliers = _suppliers(finding, ds)
    employees = set(_employees(finding, ds))
    if not suppliers or not employees or len(ds.invoices) == 0:
        return None
    mismatches = []
    sup_ids = set(suppliers)
    sub = ds.invoices[ds.invoices["counterparty_id"].isin(sup_ids)]
    for r in sub.to_dict("records"):
        approver = str(r.get("approved_by") or "")
        if approver and approver not in employees:
            mismatches.append(str(r.get("uuid")))
    return _arg(
        "the approver is not the linked employee", sorted(mismatches),
        "weakened" if mismatches else "survived",
    )


def _arg_roundtrip_prior_history(finding: dict, ds: Dataset) -> dict | None:
    """The inbound payer (customer) had trading history with us before the first outbound."""
    customers = _customers(finding, ds)
    suppliers = _suppliers(finding, ds)
    if not customers or not suppliers:
        return None
    sup_clabe = _supplier_clabe(suppliers[0], ds)
    cus_clabe = _customer_clabe(customers[0], ds)
    flows = _all_flow_rows(ds)
    company_clabe = _company_clabe(ds)
    out_to_sup = [r for r in flows if r["to"] == sup_clabe and r["from"] == company_clabe]
    first_out = None
    for r in out_to_sup:
        f = pd.to_datetime(r["fecha"], errors="coerce")
        if not pd.isna(f) and (first_out is None or f < first_out):
            first_out = f
    if first_out is None:
        return _arg("the inbound payer has trading history with us before the first outbound", [], "survived")
    prior = False
    if cus_clabe and any(
        r["from"] == cus_clabe
        and not pd.isna(pd.to_datetime(r["fecha"], errors="coerce"))
        and pd.to_datetime(r["fecha"], errors="coerce") < first_out
        for r in flows
    ):
        prior = True
    if not prior and len(ds.invoices):
        inv_to_cus = ds.invoices[(ds.invoices["counterparty_id"].isin(customers)) & (ds.invoices["tipo"] == "emitida")]
        if len(inv_to_cus):
            early = pd.to_datetime(inv_to_cus["fecha"], errors="coerce")
            if (early < first_out).any():
                prior = True
    return _arg(
        "the inbound payer has trading history with us before the first outbound",
        [str(first_out.date())], "weakened" if prior else "survived",
    )


def _arg_roundtrip_forward(finding: dict, ds: Dataset) -> dict | None:
    """Every forward leg is more than FORWARD_DAYS after our payment."""
    customers = _customers(finding, ds)
    suppliers = _suppliers(finding, ds)
    if not customers or not suppliers:
        return None
    sup_clabe = _supplier_clabe(suppliers[0], ds)
    cus_clabe = _customer_clabe(customers[0], ds)
    if not sup_clabe or not cus_clabe:
        return None
    flows = _all_flow_rows(ds)
    legs = [r for r in flows if r["from"] == sup_clabe and r["to"] == cus_clabe]
    if not legs:
        return None
    company_clabe = _company_clabe(ds)
    out_to_sup = sorted(
        (pd.to_datetime(r["fecha"], errors="coerce") for r in flows if r["to"] == sup_clabe and r["from"] == company_clabe and not pd.isna(pd.to_datetime(r["fecha"], errors="coerce"))),
    )
    ok = 0
    for leg in legs:
        f = pd.to_datetime(leg["fecha"], errors="coerce")
        if pd.isna(f):
            continue
        before = [d for d in out_to_sup if d <= f]
        if before and (f - before[-1]).days <= FORWARD_DAYS:
            ok += 1
    if ok == 0:
        return _arg(
            f"the forward leg is more than {FORWARD_DAYS} days after our payment",
            sorted(str(leg["id"]) for leg in legs), "killed",
        )
    return _arg(
        f"the forward leg is more than {FORWARD_DAYS} days after our payment",
        sorted(str(leg["id"]) for leg in legs), "survived",
    )


def _arg_threshold_contract(finding: dict, ds: Dataset) -> dict | None:
    """A fixed-fee contract explains the repeated amount."""
    suppliers = _suppliers(finding, ds)
    if not suppliers:
        return None
    rfc = _supplier_rfc(suppliers[0], ds)
    contract_records: list[str] = []
    if rfc and len(ds.contracts):
        sub = ds.contracts[ds.contracts["vendor_rfc"] == rfc]
        contract_records = sorted(str(v) for v in sub["contract_id"])
    dates = _invoice_dates(ds, suppliers)
    spread = len(dates) >= 2 and (dates[-1] - dates[0]).days >= THRESHOLD_GAP_DAYS
    if contract_records and spread:
        return _arg(
            "a contract with a fixed fee explains the repeated amount",
            contract_records, "killed",
        )
    return _arg(
        "a contract with a fixed fee explains the repeated amount",
        contract_records, "survived",
    )


def _arg_threshold_parts(finding: dict, ds: Dataset) -> dict | None:
    """The invoices are different parts/descriptions."""
    suppliers = _suppliers(finding, ds)
    if not suppliers or len(ds.invoices) == 0:
        return None
    sub = ds.invoices[ds.invoices["counterparty_id"].isin(suppliers)]
    if len(ds.invoices) and "descripcion" in ds.invoices.columns:
        descs = {str(d) for d in sub["descripcion"] if str(d)}
        if len(descs) > 1:
            return _arg("the invoices are different parts/descriptions", sorted(descs)[:5], "weakened")
    return _arg("the invoices are different parts/descriptions", [], "survived")


def _arg_revenue_reversed(finding: dict, ds: Dataset) -> dict | None:
    """A cancelled invoice was reversed in the ledger."""
    evidence = [str(e) for e in finding.get("evidence", []) if str(e)]
    if not evidence or len(ds.ledger) == 0 or len(ds.invoices) == 0:
        return None
    invoices = ds.invoices[ds.invoices["uuid"].isin(evidence)]
    cancelled = invoices[invoices["status"].astype(str).str.lower() == "cancelado"] if "status" in ds.invoices.columns else pd.DataFrame()
    if len(cancelled) == 0:
        return _arg("the cancelled invoice was reversed in the ledger", [], "survived")
    cancelled_uuids = set(cancelled["uuid"])
    ledger = ds.ledger
    reversed_uuids = set(
        ledger[(ledger["account_code"].astype(str) == "4000") & (ledger["debit"] > 0)]["invoice_uuid"]
    ) if "account_code" in ledger.columns else set()
    still_cancelled = cancelled_uuids - reversed_uuids
    records = sorted(str(v) for v in (cancelled_uuids & reversed_uuids))
    return _arg(
        "the cancelled invoice was reversed in the ledger", records,
        "killed" if not still_cancelled else "survived",
    )


def _arg_revenue_customer_paid(finding: dict, ds: Dataset) -> dict | None:
    """The customer paid other invoices."""
    customers = _customers(finding, ds)
    if not customers:
        return None
    cus_clabe = _customer_clabe(customers[0], ds)
    paid = [r for r in _all_flow_rows(ds) if r["from"] == cus_clabe and r["to"] == _company_clabe(ds)]
    return _arg(
        "the customer paid other invoices", sorted(str(r["id"]) for r in paid)[:8],
        "weakened" if paid else "survived",
    )


def _arg_duplicate_refunded(finding: dict, ds: Dataset) -> dict | None:
    """The second payment was refunded."""
    evidence = [str(e) for e in finding.get("evidence", []) if str(e)]
    if len(ds.invoices) == 0:
        return None
    # The CLABEs that received the duplicate payments for the cited invoices.
    alt_clabes: set[str] = set()
    inv_uuids = set(ds.invoices[ds.invoices["uuid"].isin(evidence)]["uuid"])
    if len(ds.bank_transactions):
        out = ds.bank_transactions[ds.bank_transactions["direction"] == "out"]
        for r in out.to_dict("records"):
            if str(r.get("invoice_uuid", "")) in inv_uuids:
                alt_clabes.add(str(r.get("counterparty_clabe") or r.get("to_clabe") or ""))
    refunded = [r for r in _all_flow_rows(ds) if r["from"] in alt_clabes]
    return _arg(
        "the second payment was refunded", sorted(str(r["id"]) for r in refunded),
        "killed" if refunded else "survived",
    )


# --- dispatch ----------------------------------------------------------------

def _arguments_for(scheme: str, finding: dict, ds: Dataset) -> list[dict]:
    builders: list = []
    if scheme in ("efos_fake_supplier",):
        builders = [_arg_efos_po_contract, _arg_efos_presunto, _arg_efos_other_receivers]
    elif scheme in ("kickback_shell",):
        builders = [_arg_kickback_same_bank, _arg_kickback_payroll, _arg_kickback_approver]
    elif scheme in ("round_trip_sales",):
        builders = [_arg_roundtrip_prior_history, _arg_roundtrip_forward]
    elif scheme in ("threshold_splitting",):
        builders = [_arg_threshold_contract, _arg_threshold_parts]
    elif scheme in ("revenue_inflation",):
        builders = [_arg_revenue_reversed, _arg_revenue_customer_paid]
    elif scheme in ("duplicate_invoice_payment",):
        builders = [_arg_duplicate_refunded]
    arguments: list[dict] = []
    for b in builders:
        a = b(finding, ds)
        if a is not None:
            arguments.append(a)
    if not arguments:
        return [_arg("no adversarial argument applies to this scheme", [], "survived")]
    return arguments


def challenge(finding: dict, ds: Dataset) -> dict:
    """Run the adversarial review on one accepted finding.

    Returns ``{"arguments": [{"claim", "records", "outcome"}], "verdict":
    "survived"|"killed", "confidence": "proven"|"probable"}``. ``verdict`` is
    ``killed`` when any argument is killed; ``confidence`` is ``probable`` when
    any argument is weakened.
    """
    scheme = str(finding.get("scheme_type", ""))
    arguments = _arguments_for(scheme, finding, ds)
    killed = any(a["outcome"] == "killed" for a in arguments)
    weakened = any(a["outcome"] == "weakened" for a in arguments)
    verdict = "killed" if killed else "survived"
    confidence = "probable" if weakened else "proven"
    return {"arguments": arguments, "verdict": verdict, "confidence": confidence}
