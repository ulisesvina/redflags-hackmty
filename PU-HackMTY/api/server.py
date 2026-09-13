"""Stdlib HTTP + SSE server so the frontend can drive the agent (#68).

The frontend is built outside this repo and needs three things: start an
investigation on a chosen dataset, watch the step log arrive live, and fetch the
finished artifacts. The CLI could not give it any of that, so this module wraps
:mod:`agent.investigate` in a small ``http.server`` application.

Standard library only -- ``ThreadingHTTPServer``, ``json``, ``threading``,
``argparse``, ``urllib.parse`` -- no FastAPI and no uvicorn (AGENTS.md rule 4).

It lives OUTSIDE ``agent/`` on purpose: ``GET /runs/{id}/score`` imports
:mod:`data_estate.score`, which reads ``hidden/ground_truth.json``. AGENTS.md
rule 2 and ``tests/test_no_hidden_access.py`` cover ``agent/`` only, so this
package may import the data side the way ``scripts/eval_batch.py`` does. Nothing
from ``hidden/`` ever reaches a response except through that one endpoint: it
exists for the team and for judges who ask how we score ourselves, and the
frontend must not show it by default.

Run it::

    python -m api.server --host 127.0.0.1 --port 8765 --runs runs --out-root data_estate/out/live

It serves both estate shapes (#96). A judges' estate — a SQLite ``estate.db`` or a
directory of their CSVs — is listed, run and scored exactly like one of ours, and a run
now leaves three artifacts next to each other: the case file, the judges'
``submission.json`` and ``report.html``. ``/runs/{id}/validate`` runs the judges' own
``validate_format.py`` in process, so the frontend can show a green tick that means what
the judges' check means rather than what we hope it means.

The endpoint table lives in ``api/README.md``; the step-log line format that
``/runs/{id}/events`` streams is ``docs/STEP_LOG.md`` (:mod:`agent.steplog`).
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import secrets
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import config as agent_config  # noqa: E402
from agent.data import load as load_dataset  # noqa: E402
from agent.investigate import run as _investigate_run  # noqa: E402
from agent.report import render as _render_report  # noqa: E402
from agent.steplog import parse_lines  # noqa: E402
from data_estate import generate as generator  # noqa: E402
from data_estate import score as dataset_score  # noqa: E402
from data_estate import validate as dataset_validate  # noqa: E402

# Indirection so tests can monkeypatch the slow parts (`api.server.run_investigation`).
run_investigation = _investigate_run
render_report = _render_report

# The four scheme names data_estate.generate plants, as scripts/eval_batch.py spells them.
ALL_SCHEMES = ["efos", "kickback", "roundtrip", "duplicate"]
# The judges' five types, accepted by POST /datasets. The generator cannot plant the last
# two yet (#81) and cannot export their schema yet (#80); asking for either is an honest
# 501 rather than a silently smaller estate. Delete the entry when its issue lands.
JUDGE_SCHEMES = {
    "phantom_vendor": "efos",
    "kickback": "kickback",
    "round_tripping": "roundtrip",
    "duplicate": "duplicate",
    "threshold_splitting": None,
    "revenue_inflation": None,
}
NOT_YET_PLANTED = {name for name, mapped in JUDGE_SCHEMES.items() if mapped is None}

# A judges' estate is a directory holding one of these, or a .db file directly under a root.
JUDGE_DB = "estate.db"
JUDGE_MARKER = "vendors.csv"

DEFAULT_OUT_ROOT = ROOT / "data_estate" / "out" / "live"
STANDARD_OUT = ROOT / "data_estate" / "out"
FROZEN = {"company_42"}

# SSE tail cadence and keep-alive silence budget.
POLL_S = 0.25
PING_EVERY_S = 15.0
# After the log's `run_end` line the thread still has to write the case file and render
# the report, so the registry needs a moment before `event: end` can state the outcome.
END_GRACE_S = 10.0

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(2)


def _csv_rows(path: Path) -> int:
    """Number of data rows in a CSV (header excluded); 0 when the file is missing."""
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


# --------------------------------------------------------------------- datasets
def dataset_format(path: Path) -> str | None:
    """``"legacy"``, ``"judges"``, or None when the path is not a dataset at all."""
    if path.is_file():
        return "judges" if path.suffix == ".db" else None
    if not path.is_dir():
        return None
    if (path / "company.json").exists():
        return "legacy"
    if (path / JUDGE_DB).exists() or (path / JUDGE_MARKER).exists():
        return "judges"
    return None


def _judge_source(path: Path) -> Path:
    """What ``agent.data.load`` should be handed for a judges' estate."""
    if path.is_file():
        return path
    db = path / JUDGE_DB
    return db if db.exists() else path


# Counting a judges' estate means deriving the company and its customers, which is the
# loader's job; cache the answer per (path, mtime) so listing stays cheap.
_COUNT_CACHE: dict[tuple[str, float], dict] = {}


def _judge_counts(path: Path) -> dict:
    source = _judge_source(path)
    key = (str(source.resolve()), source.stat().st_mtime)
    cached = _COUNT_CACHE.get(key)
    if cached is None:
        ds = load_dataset(source)
        cached = {
            "n_suppliers": len(ds.suppliers),
            "n_customers": len(ds.customers),
            "n_invoices": len(ds.invoices),
            "n_bank_txns": len(ds.bank_transactions) + len(ds.counterparty_bank),
        }
        _COUNT_CACHE[key] = cached
    return dict(cached)


def dataset_entry(path: Path) -> dict:
    """One `/datasets` row, for either estate shape."""
    shape = dataset_format(path) or "legacy"
    truth_root = path.parent if path.is_file() else path
    entry = {
        "name": path.stem if path.is_file() else path.name,
        "path": str(path),
        "format": shape,
        "has_truth": (truth_root / "hidden" / "ground_truth.json").exists(),
    }
    if shape == "judges":
        entry.update(_judge_counts(path))
    else:
        entry.update(
            {
                "n_suppliers": _csv_rows(path / "suppliers.csv"),
                "n_customers": _csv_rows(path / "customers.csv"),
                "n_invoices": _csv_rows(path / "invoices.csv"),
                "n_bank_txns": _csv_rows(path / "bank_transactions.csv"),
            }
        )
    return entry


def dataset_paths(out_root: Path) -> list[Path]:
    """Every dataset under data_estate/out/ and the live out-root: both shapes, deduplicated."""
    seen: dict[str, Path] = {}
    for root in (STANDARD_OUT, out_root):
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if dataset_format(child) is not None:
                seen.setdefault(str(child.resolve()), child)
    return sorted(seen.values(), key=lambda p: (p.stem if p.is_file() else p.name))


def list_datasets(out_root: Path) -> list[dict]:
    return [dataset_entry(d) for d in dataset_paths(out_root)]


def find_dataset(name_or_path: str, out_root: Path) -> Path | None:
    """Resolve a dataset name (``company_42``, ``estate_7``) or a filesystem path."""
    if not name_or_path:
        return None
    for path in dataset_paths(out_root):
        if (path.stem if path.is_file() else path.name) == name_or_path:
            return path
    candidate = Path(name_or_path)
    return candidate if dataset_format(candidate) is not None else None


def entities(path: Path) -> dict:
    """Every entity id in a dataset mapped to a small display record.

    Ids come out of the loader already in the shape the estate uses: ``S00004`` on ours,
    ``RFC:…`` and ``EMP:…`` on a judges' estate.
    """
    ds = load_dataset(_judge_source(path))
    out: dict[str, dict] = {}
    for row in ds.suppliers.to_dict("records"):
        out[row["supplier_id"]] = {"name": row["name"], "kind": "supplier", "category": row["category"]}
    for row in ds.customers.to_dict("records"):
        out[row["customer_id"]] = {"name": row["name"], "kind": "customer"}
    for row in ds.employees.to_dict("records"):
        out[row["employee_id"]] = {"name": row["name"], "kind": "employee", "role": row["role"]}
    out["COMPANY"] = {
        "name": ds.company.get("name", ""),
        "rfc": ds.company.get("rfc", ""),
        "clabe": ds.company.get("clabe", ""),
    }
    return out


class NotYetSupported(Exception):
    """Asked for something a dependency has not built yet; answered 501, never faked."""


def parse_schemes(value: Any) -> list[str]:
    """``"all"``, ``"clean"``, or an explicit list of our four or the judges' five names."""
    if value is None:
        return list(ALL_SCHEMES)
    if isinstance(value, list):
        names = [str(v).strip().lower() for v in value if str(v).strip()]
    else:
        text = str(value).strip().lower()
        if text in ("", "all"):
            return list(ALL_SCHEMES)
        if text == "clean":
            return []
        names = [v.strip() for v in text.split(",") if v.strip()]

    bad = [n for n in names if n not in ALL_SCHEMES and n not in JUDGE_SCHEMES]
    if bad:
        raise ValueError("unknown scheme(s): " + ", ".join(bad))
    blocked = sorted({n for n in names if n in NOT_YET_PLANTED})
    if blocked:
        raise NotYetSupported(
            f"the generator does not plant {', '.join(blocked)} yet (#81); "
            f"ask for the schemes it does plant, or wait for that issue"
        )
    return [JUDGE_SCHEMES.get(n, n) for n in names]


def generate_dataset(seed: int, schemes: list[str], out_root: Path) -> Path:
    """Generate ``<out_root>/company_<seed>/`` and validate it; raises on invalid output."""
    target = out_root / f"company_{seed}"
    estate = generator.Generator(seed).build(list(schemes))
    generator.write_estate(estate, target)
    errors = dataset_validate.check(target)
    if errors:
        raise RuntimeError("generated dataset is invalid: " + "; ".join(errors))
    return target


# ------------------------------------------------------- the judges' own validator
JUDGES_VALIDATOR = ROOT / "scripts" / "judges" / "validate_format.py"
_judges_module: Any = None


def judges_validator() -> Any:
    """Load ``scripts/judges/validate_format.py`` once, by path.

    It is the judges' file vendored verbatim and deliberately not a package, so it is
    loaded rather than imported. Running their code — not our idea of their code — is the
    whole value of ``/runs/{id}/validate``.
    """
    global _judges_module
    if _judges_module is None:
        spec = importlib.util.spec_from_file_location("judges_validate", JUDGES_VALIDATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _judges_module = module
    return _judges_module


def validate_submission(submission: dict, estate: Path | None) -> dict:
    """``{"ok": bool, "errors": [...]}`` from the judges' own checks."""
    judges = judges_validator()
    errors = list(judges.validate_structure(submission))
    if estate is not None and estate.is_file():
        errors += list(judges.validate_against_estate(submission, str(estate)))
    return {"ok": not errors, "errors": errors}


# ------------------------------------------------------------------------- runs
class RunRegistry:
    """In-memory run bookkeeping, backed by whatever is already in ``runs/``.

    One investigation at a time: the frontend drives a single machine and a second
    concurrent run would interleave two step logs on one screen.
    """

    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._runs: dict[str, dict] = {}

    # paths -----------------------------------------------------------------
    def log_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.jsonl"

    def case_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}_case.json"

    def report_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}_case.md"

    def submission_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}_submission.json"

    def html_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}_report.html"

    # state -----------------------------------------------------------------
    def active(self) -> str | None:
        with self._lock:
            for run_id, entry in self._runs.items():
                if entry["status"] == "running":
                    return run_id
        return None

    def start(self, run_id: str, dataset: str) -> dict:
        entry = {
            "run_id": run_id,
            "dataset": dataset,
            "status": "running",
            "started": _utc_now(),
            "finished": None,
            "n_findings": None,
            "error": None,
        }
        with self._lock:
            self._runs[run_id] = entry
        return dict(entry)

    def finish(self, run_id: str, n_findings: int) -> None:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is not None:
                entry.update(status="done", finished=_utc_now(), n_findings=n_findings, error=None)

    def fail(self, run_id: str, error: str) -> None:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is not None:
                entry.update(status="failed", finished=_utc_now(), error=error)

    def _disk_entry(self, run_id: str) -> dict | None:
        """Rebuild an entry for a run left behind by an earlier server process."""
        log = self.log_path(run_id)
        case = self.case_path(run_id)
        if not log.exists() and not case.exists():
            return None
        dataset = ""
        started = _mtime_iso(log) if log.exists() else _mtime_iso(case)
        if log.exists():
            entries, _ = parse_lines(log.read_text(encoding="utf-8"))
            if entries:
                started = entries[0].get("ts", started)
                dataset = str(entries[0].get("payload", {}).get("dataset", ""))
        n_findings = None
        if case.exists():
            try:
                n_findings = len(json.loads(case.read_text(encoding="utf-8")).get("findings", []))
            except (json.JSONDecodeError, OSError):
                n_findings = None
        status = "done" if case.exists() else "failed"
        return {
            "run_id": run_id,
            "dataset": dataset,
            "status": status,
            "started": started,
            "finished": _mtime_iso(case) if case.exists() else _mtime_iso(log),
            "n_findings": n_findings,
            "error": None if case.exists() else "run left no case file",
        }

    def _disk_ids(self) -> set[str]:
        ids: set[str] = set()
        if not self.runs_dir.is_dir():
            return ids
        for path in self.runs_dir.iterdir():
            if path.suffix == ".jsonl":
                ids.add(path.stem)
            elif path.name.endswith("_case.json"):
                ids.add(path.name[: -len("_case.json")])
        return ids

    def all(self) -> list[dict]:
        """Newest-first list, in-memory runs plus anything found on disk."""
        with self._lock:
            known = {k: dict(v) for k, v in self._runs.items()}
        for run_id in self._disk_ids():
            if run_id in known:
                continue
            entry = self._disk_entry(run_id)
            if entry is not None:
                known[run_id] = entry
        return sorted(known.values(), key=lambda e: (e.get("started") or "", e["run_id"]), reverse=True)

    def get(self, run_id: str) -> dict | None:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is not None:
                return dict(entry)
        return self._disk_entry(run_id)


def _investigation_thread(
    registry: RunRegistry, run_id: str, dataset: Path, options: dict
) -> None:
    """Body of the background run thread: investigate, then render the markdown report."""
    try:
        case = run_investigation(
            dataset,
            out=str(registry.case_path(run_id)),
            log=str(registry.log_path(run_id)),
            no_llm=options["no_llm"],
            max_leads=options["max_leads"],
            max_steps=options["max_steps"],
            submission=str(registry.submission_path(run_id)),
            report=str(registry.html_path(run_id)),
        )
        log_entries: list[dict] = []
        log = registry.log_path(run_id)
        if log.exists():
            log_entries, _ = parse_lines(log.read_text(encoding="utf-8"))
        markdown = render_report(case, load_dataset(dataset), log=log_entries)
        registry.report_path(run_id).write_text(markdown, encoding="utf-8")
        registry.finish(run_id, len(case.get("findings", [])))
    except Exception as exc:  # noqa: BLE001 - the thread must never die silently
        traceback.print_exc()
        registry.fail(run_id, repr(exc))


# ---------------------------------------------------------------------- handler
class Handler(BaseHTTPRequestHandler):
    server_version = "forensic-auditor-api/1.0"
    # HTTP/1.0 so a streaming response ends at EOF: SSE needs no Content-Length.
    protocol_version = "HTTP/1.0"

    # plumbing ---------------------------------------------------------------
    @property
    def registry(self) -> RunRegistry:
        return self.server.registry  # type: ignore[attr-defined]

    @property
    def out_root(self) -> Path:
        return self.server.out_root  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter test output
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)

    def _headers(self, status: int, content_type: str | None, length: int | None = None) -> None:
        self.send_response(status)
        for key, value in CORS.items():
            self.send_header(key, value)
        if content_type:
            self.send_header("Content-Type", content_type)
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
        if self.command != "HEAD":
            self.wfile.write(body)

    def _text(self, status: int, body: str, content_type: str) -> None:
        raw = body.encode("utf-8")
        self._headers(status, content_type, len(raw))
        self.wfile.write(raw)

    def _error(self, status: int, message: str, **extra: Any) -> None:
        self._json(status, {"error": message, **extra})

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        return data

    # verbs ------------------------------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._headers(204, None)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [unquote(p) for p in parsed.path.strip("/").split("/") if p]
        query = _parse_query(parsed.query)
        try:
            self._get(parts, query)
        except BrokenPipeError:  # client walked away mid-stream
            pass
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self._error(500, repr(exc))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [unquote(p) for p in parsed.path.strip("/").split("/") if p]
        try:
            body = self._body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._error(400, f"invalid JSON body: {exc}")
            return
        try:
            self._post(parts, body)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self._error(500, repr(exc))

    # routes -----------------------------------------------------------------
    def _get(self, parts: list[str], query: dict[str, str]) -> None:
        if parts == ["health"]:
            settings = agent_config.settings()
            self._json(
                200,
                {
                    "ok": True,
                    "llm_configured": settings is not None,
                    "model": settings.model if settings is not None else "",
                },
            )
            return

        if parts == ["datasets"]:
            self._json(200, list_datasets(self.out_root))
            return

        if len(parts) == 3 and parts[0] == "datasets" and parts[2] == "entities":
            directory = find_dataset(parts[1], self.out_root)
            if directory is None:
                self._error(404, f"unknown dataset {parts[1]!r}")
                return
            self._json(200, entities(directory))
            return

        if parts == ["runs"]:
            self._json(200, self.registry.all())
            return

        if len(parts) >= 2 and parts[0] == "runs":
            self._run_get(parts[1], parts[2:], query)
            return

        self._error(404, f"no route for GET /{'/'.join(parts)}")

    def _run_get(self, run_id: str, rest: list[str], query: dict[str, str]) -> None:
        entry = self.registry.get(run_id)
        if entry is None:
            self._error(404, f"unknown run {run_id!r}")
            return

        if not rest:
            self._json(200, entry)
            return

        if rest == ["log"]:
            log = self.registry.log_path(run_id)
            text = log.read_text(encoding="utf-8") if log.exists() else ""
            self._json(200, parse_lines(text)[0])
            return

        if rest == ["case"]:
            case = self.registry.case_path(run_id)
            if not case.exists():
                self._error(404, f"run {run_id!r} has no case file yet")
                return
            self._json(200, json.loads(case.read_text(encoding="utf-8")))
            return

        if rest == ["report"]:
            report = self.registry.report_path(run_id)
            if not report.exists():
                self._error(404, f"run {run_id!r} has no report yet")
                return
            self._text(200, report.read_text(encoding="utf-8"), "text/markdown; charset=utf-8")
            return

        if rest == ["report.html"]:
            html = self.registry.html_path(run_id)
            if not html.exists():
                self._error(404, f"run {run_id!r} has no HTML report yet")
                return
            self._text(200, html.read_text(encoding="utf-8"), "text/html; charset=utf-8")
            return

        if rest == ["submission"]:
            submission = self._submission(run_id)
            if submission is None:
                self._error(404, f"run {run_id!r} has no submission yet")
                return
            self._json(200, submission)
            return

        if rest == ["validate"]:
            submission = self._submission(run_id)
            if submission is None:
                self._error(404, f"run {run_id!r} has no submission yet")
                return
            dataset = find_dataset(entry.get("dataset", ""), self.out_root)
            estate = _judge_source(dataset) if dataset is not None else None
            self._json(200, validate_submission(submission, estate))
            return

        if rest == ["score"]:
            self._run_score(run_id, entry)
            return

        if rest == ["events"]:
            after = query.get("after") or self.headers.get("Last-Event-ID") or "0"
            try:
                after_step = int(after)
            except ValueError:
                after_step = 0
            self._stream_events(run_id, after_step)
            return

        self._error(404, f"no route for GET /runs/{run_id}/{'/'.join(rest)}")

    def _submission(self, run_id: str) -> dict | None:
        path = self.registry.submission_path(run_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _run_score(self, run_id: str, entry: dict) -> None:
        """Scores against hidden ground truth: for us and for judges who ask, never a default view."""
        case_path = self.registry.case_path(run_id)
        if entry["status"] != "done" or not case_path.exists():
            self._error(404, f"run {run_id!r} is not done")
            return
        directory = find_dataset(entry.get("dataset", ""), self.out_root)
        if directory is not None and directory.is_file():
            directory = directory.parent  # a .db estate keeps its truth beside it
        if directory is None or not (directory / "hidden" / "ground_truth.json").exists():
            self._error(404, f"run {run_id!r} has no scoreable dataset")
            return
        case = json.loads(case_path.read_text(encoding="utf-8"))
        self._json(200, dataset_score.score(directory, case))

    def _stream_events(self, run_id: str, after: str | int) -> None:
        """Tail the step log as Server-Sent Events until the run ends."""
        after_step = int(after)
        log = self.registry.log_path(run_id)
        self._headers(200, "text/event-stream; charset=utf-8")
        sent = after_step
        last_write = time.time()
        settle_deadline: float | None = None
        while True:
            text = log.read_text(encoding="utf-8") if log.exists() else ""
            batch, _complete = parse_lines(text)
            saw_run_end = False
            for entry in batch:
                step = entry.get("step", 0)
                if entry.get("kind") == "run_end":
                    saw_run_end = True
                if not isinstance(step, int) or step <= sent:
                    continue
                payload = json.dumps(entry, ensure_ascii=False)
                chunk = f"id: {step}\nevent: {entry.get('kind', 'message')}\ndata: {payload}\n\n"
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
                sent = step
                last_write = time.time()

            status = (self.registry.get(run_id) or {}).get("status", "done")
            if status == "running" and saw_run_end:
                # The investigation is over; wait for the thread to record the outcome.
                if settle_deadline is None:
                    settle_deadline = time.time() + END_GRACE_S
                elif time.time() >= settle_deadline:
                    status = "done"
            if status in ("done", "failed"):
                end = json.dumps({"status": status}, ensure_ascii=False)
                self.wfile.write(f"event: end\ndata: {end}\n\n".encode("utf-8"))
                self.wfile.flush()
                return
            if time.time() - last_write >= PING_EVERY_S:
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
                last_write = time.time()
            time.sleep(POLL_S)

    def _post(self, parts: list[str], body: dict) -> None:
        if parts == ["datasets"]:
            self._post_dataset(body)
            return
        if parts == ["runs"]:
            self._post_run(body)
            return
        self._error(404, f"no route for POST /{'/'.join(parts)}")

    def _post_dataset(self, body: dict) -> None:
        seed = body.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool):
            self._error(400, "seed must be an integer")
            return
        if f"company_{seed}" in FROZEN:
            self._error(409, f"company_{seed} is frozen")
            return
        shape = str(body.get("format", "legacy") or "legacy").strip().lower()
        if shape not in ("legacy", "judges"):
            self._error(400, f"format must be 'legacy' or 'judges', got {shape!r}")
            return
        try:
            schemes = parse_schemes(body.get("schemes", "all"))
        except ValueError as exc:
            self._error(400, str(exc))
            return
        except NotYetSupported as exc:
            self._error(501, str(exc))
            return
        if shape == "judges":
            # Generating straight into the judges' schema is #80. Answering 501 keeps the
            # frontend honest; silently handing back a legacy estate labelled "judges"
            # would not show up until the judges' own validator failed on stage.
            self._error(
                501,
                "generating an estate in the judges' schema needs generate.py --format judges (#80); "
                "judge estates already on disk are listed, run and validated normally",
            )
            return
        try:
            directory = generate_dataset(seed, schemes, self.out_root)
        except RuntimeError as exc:
            self._error(500, str(exc))
            return
        self._json(201, dataset_entry(directory))

    def _post_run(self, body: dict) -> None:
        name = str(body.get("dataset", "") or "")
        directory = find_dataset(name, self.out_root)
        if directory is None:
            self._error(404, f"unknown dataset {name!r}")
            return
        busy = self.registry.active()
        if busy is not None:
            self._error(409, "a run is in progress", run_id=busy)
            return

        options = {
            "no_llm": bool(body.get("no_llm", False)),
            "max_leads": int(body.get("max_leads", 12)),
            "max_steps": int(body.get("max_steps", 12)),
        }
        run_id = _new_run_id()
        name = directory.stem if directory.is_file() else directory.name
        self.registry.start(run_id, name)
        thread = threading.Thread(
            target=_investigation_thread,
            args=(self.registry, run_id, _judge_source(directory), options),
            daemon=True,
        )
        thread.start()
        self._json(
            202,
            {
                "run_id": run_id,
                "dataset": name,
                "log": str(self.registry.log_path(run_id)),
                "case": str(self.registry.case_path(run_id)),
                "report": str(self.registry.report_path(run_id)),
                "submission": str(self.registry.submission_path(run_id)),
                "report_html": str(self.registry.html_path(run_id)),
            },
        )


def _parse_query(query: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in query.split("&"):
        if not pair:
            continue
        key, _, value = pair.partition("=")
        out[unquote(key)] = unquote(value)
    return out


# ------------------------------------------------------------------------ serve
def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    runs: str | Path = "runs",
    out_root: str | Path = DEFAULT_OUT_ROOT,
    *,
    verbose: bool = False,
) -> ThreadingHTTPServer:
    """Bind and return the server without serving. Port 0 picks a free port."""
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    httpd.registry = RunRegistry(Path(runs))  # type: ignore[attr-defined]
    httpd.out_root = Path(out_root)  # type: ignore[attr-defined]
    httpd.verbose = verbose  # type: ignore[attr-defined]
    return httpd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m api.server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--runs", default="runs")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    args = parser.parse_args(argv)

    httpd = serve(args.host, args.port, args.runs, args.out_root, verbose=True)
    host, port = httpd.server_address[:2]
    print(f"serving on http://{host}:{port}  (runs={args.runs}, out-root={args.out_root})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
