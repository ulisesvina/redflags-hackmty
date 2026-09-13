"""Tests for detect_shared_supplier_address (issue #43).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.shared_supplier_address import detect_shared_supplier_address


def test_exactly_two_leads(ds):
    result = detect_shared_supplier_address(ds)
    assert {r["entity_id"] for r in result} == {"S00024", "S00026"}
    assert len(result) == 2


def test_each_shares_with_the_other(ds):
    result = detect_shared_supplier_address(ds)
    by_id = {r["entity_id"]: r for r in result}
    assert by_id["S00024"]["shares_with"] == ["S00026"]
    assert by_id["S00026"]["shares_with"] == ["S00024"]
    assert by_id["S00024"]["employee_home_match"] is False
    assert by_id["S00026"]["employee_home_match"] is False


def test_shared_address_decoy_is_a_lead(ds, truth):
    # The decoy at the shared commercial address; it is a *lead* (the loop clears it), never an
    # accusation — but it must surface so the "why did you not accuse X" story is on record.
    shares = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith("Shares address")
    }
    assert shares
    result = detect_shared_supplier_address(ds)
    assert all(s in {r["entity_id"] for r in result} for s in shares)


def test_kickback_shell_not_a_supplier_neighbour(ds, scheme):
    # S00004 shares an address with an *employee*, not another supplier, so it belongs to
    # detect_employee_address_match (#7), not here.
    shell = {e["supplier_id"] for e in scheme("kickback_shell")["entities"]}
    assert shell
    result = detect_shared_supplier_address(ds)
    assert not any(r["entity_id"] in shell for r in result)


def test_well_formed_leads(ds):
    result = detect_shared_supplier_address(ds)
    for r in result:
        assert r["entity_id"] in ds.all_entity_ids()
        assert r["street"] and r["city"]
        assert isinstance(r["shares_with"], list) and len(r["shares_with"]) >= 1
        assert set(r["shares_with"]) <= ds.all_entity_ids()
        assert all(e in ds.all_record_ids() for e in r["evidence"])
        assert r["employee_home_match"] in (True, False)
    assert json.dumps(result)


def test_sorted_and_json(ds):
    result = detect_shared_supplier_address(ds)
    assert result == sorted(result, key=lambda r: r["entity_id"])
    assert detect_shared_supplier_address(ds) == result
    assert json.dumps(result)
