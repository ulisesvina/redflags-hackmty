"""Lead aggregation and ranking (#44).

Turns the flat ``{detector_name: [lead dicts]}`` map from
:func:`agent.detectors.run_all` into one *dossier* per entity, ranked by how
strong the evidence is. That dossier list is the agent's docket: which
entities get investigated, in what order, and with what starting hypothesis.

It is pure pandas over the Dataset (no I/O, no LLM), which also makes it the
deterministic core of the ``--no-llm`` fallback — on stage, if the model
cluster is down, ``aggregate`` + ``scheme_hint`` must produce the same scores.

A lead is a *lead*, not an accusation. This module only groups and ranks; it
never says anyone did anything wrong. The evidence guard (#14) and the
investigation loop (#13) make that call.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any

# Scheme-defining detectors (same list as #29); everything else is a weak signal.
STRONG: frozenset[str] = frozenset(
    {
        "detect_efos",
        "detect_employee_address_match",
        "detect_kickback_outflow",
        "detect_round_trip",
        "detect_duplicate_payments",
        "detect_clabe_not_on_master",
        "detect_threshold_splitting",
        "detect_revenue_inflation",
    }
)

# Signatures are checked in order; every signature whose detector set is a subset
# of the entity's detectors fires (an entity may sit in two schemes, "entangled"),
# and the docket carries *all* of them. ``scheme_hint`` is kept as the first one
# for compatibility.
SIGNATURES: list[tuple[frozenset[str], str]] = [
    (frozenset({"detect_efos"}), "efos_fake_supplier"),
    # On judge estates employees have no address, so a kickback is proven by the
    # supplier's own statement outflow to an employee personal CLABE alone;
    # a shared address is corroboration, not a requirement.
    (frozenset({"detect_kickback_outflow"}), "kickback_shell"),
    (frozenset({"detect_round_trip"}), "round_trip_sales"),
    (frozenset({"detect_duplicate_payments", "detect_clabe_not_on_master"}), "duplicate_invoice_payment"),
    (frozenset({"detect_threshold_splitting"}), "threshold_splitting"),
    (frozenset({"detect_revenue_inflation"}), "revenue_inflation"),
]


def scheme_hints(detectors: set[str]) -> list[str]:
    """Return every scheme type whose full signature fires on ``detectors``, in SIGNATURES order."""
    d = set(detectors)
    return [name for signature, name in SIGNATURES if signature <= d]


def scheme_hint(detectors: set[str]) -> str:
    """Return the first scheme type whose full signature fires, else an empty string."""
    hints = scheme_hints(detectors)
    return hints[0] if hints else ""


def _kind(entity_id: str) -> str:
    if entity_id.startswith("S"):
        return "supplier"
    if entity_id.startswith("C"):
        return "customer"
    if entity_id.startswith("E"):
        return "employee"
    return ""


def _names(ds) -> dict[str, str]:
    """entity_id -> name across the three master tables."""
    names: dict[str, str] = {}
    for table, id_col in (
        ("suppliers", "supplier_id"),
        ("customers", "customer_id"),
        ("employees", "employee_id"),
    ):
        df = getattr(ds, table)
        names.update({str(k): str(v) for k, v in zip(df[id_col], df["name"])})
    return names


def _total_mxn(ds, entity_id: str) -> float:
    """Money the entity moved through us: suppliers on recibida, customers on emitida, else 0.0."""
    kind = _kind(entity_id)
    inv = ds.invoices
    if kind == "supplier":
        rows = inv[(inv["tipo"] == "recibida") & (inv["counterparty_id"] == entity_id)]
    elif kind == "customer":
        rows = inv[(inv["tipo"] == "emitida") & (inv["counterparty_id"] == entity_id)]
    else:
        return 0.0
    return round(float(rows["total"].sum()), 2)


def aggregate(ds, leads: dict[str, list[dict]] | None = None) -> list[dict]:
    """One dossier per entity with >=1 lead, ranked strongest-first.

    ``leads`` defaults to :func:`agent.detectors.run_all(ds)`. Unknown detector
    names in ``leads`` are accepted (they are simply not strong). A lead with
    ``entity_id == ""`` is skipped (it is an orphan lead, counted by the CLI).
    """
    if leads is None:
        from agent.detectors import run_all

        leads = run_all(ds)

    names = _names(ds)

    # entity_id -> detector -> [lead dicts, unchanged]
    by_entity: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for det, rows in leads.items():
        for lead in rows:
            eid = str(lead.get("entity_id", ""))
            if eid == "":
                continue
            by_entity[eid][det].append(lead)

    dossiers: list[dict[str, Any]] = []
    for eid, det_leads in by_entity.items():
        detectors = sorted(det_leads.keys())

        related: set[str] = set()
        evidence: set[str] = set()
        for rows in det_leads.values():
            for lead in rows:
                for field in ("employee_id", "customer_id"):
                    v = lead.get(field)
                    if v not in (None, ""):
                        sv = str(v)
                        if sv != eid:
                            related.add(sv)
                evidence.update(str(e) for e in lead.get("evidence", []))

        _hints = scheme_hints(set(detectors))
        dossiers.append(
            {
                "entity_id": eid,
                "kind": _kind(eid),
                "name": names.get(eid, ""),
                "detectors": detectors,
                "n_detectors": len(detectors),
                "n_strong": len(set(detectors) & STRONG),
                "n_leads": sum(len(rows) for rows in det_leads.values()),
                "total_mxn": _total_mxn(ds, eid),
                "evidence": sorted(evidence),
                "n_evidence": len(evidence),
                "related": sorted(related),
                "scheme_hints": _hints,
                "scheme_hint": _hints[0] if _hints else "",
                "leads": dict(det_leads),
            }
        )

    # Strong evidence first, then breadth, then money; never by n_leads (the
    # no-receipt detector emits one row per invoice and would swamp everything).
    dossiers.sort(key=lambda d: (-d["n_strong"], -d["n_detectors"], -d["total_mxn"], d["entity_id"]))
    for i, d in enumerate(dossiers, 1):
        d["rank"] = i
    return dossiers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agent.leads")
    parser.add_argument("dataset_dir")
    parser.add_argument("--json", action="store_true", help="print the dossier list as JSON")
    parser.add_argument("--top", type=int, default=None, help="limit printed entity rows to N")
    args = parser.parse_args(argv)

    from agent.data import load
    from agent.detectors import DETECTORS, run_all

    ds = load(args.dataset_dir)
    all_leads = run_all(ds)
    dossiers = aggregate(ds, all_leads)

    total_leads = sum(len(rows) for rows in all_leads.values())
    orphan_leads = sum(
        1 for rows in all_leads.values() for lead in rows if str(lead.get("entity_id", "")) == ""
    )

    if args.json:
        print(json.dumps(dossiers))
        return 0

    top = args.top if args.top is not None and args.top > 0 else len(dossiers)
    for d in dossiers[:top]:
        print(
            f"{d['rank']} {d['entity_id']} {d['kind']} "
            f"{d['n_strong']}/{d['n_detectors']} {d['total_mxn']:,.2f} "
            f"{d['scheme_hint']} {','.join(d['detectors'])}"
        )

    print(
        f"entities={len(dossiers)} leads={total_leads} "
        f"orphan_leads={orphan_leads} detectors={len(DETECTORS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
