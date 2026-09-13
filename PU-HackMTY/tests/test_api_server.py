"""tests/test_api_server.py (#68): the stdlib HTTP + SSE API the frontend drives.

Every request goes through a real socket with ``urllib.request`` -- no ``requests``,
no test client -- so what the frontend will see is what is asserted here. The server
is bound on port 0 and served in a thread per test, with ``runs/`` and the generator
out-root inside ``tmp_path``.
"""
from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from api import server as api_server

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def api(tmp_path):
    """A served API on a free port; returns a small client bound to its base URL."""
    httpd = api_server.serve("127.0.0.1", 0, tmp_path / "runs", tmp_path / "out")
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    client = _Client(f"http://{host}:{port}", tmp_path)
    try:
        yield client
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


class _Client:
    def __init__(self, base: str, tmp_path: Path) -> None:
        self.base = base
        self.tmp_path = tmp_path

    def request(self, path: str, *, method: str = "GET", body: dict | None = None,
                headers: dict | None = None, timeout: float = 30.0):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers=headers or {})
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8"), dict(err.headers)

    def json(self, path: str, **kw):
        status, text, headers = self.request(path, **kw)
        return status, (json.loads(text) if text else None), headers

    def stream(self, path: str, *, headers: dict | None = None, timeout: float = 10.0) -> str:
        req = urllib.request.Request(self.base + path, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.fp.raw._sock.settimeout(timeout)  # noqa: SLF001 - bound the SSE read
            return resp.read().decode("utf-8")


def _finished_run(api: _Client, dataset: str = "company_42", timeout: float = 120.0) -> str:
    """Start a no-LLM run and poll until it is done; returns the run id."""
    status, body, _ = api.json("/runs", method="POST", body={"dataset": dataset, "no_llm": True})
    assert status == 202, body
    run_id = body["run_id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, entry, _ = api.json(f"/runs/{run_id}")
        if entry["status"] in ("done", "failed"):
            assert entry["status"] == "done", entry
            return run_id
        time.sleep(0.2)
    raise AssertionError(f"run {run_id} did not finish in {timeout}s")


# ------------------------------------------------------------------------ health
def test_health_reports_llm_configuration_without_leaking_credentials(api):
    status, body, headers = api.json("/health")
    assert status == 200
    assert body["ok"] is True
    assert "llm_configured" in body
    assert "model" in body
    assert "api_key" not in body and "base_url" not in body
    assert json.dumps(body).lower().find("llm_api_key") == -1
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_options_preflight_is_204_with_cors(api):
    status, _, headers = api.request("/runs", method="OPTIONS")
    assert status == 204
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "POST" in headers["Access-Control-Allow-Methods"]


# ---------------------------------------------------------------------- datasets
def test_datasets_lists_company_42_without_naming_the_answer_key(api):
    status, body, _ = api.json("/datasets")
    assert status == 200
    by_name = {d["name"]: d for d in body}
    assert "company_42" in by_name
    entry = by_name["company_42"]
    assert entry["has_truth"] is True
    assert entry["n_invoices"] > 0
    assert entry["n_suppliers"] > 0
    assert entry["n_bank_txns"] > 0
    assert "ground_truth" not in json.dumps(body)
    assert body == sorted(body, key=lambda d: d["name"])


def test_entities_maps_ids_to_kinds(api):
    status, body, _ = api.json("/datasets/company_42/entities")
    assert status == 200
    assert body["S00030"]["kind"] == "supplier"
    assert body["S00030"]["name"]
    assert body["E00002"]["kind"] == "employee"
    assert "COMPANY" in body


def test_post_datasets_refuses_the_frozen_seed(api):
    status, body, _ = api.json("/datasets", method="POST", body={"seed": 42})
    assert status == 409
    assert "frozen" in body["error"]


def test_post_datasets_generates_a_clean_estate(api):
    status, body, _ = api.json(
        "/datasets", method="POST", body={"seed": 9001, "schemes": "clean"}, timeout=120
    )
    assert status == 201, body
    assert body["name"] == "company_9001"
    assert (api.tmp_path / "out" / "company_9001" / "company.json").exists()
    assert body["has_truth"] is True

    status, entities, _ = api.json("/datasets/company_9001/entities")
    assert status == 200
    assert "COMPANY" in entities


def test_post_datasets_rejects_an_unknown_scheme(api):
    status, body, _ = api.json("/datasets", method="POST", body={"seed": 9002, "schemes": "nope"})
    assert status == 400
    assert "nope" in body["error"]


# -------------------------------------------------------------------------- runs
def test_unknown_run_is_a_404_json_body(api):
    status, body, _ = api.json("/runs/nope")
    assert status == 404
    assert "error" in body


def test_full_run_produces_case_report_score_log_and_events(api):
    run_id = _finished_run(api)

    status, entry, _ = api.json(f"/runs/{run_id}")
    assert entry["status"] == "done"
    assert entry["dataset"] == "company_42"
    assert entry["n_findings"] == 4

    status, case, _ = api.json(f"/runs/{run_id}/case")
    assert status == 200
    assert len(case["findings"]) == 4

    status, result, _ = api.json(f"/runs/{run_id}/score")
    assert status == 200
    assert result["results_recall"] == 1.0
    assert result["judgment_penalty"] == 0

    status, text, headers = api.request(f"/runs/{run_id}/report")
    assert status == 200
    assert headers["Content-Type"].startswith("text/markdown")
    assert text.startswith("#")

    status, entries, _ = api.json(f"/runs/{run_id}/log")
    assert status == 200
    assert entries[0]["kind"] == "run_start"
    assert entries[-1]["kind"] == "run_end"

    body = api.stream(f"/runs/{run_id}/events?after=0")
    assert body.count("data: ") >= 34
    assert body.rstrip().endswith('event: end\ndata: {"status": "done"}')

    later = api.stream(f"/runs/{run_id}/events", headers={"Last-Event-ID": "30"})
    steps = [int(line.split(": ", 1)[1]) for line in later.splitlines() if line.startswith("id: ")]
    assert steps and min(steps) > 30

    _, listing, _ = api.json("/runs")
    assert [e["run_id"] for e in listing] == [run_id]


def test_a_second_run_while_one_is_in_progress_is_409(api, monkeypatch):
    real = api_server.run_investigation

    def slow(*args, **kwargs):
        time.sleep(1.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(api_server, "run_investigation", slow)

    status, first, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    assert status == 202
    status, second, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    assert status == 409
    assert second["run_id"] == first["run_id"]
    assert "in progress" in second["error"]


def test_run_on_an_unknown_dataset_is_404(api):
    status, body, _ = api.json("/runs", method="POST", body={"dataset": "company_does_not_exist"})
    assert status == 404
    assert "error" in body


def test_artifacts_are_404_until_the_run_is_done(api, monkeypatch):
    def slow(*args, **kwargs):
        time.sleep(2.0)
        raise RuntimeError("stopped on purpose")

    monkeypatch.setattr(api_server, "run_investigation", slow)
    _, body, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    run_id = body["run_id"]
    assert api.json(f"/runs/{run_id}/case")[0] == 404
    assert api.json(f"/runs/{run_id}/report")[0] == 404
    assert api.json(f"/runs/{run_id}/score")[0] == 404


def test_a_failed_run_is_reported_as_failed(api, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(api_server, "run_investigation", boom)
    _, body, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    run_id = body["run_id"]
    deadline = time.time() + 10
    while time.time() < deadline:
        _, entry, _ = api.json(f"/runs/{run_id}")
        if entry["status"] == "failed":
            assert "detector exploded" in entry["error"]
            return
        time.sleep(0.1)
    raise AssertionError("run never reached the failed state")


def test_runs_from_an_earlier_process_are_discovered_on_disk(api):
    runs_dir = api.tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "20250101T000000Z-abcd.jsonl").write_text(
        json.dumps({"ts": "2025-01-01T00:00:00+00:00", "entity_id": "", "step": 1,
                    "kind": "run_start",
                    "payload": {"dataset": "company_42", "n_leads": 1, "mode": "no-llm", "model": ""}})
        + "\n",
        encoding="utf-8",
    )
    _, listing, _ = api.json("/runs")
    found = {e["run_id"]: e for e in listing}
    assert "20250101T000000Z-abcd" in found
    assert found["20250101T000000Z-abcd"]["status"] == "failed"
    assert found["20250101T000000Z-abcd"]["dataset"] == "company_42"


def test_events_stream_tails_a_run_that_is_still_going(api):
    """Connect while the run is live: events arrive, then a terminating end event."""
    _, body, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    run_id = body["run_id"]
    stream = api.stream(f"/runs/{run_id}/events?after=0", timeout=120)
    assert "event: run_start" in stream
    assert "event: run_end" in stream
    # The end event states the run's outcome, not the state it was in when run_end
    # was logged: the thread still has the case file and the report to write.
    assert stream.rstrip().endswith('event: end\ndata: {"status": "done"}')
    assert socket.getdefaulttimeout() is None


# =============================================================== judges' estates (#96)
# Judges hand over an estate in their own schema at a path given at run time. The API has
# to list it, run it and hand back the artifacts they read, exactly as it does for ours.
@pytest.fixture
def judges_estate(api, judges_mini_db):
    """tests/fixtures/judges_mini under the out-root, as a CSV dir and as a loose .db."""
    import shutil

    out = api.tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    csv_dir = out / "estate_mini"
    shutil.copytree(ROOT / "tests" / "fixtures" / "judges_mini", csv_dir)
    loose_db = out / "estate_77.db"
    shutil.copy(judges_mini_db, loose_db)
    return {"dir": csv_dir, "db": loose_db}


def test_datasets_lists_both_estate_shapes(api, judges_estate):
    status, body, _ = api.json("/datasets")
    assert status == 200
    by_name = {d["name"]: d for d in body}

    assert by_name["company_42"]["format"] == "legacy"
    assert by_name["company_42"]["has_truth"] is True

    judge_dir = by_name["estate_mini"]
    assert judge_dir["format"] == "judges"
    assert judge_dir["has_truth"] is False          # a fixture has no answer key
    assert judge_dir["n_suppliers"] == 2
    assert judge_dir["n_invoices"] == 3
    assert judge_dir["n_bank_txns"] == 5            # the third-party leg counts too

    loose = by_name["estate_77"]                    # a .db is named by its stem
    assert loose["format"] == "judges"
    assert loose["path"].endswith("estate_77.db")
    assert loose["n_invoices"] == 3


def test_entities_on_a_judge_estate_are_keyed_by_rfc_and_emp(api, judges_estate):
    status, body, _ = api.json("/datasets/estate_mini/entities")
    assert status == 200
    assert body["RFC:AAAA010101AA1"]["kind"] == "supplier"
    assert body["RFC:AAAA010101AA1"]["name"] == "Servicios Integrales del Bajio SA de CV"
    assert body["RFC:CCCC030303CC3"]["kind"] == "customer"
    assert body["EMP:0001"]["kind"] == "employee"
    assert body["EMP:0001"]["role"] == "Gerente de Compras"
    assert body["COMPANY"]["rfc"] == "EMP920101AB1"
    assert body["COMPANY"]["clabe"] == "000000000000000099"


@pytest.mark.parametrize("target", ["dir", "db"])
def test_a_run_on_a_judge_estate_yields_every_artifact_the_judges_read(api, judges_estate, target):
    path = str(judges_estate[target])
    status, body, _ = api.json("/runs", method="POST", body={"dataset": path, "no_llm": True})
    assert status == 202, body
    run_id = body["run_id"]
    assert body["submission"].endswith(f"{run_id}_submission.json")
    assert body["report_html"].endswith(f"{run_id}_report.html")

    deadline = time.time() + 60
    while time.time() < deadline:
        _, entry, _ = api.json(f"/runs/{run_id}")
        if entry["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert entry["status"] == "done", entry

    status, submission, _ = api.json(f"/runs/{run_id}/submission")
    assert status == 200
    assert submission["findings"], "the mini estate has a listed vendor"
    assert all(e.startswith(("RFC:", "EMP:")) for f in submission["findings"] for e in f["entities"])

    status, html, headers = api.request(f"/runs/{run_id}/report.html")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert "<svg" in html
    assert "<script" not in html

    status, verdict, _ = api.json(f"/runs/{run_id}/validate")
    assert status == 200, verdict
    assert verdict["ok"] is True, verdict["errors"]
    assert verdict["errors"] == []


def test_validate_runs_the_judges_own_checks_not_our_idea_of_them(api, judges_estate):
    """A tampered submission must fail with the judges' own error text."""
    run_id = _finished_run(api, str(judges_estate["db"]), timeout=60)
    path = api.tmp_path / "runs" / f"{run_id}_submission.json"
    submission = json.loads(path.read_text(encoding="utf-8"))
    submission["findings"][0]["scheme_type"] = "creative_accounting"
    submission["findings"][0]["exhibits"][0]["record_id"] = "INV-DOES-NOT-EXIST"
    path.write_text(json.dumps(submission), encoding="utf-8")

    status, verdict, _ = api.json(f"/runs/{run_id}/validate")
    assert status == 200
    assert verdict["ok"] is False
    joined = " ".join(verdict["errors"])
    assert "scheme_type" in joined
    assert "INV-DOES-NOT-EXIST" in joined, "the estate check must resolve record ids"


def test_artifacts_are_404_before_a_run_finishes(api, monkeypatch):
    def slow(*args, **kwargs):
        time.sleep(2.0)
        raise RuntimeError("stopped on purpose")

    monkeypatch.setattr(api_server, "run_investigation", slow)
    _, body, _ = api.json("/runs", method="POST", body={"dataset": "company_42", "no_llm": True})
    run_id = body["run_id"]
    assert api.json(f"/runs/{run_id}/submission")[0] == 404
    assert api.json(f"/runs/{run_id}/report.html")[0] == 404
    assert api.json(f"/runs/{run_id}/validate")[0] == 404


def test_a_legacy_run_still_produces_a_valid_submission(api):
    run_id = _finished_run(api)
    status, verdict, _ = api.json(f"/runs/{run_id}/validate")
    assert status == 200
    assert verdict["ok"] is True, verdict["errors"]


# ---------------------------------------------------------- generating judge estates
def test_post_datasets_accepts_the_judges_scheme_names(api):
    status, body, _ = api.json(
        "/datasets", method="POST", body={"seed": 9003, "schemes": "phantom_vendor,kickback"}, timeout=120
    )
    assert status == 201, body
    assert body["format"] == "legacy"
    assert body["name"] == "company_9003"


def test_post_datasets_says_so_rather_than_faking_an_unbuilt_scheme(api):
    """#81 plants these; until then the answer is 501, not a quietly smaller estate."""
    status, body, _ = api.json("/datasets", method="POST", body={"seed": 9004, "schemes": "threshold_splitting"})
    assert status == 501
    assert "#81" in body["error"]


def test_post_datasets_in_the_judges_schema_is_not_built_yet(api):
    """#80 exports to their schema; a legacy estate labelled 'judges' would fail on stage."""
    status, body, _ = api.json("/datasets", method="POST", body={"seed": 9005, "format": "judges"})
    assert status == 501
    assert "#80" in body["error"]


def test_post_datasets_rejects_an_unknown_format(api):
    status, body, _ = api.json("/datasets", method="POST", body={"seed": 9006, "format": "parquet"})
    assert status == 400
    assert "format" in body["error"]
