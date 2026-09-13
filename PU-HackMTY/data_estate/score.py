"""
Score an agent's case file (or a judges' submission.json) against hidden ground truth.

  python -m data_estate.score out/company_42 case_file.json
  python -m data_estate.score out/estate_42 submission.json

This is the harness that speaks the judges' language (#86). It accepts **both**
truth shapes and **both** output shapes:

Truth shapes
------------
* internal (legacy estates, seed generator): ``hidden/ground_truth.json`` has a
  ``meta`` key; schemes carry ``amount_mxn`` and nested ``entities`` with legacy
  ids (``S*``/``C*``/``E*``).
* judges' (``--format judges`` / #80): ``hidden/ground_truth.json`` has a
  ``company_rfc`` key; schemes carry ``peso_amount`` and prefixed entity ids
  (``RFC:...``/``EMP:...``).

Output shapes
-------------
* our internal case file (``agent/investigate.py``): ``findings[]`` with
  ``scheme_type``, ``accused``, ``amount_mxn``, ``evidence``.
* a judges' ``submission.json`` (``agent/submit.py``, #88): detect by the
  ``run_metadata`` key; ``findings[]`` with ``scheme_type``, ``entities``,
  ``peso_amount``, ``exhibits``.

Scoring (mirrors the judging criteria):
  recall_pct       share of the judges' schemes found (>=1 planted entity accused,
                   right type, peso within 25%).
  false_accusation_rate_pct  100 x (false + decoys accused) / max(1, n accused).
  peso_reconciles  every finding's peso_amount reconciles to its cited exhibits'
                   per-table sum within 2% (exactly the judges' validator's rule;
                   shared implementation in ``agent/reconcile.py``, #87).

The old fields (``results_recall``, ``found``, ``missed``, ``false_accusations``,
``decoys_accused``, ``judgment_penalty``, ``evidence_validity``,
``not_pursued_listed``) are kept for the legacy tests and ``scripts/eval_batch.py``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Internal scheme type -> the judges' enum. ``None`` means "not a judges' scheme
# type": on a judge estate a duplicate-invoice-payment goes in ``control_observations``
# and is never a finding, so it is never counted toward the judges' recall.
TO_JUDGES = {
    "efos_fake_supplier": "phantom_vendor",
    "kickback_shell": "kickback",
    "round_trip_sales": "round_tripping",
    "duplicate_invoice_payment": None,
    "threshold_splitting": "threshold_splitting",
    "revenue_inflation": "revenue_inflation",
}


def _truth(out: Path) -> dict:
    """The answer key, regardless of truth shape."""
    return json.loads((out / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))


def _dataset_path(out: Path) -> Path:
    """Resolve an estate (legacy CSV dir, judges' ``estate.db`` or judges' CSV) to
    the path ``agent.data.load`` accepts."""
    if (out / "suppliers.csv").exists():
        return out
    if (out / "estate.db").exists():
        return out / "estate.db"
    if (out / "vendors.csv").exists():
        return out
    if (out / "csv" / "vendors.csv").exists():
        return out / "csv"
    raise FileNotFoundError(
        f"{out} is not a scoreable estate: no suppliers.csv, estate.db, vendors.csv "
        f"or csv/vendors.csv"
    )


def _dataset(out: Path):
    """A ``Dataset`` for record/entity lookups. Imported lazily so the legacy
    test path that never needs it stays fast."""
    from agent.data import load as load_ds

    return load_ds(_dataset_path(out))


def _entity_keys(ds, entity_entries) -> set[str]:
    """The set of entity ids a planted scheme/decoy is known by, in **both** the
    native and the prefixed space, so a finding matches whether it cites the
    legacy id (``S00030``) or the judges' id (``RFC:IHV020423VE4``)."""
    keys: set[str] = set()
    sup_by_id = {r["supplier_id"]: r for r in ds.suppliers.to_dict("records")} if len(ds.suppliers) else {}
    cus_by_id = {r["customer_id"]: r for r in ds.customers.to_dict("records")} if len(ds.customers) else {}
    for ent in entity_entries:
        if not isinstance(ent, dict):
            # judges' shape: already a prefixed string
            keys.add(ent)
            continue
        sid = ent.get("supplier_id")
        if sid:
            keys.add(sid)
            rfc = sup_by_id.get(sid, {}).get("rfc")
            if rfc:
                keys.add("RFC:" + rfc)
        cid = ent.get("customer_id")
        if cid:
            keys.add(cid)
            rfc = cus_by_id.get(cid, {}).get("rfc")
            if rfc:
                keys.add("RFC:" + rfc)
        eid = ent.get("employee_id")
        if eid:
            keys.add(eid)
            keys.add("EMP:" + eid[1:] if eid[1:].isdigit() else eid)
    return keys


def _collect_ids(obj) -> set[str]:
    """Recursively collect the record ids (invoice uuids, TX/CP/GR ids) a scheme's
    entity structure names, however deeply nested (e.g. round-trip ``legs``)."""
    ids: set[str] = set()
    if isinstance(obj, dict):
        for value in obj.values():
            ids |= _collect_ids(value)
    elif isinstance(obj, list):
        for value in obj:
            ids |= _collect_ids(value)
    elif isinstance(obj, str):
        if (obj[:2] in ("TX", "CP", "GR") and len(obj) > 2 and obj[2:].isdigit()) or (
            len(obj) == 36 and obj.count("-") == 4
        ):
            ids.add(obj)
    return ids


def _normalize_scheme(s: dict, kind: str, ds) -> dict:
    """One scheme as a normalized dict with type (internal + judges'), entity keys,
    peso_amount and the record ids that prove it."""
    if kind == "judges":
        stype = s.get("type", "")
        internal = stype
        judges = stype
        peso = float(s.get("peso_amount", 0.0) or 0.0)
        entries = s.get("entities", [])
        invs = list(s.get("supporting_invoices", []))
        txns = list(s.get("supporting_txns", []))
        recs = set(invs) | set(txns)
    else:
        stype = s.get("type", "")
        internal = stype
        judges = TO_JUDGES.get(stype, stype)
        peso = float(s.get("amount_mxn", 0.0) or 0.0)
        entries = s.get("entities", [])
        invs, txns = [], []
        # legacy truth nests the records inside each entity dict
        for ent in entries:
            if isinstance(ent, dict):
                invs.extend(ent.get("invoice_uuids", []) or [])
                txns.extend(ent.get("bank_txn_ids", []) or [])
                txns.extend(ent.get("counterparty_record_ids", []) or [])
        recs = _collect_ids(entries)
    return {
        "internal_type": internal,
        "judges_type": judges,
        "entity_keys": _entity_keys(ds, entries),
        "peso_amount": peso,
        "supporting_invoices": list(invs),
        "supporting_txns": list(txns),
        "planted_records": recs,
    }


def _decoy_keys(truth: dict, ds) -> set[str]:
    keys: set[str] = set()
    for decoy in truth.get("decoys", []):
        if "entity" in decoy:
            keys.add(decoy["entity"])
        if "supplier_id" in decoy:
            keys.add(decoy["supplier_id"])
            rfc = decoy.get("rfc")
            if rfc:
                keys.add("RFC:" + rfc)
    return keys


# --- finding accessors (submission and legacy case file differ) --------------


def _finding_entities(f: dict) -> set[str]:
    if f.get("entities"):
        return set(f["entities"])
    return set(f.get("accused", []))


def _finding_amount(f: dict) -> float:
    value = f.get("peso_amount")
    if value is None:
        value = f.get("amount_mxn", 0.0)
    return float(value or 0.0)


def _finding_record_ids(f: dict) -> list[str]:
    if f.get("exhibits"):
        return [ex.get("record_id") for ex in f["exhibits"] if ex.get("record_id")]
    return list(f.get("evidence", []))


def _match(scheme: dict, f: dict, ds) -> bool:
    """A finding counts as *the* scheme when the type matches (judges' or internal),
    at least one accused entity is planted, and the peso is within 25%."""
    scheme_type = f.get("scheme_type") or f.get("type")
    if scheme_type != scheme["internal_type"] and scheme_type != scheme["judges_type"]:
        return False
    if not (_finding_entities(f) & scheme["entity_keys"]):
        return False
    peso = scheme["peso_amount"]
    return abs(_finding_amount(f) - peso) <= 0.25 * peso


def _planted_evidence(scheme: dict) -> set[str]:
    """The record ids the scheme is *actually* made of (for evidence validity)."""
    return set(scheme["planted_records"])


def _peso_reconciles(findings: list, ds) -> bool:
    """True when every finding's peso_amount reconciles to its cited exhibits'
    per-table sum within 2% (the judges' validator rule, #87)."""
    if not findings:
        return True
    from agent.reconcile import best_table, per_table_sums, reconciles

    for f in findings:
        claimed = _finding_amount(f)
        if claimed <= 0:
            continue  # a 0-amount finding has nothing to reconcile
        sums = per_table_sums(_finding_record_ids(f), ds)
        _table, total = best_table(sums, claimed)
        if not reconciles(total, claimed):
            return False
    return True


def _load_all_record_ids(ds) -> set[str]:
    return set(ds.all_record_ids()) if hasattr(ds, "all_record_ids") else set()


def score(out, case: dict, ds=None) -> dict:
    out = Path(out)
    truth = _truth(out)
    ds = ds or _dataset(out)
    kind = "judges" if "company_rfc" in truth else "internal"

    schemes = [_normalize_scheme(s, kind, ds) for s in truth.get("schemes", [])]
    decoy_keys = _decoy_keys(truth, ds)
    judge_schemes = [s for s in schemes if s["judges_type"] is not None]

    findings = case.get("findings", []) or []

    # --- matching: which schemes did the findings cover? ----------------------
    matched: set[int] = set()
    for f in findings:
        for i, scheme in enumerate(schemes):
            if i in matched:
                continue
            if _match(scheme, f, ds):
                matched.add(i)

    # --- legacy metrics (kept for the old tests and eval_batch) ---------------
    found = sorted(schemes[i]["internal_type"] for i in sorted(matched))
    missed = sorted(s["internal_type"] for i, s in enumerate(schemes) if i not in matched)
    n_schemes = len(schemes)
    results_recall = len(found) / n_schemes if n_schemes else 1.0

    accused = set()
    for f in findings:
        accused |= _finding_entities(f)
    planted_all = set().union(*(s["entity_keys"] for s in schemes)) if schemes else set()
    false_acc = {a for a in accused if a not in planted_all and a not in decoy_keys}
    decoy_acc = {a for a in accused if a in decoy_keys}
    judgment_penalty = len(false_acc) + 2 * len(decoy_acc)

    all_ids = _load_all_record_ids(ds)
    ev_total = ev_valid = 0
    for f in findings:
        matched_scheme = next((schemes[i] for i in sorted(matched) if _match(schemes[i], f, ds)), None)
        pe = _planted_evidence(matched_scheme) if matched_scheme else set()
        for rec in _finding_record_ids(f):
            ev_total += 1
            if rec in all_ids and (not matched_scheme or rec in pe):
                ev_valid += 1
    evidence_validity = ev_valid / ev_total if ev_total else 0.0

    # --- judges' metrics (#86) -------------------------------------------------
    judge_matched = [i for i in sorted(matched) if schemes[i]["judges_type"] is not None]
    schemes_planted = len(judge_schemes)
    schemes_found = len(judge_matched)
    recall_pct = 100.0 * schemes_found / schemes_planted if schemes_planted else 100.0

    decoys_planted = len(truth.get("decoys", []))
    n_accused = len(accused)
    false_accusation_rate_pct = 100.0 * (len(false_acc) + len(decoy_acc)) / max(1, n_accused)

    peso_claimed = sum(_finding_amount(f) for f in findings)
    peso_actual = sum(schemes[i]["peso_amount"] for i in judge_matched)
    peso_reconciles = _peso_reconciles(findings, ds)

    meta = case.get("run_metadata", {}) or {}
    llm_calls = int(meta.get("llm_calls", 0) or 0)
    mxn_cost = float(meta.get("mxn_cost", 0.0) or 0.0)
    wall_clock_s = float(meta.get("wall_clock_s") or meta.get("wall_clock_seconds", 0.0) or 0.0)

    not_pursued = case.get("not_pursued") or case.get("leads_not_pursued") or []

    return {
        # legacy fields
        "results_recall": results_recall,
        "found": found,
        "missed": missed,
        "false_accusations": sorted(false_acc),
        "decoys_accused": sorted(decoy_acc),
        "judgment_penalty": judgment_penalty,
        "evidence_validity": evidence_validity,
        "not_pursued_listed": len(not_pursued),
        # judges' metrics (the results_table columns)
        "schemes_planted": schemes_planted,
        "schemes_found": schemes_found,
        "recall_pct": recall_pct,
        "decoys_planted": decoys_planted,
        "decoys_accused_count": len(decoy_acc),
        "false_accusations_count": len(false_acc),
        "n_accused_entities": n_accused,
        "false_accusation_rate_pct": false_accusation_rate_pct,
        "peso_claimed": peso_claimed,
        "peso_actual": peso_actual,
        "peso_reconciles": peso_reconciles,
        "llm_calls": llm_calls,
        "mxn_cost": mxn_cost,
        "wall_clock_s": wall_clock_s,
    }


def main() -> None:
    out, case_path = Path(sys.argv[1]), Path(sys.argv[2])
    res = score(out, json.loads(case_path.read_text(encoding="utf-8")))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
