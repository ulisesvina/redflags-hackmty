"""Rule catalog for the evidence guard (#14). ``agent/guard.py`` imports :data:`RULES`.

A :class:`Rule` bundles the *legal* citation that goes into a case file's ``rule``
field, the scheme types it may be used with, the record kinds its evidence must
draw from, and an ``amount`` callable that recomputes the figure the finding
*should* carry from the accused entities' records. The guard compares the LLM's
proposed ``amount_mxn`` against this recomputation (25% tolerance, the same
tolerance the scorer uses) so a hallucinated peso figure cannot enter the case
file.

The ``legal`` strings are byte-identical to the ``rule`` values in
``data_estate/out/example_case_file_for_seed42.json``, so that reference file is
recognised by the guard.

Pure, deterministic, no I/O, no LLM, never reads ``hidden/``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .data import Dataset

# Approval limits by buyer role, the gate threshold splitting circumvents (#82).
# Mirrored in data_estate/generate.py (the generator plants the scheme against these).
# A judge will ask to see this file, so the constant lives here, in code.
APPROVAL_LIMIT_SUBTOTAL = {
    "Gerente de Compras": 250_000.0,
    "Director General": float("inf"),
}

# CFF Art. 69-B (operaciones inexistentes), the SAT "facturas fantasma" blacklist.
_ACTIVE_69B = ("Presunto", "Definitivo")


def _active_69b_supplier_ids(ds: Dataset) -> set[str]:
    """Supplier ids whose RFC is on the 69-B list in a live (non-rebutted) state."""
    if len(ds.suppliers) == 0 or len(ds.efos_69b) == 0:
        return set()
    live = ds.efos_69b[ds.efos_69b["situacion"].isin(_ACTIVE_69B)]
    if len(live) == 0:
        return set()
    live_rfcs = set(live["rfc"])
    sub = ds.suppliers[ds.suppliers["rfc"].isin(live_rfcs)]
    return set(sub["supplier_id"])


def _recibida_total(ds: Dataset, supplier_ids) -> float:
    """Sum ``total`` of ``recibida`` invoices for the given supplier ids."""
    if len(ds.invoices) == 0:
        return 0.0
    ids = set(supplier_ids)
    sub = ds.invoices[ds.invoices["tipo"] == "recibida"]
    if len(ids):
        sub = sub[sub["counterparty_id"].isin(ids)]
    return float(sub["total"].sum()) if len(sub) else 0.0


def _strict_suppliers(finding: dict, ds: Dataset) -> list[str]:
    """The finding's accused ids that are actual supplier ids."""
    sup_ids = set(ds.suppliers["supplier_id"]) if len(ds.suppliers) else set()
    return [a for a in finding.get("accused", []) if a in sup_ids]


def _strict_customers(finding: dict, ds: Dataset) -> list[str]:
    """The finding's accused ids that are actual customer ids."""
    cus_ids = set(ds.customers["customer_id"]) if len(ds.customers) else set()
    return [a for a in finding.get("accused", []) if a in cus_ids]


# --- per-rule amount recomputations -----------------------------------------

def _amount_r1(finding: dict, ds: Dataset) -> float:
    """EFOS deduction: the scheme aggregate of the live 69-B suppliers.

    An EFOS finding represents the whole fake-supplier scheme, so its amount is
    the sum of every live-69-B supplier's ``recibida`` invoices (on company_42
    that is S00030 + S00020 = 2,070,600.00, matching the reference case file and
    the scorer's scheme total). Per-entity subtotals get rejected by the guard,
    which is the point: the loop must aggregate the full scheme.
    """
    return _recibida_total(ds, _active_69b_supplier_ids(ds))


def _amount_r2(finding: dict, ds: Dataset) -> float:
    """Kickback / related party: sum of the accused supplier's ``recibida`` totals."""
    return _recibida_total(ds, _strict_suppliers(finding, ds))


def _amount_r3(finding: dict, ds: Dataset) -> float:
    """Round trip: sum of ``total`` of ``emitida`` invoices to the accused customer."""
    if len(ds.invoices) == 0:
        return 0.0
    cust = _strict_customers(finding, ds)
    sub = ds.invoices[ds.invoices["tipo"] == "emitida"]
    if len(cust):
        sub = sub[sub["counterparty_id"].isin(cust)]
    return float(sub["total"].sum()) if len(sub) else 0.0


def _amount_r4(finding: dict, ds: Dataset) -> float:
    """Duplicate payment: sum of the second-and-later payments per paid invoice.

    For each ``recibida`` invoice of the accused supplier that was paid more
    than once, add every payment after the earliest. On company_42 this is the
    scheme total 484,288.28.
    """
    sup = _strict_suppliers(finding, ds)
    if not sup or len(ds.invoices) == 0 or len(ds.bank_transactions) == 0:
        return 0.0
    invs = ds.invoices[ds.invoices["tipo"] == "recibida"]
    invs = invs[invs["counterparty_id"].isin(sup)]
    inv_uuids = set(invs["uuid"])
    if not inv_uuids:
        return 0.0
    out = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out")
        & (ds.bank_transactions["invoice_uuid"].isin(inv_uuids))
    ]
    if len(out) == 0:
        return 0.0
    total = 0.0
    for _uuid, grp in out.groupby("invoice_uuid"):
        grp = grp.sort_values(["fecha", "txn_id"])
        amounts = [float(a) for a in grp["amount"]]
        if len(amounts) >= 2:
            total += sum(amounts[1:])
    return total


def _amount_r5(finding: dict, ds: Dataset) -> float:
    """``other``: no amount recomputation; the guard only checks evidence exists."""
    return 0.0


# --- exhibit policies -------------------------------------------------------
# Which records a finding must cite for its amount to reconcile against the rule's
# counted table. The guard auto-completes a finding's evidence from these, so a model
# that cites two of five invoices but claims the full scheme total still produces a
# submission the judges' validator accepts, instead of being rejected for arithmetic
# it got right.

def _recibida_uuids(ds: Dataset, supplier_ids) -> list[str]:
    """Uuids of the ``recibida`` invoices of the given suppliers, oldest first."""
    if len(ds.invoices) == 0:
        return []
    ids = set(supplier_ids)
    sub = ds.invoices[(ds.invoices["tipo"] == "recibida") & (ds.invoices["counterparty_id"].isin(ids))]
    return list(sub.sort_values(["fecha", "uuid"])["uuid"]) if len(sub) else []


def _policy_r1(finding: dict, ds: Dataset) -> list[str]:
    """EFOS: every purchase invoice of every live-69-B supplier (the scheme aggregate)."""
    return _recibida_uuids(ds, _active_69b_supplier_ids(ds))


def _policy_r2(finding: dict, ds: Dataset) -> list[str]:
    """Kickback: the accused supplier's purchase invoices."""
    return _recibida_uuids(ds, _strict_suppliers(finding, ds))


def _policy_r3(finding: dict, ds: Dataset) -> list[str]:
    """Round trip: the sales invoices to the accused customer.

    The claim is the revenue that came back, so citing the purchase side as well would
    read to the judges' validator as double the money. The purchase leg still appears in
    the money trail as bank rows, which sum into a different table.
    """
    if len(ds.invoices) == 0:
        return []
    cust = set(_strict_customers(finding, ds))
    sub = ds.invoices[ds.invoices["tipo"] == "emitida"]
    if cust:
        sub = sub[sub["counterparty_id"].isin(cust)]
    return list(sub.sort_values(["fecha", "uuid"])["uuid"]) if len(sub) else []


def _policy_r4(finding: dict, ds: Dataset) -> list[str]:
    """Duplicate payment: the second-and-later payment of each doubly-paid invoice.

    The loss is the repeat payments, not the invoices, so this rule counts bank rows.
    """
    sup = _strict_suppliers(finding, ds)
    if not sup or len(ds.invoices) == 0 or len(ds.bank_transactions) == 0:
        return []
    invs = ds.invoices[(ds.invoices["tipo"] == "recibida") & (ds.invoices["counterparty_id"].isin(sup))]
    inv_uuids = set(invs["uuid"])
    if not inv_uuids:
        return []
    out = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out")
        & (ds.bank_transactions["invoice_uuid"].isin(inv_uuids))
    ]
    extra: list[str] = []
    for _uuid, grp in out.groupby("invoice_uuid"):
        grp = grp.sort_values(["fecha", "txn_id"])
        if len(grp) >= 2:
            extra.extend(str(t) for t in grp["txn_id"].tolist()[1:])
    return sorted(extra)


def _threshold_clusters_for(ds: Dataset, supplier_ids) -> list[dict]:
    """The threshold-splitting clusters of the given supplier ids, via the detector.

    The amount and exhibit policy must agree with what the detector actually finds, so
    both are computed by re-running it (pure, deterministic) and filtering to the
    accused suppliers — never by re-deriving the clustering here.
    """
    from agent.detectors.threshold_splitting import detect_threshold_splitting

    acc = set(supplier_ids)
    return [r for r in detect_threshold_splitting(ds) if str(r["entity_id"]) in acc]


def _amount_r6(finding: dict, ds: Dataset) -> float:
    """Threshold splitting: sum of the clustered invoices' totals of the accused supplier.

    The whole point of the scheme is that the purchases are real *in aggregate* — a vendor
    whose invoices are split just under an approval limit so no single approver sees the
    total. The fraud is against the company's control, so the amount is the aggregate of
    the clustered invoices, not one split.
    """
    rows = _threshold_clusters_for(ds, _strict_suppliers(finding, ds))
    if not rows:
        return 0.0
    return round(sum(float(r["cluster_total_mxn"]) for r in rows), 2)


def _policy_r6(finding: dict, ds: Dataset) -> list[str]:
    """The clustered invoices' uuids — the records this rule's pesos are counted in."""
    rows = _threshold_clusters_for(ds, _strict_suppliers(finding, ds))
    uuids: list[str] = []
    for r in rows:
        uuids.extend(str(u) for u in r["invoice_uuids"])
    return list(dict.fromkeys(uuids))


def _revenue_rows_for(ds: Dataset, customer_ids) -> list[dict]:
    """The revenue-inflation detector rows of the given customers.

    The amount and exhibit policy must agree with what the detector actually
    finds, so both are computed by re-running it (pure, deterministic) and
    filtering to the accused customers — never by re-deriving the flagging here.
    """
    from agent.detectors.revenue_inflation import detect_revenue_inflation

    acc = set(customer_ids)
    return [r for r in detect_revenue_inflation(ds) if str(r["entity_id"]) in acc]


def _amount_r7(finding: dict, ds: Dataset) -> float:
    """Revenue inflation: sum of the flagged (booked, never-collected) invoice totals.

    The ``total_mxn`` a detector row carries is the sum of *that customer's*
    flagged invoices, so the scheme aggregate is the sum across the accused
    customers. The claim is the revenue that never arrived, not the whole sales
    book: unbooked, collected sales are not part of it.
    """
    rows = _revenue_rows_for(ds, _strict_customers(finding, ds))
    if not rows:
        return 0.0
    return round(sum(float(r["total_mxn"]) for r in rows), 2)


def _policy_r7(finding: dict, ds: Dataset) -> list[str]:
    """The flagged invoices' uuids — the records this rule's pesos are counted in."""
    rows = _revenue_rows_for(ds, _strict_customers(finding, ds))
    uuids: list[str] = []
    for r in rows:
        uuids.extend(str(u) for u in r["evidence"])
    return list(dict.fromkeys(uuids))


def _policy_none(finding: dict, ds: Dataset) -> list[str]:
    return []


@dataclass(frozen=True)
class Rule:
    """One rule in the recognised catalog."""

    id: str
    scheme_types: frozenset[str]
    legal: str
    evidence_kinds: frozenset[str]
    amount: Callable[[dict, Dataset], float]
    # The judges' table this rule's peso figure is counted in. Their validator sums
    # cited exhibits per table and compares the closest one, so a rule has to declare
    # which table carries its money or an unrelated table could reconcile by accident.
    counted_table: str = "invoices"
    # The records that must be cited for the amount to reconcile; see the policies above.
    exhibit_policy: Callable[[dict, Dataset], list[str]] = _policy_none

    def recompute_amount(self, finding: dict, ds: Dataset) -> float:
        """Return the amount the finding *should* carry for its accused set."""
        return self.amount(finding, ds)

    def required_exhibits(self, finding: dict, ds: Dataset) -> list[str]:
        """Record ids the finding must cite for its amount to reconcile."""
        return self.exhibit_policy(finding, ds)


# --- the catalog -------------------------------------------------------------
# ``legal`` values are copied verbatim from the reference case file; a finding's
# ``rule`` is accepted if it is one of these strings or the corresponding id.

RULES: dict[str, Rule] = {
    "R1": Rule(
        id="R1",
        scheme_types=frozenset({"efos_fake_supplier"}),
        legal="CFF Art. 69-B (operaciones inexistentes); CFF Art. 29-A; LISR Art. 27 (deducción improcedente)",
        evidence_kinds=frozenset({"invoice", "txn"}),
        amount=_amount_r1,
        counted_table="invoices",
        exhibit_policy=_policy_r1,
    ),
    "R2": Rule(
        id="R2",
        scheme_types=frozenset({"kickback_shell"}),
        legal="CFF Art. 69-B; LISR Art. 27-I (no estrictamente indispensable); conflict of interest / Ley General de Responsabilidades (private-sector bribery analog, Art. 7 fracc. IX of LFPIORPI where applicable)",
        evidence_kinds=frozenset({"invoice", "txn", "cp"}),
        amount=_amount_r2,
        counted_table="invoices",
        exhibit_policy=_policy_r2,
    ),
    "R3": Rule(
        id="R3",
        scheme_types=frozenset({"round_trip_sales"}),
        legal="Simulación de operaciones (CFF Art. 69-B / 113 Bis); revenue recognition — fictitious sales",
        evidence_kinds=frozenset({"invoice", "txn", "cp"}),
        amount=_amount_r3,
        counted_table="invoices",
        exhibit_policy=_policy_r3,
    ),
    "R4": Rule(
        id="R4",
        scheme_types=frozenset({"duplicate_invoice_payment"}),
        legal="Control failure / possible embezzlement; LISR Art. 27 (deducción duplicada)",
        evidence_kinds=frozenset({"invoice", "txn"}),
        amount=_amount_r4,
        counted_table="bank_txns",
        exhibit_policy=_policy_r4,
    ),
    "R5": Rule(
        id="R5",
        scheme_types=frozenset({"other"}),
        legal="N/A",
        evidence_kinds=frozenset(),
        amount=_amount_r5,
        counted_table="",
        exhibit_policy=_policy_none,
    ),
    "R6": Rule(
        id="R6",
        scheme_types=frozenset({"threshold_splitting"}),
        legal="Fraccionamiento de operaciones para evadir niveles de autorización; LGRA / política interna de compras; CFF Art. 83 (comprobantes) — approval-limit circumvention",
        evidence_kinds=frozenset({"invoice", "txn", "receipt"}),
        amount=_amount_r6,
        counted_table="invoices",
        exhibit_policy=_policy_r6,
    ),
    "R7": Rule(
        id="R7",
        scheme_types=frozenset({"revenue_inflation"}),
        legal="Ingresos simulados / reconocimiento indebido de ingresos; CFF Art. 69-B / 113 Bis; NIF D-1 (ingresos)",
        evidence_kinds=frozenset({"invoice"}),
        amount=_amount_r7,
        counted_table="invoices",
        exhibit_policy=_policy_r7,
    ),
}

# Map a rule's legal string back to its id, so the guard can recognise either.
LEGAL_TO_ID: dict[str, str] = {r.legal: rid for rid, r in RULES.items()}
