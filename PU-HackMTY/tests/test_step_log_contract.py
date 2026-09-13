"""Tests for the step-log contract (issue #67).

The step log is the data source for the demo UI (#26) and the API server (#68),
so a test that fails when the writer drifts from ``agent/steplog.py`` is the
guardrail. Tests may use the ``dataset_dir`` fixture (company_42) but never read
``hidden/``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agent.steplog import parse_lines, validate_entries

ROOT = Path(__file__).resolve().parents[1]

_KICKBACK_ARGS = {
    "scheme_type": "kickback_shell",
    "accused": ["S00004", "E00002"],
    "rule": "R2",
    "amount_mxn": 575360.0,
    "evidence": ["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"],
    "narrative": "test",
}


def _read(path: Path) -> list[dict]:
    entries, complete = parse_lines(path.read_text(encoding="utf-8"))
    assert complete
    return entries


def test_no_llm_log_validates(tmp_path, dataset_dir):
    from agent.investigate import run

    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=None, log=str(log), no_llm=True)
    assert validate_entries(_read(log)) == []


def test_fakellm_log_validates(tmp_path, dataset_dir):
    from agent.investigate import run
    from agent.llm import FakeLLM, Reply, ToolCall

    replies = [
        Reply(
            text="Checking the supplier and its kickback outflow.",
            tool_calls=[ToolCall(id="call_1", name="get_supplier", args={"supplier_id": "S00004"})],
            cached=False,
            usage={},
            raw={},
        ),
        Reply(
            text="",
            tool_calls=[ToolCall(id="call_2", name="record_finding", args=dict(_KICKBACK_ARGS))],
            cached=False,
            usage={},
            raw={},
        ),
    ]
    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=None, log=str(log), max_leads=1, llm=FakeLLM(replies))
    entries = _read(log)
    kinds = [e["kind"] for e in entries]
    assert "tool_call" in kinds and "tool_result" in kinds
    assert validate_entries(entries) == []


def test_log_is_streamed(tmp_path, dataset_dir):
    """A scripted second reply reads the log mid-run: lead+hypothesis already written."""
    from agent.investigate import run
    from agent.llm import FakeLLM, Reply, ToolCall

    log = tmp_path / "run.jsonl"

    def probe(messages):
        # Runs during the SECOND chat, before the run ends.
        text = log.read_text(encoding="utf-8")
        assert '"kind": "lead"' in text
        assert '"kind": "hypothesis"' in text
        assert '"kind": "guard"' not in text
        assert '"kind": "run_end"' not in text
        return Reply(
            text="",
            tool_calls=[ToolCall(id="call_2", name="record_finding", args=dict(_KICKBACK_ARGS))],
            cached=False,
            usage={},
            raw={},
        )

    replies = [
        Reply(
            text="checking the supplier",
            tool_calls=[ToolCall(id="call_1", name="get_supplier", args={"supplier_id": "S00004"})],
            cached=False,
            usage={},
            raw={},
        ),
        probe,
    ]
    run(str(dataset_dir), out=None, log=str(log), max_leads=1, llm=FakeLLM(replies))
    assert validate_entries(_read(log)) == []


def test_partial_last_line_tolerated():
    good = (
        '{"ts": "2026-01-01T00:00:00+00:00", "entity_id": "", "step": 1, "kind": "run_start", "payload": {}}\n'
        '{"ts": "2026-01-01T00:00:00+00:00", "entity_id": "S00004", "step": 2, "kind": "lead", "payload": {}}\n'
    )
    text = good + '{"ts": "2026-01-01T00:00:00+00:00", "entity_id": "S00004", "step": 3, "kind": "h'  # cut off
    entries, complete = parse_lines(text)
    assert complete is False
    assert len(entries) == 2
    assert [e["kind"] for e in entries] == ["run_start", "lead"]


def _entry(step: int, kind: str, entity_id: str = "", payload: dict | None = None) -> dict:
    return {
        "ts": "2026-01-01T00:00:00+00:00",
        "entity_id": entity_id,
        "step": step,
        "kind": kind,
        "payload": payload or {},
    }


def _run_start() -> dict:
    return _entry(1, "run_start", "", {"dataset": "d", "n_leads": 0, "mode": "no-llm", "model": ""})


def _run_end(step: int) -> dict:
    return _entry(step, "run_end", "", {"n_findings": 0, "n_not_pursued": 0, "wall_s": 0.0,
                                        "case_file": "", "report": ""})


def _lead(step: int, entity_id: str) -> dict:
    return _entry(
        step,
        "lead",
        entity_id,
        {"entity_id": entity_id, "name": "n", "rank": 1, "detectors": [],
         "n_detectors": 0, "total_mxn": 1.0, "leads": []},
    )


def test_validator_catches_drift():
    # (a) a guard not preceded by a record_finding decision for the same entity.
    a = [
        _run_start(),
        _lead(2, "S00004"),
        _entry(3, "decision", "S00004", {"action": "drop_lead", "reason": "r"}),
        _entry(4, "guard", "S00004", {"accepted": True, "reasons": [], "finding": {}}),
    ]
    assert any("guard must immediately follow a record_finding decision" in e for e in validate_entries(a))

    # (b) a step that skips a number.
    b = [_run_start(), _run_end(3)]
    assert any("step must be the previous step + 1" in e for e in validate_entries(b))

    # (c) a lead missing a required field.
    c = [_run_start(), _entry(2, "lead", "S00004", {"entity_id": "S00004", "name": "n"})]
    assert any("payload missing required field" in e for e in validate_entries(c))

    # An unknown kind is not an error (forward compatibility).
    d = [_run_start(), _entry(2, "mystery_kind", "", {"anything": 1})]
    assert validate_entries(d) == []


def test_sample_trace_validates():
    sample = ROOT / "demo" / "sample_trace.jsonl"
    if not sample.exists():
        pytest.skip("demo/sample_trace.jsonl is committed by #73; unavailable yet")
    entries, complete = parse_lines(sample.read_text(encoding="utf-8"))
    assert complete
    assert validate_entries(entries) == []


def test_steplog_cli(tmp_path, dataset_dir):
    from agent.investigate import run

    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=None, log=str(log), no_llm=True)
    res = subprocess.run(
        [sys.executable, "-m", "agent.steplog", str(log)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip().startswith("OK")
