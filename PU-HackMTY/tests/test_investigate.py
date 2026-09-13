"""Tests for agent/investigate.py (issue #13).

Tests may read hidden/ground_truth.json via the fixtures; agent/ code may not.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from agent.llm import FakeLLM, Reply, ToolCall


def _read_log(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_fakellm_drives_one_lead(tmp_path, dataset_dir):
    """A scripted FakeLLM drives one lead end to end without a network."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
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
            tool_calls=[
                ToolCall(
                    id="call_2",
                    name="record_finding",
                    args={
                        "scheme_type": "kickback_shell",
                        "accused": ["S00004", "E00002"],
                        "rule": "R2",
                        "amount_mxn": 575360.0,
                        "evidence": [
                            "BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F",
                            "EAC97D37-B587-8D33-1D5B-D8B04027B283",
                        ],
                        "narrative": "test",
                    },
                )
            ],
            cached=False,
            usage={},
            raw={},
        ),
    ]
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=FakeLLM(replies))

    kinds = [e["kind"] for e in _read_log(log)]
    assert kinds == [
        "run_start",
        "lead",
        "hypothesis",
        "tool_call",
        "tool_result",
        "decision",
        "guard",
        "challenge",
        "run_end",
    ]
    assert len(case["findings"]) == 1
    finding = case["findings"][0]
    assert finding["scheme_type"] == "kickback_shell"
    assert finding["accused"] == ["S00004", "E00002"]
    assert finding["amount_mxn"] == 575360.0

    from agent.contract import validate_case_file
    from agent.data import load

    assert validate_case_file(case, load(dataset_dir)) == []


def test_run_returns_same_dict_and_identical_files(tmp_path, dataset_dir):
    from agent.investigate import run

    replies = [
        Reply(
            text="no case here",
            tool_calls=[ToolCall(id="c", name="drop_lead", args={"entity_id": "S00004", "reason": "test drop"})],
            cached=False,
            usage={},
            raw={},
        )
    ]
    o1 = tmp_path / "a.json"
    l1 = tmp_path / "a.jsonl"
    o2 = tmp_path / "b.json"
    l2 = tmp_path / "b.jsonl"
    case1 = run(str(dataset_dir), out=str(o1), log=str(l1), max_leads=1, llm=FakeLLM(list(replies)))
    case2 = run(str(dataset_dir), out=str(o2), log=str(l2), max_leads=1, llm=FakeLLM(list(replies)))

    # The findings/not_pursued must be reproducible; run_metadata carries a live
    # wall_clock_seconds so it is compared separately (#89).
    canonical = {k: v for k, v in case1.items() if k != "run_metadata"}
    assert canonical == {k: v for k, v in case2.items() if k != "run_metadata"}
    assert canonical == {k: v for k, v in json.loads(Path(o1).read_text()).items() if k != "run_metadata"}
    assert canonical == {k: v for k, v in json.loads(Path(o2).read_text()).items() if k != "run_metadata"}

    for case, path in ((case1, o1), (case2, o2)):
        assert "run_metadata" in case
        assert case["run_metadata"]["wall_clock_seconds"] >= 0
        assert case["run_metadata"]["llm_calls"] == 1
        assert case["run_metadata"]["mxn_cost"] == 0.0
        assert json.dumps(case["findings"], sort_keys=True) == json.dumps(
            json.loads(Path(path).read_text())["findings"], sort_keys=True
        )


def test_run_metadata_counts_llm_and_cost(tmp_path, dataset_dir):
    """#89: run_metadata records LLM calls, tokens and cost; --no-llm writes zeros."""
    from agent.config import MXN_PER_1K_COMPLETION_TOKENS, MXN_PER_1K_PROMPT_TOKENS
    from agent.investigate import run

    log = tmp_path / "run.jsonl"
    replies = [
        Reply(
            text="Checking the supplier.",
            tool_calls=[ToolCall(id="c1", name="get_supplier", args={"supplier_id": "S00004"})],
            cached=False,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            raw={},
        ),
        Reply(
            text="nothing to accuse",
            tool_calls=[ToolCall(id="c2", name="drop_lead", args={"entity_id": "S00004", "reason": "test drop"})],
            cached=False,
            usage={"prompt_tokens": 200, "completion_tokens": 80},
            raw={},
        ),
    ]
    case = run(str(dataset_dir), out=None, log=str(log), max_leads=1, llm=FakeLLM(list(replies)))
    m = case["run_metadata"]
    assert m["llm_calls"] == 2
    assert m["prompt_tokens"] == 300
    assert m["completion_tokens"] == 130
    expected = (300 * MXN_PER_1K_PROMPT_TOKENS + 130 * MXN_PER_1K_COMPLETION_TOKENS) / 1000.0
    assert m["mxn_cost"] == pytest.approx(expected, abs=1e-6)
    assert m["cost_by_role"]["investigator"] == pytest.approx(expected, abs=1e-6)
    assert m["deterministic"] is False
    assert "run_metadata" in case

    run_end = [e for e in _read_log(log) if e["kind"] == "run_end"][0]
    assert run_end["payload"]["llm_calls"] == 2
    assert run_end["payload"]["mxn_cost"] == pytest.approx(expected, abs=1e-6)

    case2 = run(str(dataset_dir), out=None, log=None, no_llm=True)
    m2 = case2["run_metadata"]
    assert m2["llm_calls"] == 0
    assert m2["cached_calls"] == 0
    assert m2["prompt_tokens"] == 0
    assert m2["completion_tokens"] == 0
    assert m2["mxn_cost"] == 0.0
    assert m2["cost_by_role"] == {}
    assert m2["deterministic"] is True
    assert m2["deterministic_note"] == ""


def test_no_llm_scores(dataset_dir, decoy_ids):
    """--no-llm on company_42 must pass the DoD scores."""
    from agent.investigate import run
    from data_estate.score import score

    case = run(str(dataset_dir), out=None, log=None, no_llm=True)
    res = score(dataset_dir, case)
    assert res["results_recall"] >= 0.75
    assert res["found"] == sorted(res["found"])
    assert res["judgment_penalty"] == 0
    assert res["false_accusations"] == []
    assert res["decoys_accused"] == []
    assert res["evidence_validity"] >= 0.9
    pursued = {e["entity"] for e in case["not_pursued"]}
    assert decoy_ids <= pursued

    # Every finding is well-formed and the case file validates.
    from agent.contract import validate_case_file
    from agent.data import load

    assert validate_case_file(case, load(dataset_dir)) == []
    assert {f["scheme_type"] for f in case["findings"]} == {
        "efos_fake_supplier",
        "kickback_shell",
        "round_trip_sales",
        "duplicate_invoice_payment",
    }


def test_fallback_hypothesis_names_the_detectors_that_fired(tmp_path, dataset_dir):
    """#95: in a --no-llm run every hypothesis names the detectors that actually fired."""
    from agent.investigate import run

    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=None, log=str(log), no_llm=True)
    entries = _read_log(log)

    lead_dets: dict[str, set[str]] = {}
    for e in entries:
        if e["kind"] == "lead":
            lead_dets[e["entity_id"]] = set(e["payload"].get("detectors", []))

    hyps = [e for e in entries if e["kind"] == "hypothesis"]
    assert hyps, "the fallback run on company_42 must produce at least one hypothesis"
    for h in hyps:
        text = h["payload"]["text"]
        assert text.startswith("Detectors "), text
        assert " match the " in text and "signature; investigating" in text, text
        named = [d.strip() for d in text[len("Detectors ") :].split(" match the ")[0].split(",") if d.strip()]
        assert named, f"hypothesis names no detectors: {text}"
        fired = lead_dets.get(h["entity_id"], set())
        assert set(named) <= fired, f"hypothesis names detectors that did not fire: {text} -> {fired}"


def test_run_default_falls_back_without_env(dataset_dir, decoy_ids):
    """Without .env, settings() is None so the default run uses the fallback."""
    from agent.config import settings
    from agent.investigate import run

    if settings() is not None:
        pytest.skip(".env present; fallback not selected")
    case = run(str(dataset_dir), out=None, log=None)
    pursued = {e["entity"] for e in case["not_pursued"]}
    assert decoy_ids <= pursued
    assert {f["scheme_type"] for f in case["findings"]} == {
        "efos_fake_supplier",
        "kickback_shell",
        "round_trip_sales",
        "duplicate_invoice_payment",
    }


@pytest.mark.llm
def test_llm_end_to_end_with_real_endpoint(dataset_dir):
    from agent.config import settings

    if settings() is None:
        pytest.skip("no .env; skipping the live LLM end-to-end")
    from agent.investigate import run
    from data_estate.score import score

    case = run(str(dataset_dir), out=None, log=None, no_llm=False)
    res = score(dataset_dir, case)
    assert res["results_recall"] == 1.0
    assert res["judgment_penalty"] == 0


# --- #66: guard rejections are fed back; deterministic fallback on signature units ----

_KICKBACK_ARGS = {
    "scheme_type": "kickback_shell",
    "accused": ["S00004", "E00002"],
    "rule": "R2",
    "amount_mxn": 575360.0,
    "evidence": ["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"],
    "narrative": "test",
}
_BAD_AMOUNT_ARGS = {**_KICKBACK_ARGS, "amount_mxn": 1.0}


def _rf_call(args: dict, call_id: str = "call_rf") -> Reply:
    return Reply(
        text="",
        tool_calls=[ToolCall(id=call_id, name="record_finding", args=dict(args))],
        cached=False,
        usage={},
        raw={},
    )


def test_guard_rejection_is_fed_back_and_retry_succeeds(tmp_path, dataset_dir):
    """A rejected record_finding is fed back; the retry that fixes the amount is accepted."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    fake = FakeLLM([_rf_call(_BAD_AMOUNT_ARGS, "c1"), _rf_call(_KICKBACK_ARGS, "c2")])
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=fake)

    entries = _read_log(log)
    assert [e["kind"] for e in entries] == [
        "run_start", "lead", "hypothesis", "decision", "guard", "decision", "guard", "challenge", "run_end",
    ]
    guards = [e for e in entries if e["kind"] == "guard"]
    assert guards[0]["payload"]["accepted"] is False
    assert guards[1]["payload"]["accepted"] is True
    assert guards[1]["payload"]["source"] == "llm"
    assert guards[1]["payload"]["attempt"] == 2

    # The model saw the guard's reasons before retrying.
    last_msg = fake.calls[1]["messages"][-1]
    assert last_msg["role"] == "tool"
    assert "does not reconcile" in last_msg["content"]

    assert len(case["findings"]) == 1
    assert case["findings"][0]["amount_mxn"] == 575360.0


def test_retries_exhausted_falls_back_to_deterministic(tmp_path, dataset_dir):
    """Three rejected findings exhaust the budget; the deterministic finding is used."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    fake = FakeLLM([_rf_call(_BAD_AMOUNT_ARGS, f"c{i}") for i in range(3)])
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=fake)

    entries = _read_log(log)
    assert len(fake.calls) == 3
    fallback = [e for e in entries if e["kind"] == "decision" and e["payload"].get("source") == "deterministic_fallback"]
    assert len(fallback) == 1
    assert fallback[0]["payload"]["llm_outcome"] == "rejected"
    guards = [e for e in entries if e["kind"] == "guard"]
    assert guards[-1]["payload"]["accepted"] is True
    assert guards[-1]["payload"]["source"] == "deterministic_fallback"
    assert len(case["findings"]) == 1
    assert case["findings"][0]["amount_mxn"] == 575360.0
    assert "S00004" not in {e["entity"] for e in case["not_pursued"]}


def test_model_drop_on_signature_unit_is_overridden_with_reason_kept(tmp_path, dataset_dir):
    """An explicit drop_lead on a signature unit is overridden, but the reason is kept."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    reply = Reply(
        text="",
        tool_calls=[ToolCall(id="c", name="drop_lead", args={"entity_id": "S00004", "reason": "not enough"})],
        cached=False,
        usage={},
        raw={},
    )
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=FakeLLM([reply]))

    entries = _read_log(log)
    drops = [e for e in entries if e["kind"] == "decision" and e["payload"].get("action") == "drop_lead"]
    assert drops[0]["payload"]["reason"] == "not enough"
    fallback = [e for e in entries if e["kind"] == "decision" and e["payload"].get("source") == "deterministic_fallback"][0]
    assert fallback["payload"]["llm_outcome"] == "dropped"
    assert fallback["payload"]["llm_reason"] == "not enough"
    assert len(case["findings"]) == 1


def test_no_terminal_reply_falls_back(tmp_path, dataset_dir):
    """A text-only reply (no tool call) falls back to the deterministic finding."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    reply = Reply(text="I am not sure", tool_calls=[], cached=False, usage={}, raw={})
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=FakeLLM([reply]))

    entries = _read_log(log)
    fallback = [e for e in entries if e["kind"] == "decision" and e["payload"].get("source") == "deterministic_fallback"][0]
    assert fallback["payload"]["llm_outcome"] == "no_terminal"
    assert len(case["findings"]) == 1


def test_rejection_does_not_skip_sibling_tool_calls(tmp_path, dataset_dir):
    """A rejected record_finding must not skip sibling data-tool calls in the same reply."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
    first = Reply(
        text="",
        tool_calls=[
            ToolCall(id="c1", name="record_finding", args=dict(_BAD_AMOUNT_ARGS)),
            ToolCall(id="c2", name="get_supplier", args={"supplier_id": "S00004"}),
        ],
        cached=False,
        usage={},
        raw={},
    )
    fake = FakeLLM([first, _rf_call(_KICKBACK_ARGS, "c3")])
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, llm=fake)

    msgs = fake.calls[1]["messages"]
    first_asst = next(i for i, m in enumerate(msgs) if m["role"] == "assistant")
    tool_msgs_after = [m for m in msgs[first_asst + 1:] if m["role"] == "tool"]
    assert len(tool_msgs_after) == 2
    assert {m["tool_call_id"] for m in tool_msgs_after} == {"c1", "c2"}
    assert len(case["findings"]) == 1


# --- #84: entangled scheme -> one dossier in two units -----------------------

def test_entangled_dossier_yields_two_units():
    """#84: an entity in two schemes contributes a unit to each matching group."""
    from agent.investigate import _build_units

    dossier = {
        "entity_id": "S00001",
        "kind": "supplier",
        "name": "Entangled Vendor",
        "detectors": ["detect_efos", "detect_round_trip"],
        "n_detectors": 2,
        "n_strong": 2,
        "total_mxn": 100.0,
        "evidence": [],
        "n_evidence": 0,
        "related": [],
        "scheme_hints": ["efos_fake_supplier", "round_trip_sales"],
        "scheme_hint": "efos_fake_supplier",
        "leads": {},
        "n_leads": 0,
        "rank": 1,
    }
    units = _build_units([dossier])
    assert len(units) == 2
    assert {u["scheme_hint"] for u in units} == {"efos_fake_supplier", "round_trip_sales"}
    for u in units:
        assert u["entity_ids"] == ["S00001"]
        assert u["members"] == [dossier]
        # A single dossier that lands in two groups still yields one unit per group.
        assert u["total_mxn"] == 100.0


# --- #70: escalate unverified weak leads; park 'other' findings ----------------

def _keep_units(*entity_ids):
    """Wrap _build_units to keep only the units for the given entities."""
    import agent.investigate as inv

    ids = set(entity_ids)
    real = inv._build_units

    def wrapped(dossiers):
        return [u for u in real(dossiers) if u["entity_id"] in ids]

    return wrapped


def _clear_none_for(*detectors):
    """Wrap clear_reason to return None for the named detectors, else real."""
    import agent.investigate as inv

    real = inv.clear_reason

    def wrapped(det, eid, leads, ds):
        if det in detectors:
            return None
        return real(det, eid, leads, ds)

    return wrapped


def test_unverified_weak_lead_is_escalated(tmp_path, dataset_dir, monkeypatch):
    """#70: a weak lead whose innocent explanation cannot be confirmed is escalated."""
    import agent.investigate as inv
    from agent.investigate import run

    monkeypatch.setattr(inv, "_build_units", _keep_units("S00026"))
    monkeypatch.setattr(inv, "clear_reason", _clear_none_for("detect_shared_supplier_address"))

    log = tmp_path / "run.jsonl"
    replies = [
        Reply(
            text="checking the freight supplier.",
            tool_calls=[ToolCall(id="c1", name="get_supplier", args={"supplier_id": "S00026"})],
            cached=False,
            usage={},
            raw={},
        ),
        Reply(
            text="",
            tool_calls=[ToolCall(id="c2", name="drop_lead", args={"entity_id": "S00026", "reason": "freight company, carta porte on every invoice"})],
            cached=False,
            usage={},
            raw={},
        ),
    ]
    case = run(str(dataset_dir), out=None, log=str(log), llm=FakeLLM(replies))

    entries = _read_log(log)
    from agent.steplog import validate_entries
    assert validate_entries(entries) == []
    assert any(e["kind"] == "tool_call" and e["entity_id"] == "S00026" and e["payload"]["name"] == "get_supplier" for e in entries)
    drops = [e for e in entries if e["kind"] == "decision" and e["payload"].get("action") == "drop_lead"]
    assert drops[-1]["payload"]["reason"] == "freight company, carta porte on every invoice"
    assert drops[-1]["payload"]["escalated"] is True
    assert case["findings"] == []
    pursued = {e["entity"]: e["reason"] for e in case["not_pursued"]}
    assert pursued["S00026"] == "freight company, carta porte on every invoice"


def test_verified_weak_lead_not_escalated(tmp_path, dataset_dir, monkeypatch):
    """#70: a weak lead the records clear is dropped without the model ever seeing it."""
    import agent.investigate as inv
    from agent.investigate import run

    monkeypatch.setattr(inv, "_build_units", _keep_units("S00009"))

    log = tmp_path / "run.jsonl"
    fake = FakeLLM([])
    case = run(str(dataset_dir), out=None, log=str(log), llm=fake)

    assert fake.calls == []
    entries = _read_log(log)
    drops = [e for e in entries if e["kind"] == "decision" and e["payload"].get("action") == "drop_lead"]
    assert drops[0]["payload"]["verified"] is True
    assert drops[0]["payload"]["escalated"] is False
    assert case["findings"] == []


def test_other_finding_is_parked_not_accused(tmp_path, dataset_dir, ds, monkeypatch):
    """#70: an accepted `other` finding is parked as suspicious, never accused."""
    import agent.investigate as inv
    from agent.investigate import run

    monkeypatch.setattr(inv, "_build_units", _keep_units("S00026"))
    monkeypatch.setattr(inv, "clear_reason", _clear_none_for("detect_shared_supplier_address"))

    rec = ds.invoices[(ds.invoices["tipo"] == "recibida") & (ds.invoices["counterparty_id"] == "S00026")]
    assert len(rec), "S00026 must have a recibida invoice for the fake evidence"
    uuid = str(rec.iloc[0]["uuid"])

    log = tmp_path / "run.jsonl"
    reply = Reply(
        text="",
        tool_calls=[ToolCall(
            id="c1",
            name="record_finding",
            args={
                "scheme_type": "other",
                "accused": ["S00026"],
                "rule": "R5",
                "amount_mxn": 1.0,
                "evidence": [uuid],
                "narrative": "odd freight pattern",
            },
        )],
        cached=False,
        usage={},
        raw={},
    )
    case = run(str(dataset_dir), out=None, log=str(log), llm=FakeLLM([reply]))

    assert case["findings"] == []
    pursued = {e["entity"]: e for e in case["not_pursued"]}
    assert "S00026" in pursued
    reason = pursued["S00026"]["reason"]
    assert reason.startswith("suspicious, unproven: odd freight pattern")
    assert uuid in reason
    assert pursued["S00026"].get("closed_by") == "investigator"

    entries = _read_log(log)
    from agent.steplog import validate_entries
    assert validate_entries(entries) == []
    parks = [e for e in entries if e["kind"] == "decision" and e["payload"].get("action") == "park_lead"]
    assert parks and parks[0]["payload"]["tier"] == "suspicious"

    from data_estate.score import score
    res = score(dataset_dir, case)
    assert res["judgment_penalty"] == 0
    assert res["decoys_accused"] == []


def test_escalation_cap(tmp_path, dataset_dir, monkeypatch):
    """#70: only the first N unverified weak leads in rank order are escalated."""
    import agent.investigate as inv
    from agent.investigate import run

    monkeypatch.setattr(inv, "_build_units", _keep_units("S00026", "S00009"))
    monkeypatch.setattr(inv, "clear_reason", lambda det, eid, leads, ds: None)

    log = tmp_path / "run.jsonl"
    reply = Reply(
        text="",
        tool_calls=[ToolCall(id="c1", name="drop_lead", args={"entity_id": "S00009", "reason": "not enough"})],
        cached=False,
        usage={},
        raw={},
    )
    fake = FakeLLM([reply])
    case = run(str(dataset_dir), out=None, log=str(log), llm=fake, max_escalations=1)

    # S00009 is first in rank order, so it is the one escalated (1 model call);
    # S00026 exceeds the cap and is dropped unverified without a model call.
    assert len(fake.calls) == 1
    entries = _read_log(log)
    drops = {e["entity_id"]: e["payload"] for e in entries if e["kind"] == "decision" and e["payload"].get("action") == "drop_lead"}
    assert drops["S00009"]["escalated"] is True
    assert drops["S00026"]["escalated"] is False
    assert str(drops["S00026"]["reason"]).startswith("unverified:")
    assert case["findings"] == []


def test_rejected_other_after_retries_is_unverified(tmp_path, dataset_dir, monkeypatch):
    """#70: a rejected `other` finding past the retry budget is dropped unverified."""
    import agent.investigate as inv
    from agent.investigate import run

    monkeypatch.setattr(inv, "_build_units", _keep_units("S00026"))
    monkeypatch.setattr(inv, "clear_reason", _clear_none_for("detect_shared_supplier_address"))

    log = tmp_path / "run.jsonl"

    def _rejected(i):
        return Reply(
            text="",
            tool_calls=[ToolCall(
                id=f"c{i}",
                name="record_finding",
                args={
                    "scheme_type": "other",
                    "accused": ["S00026"],
                    "rule": "R5",
                    "amount_mxn": 1.0,
                    "evidence": ["TX99999"],  # does not exist -> guard rejects
                    "narrative": "odd freight pattern",
                },
            )],
            cached=False,
            usage={},
            raw={},
        )

    case = run(str(dataset_dir), out=None, log=str(log), llm=FakeLLM([_rejected(1), _rejected(2), _rejected(3)]))
    assert case["findings"] == []
    pursued = {e["entity"]: e["reason"] for e in case["not_pursued"]}
    assert str(pursued["S00026"]).startswith("unverified:")
    entries = _read_log(log)
    assert not any(e["kind"] == "guard" and e["payload"].get("accepted") for e in entries)


# --- #71: concurrent investigation --------------------------------------------

def _entities_in_prompt(messages):
    """The entity ids named in a unit's user prompt (one line per unit)."""
    content = messages[1]["content"] if len(messages) > 1 else ""
    for line in content.splitlines():
        if line.startswith("Entities in this scheme:"):
            rest = line.split(":", 1)[1].strip()
            return [x.strip() for x in rest.split(",") if x.strip()]
    return []


def _finding_by_entity(ds):
    """Map each signature unit's entity ids -> its deterministic aggregate finding."""
    import agent.investigate as inv

    dossiers = inv.aggregate(ds, inv.run_all(ds))
    units = inv._build_units(dossiers)
    by_eid: dict[str, tuple[str, dict]] = {}
    for u in units:
        hint = u["scheme_hint"]
        if not hint:
            continue
        rule_id = inv.SCHEME_TO_RULE.get(hint)
        if rule_id is None:
            continue
        finding = inv._build_finding(u, ds, hint, rule_id)
        if finding is None:
            continue
        for eid in u["entity_ids"]:
            by_eid[eid] = (hint, finding)
    return by_eid


def _parallel_fake(path):
    """A message-content-driven FakeLLM: per unit, ``get_supplier`` then the finding.

    Stateless and thread-safe, so it can answer concurrent units in any order; a
    weak lead that reaches the model (unverified, no scheme to prove) is dropped.
    """
    from agent.data import load

    ds = load(path)
    by_eid = _finding_by_entity(ds)

    def cb(messages):
        eids = _entities_in_prompt(messages)
        first = eids[0] if eids else "?"
        seen_tool = any(m.get("role") == "tool" for m in messages)
        if not seen_tool:
            return Reply(
                text="Gathering the records.",
                tool_calls=[ToolCall(id=f"c_{first}", name="get_supplier", args={"supplier_id": first})],
                cached=False,
                usage={},
                raw={},
            )
        entry = by_eid.get(first)
        if entry is None:
            return Reply(
                text="",
                tool_calls=[ToolCall(id=f"d_{first}", name="drop_lead", args={"entity_id": first, "reason": "no scheme signature we can prove"})],
                cached=False,
                usage={},
                raw={},
            )
        _hint, finding = entry
        return Reply(
            text="",
            tool_calls=[ToolCall(id=f"rf_{first}", name="record_finding", args=dict(finding))],
            cached=False,
            usage={},
            raw={},
        )

    return FakeLLM([cb])


def _canonical(case):
    return {k: v for k, v in case.items() if k != "run_metadata"}


def test_parallel_matches_sequential_case_file(tmp_path, dataset_dir):
    """#71: workers=3 produces the same case file as workers=1; both score 1.0."""
    from agent.investigate import run
    from data_estate.score import score

    o1, l1 = tmp_path / "a.json", tmp_path / "a.jsonl"
    o2, l2 = tmp_path / "b.json", tmp_path / "b.jsonl"
    c1 = run(str(dataset_dir), out=str(o1), log=str(l1), workers=1, max_leads=5, llm=_parallel_fake(dataset_dir))
    c2 = run(str(dataset_dir), out=str(o2), log=str(l2), workers=3, max_leads=5, llm=_parallel_fake(dataset_dir))
    assert _canonical(c1) == _canonical(c2)
    r1 = score(dataset_dir, c1)
    r2 = score(dataset_dir, c2)
    assert r1["results_recall"] == 1.0 and r1["judgment_penalty"] == 0
    assert r2["results_recall"] == 1.0 and r2["judgment_penalty"] == 0


def test_parallel_log_is_well_formed(tmp_path, dataset_dir):
    """#71: a workers=3 log validates under the per-entity pairing contract."""
    from agent.investigate import run
    from agent.steplog import validate_entries

    log = tmp_path / "run.jsonl"
    run(str(dataset_dir), out=None, log=str(log), workers=3, max_leads=5, llm=_parallel_fake(dataset_dir))
    entries = _read_log(log)
    assert validate_entries(entries) == []
    assert [e["step"] for e in entries] == list(range(1, len(entries) + 1))
    by_eid: dict[str, list[str]] = defaultdict(list)
    for e in entries:
        by_eid[e["entity_id"]].append(e["kind"])
    for eid, kinds in by_eid.items():
        if not eid:
            continue
        if "hypothesis" in kinds:
            assert kinds == ["lead", "hypothesis", "tool_call", "tool_result", "decision", "guard"], (eid, kinds)
        elif kinds:
            assert kinds == ["lead", "decision"], (eid, kinds)  # verified weak lead


def test_workers_one_is_byte_identical_to_previous_behaviour(tmp_path, dataset_dir):
    """#71: workers=1 reproduces the pre-#71 kinds sequence for the two-reply script."""
    from agent.investigate import run

    out = tmp_path / "case.json"
    log = tmp_path / "run.jsonl"
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
            tool_calls=[
                ToolCall(
                    id="call_2",
                    name="record_finding",
                    args={
                        "scheme_type": "kickback_shell",
                        "accused": ["S00004", "E00002"],
                        "rule": "R2",
                        "amount_mxn": 575360.0,
                        "evidence": [
                            "BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F",
                            "EAC97D37-B587-8D33-1D5B-D8B04027B283",
                        ],
                        "narrative": "test",
                    },
                )
            ],
            cached=False,
            usage={},
            raw={},
        ),
    ]
    case = run(str(dataset_dir), out=str(out), log=str(log), max_leads=1, workers=1, llm=FakeLLM(replies))
    assert [e["kind"] for e in _read_log(log)] == [
        "run_start", "lead", "hypothesis", "tool_call", "tool_result", "decision", "guard", "challenge", "run_end",
    ]
    assert len(case["findings"]) == 1
    assert case["findings"][0]["scheme_type"] == "kickback_shell"
