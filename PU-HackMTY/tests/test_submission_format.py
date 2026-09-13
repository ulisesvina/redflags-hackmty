"""tests/test_submission_format.py (#88): the JSON the judges machine-check.

The authority here is not our opinion of the format — it is the judges' own
`validate_format.py`, vendored verbatim under `scripts/judges/`. Every submission this
suite builds is run through `validate_structure`, and the ones built from a SQLite estate
through `validate_against_estate` as well, which resolves every cited record id and
reconciles `peso_amount` to the cited exhibits per table within 2%.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from agent.data import load
from agent.investigate import run
from agent.submit import build_submission, entity_id, source_table

ROOT = Path(__file__).resolve().parents[1]
ESTATE_42 = ROOT / "data_estate" / "out" / "estate_42" / "estate.db"

_spec = importlib.util.spec_from_file_location("judges_validate", ROOT / "scripts" / "judges" / "validate_format.py")
judges = importlib.util.module_from_spec(_spec)
sys.modules["judges_validate"] = judges
_spec.loader.exec_module(judges)


def _run(estate, tmp_path, name):
    """A no-LLM run over ``estate``; returns (case, submission, log entries)."""
    out = tmp_path / f"{name}_case.json"
    log = tmp_path / f"{name}.jsonl"
    case = run(estate, out=str(out), log=str(log), no_llm=True, submission=str(tmp_path / f"{name}_sub.json"))
    submission = json.loads((tmp_path / f"{name}_sub.json").read_text(encoding="utf-8"))
    return case, submission, log


@pytest.fixture(scope="module")
def mini_submission(tmp_path_factory, request):
    db = request.getfixturevalue("judges_mini_db")
    tmp = tmp_path_factory.mktemp("mini_sub")
    case, submission, _ = _run(db, tmp, "mini")
    return {"db": db, "case": case, "submission": submission}


@pytest.fixture(scope="module")
def legacy_submission(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("legacy_sub")
    case, submission, _ = _run(ROOT / "data_estate" / "out" / "company_42", tmp, "c42")
    return {"case": case, "submission": submission}


# ------------------------------------------------------- the judges' own validator
def test_a_judge_estate_submission_passes_structure_and_estate_checks(mini_submission):
    submission = mini_submission["submission"]
    assert judges.validate_structure(submission) == []
    assert judges.validate_against_estate(submission, str(mini_submission["db"])) == []
    assert submission["findings"], "the mini estate has a listed vendor; something must be found"


def test_a_legacy_dataset_submission_passes_the_structure_check(legacy_submission):
    assert judges.validate_structure(legacy_submission["submission"]) == []


@pytest.mark.skipif(not ESTATE_42.exists(), reason="estate_42 lands with #80")
def test_the_frozen_judge_estate_passes_both_checks(tmp_path):
    _, submission, _ = _run(ESTATE_42, tmp_path, "estate42")
    assert judges.validate_structure(submission) == []
    assert judges.validate_against_estate(submission, str(ESTATE_42)) == []


# ------------------------------------------------------------------- scheme types
def test_only_the_judges_five_types_appear_as_findings(legacy_submission, mini_submission):
    for submission in (legacy_submission["submission"], mini_submission["submission"]):
        for finding in submission["findings"]:
            assert finding["scheme_type"] in judges.SCHEME_TYPES


def test_a_duplicate_payment_becomes_a_control_observation_not_a_finding(legacy_submission):
    """It is a real control failure and not one of the five types, so it is declined, not dropped."""
    case, submission = legacy_submission["case"], legacy_submission["submission"]
    duplicates = [f for f in case["findings"] if f["scheme_type"] == "duplicate_invoice_payment"]
    assert duplicates, "company_42 plants a duplicate payment; the case file should carry it"

    moved = [
        lead
        for lead in submission["leads_not_pursued"]
        if "duplicate" in lead["signal"] or "duplicate" in lead["reason"]
    ]
    assert moved, "the duplicate-payment finding must survive as a declined lead"
    entry = moved[0]
    assert entry["closed_by"] == "validator"
    assert "five scheme types" in entry["reason"]
    # Its evidence is not thrown away: the ids stay in the reason for a judge to follow.
    assert any(str(e) in entry["reason"] for e in duplicates[0]["evidence"])


# -------------------------------------------------------------- entities and exhibits
def test_entity_ids_carry_a_type_prefix(legacy_submission, mini_submission):
    for submission in (legacy_submission["submission"], mini_submission["submission"]):
        for finding in submission["findings"]:
            assert finding["entities"]
            for entity in finding["entities"]:
                assert entity.startswith(("RFC:", "EMP:")), entity


def test_legacy_ids_map_to_the_prefixed_form(ds):
    supplier = ds.suppliers.iloc[0]
    assert entity_id(supplier["supplier_id"], ds) == "RFC:" + supplier["rfc"]
    assert entity_id("E00002", ds) == "EMP:00002"
    assert entity_id("RFC:AAAA010101AA1", ds) == "RFC:AAAA010101AA1"  # already prefixed


def test_every_finding_has_at_least_three_exhibits_that_name_a_real_table(legacy_submission, mini_submission):
    for submission in (legacy_submission["submission"], mini_submission["submission"]):
        for finding in submission["findings"]:
            assert len(finding["exhibits"]) >= 3
            ids = [ex["exhibit_id"] for ex in finding["exhibits"]]
            assert len(ids) == len(set(ids))
            for exhibit in finding["exhibits"]:
                assert exhibit["source_table"] in judges.SOURCE_TABLES
                assert exhibit["note"].strip()
                assert exhibit["record_id"]


def test_exhibit_record_ids_exist_in_the_table_they_name(mini_submission):
    """A hallucinated id is the fastest way to lose the judges; check every one against SQL.

    A record id can legitimately belong to two tables — a listed vendor's RFC is both a
    `vendors` row and an `efos_list` row — so what has to hold is that the record exists
    in the table the exhibit names, not that some lookup agrees on one table.
    """
    conn = sqlite3.connect(mini_submission["db"])
    try:
        for finding in mini_submission["submission"]["findings"]:
            for exhibit in finding["exhibits"]:
                table = exhibit["source_table"]
                column = judges.ID_COLUMN[table]
                found = conn.execute(
                    f"SELECT 1 FROM {table} WHERE {column} = ?", (exhibit["record_id"],)
                ).fetchone()
                assert found, f"{table}.{exhibit['record_id']} does not exist"
    finally:
        conn.close()


def test_source_table_resolves_legacy_and_judge_record_ids(ds, mini_submission):
    assert source_table(ds.invoices.iloc[0]["uuid"], ds) == "invoices"
    assert source_table("TX00079", ds) == "bank_txns"
    assert source_table("CP00002", ds) == "bank_txns"
    assert source_table("GR00001", ds) == "purchase_orders"
    judge_ds = load(mini_submission["db"])
    assert source_table("BNK-0005", judge_ds) == "bank_txns"
    assert source_table("PO-0001", judge_ds) == "purchase_orders"


def test_master_rows_tie_each_accused_entity_to_the_scheme(mini_submission):
    finding = next(f for f in mini_submission["submission"]["findings"] if f["scheme_type"] == "phantom_vendor")
    tables = {ex["source_table"] for ex in finding["exhibits"]}
    assert "vendors" in tables
    assert "efos_list" in tables       # the 69-B listing is the whole point of the accusation
    assert finding["confidence"] == "proven"


# ------------------------------------------------------------------ reconciliation
def _per_table(finding, ds):
    totals: dict[str, float] = {}
    for exhibit in finding["exhibits"]:
        table = exhibit["source_table"]
        column = judges.AMOUNT_COLUMN.get(table)
        if not column:
            continue
        from agent.submit import _amount_of

        totals[table] = totals.get(table, 0.0) + _amount_of(exhibit["record_id"], table, ds)
    return totals


def test_peso_amount_reconciles_to_a_cited_table_within_two_percent(legacy_submission, ds, mini_submission):
    """The rule that fails a submission silently: claim what the cited records add up to."""
    pairs = [(legacy_submission["submission"], ds), (mini_submission["submission"], load(mini_submission["db"]))]
    for submission, dataset in pairs:
        for finding in submission["findings"]:
            totals = _per_table(finding, dataset)
            assert totals, f"{finding['scheme_type']} cites no amount-bearing table"
            claimed = finding["peso_amount"]
            best = min(totals.values(), key=lambda v: abs(claimed - v))
            assert abs(claimed - best) <= 0.02 * max(best, 1.0), (finding["scheme_type"], claimed, totals)
            assert claimed > 0


def test_a_round_trip_claims_the_sales_side_not_both_directions(legacy_submission, ds):
    """Citing every invoice two entangled entities exchanged would read as double the money."""
    finding = next(
        (f for f in legacy_submission["submission"]["findings"] if f["scheme_type"] == "round_tripping"), None
    )
    if finding is None:
        pytest.skip("no round trip in this run")
    cited = [ex["record_id"] for ex in finding["exhibits"] if ex["source_table"] == "invoices"]
    tipos = set(ds.invoices[ds.invoices["uuid"].isin(cited)]["tipo"])
    assert tipos == {"emitida"}
    assert finding["peso_amount"] == pytest.approx(1_029_000.0)


# --------------------------------------------------------------- narrative and trail
def test_narratives_are_plain_language_within_the_word_limit(legacy_submission, mini_submission):
    for submission in (legacy_submission["submission"], mini_submission["submission"]):
        for finding in submission["findings"]:
            words = finding["narrative"].split()
            assert 0 < len(words) <= 150
            assert "MXN 0.00" not in finding["narrative"]
            assert finding["rule_broken"].strip()


def test_the_money_trail_steps_cite_their_own_exhibits(legacy_submission, mini_submission):
    for submission in (legacy_submission["submission"], mini_submission["submission"]):
        for finding in submission["findings"]:
            ids = {ex["exhibit_id"] for ex in finding["exhibits"]}
            for step in finding["money_trail"]:
                assert step["exhibit_id"] in ids
                assert step["from"] and step["to"]
                assert isinstance(step["amount"], (int, float))
            dates = [s["date"] for s in finding["money_trail"]]
            assert dates == sorted(dates)


def test_a_kickback_trail_runs_company_to_vendor_to_employee(mini_submission):
    finding = next(f for f in mini_submission["submission"]["findings"] if f["scheme_type"] == "kickback")
    trail = finding["money_trail"]
    assert len(trail) >= 2
    assert trail[0]["from"] == "the company"
    assert trail[-1]["to"] == "Ana Ruiz Medina"
    assert trail[0]["to"] == trail[1]["from"], "the trail must connect"
    assert finding["confidence"] == "proven"


# -------------------------------------------------------------------- declined leads
def test_declined_leads_carry_signal_reason_tools_and_closer(legacy_submission):
    leads = legacy_submission["submission"]["leads_not_pursued"]
    assert leads
    for lead in leads:
        assert lead["entity"].startswith(("RFC:", "EMP:"))
        assert lead["signal"].strip()
        assert lead["reason"].strip()
        assert lead["closed_by"] in judges.CLOSED_BY
        assert isinstance(lead["tool_calls_made"], list)
    assert any(lead["signal"].startswith("detect_") for lead in leads), "signals name the detector"


def test_no_accused_entity_is_also_a_declined_lead(legacy_submission):
    submission = legacy_submission["submission"]
    accused = {e for f in submission["findings"] for e in f["entities"]}
    declined = {lead["entity"] for lead in submission["leads_not_pursued"]}
    assert not (accused & declined)


# ----------------------------------------------------------------------- metadata
def test_run_metadata_carries_the_three_numbers(legacy_submission):
    meta = legacy_submission["submission"]["run_metadata"]
    assert isinstance(meta["llm_calls"], int)
    assert isinstance(meta["mxn_cost"], (int, float))
    assert isinstance(meta["wall_clock_seconds"], (int, float))
    assert meta["deterministic"] is True


def test_the_seed_comes_from_the_estate_directory(legacy_submission):
    assert legacy_submission["submission"]["seed"] == 42


def test_build_submission_is_pure_and_repeatable(legacy_submission, ds):
    once = build_submission(legacy_submission["case"], ds, [], {"seed": 42})
    twice = build_submission(legacy_submission["case"], ds, [], {"seed": 42})
    assert once == twice
    assert judges.validate_structure(once) == []


def test_the_cli_writes_a_submission(tmp_path, judges_mini_db):
    from agent.submit import main

    case_path = tmp_path / "case.json"
    run(judges_mini_db, out=str(case_path), log=str(tmp_path / "r.jsonl"), no_llm=True, submission="")
    assert not (tmp_path / "submission.json").exists(), "--submission '' must skip the file"

    out = tmp_path / "cli.json"
    assert main([str(judges_mini_db), str(case_path), "--seed", "7", "--out", str(out)]) == 0
    submission = json.loads(out.read_text(encoding="utf-8"))
    assert submission["seed"] == 7
    assert judges.validate_structure(submission) == []
