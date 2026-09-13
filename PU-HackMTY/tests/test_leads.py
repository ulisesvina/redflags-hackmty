"""Tests for agent/leads.py (issue #44).

Tests may read hidden/ground_truth.json via the fixtures; agent/ code may not.
"""
from __future__ import annotations

import json


def _by_id(dossiers):
    return {d["entity_id"]: d for d in dossiers}


def test_top5_ranking_and_rank_field(ds):
    from agent.leads import aggregate

    d = aggregate(ds)
    assert [x["entity_id"] for x in d[:5]] == ["S00004", "S00017", "S00021", "S00030", "S00020"]
    assert [x["rank"] for x in d] == list(range(1, len(d) + 1))


def test_planted_outrank_and_strong(ds, truth, decoy_ids):
    from agent.leads import aggregate

    d = aggregate(ds)
    by_id = _by_id(d)
    planted = {e["supplier_id"] for s in truth["schemes"] for e in s["entities"]}
    assert planted
    for pid in planted:
        assert by_id[pid]["n_strong"] >= 1
    for dcid in decoy_ids:
        assert by_id[dcid]["n_strong"] == 0
        assert by_id[dcid]["scheme_hint"] == ""
    max_planted_rank = max(by_id[pid]["rank"] for pid in planted)
    min_decoy_rank = min(by_id[dcid]["rank"] for dcid in decoy_ids)
    assert max_planted_rank < min_decoy_rank


def test_scheme_hint_matches_ground_truth(ds, truth):
    from agent.leads import aggregate

    by_id = _by_id(aggregate(ds))
    for scheme in truth["schemes"]:
        for entity in scheme["entities"]:
            assert by_id[entity["supplier_id"]]["scheme_hint"] == scheme["type"]


def test_s00004_shell_details(ds):
    from agent.leads import aggregate

    by_id = _by_id(aggregate(ds))
    s4 = by_id["S00004"]
    assert s4["scheme_hint"] == "kickback_shell"
    assert s4["related"] == ["E00002"]


def test_s00004_evidence_covers_truth(ds, scheme):
    from agent.leads import aggregate

    by_id = _by_id(aggregate(ds))
    s4 = by_id["S00004"]
    entity = scheme("kickback_shell")["entities"][0]
    truth_ids = set(entity["invoice_uuids"]) | set(entity["bank_txn_ids"]) | set(
        entity["counterparty_record_ids"]
    )
    assert s4["n_evidence"] == 24
    assert set(s4["evidence"]) >= truth_ids


def test_scheme_hint_function():
    from agent.leads import scheme_hint

    assert scheme_hint({"detect_efos", "detect_no_receipt"}) == "efos_fake_supplier"
    assert scheme_hint({"detect_employee_address_match"}) == ""
    assert scheme_hint(set()) == ""


def test_scheme_hints_list_detectors_84():
    # #84: scheme_hints returns every matching signature in SIGNATURES order;
    # scheme_hint stays the first for compatibility.
    from agent.leads import scheme_hint, scheme_hints

    # kickback fires on the outflow detector alone now (no address needed).
    assert scheme_hints({"detect_kickback_outflow"}) == ["kickback_shell"]
    assert scheme_hints({"detect_employee_address_match", "detect_kickback_outflow"}) == ["kickback_shell"]
    assert scheme_hints({"detect_round_trip", "detect_efos"}) == ["efos_fake_supplier", "round_trip_sales"]
    assert scheme_hints({"detect_employee_address_match"}) == []
    assert scheme_hint({"detect_round_trip", "detect_efos"}) == "efos_fake_supplier"


def test_dossier_carries_scheme_hints_list_84(ds):
    # #84: a dossier exposes scheme_hints (all matching) and scheme_hint (first).
    from agent.leads import aggregate

    by_id = {d["entity_id"]: d for d in aggregate(ds)}
    s4 = by_id["S00004"]
    assert s4["scheme_hint"] == "kickback_shell"
    assert s4["scheme_hints"] == ["kickback_shell"]
    # Decoys (no complete signature) carry an empty list and an empty scheme_hint.
    for pid in ("S00007", "S00026"):
        assert by_id[pid]["scheme_hints"] == []
        assert by_id[pid]["scheme_hint"] == ""


def test_ids_valid_serializable_and_deterministic(ds):
    from agent.leads import aggregate

    d = aggregate(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for dossier in d:
        assert dossier["entity_id"] in entity_ids
        assert dossier["evidence"]
        for evidence_id in dossier["evidence"]:
            assert evidence_id in record_ids
    assert json.dumps(d)
    assert aggregate(ds) == d


def test_empty_and_unknown_leads(ds):
    from agent.leads import aggregate

    assert aggregate(ds, {"detect_efos": []}) == []
    # An unknown detector is accepted; it simply is not strong.
    unknown = [{"entity_id": "S00005", "evidence": ["TX00001"]}]
    d = aggregate(ds, {"detect_unknown": unknown})
    assert len(d) == 1
    assert d[0]["entity_id"] == "S00005"
    assert d[0]["n_detectors"] == 1
    assert d[0]["n_strong"] == 0
    assert d[0]["scheme_hint"] == ""
    assert d[0]["n_leads"] == 1


def test_cli_top_and_json(ds, dataset_dir, capsys):
    from agent.leads import main

    assert main([str(dataset_dir), "--top", "3"]) == 0
    out = capsys.readouterr().out
    entity_lines = [line for line in out.splitlines() if line and line.split()[0].isdigit()]
    assert len(entity_lines) == 3

    assert main([str(dataset_dir), "--json"]) == 0
    parsed = json.loads(capsys.readouterr().out)
    assert len(parsed) == 19
