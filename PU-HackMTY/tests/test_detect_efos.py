"""Tests for detect_efos (issue #4).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.efos import detect_efos


def test_finds_both_planted_efos_suppliers(ds, scheme):
    expected = {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}
    result = detect_efos(ds)
    assert len(expected) == 2
    assert {r["entity_id"] for r in result} == expected


def test_matches_ground_truth_per_entity(ds, scheme):
    by_id = {e["supplier_id"]: e for e in scheme("efos_fake_supplier")["entities"]}
    result = detect_efos(ds)
    for r in result:
        ent = by_id[r["entity_id"]]
        assert r["rfc"] == ent["rfc"]
        assert r["situacion"] == ent["efos_status"]
        assert set(r["evidence"]) >= set(ent["invoice_uuids"]) | set(ent["bank_txn_ids"])
        assert r["n_invoices"] == len(ent["invoice_uuids"])


def test_name_twin_decoy_not_flagged(ds, decoy_ids, truth):
    # S00007 carries the name of a Definitivo 69-B entry but a different RFC.
    # Matching on name instead of RFC would accuse an honest supplier.
    twins = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith("Name almost")
    }
    assert twins
    result = detect_efos(ds)
    assert not any(r["entity_id"] in twins for r in result)
    assert not any(r["entity_id"] in decoy_ids for r in result)


def test_cleared_situaciones_excluded(ds):
    result = detect_efos(ds)
    assert result
    assert all(r["situacion"] in {"Presunto", "Definitivo"} for r in result)


def test_publication_date_does_not_filter(ds):
    # The Definitivo supplier was published 2025-11-15, after every one of its
    # invoices. The lag is the scheme; the finding still stands.
    result = detect_efos(ds)
    late = [r for r in result if r["situacion"] == "Definitivo"]
    assert len(late) == 1
    assert late[0]["fecha_publicacion"] == "2025-11-15"
    latest_invoice = max(
        ds.invoices[ds.invoices["counterparty_id"] == late[0]["entity_id"]]["fecha"]
    )
    assert str(latest_invoice.date()) < late[0]["fecha_publicacion"]


def test_well_formed_lead(ds):
    result = detect_efos(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert isinstance(r["rfc"], str)
        assert isinstance(r["name"], str)
        assert isinstance(r["fecha_publicacion"], str)
        assert isinstance(r["n_invoices"], int)
        assert isinstance(r["total_mxn"], float)
        assert r["n_invoices"] > 0
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_efos(ds)
    assert result == sorted(result, key=lambda r: r["entity_id"])
    assert detect_efos(ds) == result
