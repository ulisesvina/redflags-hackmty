"""Tests for detect_name_twin_69b (issue #43).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

import pytest

from agent.detectors.name_twin_69b import detect_name_twin_69b


def test_finds_exactly_the_three_name_twins(ds):
    result = detect_name_twin_69b(ds)
    assert {r["entity_id"] for r in result} == {"S00007", "S00012", "S00024"}


def test_name_twin_decoy_is_among_them(ds, truth):
    # The decoy whose name is almost identical to a live 69-B entry but with a different RFC.
    twins = {
        d["supplier_id"]
        for d in truth["decoys"]
        if d["looks_like"].startswith("Name almost")
    }
    assert twins  # the decoy exists in ground truth
    result = detect_name_twin_69b(ds)
    hits = [r for r in result if r["entity_id"] in twins]
    assert len(hits) == 1
    assert hits[0]["rfc_listed"] is False
    assert hits[0]["listed_rfc"] == "TAO890114RLQ"
    # The supplier's own RFC differs from the listed one.
    assert hits[0]["rfc"] != hits[0]["listed_rfc"]


def test_real_efos_suppliers_are_not_name_twins(ds, scheme):
    # S00020/S00030 match a 69-B entry by name too, but their RFC also matches, which is
    # detect_efos's job. This detector must not duplicate it.
    real = {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}
    result = detect_name_twin_69b(ds)
    assert not any(r["entity_id"] in real for r in result)


def test_s00007_receipt_count(ds):
    result = detect_name_twin_69b(ds)
    s07 = next(r for r in result if r["entity_id"] == "S00007")
    assert s07["n_with_receipt"] == 8
    assert s07["n_invoices"] == 8
    assert s07["total_mxn"] == pytest.approx(105356.46)


def test_decoy_has_no_evidence_for_real_efos(ds):
    result = detect_name_twin_69b(ds)
    for r in result:
        assert r["rfc_listed"] is False
        assert r["fecha_publicacion"]  # ISO string, non-empty
        assert r["evidence"] and all(e in ds.all_record_ids() for e in r["evidence"])
        assert r["n_with_receipt"] >= 0


def test_sorted_and_json(ds):
    result = detect_name_twin_69b(ds)
    assert result == sorted(result, key=lambda r: r["entity_id"])
    assert detect_name_twin_69b(ds) == result
    assert json.dumps(result)
