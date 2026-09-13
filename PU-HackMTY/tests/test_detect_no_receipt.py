"""Tests for detect_no_receipt (issue #5).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.no_receipt import detect_no_receipt


def test_counts_match_and_no_goods_row(ds):
    result = detect_no_receipt(ds)
    assert all(not r["receipt_required"] for r in result)
    n_recibida = int((ds.invoices["tipo"] == "recibida").sum())
    n_receipt_uuids = int(ds.goods_receipts["invoice_uuid"].nunique())
    assert len(result) == n_recibida - n_receipt_uuids


def test_every_row_is_a_well_formed_lead(ds):
    result = detect_no_receipt(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["total_mxn"], float)
        assert isinstance(r["receipt_required"], bool)
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_no_receipt(ds)
    assert result == sorted(result, key=lambda r: (r["entity_id"], r["fecha"], r["invoice_uuid"]))


def test_planted_purchases_appear(ds, scheme):
    uuids = {r["invoice_uuid"] for r in detect_no_receipt(ds)}
    for ent in scheme("efos_fake_supplier")["entities"]:
        assert set(ent["invoice_uuids"]) <= uuids
    shell = scheme("kickback_shell")["entities"][0]
    assert set(shell["invoice_uuids"]) <= uuids
    legs = scheme("round_trip_sales")["entities"][0]["legs"]
    assert {leg["purchase_invoice"] for leg in legs} <= uuids


def test_law_firm_decoy_is_an_expected_lead(ds, truth):
    law_firm = next(d for d in truth["decoys"] if d["looks_like"].startswith("Large one-off"))
    row = next(
        r for r in detect_no_receipt(ds) if r["invoice_uuid"] == law_firm["invoice_uuid"]
    )
    assert row["entity_id"] == law_firm["supplier_id"]
    assert row["category"] == "servicios"
    assert not row["receipt_required"]


def test_other_decoys_not_flagged(ds, truth):
    excluded = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith(("New vendor", "Shares address", "Cash payments"))
    }
    assert not any(r["entity_id"] in excluded for r in detect_no_receipt(ds))
