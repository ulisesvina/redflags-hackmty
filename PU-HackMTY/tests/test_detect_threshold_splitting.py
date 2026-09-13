"""Tests for detect_threshold_splitting (issue #82).

Tests may read ``hidden/``; under ``agent/`` nothing may. Here the ground truth comes
from the generator's in-memory ``truth`` (a test may read it), not ``hidden/``.
"""
from __future__ import annotations

from agent.data import load
from agent.detectors.threshold_splitting import detect_threshold_splitting
from agent.guard import guard
from data_estate.generate import Generator, write_estate


def _load_seed(tmp_path, seed=7):
    """Generate a legacy seed with only the threshold scheme, write it, load it."""
    estate = Generator(seed).build(["threshold"])
    out = tmp_path / f"t{seed}"
    write_estate(estate, out)
    return estate, load(out)


def _scheme(estate, scheme_type):
    return next(s for s in estate.truth["schemes"] if s["type"] == scheme_type)


def test_finds_the_planted_clusters(tmp_path):
    estate, ds = _load_seed(tmp_path)
    ent = _scheme(estate, "threshold_splitting")["entities"][0]
    result = detect_threshold_splitting(ds)
    assert result
    assert len(result) == len(ent["clusters"]) == 3
    # The only supplier flagged is the planted one.
    assert {r["entity_id"] for r in result} == {ent["supplier_id"]}
    # The union of the cluster invoice uuids is exactly the scheme's invoices.
    uuids = {u for r in result for u in r["invoice_uuids"]}
    assert uuids == set(ent["invoice_uuids"])


def test_cluster_shape_and_approver(tmp_path):
    estate, ds = _load_seed(tmp_path)
    ent = _scheme(estate, "threshold_splitting")["entities"][0]
    result = detect_threshold_splitting(ds)
    for r in result:
        assert r["approver_id"] == ent["employee_id"]
        assert r["approver_role"] == "Gerente de Compras"
        assert r["limit"] == ent["approval_limit"] == 250_000.0
        assert r["n_invoices"] >= 3
        # every invoice sits in [0.80, 1.0) x limit; the cluster clears the gate
        assert r["cluster_subtotal"] < r["limit"] * 4  # sanity: not one giant invoice
        assert r["cluster_subtotal"] >= r["limit"]


def test_d7_and_baseline_never_fire(tmp_path):
    estate, ds = _load_seed(tmp_path)
    result = detect_threshold_splitting(ds)
    # The D7 fixed-fee decoy (12 equal monthly invoices just under the limit) and the
    # other decoys must never look like a cluster.
    decoy_ids = {d.get("supplier_id") for d in estate.truth["decoys"]}
    assert all(r["entity_id"] not in decoy_ids for r in result)
    # A cluster needs >= min_cluster invoices in the window; requiring more finds nothing.
    assert detect_threshold_splitting(ds, min_cluster=99) == []


def test_evidence_is_valid_record_ids(tmp_path):
    estate, ds = _load_seed(tmp_path)
    result = detect_threshold_splitting(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["approver_id"] in entity_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert all(u in record_ids for u in r["invoice_uuids"])
        assert isinstance(r["limit"], float)
        assert isinstance(r["n_invoices"], int)


def test_sorted_deterministically(tmp_path):
    estate, ds = _load_seed(tmp_path)
    result = detect_threshold_splitting(ds)
    assert result == sorted(result, key=lambda r: (r["entity_id"], r["first_date"]))


def test_guard_accepts_threshold_finding(tmp_path):
    estate, ds = _load_seed(tmp_path)
    scheme = _scheme(estate, "threshold_splitting")
    ent = scheme["entities"][0]
    result = detect_threshold_splitting(ds)
    uuids = [u for r in result for u in r["invoice_uuids"]]
    paid = ds.bank_transactions[
        (ds.bank_transactions["direction"] == "out")
        & (ds.bank_transactions["invoice_uuid"].isin(uuids))
    ]
    evidence = uuids + [str(t) for t in paid["txn_id"]]
    finding = {
        "scheme_type": "threshold_splitting",
        "accused": [ent["supplier_id"], ent["employee_id"]],
        "rule": "R6",
        "amount_mxn": scheme["amount_mxn"],
        "evidence": evidence,
    }
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert clean["amount_mxn"] == scheme["amount_mxn"]


def test_no_baseline_supplier_on_seeds_8_and_9(tmp_path):
    """The detector must not fire on an honest supplier on neighbouring seeds."""
    for seed in (8, 9):
        estate, ds = _load_seed(tmp_path, seed=seed)
        ent = _scheme(estate, "threshold_splitting")["entities"][0]
        result = detect_threshold_splitting(ds)
        assert {r["entity_id"] for r in result} == {ent["supplier_id"]}
