"""Tests for detect_duplicate_payments (issue #6).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.duplicate_payments import detect_duplicate_payments


def test_counts_match_ground_truth(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_duplicate_payments(ds)
    assert len(result) == 3 == len(ent["payments"])


def test_same_invoice_uuids(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_duplicate_payments(ds)
    assert {r["invoice_uuid"] for r in result} == {
        p["invoice_uuid"] for p in ent["payments"]
    }


def test_each_row_matches_scheme_payments(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = {r["invoice_uuid"]: r for r in detect_duplicate_payments(ds)}
    for p in ent["payments"]:
        r = result[p["invoice_uuid"]]
        assert set(r["txn_ids"]) == {p["original_txn"], p["duplicate_txn"]}
        assert r["entity_id"] == ent["supplier_id"]
        assert r["n_payments"] == 2
        assert abs(r["overpaid_mxn"] - r["invoice_total_mxn"]) < 0.01


def test_no_other_entity_and_no_decoys(ds, scheme, decoy_ids):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_duplicate_payments(ds)
    assert all(r["entity_id"] == ent["supplier_id"] for r in result)
    assert not any(r["entity_id"] in decoy_ids for r in result)


def test_well_formed_leads_and_serializable(ds):
    result = detect_duplicate_payments(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["invoice_total_mxn"], float)
        assert isinstance(r["overpaid_mxn"], float)
        assert all(isinstance(a, float) for a in r["amounts"])
        assert r["n_payments"] >= 2
        assert abs(sum(r["amounts"]) - r["invoice_total_mxn"] - r["overpaid_mxn"]) < 0.01
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_duplicate_payments(ds)
    assert result == sorted(result, key=lambda r: r["invoice_uuid"])


def test_txns_and_fechas_in_same_order(ds):
    result = detect_duplicate_payments(ds)
    for r in result:
        idx = sorted(
            range(len(r["txn_ids"])), key=lambda i: (r["fechas"][i], r["txn_ids"][i])
        )
        assert idx == list(range(len(r["txn_ids"])))
