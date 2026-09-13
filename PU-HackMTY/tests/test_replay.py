"""tests/test_replay.py (#93): rebuild a run offline from its step log, no network.

The point the judges probe live: "replay without a network." A re-run today would
hit the LLM cache; a true replay must not depend on the model at all. So the
original run is driven by a scripted FakeLLM, the log is replayed with
``LLM_BASE_URL`` pointing at a dead port and ``socket.socket`` monkeypatched to
raise, and the rebuilt case file must equal the original except for the
``run_metadata.replayed_from`` marker. The tamper test proves nothing is trusted
blindly: swap an evidence id for ``TX99999`` and the finding is dropped by the
guard with a warning, and the CLI still exits 0.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path

from agent.data import load
from agent.llm import FakeLLM, Reply, ToolCall

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("judges_validate", ROOT / "scripts" / "judges" / "validate_format.py")
judges = importlib.util.module_from_spec(_spec)
sys.modules["judges_validate"] = judges
_spec.loader.exec_module(judges)


def _drop(messages):
    """A FakeLLM reply that drops every hint unit.

    The investigation loop overrides a dropped *signature* unit with the
    deterministic fallback finding, so this reproduces the same four findings
    the ``--no-llm`` path produces, without ever constructing a real LLM.
    """
    return Reply(
        text="no case here",
        tool_calls=[ToolCall(id="drop", name="drop_lead", args={"entity_id": "", "reason": "not enough evidence"})],
        cached=False,
        usage={},
        raw={},
    )


def _norm(case: dict) -> tuple[dict, dict]:
    """Split a case into (non-metadata content, metadata-without-replayed_from)."""
    meta = dict(case["run_metadata"])
    meta.pop("replayed_from", None)
    return {k: v for k, v in case.items() if k != "run_metadata"}, meta


def test_replay_from_case_file_offline(tmp_path, dataset_dir, monkeypatch):
    """Replay with the case file alone, network disabled, reproduces the run."""
    from agent.investigate import replay, run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    sub = tmp_path / "sub.json"
    original = run(str(dataset_dir), out=str(out), log=str(log), llm=FakeLLM([_drop] * 200),
                   submission=str(sub))
    assert original["findings"], "a scripted FakeLLM run must produce the four scheme findings"

    # Network is dead: any socket use raises; LLM endpoint points at a closed port.
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LLM_API_KEY", "x")
    monkeypatch.setenv("LLM_MODEL", "x")

    def _boom(*_a, **_k):
        raise RuntimeError("network touched during replay")

    monkeypatch.setattr(socket, "socket", _boom)

    rcase = replay(str(out), out=str(tmp_path / "replayed.json"), submission=str(tmp_path / "r_sub.json"))

    # The content (findings + not_pursued) and the metadata (minus replayed_from) agree.
    assert _norm(original) == _norm(rcase)
    assert rcase["run_metadata"]["replayed_from"] == str(out)
    assert rcase["run_metadata"]["log"] == str(log)

    # The replayed submission passes the judges' own structure check (#88).
    from agent.submit import build_submission

    rs = build_submission(rcase, load(dataset_dir), [], {"seed": 42})
    assert judges.validate_structure(rs) == []


def test_replay_from_log_path_offline(tmp_path, dataset_dir, monkeypatch):
    """``--replay <log.jsonl>`` (the raw log, no case file) rebuilds the same case."""
    from agent.investigate import replay, run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    original = run(str(dataset_dir), out=str(out), log=str(log), llm=FakeLLM([_drop] * 200))

    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(socket, "socket", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no net")))
    rcase = replay(str(log), out=str(tmp_path / "replayed.json"), submission="")
    assert _norm(original) == _norm(rcase)
    assert rcase["run_metadata"]["replayed_from"] == str(log)


def test_tampered_log_drops_the_finding_and_exits_zero(tmp_path, dataset_dir, monkeypatch, capsys):
    """An evidence id that no longer exists is dropped by the guard on replay, exit 0."""
    from agent.contract import validate_case_file
    from agent.investigate import main as cli_main
    from agent.investigate import replay, run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=str(out), log=str(log), llm=FakeLLM([_drop] * 200))

    # Tamper with the log: rewrite the accepted EFOS finding's evidence to a bogus id.
    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    tampered = []
    done = False
    for e in entries:
        if not done and e["kind"] == "guard" and e["payload"].get("accepted") is True:
            f = e["payload"]["finding"]
            if f.get("scheme_type") == "efos_fake_supplier" and f.get("evidence"):
                e = dict(e)
                e["payload"] = dict(e["payload"])
                e["payload"]["finding"] = dict(f)
                e["payload"]["finding"]["evidence"] = ["TX99999"] + list(f["evidence"])
                done = True
        tampered.append(json.dumps(e, ensure_ascii=False))
    log.write_text("\n".join(tampered) + "\n", encoding="utf-8")
    assert done, "the EFOS finding must exist in the log to tamper"

    # Replay through the CLI; it must exit 0 and print a warning, not raise.
    rcase = replay(str(log), out=str(tmp_path / "tampered.json"), submission="")
    types = [f["scheme_type"] for f in rcase["findings"]]
    assert "efos_fake_supplier" not in types
    assert rcase["findings"], "the other three findings must survive"
    assert validate_case_file(rcase, load(dataset_dir)) == []

    captured = capsys.readouterr()
    assert "WARNING: dropped" in captured.err
    assert "TX99999" in captured.err

    # The CLI path returns 0 even after the drop (nothing is fatal on replay).
    rc = cli_main(["--replay", str(log), "--out", str(tmp_path / "cli.json"), "--submission", ""])
    assert rc == 0
