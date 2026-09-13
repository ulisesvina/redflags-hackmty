# `api/` — the HTTP surface the frontend drives (#68)

Standard library only (`http.server.ThreadingHTTPServer`, `json`, `threading`); no FastAPI, no uvicorn
(AGENTS.md rule 4). It sits **outside** `agent/` because `GET /runs/{id}/score` imports `data_estate.score`,
which reads `hidden/ground_truth.json`; nothing from `hidden/` reaches any other response.

Both estate shapes are first class (#96). A **judges' estate** — a SQLite `estate.db`, a loose `*.db` under a
root, or a directory of their CSVs — is listed, run, and validated exactly like one of ours; `format` on every
`/datasets` row says which shape it is. A run leaves three artifacts beside each other: the case file, the
judges' `submission.json` and `report.html`.

```bash
python -m api.server --host 127.0.0.1 --port 8765 --runs runs --out-root data_estate/out/live
```

Every response carries `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Headers: Content-Type` and
`Access-Control-Allow-Methods: GET, POST, OPTIONS`; any `OPTIONS` returns 204 with those headers. Errors are
JSON `{"error": "<message>"}` with 400/404/409/500. All JSON is UTF-8, `ensure_ascii=False`.

| Method & path | Body / query | Returns |
|---|---|---|
| `GET /health` | | `{"ok": true, "llm_configured": bool, "model": "<LLM_MODEL or ''>"}` — never the key or the URL |
| `GET /datasets` | | `{"name", "path", "format": "legacy" \| "judges", "has_truth", "n_suppliers", "n_customers", "n_invoices", "n_bank_txns"}` for every dataset under `data_estate/out/` and `--out-root`, sorted by name. A directory counts when it holds `company.json` (legacy) or `estate.db`/`vendors.csv` (judges); a `*.db` file directly under a root is listed under its stem |
| `POST /datasets` | `{"seed": int, "schemes": "all" \| "clean" \| "efos,kickback,roundtrip,duplicate" or the judges' `phantom_vendor,kickback,round_tripping,…`, "format": "legacy" \| "judges"}` | 201 with that dataset's entry. Seed 42 → 409 (`company_42` is frozen). An existing directory is regenerated (deterministic). 500 with the errors when `data_estate.validate.check` rejects the result. **501** for `"format": "judges"` (needs #80) and for `threshold_splitting` / `revenue_inflation` (needs #81) — see "Not built yet" below |
| `GET /datasets/{name}/entities` | | `{"<entity id>": {"name", "kind": "supplier" \| "customer" \| "employee", "category"/"role"}, …, "COMPANY": {"name", "rfc", "clabe"}}`. Ids are whatever the estate uses: `S00004`/`C00005`/`E00002` on ours, `RFC:…`/`EMP:…` on a judges' estate |
| `POST /runs` | `{"dataset": "company_42" \| "estate_7" \| "<path to a dir or a .db>", "no_llm": false, "max_leads": 12, "max_steps": 12}` | 202 `{"run_id", "dataset", "log", "case", "report", "submission", "report_html"}`. Runs in a background thread. One run at a time: while one is `running`, 409 `{"error": "a run is in progress", "run_id": "<that id>"}` |
| `GET /runs` | | newest-first `{"run_id", "dataset", "status": "running"\|"done"\|"failed", "started", "finished", "n_findings", "error"}`, including runs left in `--runs` by an earlier server process |
| `GET /runs/{id}` | | one entry as above, 404 if unknown |
| `GET /runs/{id}/events` | `?after=<step>`, or the `Last-Event-ID` header | `text/event-stream`: `id: <step>` / `event: <kind>` / `data: <the step-log line>` for every step after `after`. Tails a live run (250 ms poll, `: ping` every 15 s of silence) and closes with `event: end` + `{"status": …}` |
| `GET /runs/{id}/log` | | JSON array of every step-log entry so far |
| `GET /runs/{id}/case` | | the case file (404 until `done`) |
| `GET /runs/{id}/report` | | the markdown as `text/markdown; charset=utf-8` (404 until `done`) |
| `GET /runs/{id}/report.html` | | the five-section case file as `text/html; charset=utf-8` (404 until `done`). Self-contained: inline SVG money trail, no script, no URL |
| `GET /runs/{id}/submission` | | the judges' `submission.json` (404 until `done`) |
| `GET /runs/{id}/validate` | | `{"ok": bool, "errors": [...]}` from the judges' own `scripts/judges/validate_format.py`, run in process — `validate_structure`, plus `validate_against_estate` when the dataset is a `.db`. A green tick here means what their check means |
| `GET /runs/{id}/score` | | `data_estate.score.score(dataset, case)` (404 when the dataset has no hidden truth or the run is not `done`). **For the team and for judges who ask — the frontend must not show it by default.** |

`run_id` is `<UTC %Y%m%dT%H%M%SZ>-<4 hex>`. Artifacts land in `--runs`: `<run_id>.jsonl` (step log),
`<run_id>_case.json`, `<run_id>_case.md`, `<run_id>_submission.json`, `<run_id>_report.html`. The step log's
final `run_end` line names the artifact paths too (`case_file`, `report`, `submission`), so a client watching
the event stream knows where they landed without a second call.

## Not built yet, and said so

`POST /datasets` answers **501** rather than pretending, in two cases:

* `"format": "judges"` — generating an estate straight into the judges' schema is #80. Judge estates that
  already exist on disk are listed, run and validated normally; it is only *generation* that is missing.
* `"schemes"` naming `threshold_splitting` or `revenue_inflation` — the generator does not plant them yet (#81).

Handing back a legacy estate labelled `"judges"`, or a quietly smaller one, would not surface until the judges'
own validator failed on stage. When those issues land, delete the entry from `JUDGE_SCHEMES` / the `judges`
branch in `_post_dataset`.

The event line format is the step-log contract, `docs/STEP_LOG.md` (`agent/steplog.py` validates it);
`demo/sample_trace.jsonl` is a real run to build a frontend against without a backend.

Smoke test by hand:

```bash
python -m api.server &
curl -s -X POST localhost:8765/runs -H 'Content-Type: application/json' \
     -d '{"dataset":"company_42","no_llm":true}'
curl -N localhost:8765/runs/<id>/events        # ends with `event: end`
curl -s localhost:8765/runs/<id>/validate      # {"ok": true, "errors": []}
curl -s localhost:8765/runs/<id>/report.html -o report.html && xdg-open report.html
```
