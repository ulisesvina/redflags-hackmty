# AGENTS.md — rules for every agent working in this repo (Claude Code, Codex, Hermes)

## What we are building
An AI forensic auditor for the HackMTY 2026 Infosys "Forensic Auditor" track. Given a company's
books it must find invoice fraud, follow the money, and hand in a case file — and must NOT accuse
suppliers it cannot back with a rule broken, a peso amount, and record IDs. See docs/brief.md.

## Layout
- `data_estate/` — synthetic company generator, validator, scorer (stdlib only). Owner: Codex. Read data_estate/README.md first.
- `data_estate/out/company_42/` — FROZEN demo dataset. Never regenerate, never edit. `tests/test_frozen_dataset.py` enforces this.
- `data_estate/out/estate_42/` — FROZEN judge-shaped export of seed 42 (`estate.db` + `csv/`), once #80 lands. Same rule, same test.
- `scripts/judges/` — the judges' `validate_format.py`, vendored verbatim (#88). `agent/submit.py` writes the judges' `submission.json` (#88); `agent/challenge.py` is the adversarial review (#91).
- `agent/` — the investigation agent: loader, detectors, tools, loop, evidence guard, case-file writer. Owner: Claude Code.
  `agent/detectors/` holds one module per detector (`<name>.py` → `detect_<name>(ds)`), auto-registered by its `__init__.py`; never edit another detector's module.
- `tests/conftest.py` — fixtures `ds` (company_42 loaded), `truth`, `scheme(type)`, `decoy_ids`. Tests may read `hidden/`; `agent/` may not.
- `demo/` — story, live-trace UI, demo script. Owner: human.
- `tests/` — pytest, one file per module (`tests/test_detect_<name>.py` for detectors). CI runs `pytest -q` on every push and PR.
- `docs/` — brief, strategy, plan, issue queue mirror, Hermes brief. `scripts/` — one-off checks such as `check_llm.py`.

## Hard rules
1. Never push to `master`. All work goes through a PR, and CI must be green before it merges.
   **Hermes merges its own PRs.** Once the required `test` check passes it runs
   `gh pr merge <n> --squash --delete-branch` itself; it does not wait for a human. Never `--admin`,
   never a PR it did not open, never on a red or pending check, and never make a check green by
   weakening, skipping or deleting a test. Other agents open the PR and leave it for a human.
2. Never read or copy anything under any `hidden/` directory into `agent/`. The agent must not see ground truth. Tests may read it.
   The string `ground_truth` must not appear anywhere under `agent/` (judges grep for it), and `agent/` never imports `data_estate`.
3. Every accusation in a case file must reference record IDs that exist in the dataset. `tests/test_case_file_contract.py` enforces this; do not weaken it.
4. Do not add heavy dependencies without an issue approving it. Stdlib + pandas + the LLM client is the baseline.
5. Contracts. **Input:** the judges' `estate_schema.sql` (a SQLite `.db` or a CSV dir with `vendors`, `invoices`, `ledger`, `bank_txns`,
   `purchase_orders`, `contracts`, `employees`, `efos_list`) **and** our legacy CSV layout; `agent.data.load(path)` accepts both (#79).
   **Output:** the judges' `submission_schema.json` (`agent/submit.py`, #88) plus our internal case file (`data_estate/score.py` docstring).
   Issues #78–#96 are the approved changes to these contracts (see `docs/SPEC_GAP.md`). Any other change to either contract needs an issue
   labelled `needs-human`; open it and stop.
6. One issue per branch. Branch name `hermes/<n>`, `cc/<n>`, or `codex/<n>`. PR title starts with `#<n>`.
7. Run `python -m pytest -q` before opening a PR. A PR with failing tests will be closed.
8. All LLM calls go to the OpenAI-compatible endpoint configured in `.env` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`):
   an open-weight model on a teammate's HPC cluster that is approved for sensitive data. Never send dataset rows,
   IDs, RFCs, or CLABEs to any other provider, and never fall back to a hosted API for anything that carries data.
   Never commit `.env`. `.env.example` lists the variables; `python scripts/check_llm.py` verifies the endpoint.

## LLM access
Copy `.env.example` to `.env` and fill it in. Read the variables with `os.environ` or the small loader in
`scripts/check_llm.py`; do not add python-dotenv. Do not hard-code model names or URLs anywhere.

## Case-file contract (summary — full spec in data_estate/score.py)
findings[]: scheme_type, accused[ids], rule, amount_mxn, evidence[record ids]
not_pursued[]: entity, reason

## Scheme types
**Judges' enum, the only values a `submission.json` finding may carry:** `phantom_vendor` · `kickback` · `round_tripping` · `threshold_splitting` · `revenue_inflation`.

**Internal (detectors, leads, rules, case file):** `efos_fake_supplier` → `phantom_vendor` · `kickback_shell` → `kickback` · `round_trip_sales` → `round_tripping` ·
`threshold_splitting` · `revenue_inflation` · `duplicate_invoice_payment` (no judges' type: reported as a control observation in `leads_not_pursued`, never a finding) · `other` (parked as suspicious, never a finding).

## Entity ids
On judge estates entity ids are `RFC:<rfc>` (vendors, customers, the company) and `EMP:<id>` (employees); on legacy datasets `S*`, `C*`, `E*`.
Detectors and tools must never assume a prefix; `agent/submit.py` maps legacy ids to the prefixed form.

## How to run things
python -m venv .venv && . .venv/bin/activate && pip install pytest pandas
python -m data_estate.generate --seed 7 --out data_estate/out/company_7     # never write to company_42
python -m data_estate.generate --seed 7 --format judges --out data_estate/out/estate_7   # judges' schema (#80); never write to estate_42
python -m data_estate.validate data_estate/out/company_42
python -m data_estate.score data_estate/out/company_42 data_estate/out/example_case_file_for_seed42.json
python -m agent.investigate <estate.db | dir> --no-llm --out case_file.json --submission submission.json   # --submission from #88; --report from #90
python scripts/judges/validate_format.py --submission submission.json --estate estate.db                      # the judges' own check (#88)
python -m pytest -q
python scripts/check_llm.py
