# Step log (`runs/<UTC timestamp>.jsonl`)

## What this file is

`agent.investigate` writes the story of an investigation, one JSON object per
line, to the path given by `--log`. Every event — a lead being picked up, a
hypothesis, a tool call and its result, a decision to accuse or drop, the
evidence guard's verdict — is a single line. The demo UI (#26) and the API
server (#68) read this file to replay a run on screen, so the format below is a
contract: **writers may add fields, never rename or remove them; readers must
ignore unknown kinds and unknown fields.**

The validation is in code, not just prose: `agent/steplog.py` exports
`parse_lines` (tolerant) and `validate_entries` (the contract), and
`tests/test_step_log_contract.py` fails if the writer drifts from it. Run
`python -m agent.steplog runs/<file>.jsonl` to check a file.

## Where it lands, and how to tail it

- `python -m agent.investigate <dataset> --log runs/myrun.jsonl` writes to
  `runs/myrun.jsonl`. The default (no `--log`) is `runs/<UTC ts>.jsonl`.
- The file is **opened at the start of the run and appended+flushed per event**,
  so a reader can `tail -f` it live while the run is still going.
- **Detecting the end of a run:** a partial last line means the writer is
  mid-write — wait and retry. A `run_end` line means the run finished. If there is
  **no `run_end` and no new line for 60 seconds**, the run was aborted (the
  writer closes the file on a crash, so the file is still readable, it just never
  got a `run_end`).

## The envelope

Every line is one JSON object with exactly these five keys:

| key | type | meaning |
|---|---|---|
| `ts` | string (ISO 8601, local timezone) | when the event happened |
| `entity_id` | string | which entity this step is about; `""` for run-level events |
| `step` | int | strictly increasing by 1 from 1 |
| `kind` | string | one of the kinds below (unknown kinds are ignored) |
| `payload` | object | kind-specific fields; extra fields are allowed |

Example (the very first line of a run):

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "", "step": 1, "kind": "run_start", "payload": {"dataset": "data_estate/out/company_42", "n_leads": 19, "mode": "no-llm", "model": ""}}
```

## Kinds

### `run_start`

| field | type | meaning |
|---|---|---|
| `dataset` | string | dataset directory (or name) being investigated |
| `n_leads` | int | how many leads (dossiers) the detectors found |
| `mode` | string | `"llm"` or `"no-llm"` |
| `model` | string | the LLM model, or `""` when not using one |

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "", "step": 1, "kind": "run_start", "payload": {"dataset": "data_estate/out/company_42", "n_leads": 19, "mode": "no-llm", "model": ""}}
```

### `lead`

| field | type | meaning |
|---|---|---|
| `entity_id` | string | the entity under investigation |
| `name` | string | its name |
| `rank` | int | its rank among all leads |
| `detectors` | list of strings | which detectors fired on it |
| `n_detectors` | int | how many detectors fired |
| `total_mxn` | number | money moved through it, in pesos |
| `leads` | list | the raw detector lead rows |

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "S00004", "step": 2, "kind": "lead", "payload": {"entity_id": "S00004", "name": "Gestoría y Enlace San Nicolás S de RL de CV", "rank": 1, "detectors": ["detect_employee_address_match", "detect_fast_pay_no_deliverable", "detect_kickback_outflow", "detect_new_vendor_round_amounts", "detect_no_receipt"], "n_detectors": 5, "total_mxn": 575360.0, "leads": [{"entity_id": "S00004", "supplier_name": "Gestoría y Enlace San Nicolás S de RL de CV", "employee_id": "E00002", "employee_role": "Gerente de Compras", "same_approver": true, "street": "Av. Universidad 859", "city": "Guadalupe, NL", "n_invoices": 8, "total_mxn": 575360.0, "evidence": ["08D16094-B6E3-B91B-3777-D8232D8D7DB8", "BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F"]}]}}
```

### `hypothesis`

| field | type | meaning |
|---|---|---|
| `text` | string | a readable statement of what the agent thinks is going on. In the deterministic fallback it is `"Detectors <a>, <b> match the <scheme> signature; investigating."`, naming the detector modules that actually fired for the entity. |
| `scheme_type` | string | the scheme type it suspects (`efos_fake_supplier`, `kickback_shell`, `round_trip_sales`, `duplicate_invoice_payment`, or `other`) |
| `derived_from` | array of string | (LLM mode only) the detector modules whose leads this hypothesis derives from |

```json
{"ts": "2026-09-12T23:14:20+02:00", "entity_id": "S00004", "step": 3, "kind": "hypothesis", "payload": {"text": "Detectors detect_employee_address_match, detect_fast_pay_no_deliverable, detect_kickback_outflow, detect_new_vendor_round_amounts, detect_no_receipt match the kickback_shell signature; investigating.", "scheme_type": "kickback_shell"}}
```

### `tool_call` (LLM mode only)

| field | type | meaning |
|---|---|---|
| `name` | string | the data tool the model called (`get_supplier`, `get_invoices`, `trace_flow`, …) |
| `args` | object | the call's arguments |

```json
{"ts": "2026-09-12T21:51:24+02:00", "entity_id": "S00004", "step": 4, "kind": "tool_call", "payload": {"name": "get_supplier", "args": {"supplier_id": "S00004"}}}
```

### `tool_result` (LLM mode only)

| field | type | meaning |
|---|---|---|
| `name` | string | the tool that ran |
| `n_rows` | int | how many rows it returned |
| `summary` | string | a one-line summary |
| `ids` | list of strings | record IDs found in the result (invoice UUIDs, `TX*`, `CP*`, `GR*`) |
| `rows` | list | up to the first 5 rows of the result |

```json
{"ts": "2026-09-12T21:51:24+02:00", "entity_id": "S00004", "step": 5, "kind": "tool_result", "payload": {"name": "get_supplier", "n_rows": 1, "summary": "1 rows", "ids": [], "rows": [{"supplier_id": "S00004", "name": "Gestoría y Enlace San Nicolás S de RL de CV", "rfc": "EOK870428F5T", "category": "servicios", "approved_by": "E00002", "status": "activo", "efos": {"listed": false, "situacion": "", "fecha_publicacion": ""}, "stats": {"n_invoices": 8, "total_mxn": 575360.0}}]}}
```

### `decision`

| field | type | meaning |
|---|---|---|
| `action` | string | `record_finding`, `drop_lead` or `park_lead` |
| `finding` | object | only for `record_finding`: `{scheme_type, accused[ids], rule, amount_mxn, evidence[ids], narrative}` |
| `reason` | string | only for `drop_lead`: why the lead was dropped |
| `source` | string | extra: `llm` / `deterministic` / `deterministic_fallback` |
| `attempt` | int | extra: which `record_finding` attempt this was |

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "S00004", "step": 4, "kind": "decision", "payload": {"action": "record_finding", "finding": {"scheme_type": "kickback_shell", "accused": ["E00002", "S00004"], "rule": "CFF Art. 69-B; LISR Art. 27-I", "amount_mxn": 575360.0, "evidence": ["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"], "narrative": "kickback shell: Gestoría y Enlace San Nicolás S de RL de CV — R2."}, "source": "deterministic", "attempt": 1}}
```

A `drop_lead` decision:

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "S00024", "step": 19, "kind": "decision", "payload": {"action": "drop_lead", "reason": "the 69-B list is matched on RFC, not on name — this RFC is not on it; the invoices without a goods receipt are for a category where a receipt is not mandatory; the shared address is a commercial building, not an employee's home"}}
```

A `park_lead` decision (#70): an `other` finding the evidence guard accepted is
never accused — it becomes a "suspicious, unproven" declined lead. One per
accused entity; `tier` is `suspicious` and `reason` is the declined-lead story:

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "S00026", "step": 21, "kind": "decision", "payload": {"action": "park_lead", "tier": "suspicious", "entity_id": "S00026", "reason": "suspicious, unproven: odd freight pattern. Evidence: BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F"}}
```

### `guard`

| field | type | meaning |
|---|---|---|
| `accepted` | bool | did the evidence guard accept the finding |
| `reasons` | list of strings | why it was rejected (empty when accepted) |
| `finding` | object | the finding the guard looked at |
| `source` | string | extra: `llm` / `deterministic` / `deterministic_fallback` |
| `attempt` | int | extra: which attempt this verdict is on |

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "S00004", "step": 5, "kind": "guard", "payload": {"accepted": true, "reasons": [], "finding": {"scheme_type": "kickback_shell", "accused": ["E00002", "S00004"], "rule": "CFF Art. 69-B; LISR Art. 27-I", "amount_mxn": 575360.0, "evidence": ["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"]}, "source": "deterministic", "attempt": 1}}
```

### `run_end`

| field | type | meaning |
|---|---|---|
| `n_findings` | int | how many findings the case file holds |
| `n_not_pursued` | int | how many leads were not pursued |
| `wall_s` | number | wall-clock seconds for the whole run |
| `llm_calls` | int | number of LLM `chat` calls (#89) |
| `cached_calls` | int | how many of those came from the disk cache |
| `prompt_tokens` | int | prompt tokens from *uncached* calls (cached cost 0) |
| `completion_tokens` | int | completion tokens from *uncached* calls (cached cost 0) |
| `mxn_cost` | number | MXN cost at the reference hosted rate (0 for `--no-llm`) |
| `cost_by_role` | object | per-role MXN cost, e.g. `{"investigator": ...}` |
| `case_file` | string | where the case file was written (`""` when `--out` was omitted) |
| `report` | string | where `report.html` was written (`""` when `--report ""`) (#90) |
| `submission` | string | where the judges' `submission.json` was written (`""` when `--submission ""`) (#88) |

```json
{"ts": "2026-09-12T21:51:15+02:00", "entity_id": "", "step": 34, "kind": "run_end", "payload": {"n_findings": 4, "n_not_pursued": 14, "wall_s": 0.178, "llm_calls": 0, "cached_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "mxn_cost": 0.0, "cost_by_role": {}, "case_file": "/tmp/sample_case.json", "report": "/tmp/report.html", "submission": "/tmp/submission.json"}}
```

The case file itself gains a top-level `run_metadata` block with the same
counters plus `wall_clock_seconds`, `deterministic` (true in no-LLM mode, and in
LLM mode only when every call came from the cache) and `deterministic_note`
("replay from cache is deterministic" for a fully-cached LLM run).

## Ordering guarantees

For each entity, the steps appear in this order:

```
lead → (hypothesis) → zero or more (tool_call / tool_result pairs) → decision (+ guard after a record_finding)
```

`tool_call`/`tool_result` only appear when the run is in LLM mode; the `--no-llm`
deterministic path emits `lead → hypothesis → decision → guard`. There may be
several `decision`/`guard` pairs for one entity if a finding is rejected and
retried. A `drop_lead` decision is not followed by a `guard`.

Once runs are investigated concurrently (#71), entities interleave in the file —
**group by `entity_id`, never assume contiguity**. The per-entity subsequence above
still holds.

## ID conventions

- Entity IDs: `S…` supplier, `C…` customer, `E…` employee, `""` run-level.
- Record IDs (evidence): 36-char UUID = invoice, `TX` = company bank
  transaction, `CP` = counterparty statement row, `GR` = goods receipt.
  `GL` = ledger entry — context only, never evidence.

Entity names come from `agent.data.load(...).suppliers/customers/employees`; the
API server (#68) exposes them via `GET /datasets/{name}/entities`.
