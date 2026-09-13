"""Tests for agent/contract.py (#3)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from agent.contract import validate_case_file

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "data_estate" / "out" / "example_case_file_for_seed42.json"


def _load_case() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_case_file_valid(ds):
    assert validate_case_file(_load_case(), ds) == []


def test_bad_evidence_id(ds):
    case = _load_case()
    i, old = next(
        (i, ev)
        for i, f in enumerate(case["findings"])
        for ev in f["evidence"]
        if ev.startswith("TX")
    )
    case["findings"][i]["evidence"].remove(old)
    case["findings"][i]["evidence"].append("TX99999")
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "TX99999" in errors[0] and f"findings[{i}]" in errors[0]


def test_bad_accused_id(ds):
    case = _load_case()
    case["findings"][0]["accused"][0] = "S99999"
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "S99999" in errors[0] and "findings[0]" in errors[0]


def test_bad_scheme_type(ds):
    case = _load_case()
    case["findings"][0]["scheme_type"] = "bribery"
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "bribery" in errors[0]


def test_zero_amount(ds):
    case = _load_case()
    case["findings"][0]["amount_mxn"] = 0
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "amount_mxn" in errors[0]


def test_entity_accused_and_not_pursued(ds):
    case = _load_case()
    entity = case["findings"][0]["accused"][0]
    case["not_pursued"].append({"entity": entity, "reason": "testing double-booked entity"})
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert entity in errors[0] and "not_pursued" in errors[0]


def test_empty_evidence(ds):
    case = _load_case()
    case["findings"].append(
        {
            "scheme_type": "other",
            "accused": ["S00001"],
            "rule": "test rule",
            "amount_mxn": 1.0,
            "evidence": [],
        }
    )
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "evidence" in errors[0] and f"findings[{len(case['findings']) - 1}]" in errors[0]


def test_duplicate_evidence_ids(ds):
    case = _load_case()
    ev = case["findings"][0]["evidence"]
    case["findings"][0]["evidence"] = [ev[0]] + ev  # first ID appears twice
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "duplicate" in errors[0]


def test_bad_not_pursued_entity(ds):
    case = _load_case()
    case["not_pursued"][0]["entity"] = "S99999"
    errors = validate_case_file(case, ds)
    assert len(errors) == 1, errors
    assert "S99999" in errors[0]


def test_missing_top_level_key(ds):
    case = _load_case()
    del case["not_pursued"]
    errors = validate_case_file(case, ds)
    assert errors and "not_pursued" in errors[0]


def _run_cli(case_path: Path, dataset: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agent.contract", str(dataset), str(case_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_cli(ds, dataset_dir, tmp_path):
    good = _run_cli(EXAMPLE, dataset_dir)
    assert good.returncode == 0 and "OK" in good.stdout

    bad_case = copy.deepcopy(_load_case())
    bad_case["findings"][0]["evidence"].append("TX99999")
    bad_file = tmp_path / "bad_case.json"
    bad_file.write_text(json.dumps(bad_case), encoding="utf-8")
    bad = _run_cli(bad_file, dataset_dir)
    assert bad.returncode == 1 and "TX99999" in bad.stdout
