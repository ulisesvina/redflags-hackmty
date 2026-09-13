# PU-HackMTY — The Forensic Auditor

HackMTY 2026, Infosys track 2. An AI agent that takes a company's books plus the hint "something is wrong",
follows the money, and hands in a case file: scheme, accused entities, rule broken, peso amount, evidence record
IDs, and the leads it declined to pursue and why.

Start here: [`AGENTS.md`](AGENTS.md) (rules, binding for humans and agents) → [`docs/brief.md`](docs/brief.md)
(what the judges asked) → [`docs/PLAN.md`](docs/PLAN.md) (who does what, when) → [`docs/STRATEGY.md`](docs/STRATEGY.md).

## Layout
| Path | What | Owner |
|---|---|---|
| `data_estate/` | Synthetic Monterrey company: generator, validator, scorer (stdlib only) | Filip / Codex |
| `data_estate/out/company_42/` | Frozen demo dataset. Never regenerate. Checksum-tested. | — |
| `data_estate/out/estate_42/` | Frozen judge-shaped export of seed 42 (`estate.db`, `csv/`). Never regenerate. | — |
| `agent/` | Loader, detectors, tools, investigation loop, evidence guard, case-file writer | Sondre / Claude Code |
| `demo/` | Story, live-trace UI, demo script | whoever is free |
| `tests/` | pytest; CI runs it on every push and PR | everyone |
| `docs/` | Brief, strategy, plan, issue-queue mirror, Hermes brief, transcript, PDF | — |
| `scripts/` | One-off checks (`check_llm.py`), batch evaluation, the vendored judges' validator (`scripts/judges/`) | — |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in the HPC endpoint, key, and model
python scripts/check_llm.py   # round-trips one prompt through the endpoint
python -m pytest -q
```

## Everyday commands
```bash
python -m data_estate.generate --seed 7 --out data_estate/out/company_7   # fresh dataset; company_42 is frozen
python -m data_estate.validate data_estate/out/company_7
python -m data_estate.score data_estate/out/company_42 case_file.json
python -m data_estate.generate --seed 7 --format judges --out data_estate/out/estate_7        # judges' schema (#80)
python -m agent.investigate data_estate/out/estate_7/estate.db --out case_file.json --submission submission.json --report report.html
python scripts/judges/validate_format.py --submission submission.json --estate data_estate/out/estate_7/estate.db
python scripts/eval_batch.py --seeds 901-910 --report --format judges                             # the results slide (#86)
python -m api.server --port 8765                                   # HTTP + SSE for the frontend (api/README.md)
```

## Judges' pack
The judges score on estates generated to their own schema, validate a `submission.json`, and read a five-section case file with a
rendered money trail. `docs/SPEC_GAP.md` maps their pack onto this build and is the plan behind issues #78–#96. Seeds used for tuning:
42, 101–110, 201–205, 301–306. Seeds reserved for reporting: 901–910, never run by hand before the final evaluation.

## How work flows
GitHub issues are the queue (`docs/ISSUES.md` is the mirror). Labels: `hermes-ok` the unattended Hermes agent
may take it · `cc` Claude Code · `codex` Codex · `needs-human` a person decides. One issue per branch
(`hermes/<n>`, `cc/<n>`, `codex/<n>`), PR title starts with `#<n>`, CI must be green (required check on `master`).
Hermes merges its own PRs once CI is green; humans merge everything else. Queue order and dependencies: `docs/PLAN.md`.

The frontend is built outside this repo. Its contract with the backend is the step log (`docs/STEP_LOG.md`, #67)
and the API server (`api/server.py`, #68); `demo/sample_trace.jsonl` is a real run to build against (deterministic mode, so it carries no `tool_call`
events yet). Measured results: [`docs/eval/`](docs/eval/README.md).

The LLM runs on a teammate's HPC cluster approved for sensitive data. Dataset contents never go to any other
provider (AGENTS.md rule 8).

## Learnings
The judges asked for failures and learnings. `LEARNINGS.md` gets an entry whenever something breaks, changes, or surprises us.
