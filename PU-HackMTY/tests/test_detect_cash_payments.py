"""Tests for detect_cash_payments (issue #43).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

import pytest

from agent.detectors import run_all
from agent.detectors.cash_payments import DEFAULT_CAP_MXN, detect_cash_payments


def test_exactly_one_lead_is_the_cash_decoy(ds, truth):
    result = detect_cash_payments(ds)
    assert len(result) == 1
    cash_decoy = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith("Cash payments")
    }
    assert cash_decoy
    assert result[0]["entity_id"] in cash_decoy


def test_cardinality_and_amounts(ds, truth):
    result = detect_cash_payments(ds)
    r = result[0]
    assert r["n_cash_invoices"] == 3
    assert r["cash_total_mxn"] == pytest.approx(5347.97)
    assert r["max_cash_invoice_mxn"] == pytest.approx(1821.72)
    assert r["all_under_cap"] is True
    assert r["n_over_cap"] == 0
    assert len(r["evidence"]) == 6


def test_cap_crossing_when_lowered(ds):
    # With the cap at 1800 the 1821.72 invoice crosses it; with the default it does not.
    result = detect_cash_payments(ds, cap_mxn=1800.0)
    assert result[0]["n_over_cap"] == 1
    assert result[0]["all_under_cap"] is False
    # Default cap is 2000 and nothing crosses it.
    assert DEFAULT_CAP_MXN == 2000.0
    assert detect_cash_payments(ds)[0]["n_over_cap"] == 0


def test_evidence_are_real_record_ids(ds):
    result = detect_cash_payments(ds)
    record_ids = ds.all_record_ids()
    for r in result:
        assert r["entity_id"] in ds.all_entity_ids()
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
    assert json.dumps(result)


def test_sorted_and_json(ds):
    result = detect_cash_payments(ds)
    assert result == sorted(result, key=lambda r: r["entity_id"])
    assert detect_cash_payments(ds) == result
    assert json.dumps(result)


def test_every_decoy_is_now_a_lead(ds, decoy_ids):
    # Definition of done (#43): after this PR, all five decoys surface as leads somewhere in
    # run_all, so the loop can clear each one on record.
    leads = run_all(ds)
    surfaced = {r["entity_id"] for rows in leads.values() for r in rows}
    assert decoy_ids <= surfaced
