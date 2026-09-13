# `agent/` — the investigation agent

Given a company's books, the agent finds the fraud, follows the money, and hands
in a case file. It never accuses anyone it cannot back with a rule broken, a
peso amount, and record IDs (`docs/brief.md`). This package is the backend; the
frontend (built separately, outside this repo) reads the step log and the API
server.

## Modules

| module | what it does |
|---|---|
| `data.py` | load a dataset into a typed `Dataset` — our CSV layout, a judges' `.db`, or a judges' CSV dir (#2, #79). Never opens the answer key. |
| `detectors/` | one module per detector; `detect_<name>(ds) -> list[dict]`, pure & deterministic. Auto-registered. |
| `leads.py` | aggregate detector output into ranked dossiers + `scheme_hint` (#44). |
| `tools.py` | read-only tool layer the LLM may call; every result carries record IDs (#12). |
| `llm.py` | OpenAI-compatible client (via `.env`), disk cache, retries, `FakeLLM` for tests (#22). |
| `config.py` | the `.env` settings loader (`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`) (#22). |
| `rules.py` | the rule catalog R1–R5 (legal strings) (#14). |
| `guard.py` | the evidence guard: contract, recognised rule, evidence belongs to accused, kinds, 25 % amount recompute (#14). |
| `contract.py` | case-file contract validation (`findings[]`, `not_pursued[]`) (#14). |
| `steplog.py` | the step-log contract as code: `KINDS`, `REQUIRED_PAYLOAD`, `parse_lines`, `validate_entries` (#67). |
| `investigate.py` | the loop: detectors → units → (`--no-llm` fallback or LLM loop) → case file + step log (#13). |
| `report.py` | the case file a judge reads: five required sections, money trail as a diagram, Markdown + self-contained HTML (#23, #90). |
| `submit.py` | the judges' `submission.json`: prefixed ids, exhibits with a `source_table`, money trail, confidence, declined leads (#88). |

## CLI commands

All are run as `python -m agent.<module>`:

- `python -m agent.investigate <estate> [--out case_file.json] [--log runs/T.jsonl] [--submission submission.json] [--report report.html] [--seed N] [--max-leads 12] [--max-steps 12] [--no-llm]`
  — `<estate>` is a legacy dataset dir, a judges' `estate.db` or a judges' CSV dir. `--submission` defaults to
  `submission.json` next to `--out` and `--report` to `report.html`; pass `""` to skip either.
- `python -m agent.investigate --replay <log.jsonl | case_file.json> [--out case_file.json] [--submission submission.json] [--report report.html]`
  — rebuild the case file, submission and report from a stored run's step log, **with the network off**:
  run the investigation, then replay it as `--replay runs/T.jsonl` (or `--replay case_file.json`, which names its
  own log). It never constructs an `LLM` and re-validates every finding through the guard, so a tampered log drops
  the offending finding and the run still exits 0. `run_metadata` copies the original numbers and adds `replayed_from`.
- `python -m agent.submit <estate> <case_file.json> [--log run.jsonl] [--seed N] [--out submission.json]`
  — rebuild the judges' JSON from a case file that already exists.
- `python -m agent.leads <dataset_dir> [--json] [--top N]`
- `python -m agent.steplog <log_file>` — validate a step log ("OK N entries").
- `python -m agent.report <estate> <case_file.json> [--submission submission.json] [--out report.md] [--html report.html] [--log runs/T.jsonl]`
  — the submission is rebuilt from the case file when not supplied, so the two artifacts cannot drift apart.
- `python -m agent.guard <dataset_dir> <case_file.json>` and `python -m agent.contract <dataset_dir> <case_file.json>` for the guard / contract checks.

The LLM client is only reachable when `.env` is configured (see `.env.example`
and `scripts/check_llm.py`); without it the default path is the deterministic
`--no-llm` fallback.

## Two execution paths

1. **Deterministic (`--no-llm`, or no `.env`).** Turn the four known scheme
   signatures directly into findings through the same evidence guard. This is the
   stage-safe path and what CI exercises; it needs no LLM.
2. **LLM loop.** For each unit the model forms a hypothesis and calls the tool
   layer (#12) to prove it. Every `record_finding` goes through the guard (#14);
   a rejection is fed back so the model can fix and retry (up to `MAX_GUARD_RETRIES`,
   then a deterministic fallback for signature units) — so LLM and `--no-llm`
   agree on the four known schemes.

## Where outputs go

- The case file (JSON) at `--out` (default `case_file.json`).
- The step log (JSONL) at `--log` (default `runs/<UTC ts>.jsonl`), streamed and
  flushed per event. See [`docs/STEP_LOG.md`](../docs/STEP_LOG.md) for the full
  contract and how to tail it.
- The human-readable report at `--out` of `agent.report`.
- The judges' `submission.json` next to the case file (`--submission`), checked by
  their own validator: `python scripts/judges/validate_format.py --submission submission.json --estate estate.db`.
- `report.html` next to the case file (`--report`): the five sections `case_file_structure.md`
  requires, with the money trail drawn as inline SVG. No script, no external asset and no URL
  anywhere in the file, so it opens from a file path with the network off — judges may ask.

Two output contracts, both live. The case file (`findings[]`, `not_pursued[]`, our scheme
types) is defined in `data_estate/score.py` and enforced by `agent/contract.py`. The
submission is `submission_schema.json` from the judges' pack, built by `agent/submit.py`
and enforced in CI by the vendored `scripts/judges/validate_format.py`. Where they
disagree, the submission wins: a `duplicate_invoice_payment` finding is a real control
failure but not one of the judges' five scheme types, so it is *moved* into
`leads_not_pursued` with its evidence ids in the reason, never dropped and never relabelled.
