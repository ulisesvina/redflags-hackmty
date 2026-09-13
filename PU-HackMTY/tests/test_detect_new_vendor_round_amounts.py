"""Tests for detect_new_vendor_round_amounts (issue #11).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.new_vendor_round import detect_new_vendor_round_amounts


def _new_vendor_decoy(truth: dict) -> dict:
    return next(d for d in truth["decoys"] if d["looks_like"].startswith("New vendor"))


def test_expected_entities_only(ds, scheme, truth):
    expected = (
        {_new_vendor_decoy(truth)["supplier_id"]}
        | {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}
        | {
            scheme("kickback_shell")["entities"][0]["supplier_id"],
            scheme("round_trip_sales")["entities"][0]["supplier_id"],
        }
    )
    result = detect_new_vendor_round_amounts(ds)
    assert {r["entity_id"] for r in result} == expected


def test_rows_meet_constraints(ds):
    result = detect_new_vendor_round_amounts(ds)
    for r in result:
        assert r["round_share"] >= 0.6
        assert r["onboarded"] >= "2024-07-01"
        assert r["n_invoices"] >= 1
        assert isinstance(r["n_round"], int)
        assert 0 <= r["n_round"] <= r["n_invoices"]
        assert isinstance(r["round_share"], float)
        assert len(r["evidence"]) == r["n_invoices"]


def test_no_other_decoys(ds, truth):
    result = detect_new_vendor_round_amounts(ds)
    hit_ids = {r["entity_id"] for r in result}
    for d in truth["decoys"]:
        if d["looks_like"].startswith("New vendor"):
            continue
        assert d["supplier_id"] not in hit_ids


def test_zero_max_share_empty(ds):
    # A too-high threshold excludes everything; the planted suppliers all sit at 1.0.
    assert detect_new_vendor_round_amounts(ds, since="2026-01-01") == []


def test_every_row_is_a_well_formed_lead(ds):
    result = detect_new_vendor_round_amounts(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert isinstance(r["name"], str)
        assert isinstance(r["category"], str)
        assert isinstance(r["onboarded"], str)
        assert isinstance(r["first_invoice"], str)
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["total_mxn"], float)
        assert r["total_mxn"] >= 0
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_new_vendor_round_amounts(ds)
    assert result == sorted(result, key=lambda r: r["entity_id"])
