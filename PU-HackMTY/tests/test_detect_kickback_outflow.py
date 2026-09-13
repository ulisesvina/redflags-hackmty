"""Tests for detect_kickback_outflow (issue #42).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from agent.detectors.kickback_outflow import detect_kickback_outflow


def test_single_exact_hit(ds, scheme):
    ent = scheme("kickback_shell")["entities"][0]
    result = detect_kickback_outflow(ds)
    assert len(result) == 1
    assert result[0]["entity_id"] == ent["supplier_id"]
    assert result[0]["employee_id"] == ent["employee_id"]


def test_evidence_matches_ground_truth_cp_ids(ds, scheme):
    ent = scheme("kickback_shell")["entities"][0]
    result = detect_kickback_outflow(ds)
    assert set(result[0]["evidence"]) == set(ent["counterparty_record_ids"])
    assert len(result[0]["evidence"]) == 8


def test_key_fields(ds, scheme):
    result = detect_kickback_outflow(ds)
    lead = result[0]
    assert lead["same_approver"] is True
    assert lead["n_outflows"] == 8
    assert lead["outflow_total_mxn"] == pytest.approx(230144.0)
    assert lead["outflow_ratio"] == pytest.approx(0.4)
    assert lead["supplier_invoice_total_mxn"] == pytest.approx(575360.0)
    assert lead["first_outflow"] <= lead["last_outflow"]


def test_well_formed_lead(ds):
    result = detect_kickback_outflow(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["employee_id"] in entity_ids
        assert isinstance(r["same_approver"], bool)
        assert isinstance(r["n_outflows"], int)
        assert isinstance(r["outflow_total_mxn"], float)
        assert isinstance(r["outflow_ratio"], float)
        assert isinstance(r["employee_role"], str)
        assert isinstance(r["supplier_name"], str)
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        for e in r["evidence"]:
            assert e.startswith("CP")
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_kickback_outflow(ds)
    assert result == sorted(result, key=lambda r: (r["entity_id"], r["employee_id"]))


def test_no_decoy_flags(ds, decoy_ids):
    result = detect_kickback_outflow(ds)
    assert not any(r["entity_id"] in decoy_ids for r in result)


def test_round_trip_outflow_to_customer_not_flagged(ds, scheme):
    # S00021's outflows leave to a customer CLABE, never an employee: zero leads from it.
    rt = scheme("round_trip_sales")["entities"]
    rt_suppliers = {e["supplier_id"] for e in rt}
    result = detect_kickback_outflow(ds)
    assert not any(r["entity_id"] in rt_suppliers for r in result)


def test_negative_direction_in(ds):
    # Only "in" rows remain: nothing can land on an employee personal account.
    neg = ds.counterparty_bank[ds.counterparty_bank["direction"] == "in"]
    swapped = dataclasses.replace(ds, counterparty_bank=neg)
    assert detect_kickback_outflow(swapped) == []


def test_approver_link_and_same_bank_only_84(ds):
    """#84 judge-shape fields: approver_link is set (approver == payee) and a real
    transfer exists, so same_bank_only is False (never the weak same-institution
    decoy pattern — that needs no transfer)."""
    result = detect_kickback_outflow(ds)
    assert len(result) == 1
    lead = result[0]
    assert lead["approver_link"] is True
    assert lead["same_bank_only"] is False
    assert lead["approver_link"] == lead["same_approver"]
