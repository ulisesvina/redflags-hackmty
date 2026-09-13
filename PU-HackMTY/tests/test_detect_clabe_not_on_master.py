"""Tests for detect_clabe_not_on_master (issue #8).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.clabe_mismatch import detect_clabe_not_on_master


def test_counts_match_ground_truth(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_clabe_not_on_master(ds)
    assert len(result) == 3 == len(ent["payments"])


def test_txn_ids_are_the_duplicate_payments(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_clabe_not_on_master(ds)
    assert {r["txn_id"] for r in result} == {
        p["duplicate_txn"] for p in ent["payments"]
    }
    # the original (correct) payments to the master CLABE must NOT appear
    assert not any(r["txn_id"] == p["original_txn"] for r in result for p in ent["payments"])


def test_paid_clabe_is_alternate_and_entity_correct(ds, scheme):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    result = detect_clabe_not_on_master(ds)
    assert all(r["paid_clabe"] == ent["alternate_clabe"] for r in result)
    assert all(r["entity_id"] == ent["supplier_id"] for r in result)
    assert all(r["master_clabe"] != ent["alternate_clabe"] for r in result)


def test_clabes_are_18_digit_strings(ds):
    result = detect_clabe_not_on_master(ds)
    for r in result:
        assert len(r["paid_clabe"]) == 18 and r["paid_clabe"].isdigit()
        assert len(r["master_clabe"]) == 18 and r["master_clabe"].isdigit()


def test_only_supplier_s00017_and_no_decoys(ds, decoy_ids):
    result = detect_clabe_not_on_master(ds)
    assert all(r["entity_id"] == "S00017" for r in result)
    assert not any(r["entity_id"] in decoy_ids for r in result)


def test_well_formed_leads_and_serializable(ds):
    result = detect_clabe_not_on_master(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["txn_id"] in record_ids
        assert r["invoice_uuid"] in record_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["amount_mxn"], float)
        assert isinstance(r["fecha"], str)
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_clabe_not_on_master(ds)
    assert result == sorted(result, key=lambda r: r["txn_id"])
