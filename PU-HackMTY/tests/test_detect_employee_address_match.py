"""Tests for detect_employee_address_match (issue #7).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.employee_address import detect_employee_address_match


def test_single_exact_hit(ds, scheme):
    ent = scheme("kickback_shell")["entities"][0]
    result = detect_employee_address_match(ds)
    assert len(result) == 1
    assert result[0]["entity_id"] == ent["supplier_id"]
    assert result[0]["employee_id"] == ent["employee_id"]
    assert result[0]["same_approver"] is True


def test_evidence_covers_ground_truth(ds, scheme):
    ent = scheme("kickback_shell")["entities"][0]
    result = detect_employee_address_match(ds)
    expected = set(ent["invoice_uuids"]) | set(ent["bank_txn_ids"])
    assert set(result[0]["evidence"]) >= expected


def test_well_formed_lead(ds):
    result = detect_employee_address_match(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["employee_id"] in entity_ids
        assert isinstance(r["same_approver"], bool)
        assert isinstance(r["n_invoices"], int)
        assert isinstance(r["total_mxn"], float)
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["street"], str)
        assert isinstance(r["city"], str)
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_employee_address_match(ds)
    assert result == sorted(result, key=lambda r: (r["entity_id"], r["employee_id"]))


def test_shared_address_decoy_not_flagged(ds, decoy_ids, truth):
    # The "Shares address" decoy is two suppliers sharing a commercial address
    # with each other; neither is an employee home, so it must not appear.
    shares = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith("Shares address")
    }
    assert shares
    result = detect_employee_address_match(ds)
    assert not any(r["entity_id"] in shares for r in result)
    assert not any(r["entity_id"] in decoy_ids for r in result)
