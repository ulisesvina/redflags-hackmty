"""Tests for detect_fast_pay_no_deliverable (issue #10).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.fast_pay import detect_fast_pay_no_deliverable


def _law_firm(truth: dict) -> dict:
    return next(d for d in truth["decoys"] if d["looks_like"].startswith("Large one-off"))


def test_expected_entities_only(ds, scheme, truth):
    expected = (
        {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}
        | {
            scheme("kickback_shell")["entities"][0]["supplier_id"],
            scheme("round_trip_sales")["entities"][0]["supplier_id"],
            _law_firm(truth)["supplier_id"],
        }
    )
    result = detect_fast_pay_no_deliverable(ds)
    assert {r["entity_id"] for r in result} == expected


def test_rows_per_supplier(ds, scheme, truth):
    result = detect_fast_pay_no_deliverable(ds)
    counts: dict[str, int] = {}
    for r in result:
        counts[r["entity_id"]] = counts.get(r["entity_id"], 0) + 1
    for e in scheme("efos_fake_supplier")["entities"]:
        assert counts[e["supplier_id"]] == len(e["invoice_uuids"])
    shell = scheme("kickback_shell")["entities"][0]
    assert counts[shell["supplier_id"]] == len(shell["invoice_uuids"])
    rt = scheme("round_trip_sales")["entities"][0]
    assert counts[rt["supplier_id"]] == len(rt["legs"])
    law_firm = _law_firm(truth)
    assert counts[law_firm["supplier_id"]] == 1
    row = next(r for r in result if r["entity_id"] == law_firm["supplier_id"])
    assert row["invoice_uuid"] == law_firm["invoice_uuid"]


def test_days_in_range_and_no_other_decoys(ds, truth):
    result = detect_fast_pay_no_deliverable(ds)
    for r in result:
        assert 0 <= r["days_to_pay"] <= 10
    excluded = {
        d["supplier_id"]
        for d in truth["decoys"]
        if not d["looks_like"].startswith("Large one-off")
    }
    assert not any(r["entity_id"] in excluded for r in result)


def test_zero_max_days_empty(ds):
    assert detect_fast_pay_no_deliverable(ds, max_days=0) == []


def test_every_row_is_a_well_formed_lead(ds):
    result = detect_fast_pay_no_deliverable(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["invoice_uuid"] in record_ids
        assert r["txn_id"] in record_ids
        assert r["evidence"] == [r["invoice_uuid"], r["txn_id"]]
        assert all(e in record_ids for e in r["evidence"])
        assert isinstance(r["total_mxn"], float)
        assert isinstance(r["days_to_pay"], int)
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_fast_pay_no_deliverable(ds)
    assert result == sorted(
        result, key=lambda r: (r["entity_id"], r["fecha_invoice"], r["invoice_uuid"])
    )
