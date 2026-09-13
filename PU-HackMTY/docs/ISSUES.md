# Issue queue — snapshot of the GitHub issues (regenerated 2026-09-12). GitHub is the source of truth: `gh issue view <n>`.

| # | State | Label | Title | PR |
|---|---|---|---|---|
| #1 | CLOSED | `needs-human` | Repo skeleton + CI |  |
| #2 | CLOSED | `cc` | Loader module agent/data.py | #33 (merged) |
| #3 | CLOSED | `cc` | Case-file contract test | #34 (merged) |
| #4 | CLOSED | `hermes-ok` | detect_efos(ds) | #47 (merged) |
| #5 | CLOSED | `hermes-ok` | detect_no_receipt(ds) | #35 (merged) |
| #6 | CLOSED | `hermes-ok` | detect_duplicate_payments(ds) | #36 (merged) |
| #7 | CLOSED | `hermes-ok` | detect_employee_address_match(ds) | #37 (merged) |
| #8 | CLOSED | `hermes-ok` | detect_clabe_not_on_master(ds) | #38 (merged) |
| #9 | CLOSED | `hermes-ok` | detect_round_trip(ds) | #39 (merged) |
| #10 | CLOSED | `hermes-ok` | detect_fast_pay_no_deliverable(ds) | #40 (merged) |
| #11 | CLOSED | `hermes-ok` | detect_new_vendor_round_amounts(ds) | #41 (merged) |
| #12 | CLOSED | `cc` | Tool layer agent/tools.py | #53 (merged) |
| #13 | CLOSED | `cc` | Investigation loop agent/investigate.py | #56 (merged) |
| #14 | CLOSED | `cc` | Evidence guard agent/guard.py + rule catalog agent/rules.py | #55 (merged) |
| #15 | CLOSED | `hermes-ok` | requirements.txt + Makefile | #19 (merged) |
| #16 | CLOSED | `hermes-ok` | ruff config + fix lint in data_estate/ | #20 (merged) |
| #17 | CLOSED | `hermes-ok` | --n flag for generate.py (batch of seeds) | #60 (merged) |
| #18 | CLOSED | `hermes-ok` | tests/test_generate_batch.py: 5 seeds validate | #32 (merged) |
| #22 | CLOSED | `cc` | LLM client agent/llm.py + agent/config.py (tool calling, cache, offline fake, --tools check) | #54 (merged) |
| #23 | CLOSED | `cc` | Human-readable case file agent/report.py (money trail + tax exposure) | #57 (merged) |
| #24 | CLOSED | `codex` | generate.py crashes on ~1.5% of seeds (13, 34, 74): decoy D3 needs a logistics supplier | #59 (merged) |
| #25 | CLOSED | `codex` | Batch evaluation scripts/eval_batch.py: recall, penalty, evidence over N unseen seeds | #58 (merged) |
| #26 | OPEN | `needs-human` | Demo live-trace UI demo/trace_ui.py + demo/index.html (reads the step log, replay mode) |  |
| #27 | OPEN | `hermes-ok` | One-command demo run scripts/demo_run.py + docs/INJECT.md for judges (serves the API for the frontend) |  |
| #28 | CLOSED | `hermes-ok` | tests/test_no_hidden_access.py: mechanically enforce AGENTS.md rule 2 | #61 (merged) |
| #29 | CLOSED | `hermes-ok` | tests/test_detectors_batch.py: every planted entity hit on fresh seeds, no decoy on strong detectors | #51 (merged) |
| #30 | CLOSED | `hermes-ok` | scripts/sync_issues.py: regenerate docs/ISSUES.md from GitHub | #49 (merged) |
| #31 | OPEN | `needs-human` | Demo rehearsal pack: script, surprise-question answers, cannot-do slide, venue checks |  |
| #42 | CLOSED | `hermes-ok` | detect_kickback_outflow(ds): supplier statement outflows to an employee's personal CLABE | #46 (merged) |
| #43 | CLOSED | `hermes-ok` | Decoy-surfacing detectors: detect_name_twin_69b, detect_shared_supplier_address, detect_cash_payments | #50 (merged) |
| #44 | CLOSED | `hermes-ok` | Lead aggregation and ranking agent/leads.py (docket per entity, scheme_hint, CLI) | #52 (merged) |
| #45 | CLOSED | `hermes-ok` | ruff check in CI + fix the 3 existing lint errors | #48 (merged) |
| #65 | CLOSED | `hermes-ok` | agent/guard.py: ledger entry IDs in evidence are set aside, not a rejection | #74 (merged) |
| #66 | CLOSED | `hermes-ok` | agent/investigate.py: feed guard rejections back to the model, then fall back to the deterministic finding | #76 (merged) |
| #67 | CLOSED | `hermes-ok` | Streamed step log + docs/STEP_LOG.md contract + agent/steplog.py validator + agent/README.md refresh | #77 (merged) |
| #68 | OPEN | `hermes-ok` | api/server.py: stdlib HTTP + SSE server so the frontend can start runs and stream the step log |  |
| #69 | OPEN | `hermes-ok` | agent/clear.py: replace canned drop reasons with checks that cite records (or admit they cannot) |  |
| #70 | OPEN | `hermes-ok` | agent/investigate.py: escalate unverified weak leads to the model; 'other' findings become a suspicious tier in not_pursued |  |
| #71 | OPEN | `hermes-ok` | agent/investigate.py: investigate units concurrently (--workers) to keep a cold LLM run under 30 s |  |
| #72 | OPEN | `cc` | LLM-mode batch evaluation on 10 unseen seeds: docs/eval tables + LEARNINGS entry |  |
| #73 | CLOSED | `cc` | docs: PLAN.md refresh, HERMES_BRIEF.md for auto-merge, demo/sample_trace.jsonl, issue queue cleanup | #75 (merged) |
| #78 | OPEN | `cc` | AGENTS.md + README: judges' estate as input contract, submission.json as output contract, five scheme types |  |
| #79 | OPEN | `cc` | agent/data.py: load a judges' estate (SQLite .db or CSV dir per estate_schema.sql) into Dataset |  |
| #80 | OPEN | `codex` | generate.py --format judges: export estates to the judges' schema (SQLite + CSV) with judges'-shape ground truth; freeze estate_42 |  |
| #81 | OPEN | `codex` | generate.py: plant threshold_splitting and revenue_inflation; add same-bank-institution and fixed-fee-contract decoys |  |
| #82 | OPEN | `hermes-ok` | detect_threshold_splitting(ds): invoice clusters just under an approval limit |  |
| #83 | OPEN | `hermes-ok` | detect_revenue_inflation(ds): sales booked as revenue that were never collected or were cancelled without reversal |  |
| #84 | OPEN | `hermes-ok` | Judge-shape signatures: kickback without address, round-trip 2-hop fallback, scheme_hints as a list |  |
| #85 | OPEN | `cc` | agent/tools.py: judge-estate aware tools (RFC ids, purchase orders, contracts, trace_flow over third-party legs) |  |
| #86 | OPEN | `codex` | score.py + eval_batch.py: judges' ground-truth shape, false-accusation rate, 2% peso reconciliation, results_table.csv |  |
| #87 | OPEN | `cc` | guard: 2% per-table reconciliation to cited exhibits, exhibit policy per rule, confidence tier |  |
| #88 | OPEN | `cc` | agent/submit.py: write submission.json per submission_schema.json; vendor validate_format.py; run it in CI |  |
| #89 | OPEN | `hermes-ok` | run_metadata: count LLM calls and tokens in agent/llm.py, price constants, cost in the step log |  |
| #90 | OPEN | `hermes-ok` | agent/report.py: the judges' five-section case file with a rendered money-trail diagram (Markdown + self-contained HTML) |  |
| #91 | OPEN | `hermes-ok` | agent/challenge.py: adversarial review that tries to break every finding before it is printed |  |
| #92 | OPEN | `hermes-ok` | Entangled schemes: one entity in two findings, no double-counting, declined-leads bookkeeping |  |
| #93 | OPEN | `hermes-ok` | --replay: rebuild case file, submission and report from a stored run with the network disabled |  |
| #94 | OPEN | `hermes-ok` | agent/clear.py on judge estates: PO, contract, same-bank-institution and cancelled-invoice checks; tool_calls_made and closed_by |  |
| #95 | OPEN | `hermes-ok` | Leak hygiene: ground_truth string check under agent/, hypothesis log line names its detectors |  |
| #96 | OPEN | `hermes-ok` | api/server.py: judge-estate datasets and the submission / report.html / validate endpoints (follow-up to #68) |  |

---

## #1 Repo skeleton + CI  `needs-human`  CLOSED

## Goal
A repo that three agents (Claude Code, Codex, Hermes) can work in from hour zero, coordinated only by GitHub issues and `AGENTS.md`.

## Done (commit `c5a46d6` and the follow-up that added `agent/detectors/` and `tests/conftest.py`)
- [x] `data_estate/` unpacked from the zip (generator, validator, scorer, README); the zip and the duplicate `out/c42` removed
- [x] `data_estate/out/company_42/` committed (including `hidden/`) and frozen behind `tests/test_frozen_dataset.py` (sha256 of every byte)
- [x] CI at `.github/workflows/ci.yml`: pytest + pandas, `data_estate.validate` on company_42, `pytest -q`, on every push and PR
- [x] `AGENTS.md` (rules, `master` not `main`, rule 8: all LLM calls via the `.env` HPC endpoint), `CLAUDE.md` imports it
- [x] `docs/` (brief, STRATEGY, PLAN, ISSUES mirror, HERMES_BRIEF, transcript, PDF), `README.md`, `LEARNINGS.md`
- [x] `.env.example`, `scripts/check_llm.py`, `.gitignore`, `.gitattributes`, `pyproject.toml` (pytest config)
- [x] `agent/detectors/__init__.py` auto-registry (one module per detector, no shared-file edits) and `tests/conftest.py` fixtures
- [x] Labels `hermes-ok`, `cc`, `codex`, `needs-human`; issues #1–#18 filed

## Definition of done
- [ ] `master` pushed and the first CI run is green
- [ ] Repo owner enables branch protection on `master`: require a PR and the `ci / test` check (nobody else has admin)
- [ ] Hermes host set up per `docs/HERMES_BRIEF.md` and has opened its first PR (expected: #15)

## #2 Loader module agent/data.py  `cc`  CLOSED

## Goal
One typed, in-memory view of a dataset directory that every detector (#4–#11), the tool layer (#12) and the guard (#14) build on. Everything downstream assumes the dtypes below, so get them exactly right here.

## Spec
```python
# agent/data.py
@dataclass
class Dataset:
    path: Path
    company: dict                     # company.json: name, rfc, clabe, city
    suppliers: pd.DataFrame           # supplier_id, name, rfc, street, city, clabe, account_holder, category, onboarded, approved_by, status
    customers: pd.DataFrame           # customer_id, name, rfc, street, city, clabe
    employees: pd.DataFrame           # employee_id, name, rfc, role, home_street, home_city, personal_clabe
    invoices: pd.DataFrame            # uuid, tipo, serie, folio, fecha, fecha_timbrado, rfc_emisor, nombre_emisor, rfc_receptor, nombre_receptor, uso_cfdi, forma_pago, metodo_pago, clave_prod_serv, descripcion, cantidad, valor_unitario, subtotal, iva, total, moneda, po_number, counterparty_id, approved_by
    goods_receipts: pd.DataFrame      # receipt_id, po_number, supplier_id, invoice_uuid, fecha, descripcion, cantidad, received_by, warehouse
    bank_transactions: pd.DataFrame   # txn_id, fecha, account_clabe, direction, amount, counterparty_name, counterparty_clabe, reference, invoice_uuid
    counterparty_bank: pd.DataFrame   # record_id, entity_name, entity_clabe, fecha, direction, amount, counterparty_name, counterparty_clabe, reference
    ledger: pd.DataFrame              # entry_id, fecha, account_code, account_name, debit, credit, descripcion, invoice_uuid, txn_id
    efos_69b: pd.DataFrame            # rfc, nombre, situacion, fecha_publicacion

    def all_record_ids(self) -> set[str]: ...   # invoice uuids | txn_ids | counterparty record_ids | receipt_ids
    def all_entity_ids(self) -> set[str]: ...   # supplier_ids | customer_ids | employee_ids

def load(path: str | Path) -> Dataset: ...
```
Typing rules:
- Read every CSV with `pd.read_csv(..., dtype=str, keep_default_na=False, encoding="utf-8")` first, then convert. Empty cells must stay `""`, never NaN (joins on NaN silently fail). In company_42: 12 bank rows (payroll) have empty `invoice_uuid` and `counterparty_clabe`; 156 issued invoices have empty `po_number`; 1,791 ledger lines have empty `txn_id`.
- Dates → `datetime64[ns]`: `fecha`, `fecha_timbrado`, `onboarded`, `fecha_publicacion`.
- Money/quantity → `float64`: `subtotal`, `iva`, `total`, `cantidad`, `valor_unitario`, `amount`, `debit`, `credit`.
- Everything else stays `str`, in particular CLABEs (18 digits, 88% start with `0`), `folio` (all digits), `po_number`, `account_code` (`1020`, `2100`, …), `rfc`.
- `load` must never open anything under `hidden/`; it must work on a directory that has no `hidden/` at all.
- Also add the `ds` fixture to `tests/conftest.py`:
  ```python
  @pytest.fixture(scope="session")
  def ds(dataset_dir):
      from agent.data import load
      return load(dataset_dir)
  ```

## Test: `tests/test_loader.py`
- Row count of every frame equals the count from `csv.DictReader` on the same file (compute in-test, do not hard-code). For reference company_42 has suppliers 42, customers 19, employees 16, invoices 597, goods_receipts 357, bank_transactions 612, counterparty_bank 22, ledger 3015, efos_69b 62.
- dtypes: `invoices.fecha` is datetime64, `invoices.total` float, `suppliers.clabe` object/str; `ds.company["clabe"]` (`012580001234567890`) appears verbatim in `bank_transactions.account_clabe` (leading zero survived).
- `(ds.bank_transactions.invoice_uuid == "").sum() == 12` and no NaN anywhere (`frame.isna().sum().sum() == 0` for every frame).
- `ds.all_record_ids()` contains `"TX00001"`, `"GR00001"`, `"CP00001"` and every `evidence` ID in `data_estate/out/example_case_file_for_seed42.json`; `ds.all_entity_ids()` contains every `accused` and `not_pursued.entity` ID in that file.
- Copy company_42 to `tmp_path` without `hidden/` and `load` it: same row counts.

## Definition of done
- [ ] `agent/data.py` as specified, `ds` fixture in `tests/conftest.py`, `tests/test_loader.py` green
- [ ] No reference to `hidden` anywhere in `agent/` (`grep -r hidden agent/` is empty apart from the package docstring)
- [ ] `python -m pytest -q` green

## #3 Case-file contract test  `cc`  CLOSED

## Goal
The mechanical half of AGENTS.md rule 3: a case file that names an ID which does not exist in the dataset is invalid, full stop. This check is reused by the evidence guard (#14) and can be run by hand before the demo.

## Spec
```python
# agent/contract.py
SCHEME_TYPES = {"efos_fake_supplier", "kickback_shell", "round_trip_sales", "duplicate_invoice_payment", "other"}

def validate_case_file(case: dict, ds: Dataset) -> list[str]:
    """Return [] when valid, else one human-readable error per problem, e.g.
    'findings[0].evidence: TX99999 not in dataset'  'findings[2].accused: S99999 not in dataset'."""
```
Checks, all of them:
- top level has `findings` (list) and `not_pursued` (list); nothing else is required
- each finding: `scheme_type ∈ SCHEME_TYPES`; `accused` non-empty list of str, each in `ds.all_entity_ids()`; `rule` non-empty str; `amount_mxn` int/float > 0; `evidence` non-empty list of str, each in `ds.all_record_ids()`; no duplicate IDs inside `accused` or `evidence`
- each not_pursued: `entity` in `ds.all_entity_ids()`, `reason` non-empty str
- an entity may not appear both in some finding's `accused` and in `not_pursued`
- CLI: `python -m agent.contract <dataset_dir> <case_file.json>` prints the errors and exits 1, or prints `OK` and exits 0

Contract reference: docstring of `data_estate/score.py`. Do not change that contract.

## Test: `tests/test_case_file_contract.py`
- `data_estate/out/example_case_file_for_seed42.json` → `[]`
- same file with one evidence ID replaced by `"TX99999"` → exactly one error, containing `TX99999` and `findings[<i>]`
- accused `"S99999"` → one error; `scheme_type: "bribery"` → one error; `amount_mxn: 0` → one error; an entity both accused and not_pursued → one error
- a finding with `evidence: []` → one error
- CLI: `subprocess.run([...agent.contract, dataset, bad_file])` returns 1, good file returns 0

## Definition of done
- [ ] `agent/contract.py` + `tests/test_case_file_contract.py` green; AGENTS.md rule 3 now points at a real file
- [ ] `python -m pytest -q` green

**Depends on #2** (`all_record_ids`, `all_entity_ids`).

## #4 detect_efos(ds)  `hermes-ok`  CLOSED

## Goal
The cheapest, strongest lead: a supplier whose RFC is on SAT's Article 69-B list (EFOS). Match on **RFC**, never on name: one decoy in every dataset has the same *name* as a listed company but a different RFC.

## Spec
`agent/detectors/efos.py` → `detect_efos(ds) -> list[dict]`
1. Inner-join `ds.suppliers` to `ds.efos_69b` on `rfc` (exact, case-sensitive string equality).
2. Keep rows with `situacion` in `{"Presunto", "Definitivo"}`. `Desvirtuado` and `Sentencia favorable` mean SAT cleared them: not a lead.
3. Do **not** filter on `fecha_publicacion`. In company_42 the Definitivo supplier was published 2025-11-15, after every one of its invoices (Feb–Aug 2025). That lag is the whole point of the scheme; the finding still stands.
4. One dict per matched supplier, sorted by `entity_id`:
   - `entity_id`: supplier_id · `rfc` · `name` · `situacion` · `fecha_publicacion` (ISO str)
   - `n_invoices`, `total_mxn`: count and sum of `total` over that supplier's `invoices` rows with `tipo == "recibida"` and `counterparty_id == supplier_id`
   - `evidence`: those invoice UUIDs plus the `txn_id` of every `bank_transactions` row with `direction == "out"` whose `invoice_uuid` is one of them

## Data facts (company_42, verified)
- `efos_69b` has 62 rows: 17 Presunto, 17 Definitivo, 13 Desvirtuado, 15 Sentencia favorable. Exactly 2 supplier RFCs match with an active status; one is Presunto (published 2025-07-10), one Definitivo (2025-11-15). Each has 5 invoices.
- Decoy: supplier `Refacciones San Nicolás S de RL de CV` has the same name as a Definitivo entry but a different RFC. It must not appear.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_efos.py`
- `{r["entity_id"]}` == `{e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}` (2 suppliers)
- for each result, `situacion == e["efos_status"]`, `set(evidence) ⊇ set(e["invoice_uuids"]) | set(e["bank_txn_ids"])`, `n_invoices == len(e["invoice_uuids"])`
- no `entity_id` in `decoy_ids`
- result is `json.dumps`-able and sorted by `entity_id`

## Definition of done
- [ ] Module + test as above, `python -m pytest -q` green, no other files touched (except adding nothing to `__init__.py`)
- [ ] Finds both planted EFOS suppliers, does not return the name-twin decoy

**Depends on #2** (`ds` fixture and dtypes). If #2 is still open, skip this issue (see `docs/HERMES_BRIEF.md`).

## #5 detect_no_receipt(ds)  `hermes-ok`  CLOSED

## Goal
"Materialidad": a purchase with no proof of delivery. This detector lists every purchase invoice without a goods receipt and says whether the supplier's category should have had one. It is a lead generator and context provider for the loop, not an accusation: most hits are honest service suppliers.

Note: the original one-line spec ("goods categories with no receipt") returns **zero rows** on company_42, because every goods invoice there has a receipt by construction. The spec below is broadened so the detector is testable and useful.

## Spec
`agent/detectors/no_receipt.py` → `detect_no_receipt(ds) -> list[dict]`
1. Take `ds.invoices` with `tipo == "recibida"` (441 rows in company_42). Supplier = `counterparty_id`.
2. Left-join `ds.goods_receipts` on `invoice_uuid`; keep invoices with **no** receipt.
3. Join `ds.suppliers.category`. `receipt_required = category in {"materia_prima", "refacciones", "consumibles"}` (goods categories; `servicios`, `logistica`, `renta_util` are services and never have receipts).
4. One dict per invoice, sorted by `(entity_id, fecha, invoice_uuid)`:
   `entity_id` (supplier) · `invoice_uuid` · `fecha` (ISO) · `category` · `receipt_required` (bool) · `total_mxn` · `descripcion` · `approved_by` · `po_number` · `evidence = [invoice_uuid]`

## Data facts (company_42, verified)
- 84 purchase invoices have no receipt: servicios 58, renta_util 15, logistica 11. None of them is `receipt_required` (0 goods invoices lack a receipt).
- Every planted purchase invoice (both EFOS suppliers, the kickback shell, the round-trip supplier) is in that set, and so is the law-firm decoy's single invoice ("Honorarios — litigio mercantil exp. 412/2025"). The other four decoys all have receipts.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_no_receipt.py`
- `all(not r["receipt_required"] for r in result)`
- `len(result) == n_recibida - n_distinct_invoice_uuid_in_goods_receipts` (compute both from `ds`)
- returned UUIDs ⊇ every `invoice_uuids` of `scheme("efos_fake_supplier")["entities"]` and of `scheme("kickback_shell")["entities"][0]`, and every `legs[i]["purchase_invoice"]` of `scheme("round_trip_sales")["entities"][0]`
- the law-firm decoy (`looks_like` starts with `"Large one-off"`) has its `invoice_uuid` in the result, with `category == "servicios"`
- no row whose `entity_id` is the decoy with `looks_like` starting `"New vendor"`, `"Shares address"`, or `"Cash payments"`

## Definition of done
- [ ] Module + test green; docstring states this is a lead list, not an accusation list
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #6 detect_duplicate_payments(ds)  `hermes-ok`  CLOSED

## Goal
The same invoice paid twice. In this scheme the **supplier is honest**; the accusation targets the payment (a control failure or embezzlement), so the detector reports per invoice, and the docstring must say so.

## Spec
`agent/detectors/duplicate_payments.py` → `detect_duplicate_payments(ds) -> list[dict]`
1. `ds.bank_transactions` with `direction == "out"` **and** `invoice_uuid != ""` (12 payroll rows have an empty `invoice_uuid`; never group on `""`).
2. Group by `invoice_uuid`; keep groups with 2 or more transactions.
3. Join `ds.invoices` (`uuid`) for `counterparty_id` (supplier) and `total`.
4. One dict per invoice, sorted by `invoice_uuid`:
   `entity_id` (supplier) · `invoice_uuid` · `n_payments` · `txn_ids` (ordered by `fecha`, then `txn_id`) · `fechas` (ISO, same order) · `clabes` (same order) · `amounts` (same order) · `invoice_total_mxn` · `overpaid_mxn = sum(amounts) - invoice_total` · `evidence = [invoice_uuid] + txn_ids`

## Data facts (company_42, verified)
- Exactly 3 invoices are paid twice, all from one honest goods supplier. The second payment goes to a CLABE that is not on the supplier master (that is #8's job to flag) 10–40 days after the first, and is booked to expense `6000` instead of AP `2100` (visible in `ds.ledger`, not this detector's job).
- Baseline invoices are paid exactly once; there are no accidental duplicates.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_duplicate_payments.py`
- `ent = scheme("duplicate_invoice_payment")["entities"][0]`; `len(result) == 3 == len(ent["payments"])`
- `{r["invoice_uuid"]}` == `{p["invoice_uuid"] for p in ent["payments"]}`
- for each row, `set(r["txn_ids"]) == {p["original_txn"], p["duplicate_txn"]}` and `r["entity_id"] == ent["supplier_id"]` and `r["n_payments"] == 2` and `abs(r["overpaid_mxn"] - r["invoice_total_mxn"]) < 0.01`
- no other `entity_id` appears; nothing in `decoy_ids`

## Definition of done
- [ ] Module + test green; docstring says the supplier is honest and the lead is about the payment
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #7 detect_employee_address_match(ds)  `hermes-ok`  CLOSED

## Goal
Undisclosed related party: a supplier registered at an employee's home. Combined with "the same employee approves the supplier", this is the tell for the kickback shell.

## Spec
`agent/detectors/employee_address.py` → `detect_employee_address_match(ds) -> list[dict]`
1. Inner-join `ds.suppliers` `(street, city)` to `ds.employees` `(home_street, home_city)`; exact match after `.str.strip()` on both sides. Do **not** fuzzy-match and do **not** compare supplier addresses to other suppliers' addresses (that is the shared-office decoy).
2. `same_approver = suppliers.approved_by == employees.employee_id` for the matched pair.
3. One dict per (supplier, employee) pair, sorted by `(entity_id, employee_id)`:
   `entity_id` (supplier) · `supplier_name` · `employee_id` · `employee_name` · `employee_role` · `same_approver` (bool) · `street` · `city` · `n_invoices` · `total_mxn` (that supplier's `recibida` invoices) · `evidence` = those invoice UUIDs + the `out` `txn_id`s that reference them

## Data facts (company_42, verified)
- Exactly one hit: the shell `Gestoría y Enlace … S de RL de CV` sits at the home address of the purchasing manager (`Gerente de Compras`), who also approved it (`same_approver == True`). 8 invoices.
- 16 employees. The purchasing manager approves 41 of 42 suppliers, so `same_approver` alone means nothing; only the address match makes it a lead.
- Decoy: two logistics suppliers share one commercial address with each other. Neither address is an employee's home. They must not appear.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_employee_address_match.py`
- `ent = scheme("kickback_shell")["entities"][0]`; `len(result) == 1`
- `result[0]["entity_id"] == ent["supplier_id"]`, `result[0]["employee_id"] == ent["employee_id"]`, `result[0]["same_approver"] is True`
- `set(result[0]["evidence"]) ⊇ set(ent["invoice_uuids"]) | set(ent["bank_txn_ids"])`
- no `entity_id` in `decoy_ids` (in particular not the `"Shares address"` decoy)

## Definition of done
- [ ] Module + test green
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #8 detect_clabe_not_on_master(ds)  `hermes-ok`  CLOSED

## Goal
Payment diversion: money for a real invoice sent to a bank account that is not the supplier's account of record.

## Spec
`agent/detectors/clabe_mismatch.py` → `detect_clabe_not_on_master(ds) -> list[dict]`
1. `ds.bank_transactions` with `direction == "out"` and `invoice_uuid != ""`.
2. Join `ds.invoices` on `uuid` to get `counterparty_id` (supplier), then `ds.suppliers` on `supplier_id` to get the master `clabe`.
3. Keep rows where `counterparty_clabe != clabe`. Compare as strings: CLABEs are 18 digits and 88% of them start with `0`; if you ever see 17-digit values the loader is wrong, stop and comment on #2.
4. One dict per transaction, sorted by `txn_id`:
   `entity_id` (supplier) · `txn_id` · `invoice_uuid` · `fecha` (ISO) · `amount_mxn` · `paid_clabe` · `master_clabe` · `counterparty_name` · `evidence = [txn_id, invoice_uuid]`

## Data facts (company_42, verified)
- Exactly 3 hits: the second payments of the three duplicate-paid invoices (#6), all to the same alternate CLABE, all for the same honest supplier. The original payments go to the master CLABE and must not appear.
- Payroll rows (`counterparty_clabe == ""`, `invoice_uuid == ""`) must be excluded by step 1.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_clabe_not_on_master.py`
- `ent = scheme("duplicate_invoice_payment")["entities"][0]`; `len(result) == 3`
- `{r["txn_id"]}` == `{p["duplicate_txn"] for p in ent["payments"]}`; no `p["original_txn"]` appears
- every `r["paid_clabe"] == ent["alternate_clabe"]` and `r["entity_id"] == ent["supplier_id"]`
- every `paid_clabe` and `master_clabe` is an 18-character digit string

## Definition of done
- [ ] Module + test green
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #9 detect_round_trip(ds)  `hermes-ok`  CLOSED

## Goal
Money that leaves as a purchase and comes back as a sale. This is the one scheme no single-row rule can see; it needs the counterparty statement (`counterparty_bank`) to bridge the two legs.

## Spec
`agent/detectors/round_trip.py` → `detect_round_trip(ds, *, forward_min_ratio=0.95, forward_days=7, return_min_ratio=0.80, return_days=14) -> list[dict]`

For every outgoing payment `O` (`ds.bank_transactions`, `direction == "out"`, amount `A`):
1. **Forward leg.** Find `F` in `ds.counterparty_bank` with `entity_clabe == O.counterparty_clabe`, `direction == "out"`, `O.fecha ≤ F.fecha ≤ O.fecha + forward_days`, `F.amount ≥ forward_min_ratio × A`.
2. **Return leg.** For each `F`, find `I` in `ds.bank_transactions` with `direction == "in"`, `I.counterparty_clabe == F.counterparty_clabe`, `F.fecha ≤ I.fecha ≤ F.fecha + return_days`, `I.amount ≥ return_min_ratio × F.amount`.
3. One dict per `(O, F, I)` chain, sorted by `out_txn`:
   `entity_id` (supplier of `O`, via `invoices.counterparty_id` of `O.invoice_uuid`; `""` if none) · `customer_id` (via `invoices.counterparty_id` of `I.invoice_uuid`; `""` if none) · `out_txn` · `forward_record` · `in_txn` · `purchase_invoice` (`O.invoice_uuid`) · `sales_invoice` (`I.invoice_uuid`) · `amount_out` · `amount_forward` · `amount_in` · `days_out_to_forward` · `days_forward_to_in` · `evidence` = `[purchase_invoice, out_txn, forward_record, sales_invoice, in_txn]` without empty strings

**Why the windows are 7 and 14 days, not 5 and 10.** Every hop date rolls forward to the next business day. Across seeds 1–200 the forward leg lands 1–5 days after our payment and the return leg 1–11 days after the forward (seed 105 has an 11-day return; company_42 tops out at 6). Defaults of 5/10 would miss chains on other seeds; 7/14 keep a margin and cannot create false chains, because no honest customer ever receives money from one of our suppliers in `counterparty_bank`. On company_42, 5/10 and 7/14 give identical results. `tests/test_detectors_batch.py` (#29) checks seed 105.

**Why `return_min_ratio` is 0.80, not 0.90.** The forward is 98% of the outgoing total, but the "sale" that brings it back is invoiced net of IVA, so the inbound total is ≈ 0.98 / 1.16 ≈ 0.845 of the outbound total and 0.862 of the forwarded amount. On company_42 all three planted legs return exactly 0.862 of the forward; a 0.90 threshold finds **nothing** (verified). 0.80 finds exactly the three planted chains.

## Data facts (company_42, verified)
- `counterparty_bank` has 22 rows for only two entities: the kickback shell and the round-trip supplier. Both receive our payments (`direction == "in"`) and forward them (`direction == "out"`).
- 3 planted chains: forward 1–3 days after our payment, return 5–6 days after the forward. Amounts: out 348,000 → forward 341,040 → in 294,000 (and the same shape for the other two).
- The kickback shell forwards ~40% to an employee's personal CLABE; that CLABE never pays us, so no chain is produced there. Good.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_round_trip.py`
- `ent = scheme("round_trip_sales")["entities"][0]`; `len(result) == len(ent["legs"]) == 3`
- `{(r["out_txn"], r["forward_record"], r["in_txn"])}` == `{(l["out_txn"], l["forward_record"], l["in_txn"]) for l in ent["legs"]}`
- for each row: `purchase_invoice`/`sales_invoice` equal the leg's `purchase_invoice`/`sales_invoice`; `entity_id == ent["supplier_id"]`; `customer_id == ent["customer_id"]`; `0.8 ≤ amount_in / amount_forward ≤ 1.0`; `0 ≤ days_forward_to_in ≤ 14`
- `detect_round_trip(ds, return_min_ratio=0.90) == []` (documents the IVA effect so nobody "fixes" the threshold back)
- nothing in `decoy_ids`

## Definition of done
- [ ] Module + test green; the docstring explains the 0.80 ratio and the 7/14-day windows
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #10 detect_fast_pay_no_deliverable(ds)  `hermes-ok`  CLOSED

## Goal
Service invoices with no deliverable that were paid unusually fast. Honest suppliers get paid on 15–45 day terms; the planted schemes are paid within a week. This detector **will** flag the law-firm decoy. That is expected and correct: it is a lead, the loop clears it (court case number, approved by the director).

## Spec
`agent/detectors/fast_pay.py` → `detect_fast_pay_no_deliverable(ds, *, max_days=10) -> list[dict]`
1. `ds.bank_transactions` with `direction == "out"` and `invoice_uuid != ""`, joined to `ds.invoices` (`uuid`, `tipo == "recibida"`) and `ds.suppliers` (`counterparty_id` → `category`).
2. Keep invoices with **no** `goods_receipts` row **and** `category in {"servicios", "logistica", "renta_util"}` (service categories never have receipts; goods without receipts are #5's business).
3. `days_to_pay = (txn.fecha - invoice.fecha).days`; keep `days_to_pay ≤ max_days`.
4. One dict per (invoice, payment), sorted by `(entity_id, fecha_invoice, invoice_uuid)`:
   `entity_id` (supplier) · `invoice_uuid` · `txn_id` · `category` · `fecha_invoice` · `fecha_paid` (ISO) · `days_to_pay` · `total_mxn` · `descripcion` · `approved_by` · `evidence = [invoice_uuid, txn_id]`

**Why `max_days` is 10, not 7.** Planted payments land 1–7 days after the invoice; honest service invoices are never paid before day 15 (no honest purchase of any kind before day 12 in company_42). Payment dates roll forward to the next business day, so a 7-day term can land on day 9 in other seeds. 10 keeps the margin on both sides; 7, 10 and 12 give identical results on company_42.

## Data facts (company_42, verified)
- 22 hits: 8 for the kickback shell, 5 + 5 for the two EFOS suppliers, 3 for the round-trip supplier, 1 for the law-firm decoy (paid in 4 days, 380,000 subtotal, approved by the director).

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_fast_pay_no_deliverable.py`
- `expected = {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]} | {scheme("kickback_shell")["entities"][0]["supplier_id"], scheme("round_trip_sales")["entities"][0]["supplier_id"], law_firm["supplier_id"]}` where `law_firm` is the decoy whose `looks_like` starts with `"Large one-off"`; assert `{r["entity_id"]} == expected`
- rows per supplier: `len(e["invoice_uuids"])` for each EFOS entity and the shell, `len(legs)` for the round-trip supplier, 1 for the law firm whose `invoice_uuid` equals `law_firm["invoice_uuid"]`
- every `0 ≤ r["days_to_pay"] ≤ 10`; no other decoy in the result
- `detect_fast_pay_no_deliverable(ds, max_days=0) == []`

## Definition of done
- [ ] Module + test green; docstring says the law firm is an expected lead
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #11 detect_new_vendor_round_amounts(ds)  `hermes-ok`  CLOSED

## Goal
Classic EFOS smell: a recently onboarded supplier whose invoices are suspiciously round. Flags the new-vendor decoy too, by design: it is a lead, and the loop clears it because every one of its invoices has a warehouse-signed receipt.

## Spec
`agent/detectors/new_vendor_round.py` → `detect_new_vendor_round_amounts(ds, *, since="2024-07-01", min_share=0.6) -> list[dict]`
1. Suppliers with `onboarded >= since` (six months before the fiscal year starts; keep it a parameter) and at least one `recibida` invoice.
2. Per supplier, `round_share` = share of its invoices whose **`subtotal`** is a multiple of 1,000 (`subtotal % 1000 == 0`, compare with a tolerance of 0.005 after rounding to 2 decimals).
3. Keep `round_share >= min_share`.
4. One dict per supplier, sorted by `entity_id`:
   `entity_id` · `name` · `category` · `onboarded` (ISO) · `first_invoice` (ISO) · `n_invoices` · `n_round` · `round_share` · `total_mxn` · `evidence` = that supplier's invoice UUIDs

**Use `subtotal`, not `total`.** Totals carry 16% IVA: a round 85,000 subtotal is a 98,600 total. On `total` the kickback shell's share is 0.0 and this detector misses it (verified); on `subtotal` it is 1.0.

## Data facts (company_42, verified)
- 5 hits, all with `round_share == 1.0`: the new-vendor decoy (onboarded 2025-06-02), both EFOS suppliers (onboarded 2024-10-23 and 2024-12-02), the kickback shell (2025-03-03), the round-trip supplier (2025-04-01).
- Baseline suppliers are onboarded between 2019 and 2024-10 and their subtotals are practically never round thousands. The law firm's single 380,000 invoice is round, but it was onboarded years earlier, so the date filter removes it.

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file.

### Ground-truth shape (for the test only)
`truth["schemes"]` is a list; `scheme(t)` returns the one with `type == t`. `truth["decoys"]` is a list of `{supplier_id, rfc, name, looks_like, why_honest}` (the law-firm decoy also has `invoice_uuid`). Identify a decoy by the start of `looks_like`: `"New vendor"`, `"Name almost"`, `"Shares address"`, `"Large one-off"`, `"Cash payments"`.

## Test: `tests/test_detect_new_vendor_round_amounts.py`
- `expected = {new_vendor_decoy["supplier_id"]} | {e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]} | {scheme("kickback_shell")["entities"][0]["supplier_id"], scheme("round_trip_sales")["entities"][0]["supplier_id"]}` where the decoy is the one whose `looks_like` starts with `"New vendor"`; assert `{r["entity_id"]} == expected`
- every row: `round_share >= 0.6`, `onboarded >= "2024-07-01"`, `n_invoices >= 1`, `len(evidence) == n_invoices`
- no other decoy in the result
- `detect_new_vendor_round_amounts(ds, since="2026-01-01") == []`

## Definition of done
- [ ] Module + test green; docstring says the new-vendor decoy is an expected lead
- [ ] `python -m pytest -q` green

**Depends on #2.** If #2 is still open, skip this issue.

## #12 Tool layer agent/tools.py  `cc`  CLOSED

## Goal
The only way the LLM touches data. Every tool returns JSON-serialisable dicts whose rows carry record IDs, so anything the model cites can be re-checked by the guard (#14). No tool ever produces a number the model could not point back to a row.

## Spec
```python
# agent/tools.py
class Tools:
    def __init__(self, ds: Dataset): ...
    def get_supplier(self, supplier_id: str) -> dict
    def get_customer(self, customer_id: str) -> dict
    def get_employee(self, employee_id: str) -> dict
    def get_invoices(self, counterparty_id: str, limit: int = 50) -> list[dict]
    def get_bank_txns(self, *, counterparty_clabe: str = "", invoice_uuid: str = "", direction: str = "", limit: int = 100) -> list[dict]
    def get_receipts(self, invoice_uuid: str) -> list[dict]
    def check_69b(self, rfc: str) -> dict
    def trace_flow(self, clabe: str, *, days: int = 10, min_ratio: float = 0.8, depth: int = 2) -> list[dict]
    def query_ledger(self, *, invoice_uuid: str = "", txn_id: str = "", account_code: str = "", limit: int = 100) -> list[dict]

TOOL_SCHEMAS: list[dict]   # OpenAI function-calling schemas, one per method, descriptions written for the model
```
Shapes:
- `get_supplier`: the master row + `efos: {listed, situacion, fecha_publicacion}` + `stats: {n_invoices, total_mxn, first_invoice, last_invoice, n_with_receipt, median_days_to_pay}` + `employee_links: [{employee_id, kind: "address"|"clabe"|"approver", detail}]`.
- `get_invoices`: invoice rows (drop `nombre_*`/`moneda`/`serie` noise) with `has_receipt`, `receipt_ids`, `paid_by` (txn ids), `days_to_pay` (first payment).
- `get_bank_txns`: rows of `bank_transactions` filtered by any combination of the keyword args.
- `check_69b`: `{rfc, listed: bool, situacion, fecha_publicacion, nombre, name_matches: [{rfc, nombre, situacion}]}` where `name_matches` are list entries whose `nombre` equals the supplier's name ignoring the legal suffix (`SA de CV` vs `S de RL de CV`). Exact RFC decides `listed`; `name_matches` exists so the model can *see* the decoy trap and explain why it is not a match.
- `trace_flow`: hops starting from `counterparty_bank` rows with `entity_clabe == clabe`, following `counterparty_clabe` up to `depth`; each hop `{hop, record_id or txn_id, fecha, from_clabe, to_clabe, amount, returns_to_company: bool}` where `returns_to_company` is true when a later `bank_transactions` `in` row from that CLABE exists within `days` and `≥ min_ratio` of the amount.
- `query_ledger`: ledger rows; lets the model see that a duplicate payment was booked to `6000` instead of `2100`.
- Every list is capped at `limit`, sorted deterministically, dates ISO strings, floats plain. Unknown IDs return `{"error": "... not found"}` rather than raising. Never touches `hidden/`.

## Test: `tests/test_tools.py`
- Pick IDs from the `scheme(...)` fixtures. `get_supplier` on an EFOS supplier: `efos.listed is True`, `stats.n_with_receipt == 0`. On the kickback shell: `employee_links` contains an `"address"` and an `"approver"` link to the same employee.
- `check_69b` on the name-twin decoy's RFC: `listed is False`, `name_matches` non-empty.
- `trace_flow` from the round-trip supplier's CLABE: a hop with `returns_to_company is True`.
- `get_bank_txns(invoice_uuid=<duplicate uuid>)` returns 2 rows; `query_ledger(txn_id=<duplicate txn>)` shows account `6000`.
- `json.dumps` succeeds on every tool result; every result is `≤ limit`; unknown ID → `error` key.
- `TOOL_SCHEMAS` names match the methods and each has `parameters.type == "object"`.

## Definition of done
- [ ] `agent/tools.py`, `tests/test_tools.py` green, `python -m pytest -q` green

**Depends on #2.**

## #13 Investigation loop agent/investigate.py  `cc`  CLOSED

## Goal
The agent: detectors produce leads, the LLM forms a hypothesis per lead and calls tools to prove or drop it, the guard (#14) keeps invented evidence out, and the result is a case file `data_estate/score.py` can score. The step log is what the demo shows on screen.

## Spec
CLI: `python -m agent.investigate <dataset_dir> [--out case_file.json] [--log runs/<timestamp>.jsonl] [--max-leads 12] [--max-steps 12] [--no-llm]`

Flow:
1. `load` (#2) → `agent.detectors.run_all(ds)` → group leads by `entity_id`; rank by (number of distinct detectors hit, `total_mxn`).
2. For each entity (up to `--max-leads`): build a dossier (all its leads with their fields) and run the LLM loop: system prompt = scheme types, the rule catalog from `agent/rules.py` (#14), the case-file contract, and the instruction that an accusation needs a rule, a peso amount and evidence IDs, or the lead is dropped with a reason. The model gets `TOOL_SCHEMAS` (#12) plus two terminal tools: `record_finding(scheme_type, accused, rule_id, amount_mxn, evidence, narrative)` and `drop_lead(entity_id, reason)`. `temperature=0`, at most `--max-steps` tool calls per lead, then force a decision.
3. Every `record_finding` goes through `guard` (#14); a rejected finding is logged and turned into a `drop_lead` with the guard's reason.
4. Write `findings[]` and `not_pursued[]` per the contract, validate with `agent.contract` (#3), write the file.
5. Step log, one JSON object per line: `{"ts": ISO-8601, "entity_id": "S00030" | "", "step": int, "kind": ..., "payload": {...}}`. This is the demo UI's data source (#26 renders exactly this); keep it stable. Kinds and payloads:
   - `run_start`: `{dataset, n_leads, mode: "llm"|"no-llm", model}`
   - `lead`: `{entity_id, name, rank, detectors: [detector names], n_detectors, total_mxn, leads: [the lead dicts]}`
   - `hypothesis`: `{text, scheme_type}` (the model's first message for the entity; in `--no-llm` mode a fixed sentence per signature)
   - `tool_call`: `{name, args}`
   - `tool_result`: `{name, n_rows, summary, ids: [record ids in the result, at most 50], rows: [at most 5 rows]}`
   - `decision`: `{action: "record_finding", finding: {scheme_type, accused, rule, amount_mxn, evidence, narrative}}` or `{action: "drop_lead", reason}`
   - `guard`: `{accepted: bool, reasons: [str], finding}`
   - `run_end`: `{n_findings, n_not_pursued, wall_s, case_file, report}`

LLM access: only through `agent.llm.LLM` built from `agent.config.settings()` (#22); never construct an HTTP client here. `--no-llm`, or `settings()` returning `None` (no `.env`), selects the deterministic fallback below. Tests drive the loop with `agent.llm.FakeLLM`. Use `agent.llm.assistant_message` / `tool_message` to build the conversation. Nothing with dataset content goes anywhere else (AGENTS.md rule 8).

Speed: response caching lives in `agent.llm` (#22); target ≤ 90 s for company_42 and print the wall time.

Entry point: expose `run(dataset_dir, *, out, log, no_llm=False, max_leads=12, max_steps=12, llm=None) -> dict` (returns the case-file dict after writing it and the log) so the batch evaluation (#25) and the demo runner (#27) call it in-process; the CLI is a thin wrapper around it. `llm=None` means build it from `settings()`.

Findings keep the model's `narrative` (a short string) through the guard (#14 keeps it, truncated) so the human-readable report (#23) can print it; the scorer ignores extra keys.

`--no-llm`: deterministic fallback that turns the four known scheme signatures (EFOS match; address match + counterparty outflow to employee; round-trip chain; duplicate payment + CLABE mismatch) into findings via the same guard, and lists everything else as not pursued with the detector's reason. This is the demo's safety net if the cluster is unreachable; it must also pass the DoD scores.

## Tests: `tests/test_investigate.py`
- `agent.llm.FakeLLM` (#22) scripted with tool calls and a final `record_finding`/`drop_lead` drives one lead end to end without a network; asserts the log has `run_start → lead → hypothesis → tool_call → tool_result → decision → guard → run_end` and the case file validates.
- `run(...)` returns the same dict it wrote; calling it twice with the same arguments and `FakeLLM` gives identical files.
- `--no-llm` on company_42: `score()` from `data_estate.score` gives `results_recall >= 0.75`, `judgment_penalty == 0`, `evidence_validity >= 0.9`, and `not_pursued` contains all five decoy IDs.
- `@pytest.mark.llm` end-to-end with the real endpoint, auto-skipped when `.env` is missing (CI has no `.env`).

## Definition of done
- [ ] `python -m agent.investigate data_estate/out/company_42 --out case_file.json` then `python -m data_estate.score data_estate/out/company_42 case_file.json`: `results_recall >= 0.75`, `judgment_penalty == 0`
- [ ] Same with `--no-llm`
- [ ] Every decoy appears in `not_pursued` with a reason a non-engineer can read
- [ ] `python -m pytest -q` green without `.env`

**Depends on #12, #14 and #22**, and on detectors #4–#11 as they land (the loop must run with whatever subset is merged).

## #14 Evidence guard agent/guard.py + rule catalog agent/rules.py  `cc`  CLOSED

## Goal
"The LLM proposes, deterministic code proves." Nothing enters the case file unless every cited ID exists, the rule is one we recognise, and the peso amount is consistent with the records. This is the answer to "how do you know it did not hallucinate?".

## Spec
```python
# agent/rules.py
@dataclass(frozen=True)
class Rule:
    id: str                      # "R1".."R5"
    scheme_types: frozenset[str] # which scheme_type values it may be used with
    legal: str                   # citation text that goes into the case file's "rule" field
    evidence_kinds: frozenset[str]   # {"invoice","txn","cp","receipt"} that must be present
    amount: Callable[[Finding, Dataset], float]   # recompute the amount from the accused entities' records
RULES: dict[str, Rule]
```
Initial catalog (legal text must equal the strings in `data_estate/out/example_case_file_for_seed42.json` so that file passes):
- R1 EFOS deduction: `scheme_types={efos_fake_supplier}`, legal `"CFF Art. 69-B (operaciones inexistentes); CFF Art. 29-A; LISR Art. 27 (deducción improcedente)"`, evidence needs invoice + txn, amount = sum of `total` of the accused suppliers' `recibida` invoices.
- R2 kickback / related party: `{kickback_shell}`, legal = the kickback string from the example file, evidence needs invoice + txn + cp, amount = sum of the accused supplier's invoice totals.
- R3 round trip: `{round_trip_sales}`, legal `"Simulación de operaciones (CFF Art. 69-B / 113 Bis); revenue recognition — fictitious sales"`, evidence needs invoice + txn + cp, amount = sum of `total` of `emitida` invoices to the accused customer.
- R4 duplicate payment: `{duplicate_invoice_payment}`, legal `"Control failure / possible embezzlement; LISR Art. 27 (deducción duplicada)"`, evidence needs invoice + txn, amount = sum of the second-and-later payments per invoice for the accused supplier.
- R5 other: `{other}`, no amount recomputation, but evidence must exist and be non-empty.

```python
# agent/guard.py
def guard(finding: dict, ds: Dataset) -> tuple[dict | None, list[str]]:
    """Return (clean_finding, []) or (None, reasons). Never raises."""
```
Checks, in order, all reasons collected:
1. `agent.contract` (#3) checks on this single finding (IDs exist, no duplicates, amount > 0, scheme type known).
2. `rule` is a catalog id or exactly a catalog `legal` string; the finding's `scheme_type` is allowed for it. Output finding always carries the `legal` text in `rule`.
3. Every cited evidence ID belongs to an accused entity's records (its invoices, payments of those invoices, counterparty rows of its CLABE, receipts of its invoices). Evidence about someone else is a reason to reject.
4. Evidence kinds required by the rule are present.
5. `amount_mxn` within 25% of the rule's recomputation (the scorer's tolerance). On mismatch, reject with both numbers in the reason.
6. Strip unknown fields (keep an optional `narrative` string, truncated to 1,000 characters, for the human-readable report #23), dedupe `accused` and `evidence`, round `amount_mxn` to 2 decimals.

## Test: `tests/test_guard.py`
- Each of the four findings in the example case file passes unchanged (apart from rounding). A finding with `narrative: "x" * 2000` and an unknown key `foo` comes back with `narrative` of length 1,000 and no `foo`.
- Fabricated evidence `"TX99999"` → rejected, reason names it. Evidence from another supplier → rejected. `rule: "made up"` → rejected. `amount_mxn` ×3 → rejected with both numbers. Rule/scheme mismatch (R1 with `kickback_shell`) → rejected. `rule: "R1"` → accepted and rewritten to the legal text.

## Definition of done
- [ ] `agent/rules.py`, `agent/guard.py`, `tests/test_guard.py` green; `python -m pytest -q` green

**Depends on #2 and #3.**

## #15 requirements.txt + Makefile  `hermes-ok`  CLOSED

## Goal
One-command setup and the three commands everyone runs all day. CI already does `pip install -r requirements.txt` when the file exists.

## Spec
`requirements.txt`:
```
pandas>=2.2
pytest>=8
```
`Makefile` (tabs, `.PHONY` for every target, `PY ?= python` so it works inside or outside the venv):
- `venv`: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- `test`: `$(PY) -m pytest -q`
- `validate`: `$(PY) -m data_estate.validate data_estate/out/company_42`
- `gen`: `SEED ?= 7`; refuses `SEED=42` (`company_42` is frozen; exit 1 with a message) then `$(PY) -m data_estate.generate --seed $(SEED) --out data_estate/out/company_$(SEED)`
- `score`: `DATASET ?= data_estate/out/company_42`, `CASE ?= data_estate/out/example_case_file_for_seed42.json`; `$(PY) -m data_estate.score $(DATASET) $(CASE)`
- `check-llm`: `$(PY) scripts/check_llm.py`
- `help` (default target): one line per target

Also add a "Setup" line to `README.md` pointing at `make venv`, and mention the targets in `AGENTS.md` "How to run things". Do not touch anything else.

## Test: `tests/test_makefile.py`
- `subprocess.run(["make", "gen", "SEED=42"], cwd=repo_root)` returns non-zero and `tests/test_frozen_dataset.py`'s digest is unchanged afterwards (import and call `digest`).
- `make -n score` output contains `data_estate.score` and the example case-file path; `make -n test` contains `pytest`.
- `make gen SEED=<random 1000–9999>` with `cwd=tmp` is not needed; instead run `make -n gen SEED=7` and assert it contains `company_7`.
- Skip the whole file with `pytest.skip` when `make` is not on PATH.

## Definition of done
- [ ] `make test` green; `make gen SEED=7` then `python -m data_estate.validate data_estate/out/company_7` passes (do not commit `company_7`; it is gitignored)
- [ ] `make score` prints `"results_recall": 1.0` for the example file
- [ ] CI green with `requirements.txt` present

## #16 ruff config + fix lint in data_estate/  `hermes-ok`  CLOSED

## Goal
Lint without behaviour change. `data_estate/` is the generator of every dataset we will ever score; a "cleanup" that changes one random call would silently change every seed.

## Spec
- Add to `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 120
  target-version = "py312"
  [tool.ruff.lint]
  select = ["E", "F", "I", "B", "UP"]
  ```
- Run `ruff check data_estate --fix` and fix what remains by hand, **in `data_estate/` only**. Do not touch `agent/`, `tests/`, `scripts/`, or `data_estate/out/`.
- ruff is a dev tool approved by this issue: install it in your venv, do **not** add it to `requirements.txt` or to CI.
- Determinism check, mandatory before the PR:
  ```
  python -m data_estate.generate --seed 42 --out /tmp/c42 && diff -r /tmp/c42 data_estate/out/company_42 && echo SAME
  ```
  must print `SAME`. If it does not, revert the change that broke it; do not "fix" the frozen dataset.

## Test
No new test file. Existing `tests/test_frozen_dataset.py`, `tests/test_estate.py` and `python -m data_estate.validate data_estate/out/company_42` must stay green.

## Definition of done
- [ ] `ruff check data_estate` clean
- [ ] `python -m pytest -q` green, validate green, regeneration diff empty (`SAME`)
- [ ] PR body shows the `SAME` line from the determinism check

## #17 --n flag for generate.py (batch of seeds)  `hermes-ok`  CLOSED

## Goal
Batch evaluation over many seeds ("mean recall ≥ 0.8, penalty 0 on every seed" in `docs/PLAN.md`) needs many datasets in one command.

## Spec
- `python -m data_estate.generate --seed 100 --n 5 --out data_estate/out/batch_100` writes `batch_100/company_100/ … batch_100/company_104/`, one summary line each (same format as today).
- `--n 1` (default) keeps today's behaviour exactly: writes to `--out` itself, not nested.
- Change **only** `main()` in `data_estate/generate.py`: loop over `range(seed, seed + n)`, call `Generator(s).build(schemes)` and `write_estate(...)`. Do not touch `Generator`, `renumber`, or any constant. Seed 42 must remain byte-identical (`python -m data_estate.generate --seed 42 --out /tmp/c42 && diff -r /tmp/c42 data_estate/out/company_42`).
- Update the usage block at the top of `generate.py` and the command table in `data_estate/README.md`.

## Test: `tests/test_generate_batch_flag.py`
- Run `python -m data_estate.generate --seed 500 --n 2 --out <tmp>/b` via `subprocess` (cwd = repo root): `<tmp>/b/company_500` and `<tmp>/b/company_501` exist and `data_estate.validate.check` returns `[]` for both.
- `--seed 7 --n 1 --out <tmp>/single`: `<tmp>/single/invoices.csv` exists (not nested).
- `--n 0` or negative exits non-zero.

## Definition of done
- [ ] Flag works as specified, test green, `python -m pytest -q` green, determinism diff empty

## #18 tests/test_generate_batch.py: 5 seeds validate  `hermes-ok`  CLOSED

## Goal
Catch generator bugs that only appear on some seeds before a judge does. `tests/test_estate.py` covers seeds 1–3; this covers five new seeds every day.

## Spec: `tests/test_generate_batch.py`
- Choose seeds reproducibly per day: `rng = random.Random(os.environ.get("BATCH_SEED", date.today().isoformat()))`, `seeds = rng.sample(range(1_000, 100_000), 5)`. Same seeds all day for everyone (a failure is reproducible), new seeds tomorrow.
- For each seed: `Generator(seed).build(schemes)` with `schemes` cycling through `["efos","kickback","roundtrip","duplicate"]`, `[]` (clean books) and a random non-empty subset, then `write_estate(...)` into `tmp_path / f"c{seed}"` and `assert check(path) == [], f"seed {seed} schemes {schemes}: {errs[:5]}"`.
- Also assert `len(truth["schemes"]) == len(schemes)` and `len(truth["decoys"]) == 5` by reading the written `hidden/ground_truth.json` (allowed in tests).
- Keep it under ~3 s (generation is ~0.1 s per seed). Use `Generator`/`write_estate`/`check` directly; no subprocess.
- If a seed fails, do **not** hide it: comment on this issue with the seed and the first errors, and leave the test red in the PR so a human sees it.

## Definition of done
- [ ] Test present and green today; `python -m pytest -q` green
- [ ] `BATCH_SEED=anything python -m pytest -q tests/test_generate_batch.py` also green

## #22 LLM client agent/llm.py + agent/config.py (tool calling, cache, offline fake, --tools check)  `cc`  CLOSED

## Goal
One place that talks to the model, so the investigation loop (#13) is only about leads and evidence. Every call goes to the OpenAI-compatible endpoint in `.env` (AGENTS.md rule 8), is cached on disk so a demo re-run costs zero network, and can be swapped for a scripted fake in tests. It also delivers the one check that matters most for the demo infrastructure: does the endpoint return **structured tool calls**? vLLM needs `--enable-auto-tool-choice --tool-call-parser <name>`; without it the model prints `<tool_call>` text and the loop cannot work. We must find that out from the venue, not on stage.

Split out of #13 so the loop can be built and tested against `FakeLLM` before the cluster is reachable.

## Spec

### `agent/config.py`
```python
ROOT = Path(__file__).resolve().parents[1]
KEYS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")

def load_env(path: Path = ROOT / ".env") -> dict[str, str]:
    """KEY=VALUE lines, # comments, optional quotes; real environment variables win over the file."""

@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str

def settings(path: Path = ROOT / ".env") -> Settings | None:
    """None when any of KEYS is missing or empty (CI has no .env)."""
```
Move the body of `load_env` out of `scripts/check_llm.py` into here and make the script import it (`from agent.config import load_env, KEYS`). The script's behaviour and output stay the same. No python-dotenv (AGENTS.md).

### `agent/llm.py`
```python
@dataclass
class ToolCall:
    id: str
    name: str
    args: dict             # parsed JSON arguments; {} when parsing failed
    parse_error: str = ""  # set when `arguments` was not valid JSON

@dataclass
class Reply:
    text: str                   # assistant content; "" when the model only called tools
    tool_calls: list[ToolCall]
    cached: bool
    usage: dict                 # {"prompt_tokens", "completion_tokens"} when the server reports them, else {}
    raw: dict                   # the whole response as a plain dict (goes into the step log)

class LLM:
    def __init__(self, settings: Settings, *, client=None, cache_dir: Path | None = ROOT / ".cache" / "llm",
                 temperature: float = 0.0, timeout: float = 120.0, max_retries: int = 3): ...
    def chat(self, messages: list[dict], tools: list[dict] | None = None, *,
             tool_choice: str | dict = "auto", max_tokens: int = 1024) -> Reply: ...

class FakeLLM:
    """Scripted stand-in with the same .chat signature. Takes a list of Reply objects (or callables
    messages -> Reply) and returns them in order; records every call in .calls; raises RuntimeError
    when it runs out. Used by tests of #13."""

def assistant_message(reply: Reply) -> dict
    # the dict to append to `messages` after a call: {"role": "assistant", "content": text, "tool_calls": [...]} in OpenAI shape
def tool_message(call: ToolCall, result) -> dict
    # {"role": "tool", "tool_call_id": call.id, "name": call.name, "content": json.dumps(result, ensure_ascii=False, default=str)}
```
Rules:
- **Transport:** the `openai` package (`openai>=1.40`; approved by #13, add the line to `requirements.txt`). `client` defaults to `openai.OpenAI(base_url=settings.base_url, api_key=settings.api_key, timeout=timeout)`; tests pass a stub whose `.chat.completions.create(**kw)` returns a canned response. Normalise the response with `.model_dump()` when the object has one, otherwise treat it as a dict already. Tool-call `arguments` arrive as a JSON **string**: `json.loads` it; on failure set `parse_error` and `args = {}`. Never raise on a malformed tool call.
- **Cache:** key = sha256 of `json.dumps({"model", "messages", "tools", "tool_choice", "temperature", "max_tokens"}, sort_keys=True, ensure_ascii=False)`; file `<cache_dir>/<key>.json` holds the normalised response dict. Hit → `Reply.cached = True`, no network. `cache_dir=None` or environment variable `LLM_CACHE=0` disables it. Add `.cache/` to `.gitignore`.
- **Retries:** on connection errors, timeouts, HTTP 5xx and 429 retry up to `max_retries` times with 1 s, 2 s, 4 s backoff, then re-raise. Never retry other 4xx.
- Always send `temperature` and `seed=0` (vLLM honours `seed`; other servers ignore it).
- This module never reads a dataset or anything under `hidden/`, and never logs or prints `api_key`.

### `scripts/check_llm.py --tools`
Keep the script stdlib-only (do not import `openai` there). With `--tools`, after the existing plain round-trip, POST a chat completion with one tool
```json
{"type": "function", "function": {"name": "add", "description": "Add two integers",
 "parameters": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}}}
```
user message `"Use the add tool to add 2 and 3."`, `tool_choice: "auto"`, `temperature: 0`, `max_tokens: 64`. Print `OK tools  name=add args={"a": 2, "b": 3}` and exit 0 when `choices[0].message.tool_calls[0].function.name == "add"` and the parsed arguments equal `{"a": 2, "b": 3}`. Otherwise print the raw `message` (content and tool_calls) and exit 1 with the hint `endpoint did not return a structured tool call; vLLM needs --enable-auto-tool-choice --tool-call-parser <hermes|llama3_json|mistral|...> matching the model`. Update the docstring at the top of the script.

## Tests: `tests/test_llm.py` (no network; CI has no `.env`)
- `load_env` on a tmp file containing a comment, a quoted value, a blank line and three keys → the three keys; `monkeypatch.setenv("LLM_MODEL", "x")` overrides the file. `settings(tmp_path_without_key)` → `None`.
- Stub client returning an OpenAI-shaped dict with `"tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "get_supplier", "arguments": "{\"supplier_id\": \"S00030\"}"}}]` → `Reply.tool_calls[0].args == {"supplier_id": "S00030"}`. Arguments `"{not json"` → `args == {}` and `parse_error` non-empty. Content-only reply → `tool_calls == []` and `text` set.
- Cache: same `messages` twice with `cache_dir=tmp_path` → stub called once, second `Reply.cached is True`; a different `max_tokens` → stub called again; `monkeypatch.setenv("LLM_CACHE", "0")` → called twice.
- Retry: stub raising `openai.APIConnectionError` twice then succeeding → one `Reply`, three calls (monkeypatch `time.sleep`); raising four times → the exception propagates.
- `FakeLLM([r1, r2])` returns `r1` then `r2`, records `.calls`, raises on the third call.
- `assistant_message` / `tool_message` results `json.dumps` and carry `tool_call_id`.
- `@pytest.mark.llm` real round-trip: `pytest.skip` when `settings() is None`; otherwise a plain reply is non-empty and the `add` tool call comes back structured. Register the marker in `pyproject.toml`: `markers = ["llm: needs .env and the cluster"]` under `[tool.pytest.ini_options]`.

## Definition of done
- [ ] `agent/config.py`, `agent/llm.py`, `scripts/check_llm.py --tools`, the `requirements.txt` and `.gitignore` lines, `tests/test_llm.py` green without `.env`
- [ ] `python scripts/check_llm.py --tools` prints `OK tools` against the cluster; paste that line into the PR body. If it fails, comment here with the model name and the raw message: that is a server-side flag, not a client bug, and a human has to fix it on the cluster.
- [ ] `python -m pytest -q` green

No dependency on #2. #13 depends on this issue.

## #23 Human-readable case file agent/report.py (money trail + tax exposure)  `cc`  CLOSED

## Goal
The Clarity and Feasibility criteria: "is the case file easy to follow, with a clear money trail?" and "could a finance team use this?". `case_file.json` (#13) is for the scorer. This module turns it into a document a CFO or an auditor can read: one section per finding with the rule broken, the peso amount, the **tax exposure in pesos**, the **money trail as a dated table built from the cited records**, and a section listing every lead that was cleared and why. Deterministic, no LLM: every number is recomputed from the dataset rows the finding cites, so the document can be defended line by line.

## Spec
CLI: `python -m agent.report <dataset_dir> <case_file.json> [--out case_file.md] [--log runs/<ts>.jsonl]`. Default `--out` is the case-file path with the extension replaced by `.md`. Exit 1, printing the errors, when `agent.contract.validate_case_file` (#3) rejects the file: never render an invalid case file.

```python
# agent/report.py
ISR_RATE = 0.30   # LISR Art. 9, corporate income tax rate; stated as an assumption in the document
IVA_RATE = 0.16

def exposure(finding: dict, ds: Dataset) -> dict          # see table
def money_trail(finding: dict, ds: Dataset) -> list[dict] # see below
def render(case: dict, ds: Dataset, *, log: list[dict] | None = None, generated_at: str | None = None) -> str
```

**Names.** Resolve every `S*` / `C*` / `E*` to its `name` (plus `category` for suppliers, `role` for employees) through the loader (#2) and print `Metálica Santa Catarina SA de CV (S00030, servicios)`. Never print a bare ID for an entity.

**Tax exposure per `scheme_type`.** All sums are over records the finding cites, restricted to the accused entities; `subtotal` and `iva` come from `ds.invoices`. When a finding cites no invoice of an accused supplier, fall back to all of that supplier's `recibida` invoices.

| scheme_type | fields | computed from |
|---|---|---|
| `efos_fake_supplier`, `kickback_shell` | `isr_deduction_at_risk = ISR_RATE × Σ subtotal`; `iva_credit_at_risk = Σ iva` | `recibida` invoices of the accused suppliers |
| `kickback_shell`, additionally | `paid_to_employee = Σ amount` of `counterparty_bank` rows with `direction == "out"` whose `counterparty_clabe` equals an accused employee's `personal_clabe` | `ds.counterparty_bank`, `ds.employees` |
| `round_trip_sales` | `revenue_overstated = Σ subtotal` of `emitida` invoices to the accused customer; plus `isr_deduction_at_risk` and `iva_credit_at_risk` as above over the accused supplier's `recibida` invoices | `ds.invoices` |
| `duplicate_invoice_payment` | `cash_loss = Σ over the cited invoices of (Σ payments − total)`; `isr_deduction_at_risk = ISR_RATE × cash_loss` (the second payment was expensed to account `6000`; visible in `ds.ledger`) | `ds.bank_transactions`, `ds.invoices` |
| `other` | `{}` | — |

Expected on `data_estate/out/example_case_file_for_seed42.json` (verified against company_42): EFOS `isr_deduction_at_risk 535,500.00`, `iva_credit_at_risk 285,600.00`; kickback `148,800.00`, `79,360.00`, `paid_to_employee 230,144.00` (employee `E00002`, Gerente de Compras); round trip `revenue_overstated 887,068.97`, `isr 315,000.00`, `iva 168,000.00`; duplicate `cash_loss 484,288.28`, `isr 145,286.48`.

**Money trail.** One row per cited record, sorted by `(fecha, record_id)`: `{step, fecha, kind, record_id, from, to, amount_mxn, note}` where
- invoice `recibida`: from = supplier name, to = company name, amount = `total`, note = `descripcion` plus `receipt GR…` when a goods receipt exists or `no goods receipt` when not;
- invoice `emitida`: from = company, to = customer name, note = `descripcion`;
- `TX*` with `direction == "out"`: from = company, to = `counterparty_name`, note = `reference`, and append ` ⚠ CLABE not on supplier master` when `counterparty_clabe` differs from the invoiced supplier's master `clabe`; `in` rows reversed;
- `CP*`: from = `entity_name`, to = `counterparty_name`, note = `reference`, and append ` = personal CLABE of <employee name> (<role>)` when `counterparty_clabe` matches an employee's `personal_clabe`;
- `GR*`: from = supplier name, to = `warehouse`, note = `received_by` resolved to a name.
Rendered as a markdown table under each finding. For a round-trip finding the rows read out → forward → in in date order; that is the money trail the judges asked for.

**Document layout** (markdown, in this order):
1. Title with company name, RFC and fiscal year (from `ds.company` and the invoice date range); `generated_at`.
2. One paragraph: number of findings, total `amount_mxn`, number of leads not pursued.
3. Summary table: finding #, scheme in plain words, accused (names), amount MXN, main exposure figure.
4. `## Finding n — <plain-words scheme>` sections: accused (names, with role/category); rule broken (the `rule` string verbatim); amount; exposure lines with the formula stated once (e.g. `30 % of 1,785,000.00 subtotal`); the finding's `narrative` when present (#13 records it, #14 keeps it); the money-trail table; an evidence list grouped by kind (invoices, bank transactions, counterparty records, receipts) with one line each.
5. `## Leads not pursued`: table of entity (name and ID), reason.
6. `## Method`: three sentences (deterministic detectors → hypothesis per lead → tool calls that return record IDs → evidence guard), the ISR and IVA rates as assumptions, and what the books cannot prove (materialidad of a service without contracts; counterparties beyond the statements in `counterparty_bank`).
7. With `--log`: `## Investigation trace`, one line per `decision` and `guard` event from the #13 step log (entity name, action, reason or rule + amount); unknown kinds ignored.

Plain-words scheme names: `efos_fake_supplier` → "Fake supplier on the SAT 69-B list", `kickback_shell` → "Kickback through a related-party shell", `round_trip_sales` → "Round-trip sales (fictitious revenue)", `duplicate_invoice_payment` → "Duplicate payment diverted to an unregistered account", `other` → "Other". Money formatted `1,234,567.89`; dates ISO. Pure function of the case file and the dataset; no LLM; never reads `hidden/`.

## Test: `tests/test_report.py`
- `render(example_case, ds)` contains: every accused ID **and** its name; every evidence ID; the strings `535,500.00`, `230,144.00`, `887,068.97`, `484,288.28`; each of the five `not_pursued` reasons verbatim; exactly four `## Finding` headings; all four plain-words scheme names.
- `money_trail` of the round-trip finding: rows sorted by date; contains a `CP*` row whose `to` is the customer's name and a `TX*` row with from = customer, to = company.
- `exposure` of each example finding equals the numbers above within 0.01.
- Entity names resolved: `"(E00002" in text` and the pattern `accused: E00002` does not occur.
- CLI: on the example file exit 0 and `--out` written; on a copy with one evidence ID changed to `TX99999` exit 1 and no file written.

## Definition of done
- [ ] `agent/report.py` and `tests/test_report.py` green; `python -m agent.report data_estate/out/company_42 data_estate/out/example_case_file_for_seed42.json --out /tmp/c42.md` renders and a teammate who did not build the agent reads the round-trip section and can say where the money went
- [ ] `python -m pytest -q` green

**Depends on #2 and #3.** Used by the demo run (#27) and linked from the trace UI (#26).

## #24 generate.py crashes on ~1.5% of seeds (13, 34, 74): decoy D3 needs a logistics supplier  `codex`  CLOSED

## Problem
`python -m data_estate.generate --seed 13 --out /tmp/c13` raises
```
File "data_estate/generate.py", line 650, in decoys
    anchor = rng.choice([s for s in self.e.suppliers if s.category == "logistica"])
IndexError: Cannot choose from an empty sequence
```
`make_suppliers` draws 34 categories with weights `[5, 4, 4, 3, 2, 2]`, so the probability that no `logistica` supplier is drawn is (18/20)^34 ≈ 2.8 %. Measured on seeds 1–200: **13, 34 and 74 crash** (3 of 200). Judges pick a seed live on stage, and a traceback is not an acceptable outcome. The same construction exists for decoy D5 (`consumibles`; ≈ 0.05 %) and in `scheme_duplicate_payment` (`materia_prima`/`refacciones` not already in a scheme; small but non-zero).

## Fix (in `data_estate/generate.py` only)
- Decoy D3: build the pool with fallbacks and pick from it: `pool = [s for s in self.e.suppliers if s.category == "logistica"] or [s for s in self.e.suppliers if s.category in ("renta_util", "servicios")] or self.e.suppliers`, then `anchor = rng.choice(pool)`. Keep `s3 = self.make_supplier("logistica", street=anchor.street, city=anchor.city)`; the decoy text "Shares address with <anchor>" stays true (a shared commercial building).
- Decoy D5: same pattern; fall back to `refacciones`, then to any supplier that is not `s2` and not named in `self.e.truth["schemes"]`.
- `scheme_duplicate_payment`: when `cands` is empty fall back to any supplier with at least three invoices that is not in a scheme; if still none, `raise ValueError(f"seed {self.seed}: no candidate supplier for duplicate payment")`. A clear error beats an IndexError.
- **Do not** change `make_suppliers`, the weights, or the order of any other `rng` call. The fallback branches run only when the original list is empty, so every seed that works today must stay byte-identical. Mandatory check before opening the PR, and the `SAME` line goes into the PR body:
  ```
  python -m data_estate.generate --seed 42 --out /tmp/c42 && diff -r /tmp/c42 data_estate/out/company_42 && echo SAME
  ```

## Test: extend `tests/test_estate.py`
- `test_sparse_category_seeds`: for `seed in (13, 34, 74)`: `Generator(seed).build(["efos", "kickback", "roundtrip", "duplicate"])`, `write_estate` into `tmp_path / f"c{seed}"`, `assert check(path) == []`, and `len(truth["decoys"]) == 5` read from the written `hidden/ground_truth.json` (tests may read it).
- `test_seed_42_unchanged`: `write_estate(Generator(42).build([all four]), tmp_path / "c42")` then `from tests.test_frozen_dataset import digest, EXPECTED` and `assert digest(tmp_path / "c42") == EXPECTED`.

## Definition of done
- [ ] Seeds 13, 34 and 74 generate and validate; `SAME` printed in the PR body
- [ ] `python -m pytest -q` green; `data_estate/out/company_42` untouched (the frozen-dataset test proves it)

Related: #18 (daily random seeds) would have caught this eventually; this fixes it now. No dependencies. Small diff: one file plus two tests.

## #25 Batch evaluation scripts/eval_batch.py: recall, penalty, evidence over N unseen seeds  `codex`  CLOSED

## Goal
The "on records it has never seen" number for the pitch, and the go/no-go gate before the feature freeze (docs/PLAN.md hours 12–24: **mean recall ≥ 0.8 and judgment penalty 0 on every seed**). One command generates N fresh datasets, runs the agent on each, scores every run, and prints a table plus a markdown file for the slides. It is also the honest answer to "how sure are you?" during the surprise question.

## Spec
`python scripts/eval_batch.py --seeds 101-120 [--schemes all|clean|random|efos,kickback] [--no-llm] [--out docs/eval/<YYYY-MM-DD>.md] [--workdir data_estate/out/batch] [--max-leads 12] [--min-recall 0.8] [--max-penalty 0]`

- `--seeds` accepts a range `a-b`, a comma list, or both (`101-105,200`). Seed 42 is refused with a message (company_42 is frozen and its answer file is in the repo, so it is not "unseen").
- `--schemes all` (default) plants all four; `clean` plants none, so the agent must produce **zero findings**; `random` picks, per seed, a subset with `random.Random(seed).sample(...)` of random size 0–4; an explicit comma list plants exactly those. Scheme names as in `generate.py`: `efos,kickback,roundtrip,duplicate`.
- Per seed: `Generator(seed).build(schemes)` → `write_estate(workdir / f"company_{seed}")` (`data_estate/out/*` is already gitignored) → `data_estate.validate.check(path) == []` → `agent.investigate.run(path, out=case_path, log=log_path, no_llm=args.no_llm, max_leads=args.max_leads)` (the in-process entry point #13 exposes; it returns the case dict) → `data_estate.score.score(path, case)` → `agent.contract.validate_case_file(case, ds)` error count.
- Each seed is timed. An exception inside the agent is caught, printed with its traceback, and recorded as recall 0, penalty 0, `error` set; the batch always finishes.
- Output table on stdout (aligned columns) and, with `--out`, the same as a markdown table: `seed | schemes | recall | found | missed | penalty | false_acc | decoys_acc | evidence_validity | not_pursued | contract_errors | wall_s | error`.
- Summary block after the table: `seeds`, `mode` (`llm` or `no-llm`, plus the model name from `agent.config.settings()` in LLM mode), `mean_recall`, `min_recall`, `seeds_with_penalty` (list), `clean_seeds_with_findings` (list; must be empty), `mean_evidence_validity`, `wall_p50_s`, `wall_p95_s`, and the exact command line.
- Exit code 1 when `mean_recall < --min-recall`, or any seed's penalty `> --max-penalty`, or any clean seed has a finding; else 0. CI does not run this (it needs the whole agent and, in LLM mode, `.env`); it is a manual gate that a human runs before the freeze.
- Create `docs/eval/.gitkeep`. Eval markdown files are committed by humans when they want them on a slide.
- Stdlib (`argparse`, `statistics`, `time`, `traceback`) plus the existing `data_estate` and `agent` packages. No new dependencies.

Design the module so the CLI and the test share one function: `run_batch(seed_plan: list[tuple[int, list[str]]], *, no_llm: bool, workdir: Path, max_leads: int = 12) -> tuple[list[dict], dict]` returning `(rows, summary)`; `parse_seeds(text) -> list[int]`; `plan(seeds, schemes_arg) -> list[tuple[int, list[str]]]`; `to_markdown(rows, summary, argv) -> str`.

## Test: `tests/test_eval_batch.py`
- `pytest.importorskip("agent.investigate")` at the top so the file skips until #13 lands and never blocks CI for the detector PRs.
- `run_batch([(101, ["efos", "kickback", "roundtrip", "duplicate"]), (102, [])], no_llm=True, workdir=tmp_path)`: two rows; row 101 has `recall == 1.0` and `penalty == 0`; row 102 has `found == []`, `penalty == 0`; `summary["clean_seeds_with_findings"] == []`.
- `parse_seeds("101-103,200") == [101, 102, 103, 200]`; `parse_seeds("42")` raises `SystemExit`.
- `to_markdown` output contains the header row above and one line per seed.

## Definition of done
- [ ] `python scripts/eval_batch.py --seeds 101-110 --no-llm` prints the table, `mean_recall ≥ 0.8`, `seeds_with_penalty == []`, exit 0
- [ ] `python scripts/eval_batch.py --seeds 101-105 --schemes clean --no-llm` reports zero findings on every seed
- [ ] With `.env`: `python scripts/eval_batch.py --seeds 101-110 --out docs/eval/$(date +%F).md`; post the summary block as a comment on this issue
- [ ] `python -m pytest -q` green

**Depends on #13** (`agent.investigate.run`) and on #24 (so no seed crashes). Calls `Generator` directly; does not need #17.

## #26 Demo live-trace UI demo/trace_ui.py + demo/index.html (reads the step log, replay mode)  `needs-human`  OPEN

## Goal
The Clarity criterion on stage: while the agent runs, the judges see leads appear, the hypothesis, every tool call, the money moving hop by hop, and the decision (accuse with rule and amount, or drop with a reason). The UI is a **viewer of the step log** written by `agent.investigate` (#13). It never calls the LLM or the detectors itself; it only reads the JSONL file and the dataset masters for names. It must also **replay** an old log at a chosen speed so we can rehearse, and fall back, without the cluster.

## Constraints
- Python side stdlib only (`http.server`, `json`, `argparse`, `threading`, `shutil`) plus `agent.data.load` (#2) for names. No node, no build step, no CDN: `demo/index.html` is one file with inline CSS and JS and must work with the venue's network down.
- Do not modify `agent/`. If the log lacks something you need, comment on #13 rather than working around it.

## Step-log format (the contract; identical to #13)
One JSON object per line: `{"ts": "<ISO-8601>", "entity_id": "S00030" | "", "step": <int>, "kind": "<kind>", "payload": {...}}`. Kinds and payloads:
- `run_start`: `{dataset, n_leads, mode: "llm"|"no-llm", model}`
- `lead`: `{entity_id, name, rank, detectors: [detector names], n_detectors, total_mxn, leads: [the lead dicts]}`
- `hypothesis`: `{text, scheme_type}` — the model's first message for this entity
- `tool_call`: `{name, args}`
- `tool_result`: `{name, n_rows, summary, ids: [record ids in the result, at most 50], rows: [at most 5 rows]}`
- `decision`: `{action: "record_finding", finding: {scheme_type, accused, rule, amount_mxn, evidence, narrative}}` or `{action: "drop_lead", reason}`
- `guard`: `{accepted: bool, reasons: [str], finding}`
- `run_end`: `{n_findings, n_not_pursued, wall_s, case_file, report}`
Unknown kinds are ignored (forward compatibility).

## Spec
`python -m demo.trace_ui --log runs/latest.jsonl --dataset data_estate/out/company_42 [--port 8765] [--replay 0.4] [--case case_file.json] [--report case_file.md]`
- Serves `demo/index.html` at `/`. `GET /log` returns the parsed lines as a JSON array, re-read from disk on every request, tolerating a partial last line (the writer may be mid-line). `GET /entities` returns `{id: {name, kind: "supplier"|"customer"|"employee", category|role}}` for every master row plus `{"COMPANY": {name, clabe}}`. `GET /case` returns the case-file JSON when the file exists (404 otherwise). `GET /report` returns the markdown from #23 as `text/plain` when present (404 otherwise).
- `--replay <seconds>`: copy the given log to a temp file **line by line** with that delay between lines in a background thread, and serve the growing copy. This is the rehearsal and fallback mode.
- `index.html` polls `/log` every 500 ms (only re-rendering new lines) and shows three panes plus a footer:
  1. **Leads** (left): one card per `lead` event ordered by `rank`: name, detectors hit, total MXN. State colour: pending → investigating (first `hypothesis`) → accused (a `guard` with `accepted: true`) or dropped (`drop_lead`, or a rejected guard). Clicking a card filters the trace pane to that entity.
  2. **Money trail** (centre): an SVG graph. Nodes: the company fixed at the centre, plus every entity or CLABE that appears in `tool_result.rows` of `get_bank_txns`, `trace_flow`, `get_invoices` and in `decision.finding.evidence`. Edges: bank rows (company → counterparty for `out`, reversed for `in`) and `trace_flow` hops (`from_clabe → to_clabe`), labelled with the amount. Draw an edge the moment its `tool_result` arrives (a short CSS transition), grey out the subgraph of a dropped lead, thicken and colour the edges of an accepted finding. Labels from `/entities`, falling back to the last four digits of a CLABE. A simple radial layout; no physics library.
  3. **Trace** (right): scrolling list of events for the selected lead (or all): hypothesis text; tool calls as `name(args)`; result summary; decision with rule and amount, or the drop reason; guard verdict, reasons in red when rejected. Auto-scroll unless the user has scrolled up.
  Footer: `run_start` info (mode, model, dataset) and, after `run_end`, the counts, wall time and a link to `/report`.
- Legible from three metres: base font size at least 16 px, high contrast; fits 1920×1080 without scrolling in the leads and graph panes.

## Fixture for development
Generate it, do not hand-write it: `python -m agent.investigate data_estate/out/company_42 --no-llm --log demo/sample_trace.jsonl --out /tmp/cf.json`, and commit `demo/sample_trace.jsonl`. The UI must render it completely: four findings built, five decoys dropped.

## Test: `tests/test_trace_ui.py`
- Start the server on a free port in a thread against `demo/sample_trace.jsonl` and company_42. `GET /log` is a JSON list whose kinds include `lead`, `decision` and `guard`; `GET /entities` maps `"S00030"` to a dict with `name`; `GET /` is HTML containing `id="leads"`, `id="graph"` and `id="trace"`; `GET /case` on a missing file → 404.
- A truncated last line in the log is skipped, not an error.
- With `--replay 0.2`, `/log` is longer on a second request one second later.

## Definition of done
- [ ] `python -m demo.trace_ui --log demo/sample_trace.jsonl --dataset data_estate/out/company_42 --replay 0.3` shows the four findings being built and every decoy dropped, and the round-trip trail is visible as three hops
- [ ] Works live: `python -m agent.investigate ... --log runs/latest.jsonl` in one terminal, the UI in another
- [ ] `python -m pytest -q` green; no new dependencies; `demo/README.md` lists the two commands

**Depends on #13** (log format) and **#2** (names). #23's report is optional: `/report` just returns 404 without it.

## #27 One-command demo run scripts/demo_run.py + docs/INJECT.md for judges (serves the API for the frontend)  `hermes-ok`  OPEN

## Goal
On stage a judge picks a seed and a scheme, we type one command, the frontend shows the run, and the case file and the score appear. The judges' brief says they "hide a fresh scheme in the data", so they also need a one-page guide to injecting one: through our generator (seed plus scheme subset) or by editing CSVs by hand. This issue delivers the command, the page, and the fallback paths for when the cluster is unreachable.

The frontend is built outside this repo against the API server (#68); this script does not render anything itself. `--serve` starts the API server so the frontend can attach.

Depends on #68, #79, #88, #90, #93 (judges' pack: estate loader, submission, HTML report, replay). #23 is closed.

## Spec: `scripts/demo_run.py`
`python scripts/demo_run.py --seed 7 [--schemes efos,roundtrip|all|clean] [--dataset <existing dir>] [--no-llm] [--max-leads 12] [--workers 4] [--serve] [--port 8765] [--runs runs]`
1. Refuse `--seed 42` unless `--dataset data_estate/out/company_42` is passed explicitly (never regenerate the frozen set). Exit 2 with a message naming the frozen dataset.
2. Generate unless `--dataset` is given: `Generator(seed).build(schemes)` → `data_estate/out/live/company_<seed>/` (gitignored), then `data_estate.validate.check` must return `[]` (exit 1 with the errors otherwise). Map `all`/`clean`/comma list exactly like `scripts/eval_batch.py::plan`.
3. Print the judge sheet: company name, counts of suppliers, customers, invoices and bank transactions, and **nothing about what was planted**.
4. Run `agent.investigate.run(dataset, out=<runs>/<ts>_case.json, log=<runs>/<ts>.jsonl, no_llm=..., max_leads=..., workers=... if the parameter exists)`. Also maintain `<runs>/latest.jsonl` as a copy of the finished log (for `--replay-from` and for anyone tailing a fixed path).
5. Render the report (`agent.report.render`) to `<runs>/<ts>_case.md` and print the path.
6. If `<dataset>/hidden/ground_truth.json` exists, run `data_estate.score.score` and print the JSON under the heading `SCORE (uses hidden ground truth; show the judges only when they ask)`.
7. `--serve`: start `api.server.serve(host, port, runs, out_root)` in a background thread BEFORE step 4 and submit the run through the registry (so the frontend sees it under `/runs`); keep serving after the run until Ctrl-C.
8. `--replay-from <log>`: skip steps 2–6; copy that log line by line into `<runs>/replay_<ts>.jsonl` with a 0.3 s delay in a background thread and register it as a run so `/runs/<id>/events` streams it. This is the no-cluster fallback; `--no-llm` (deterministic findings, real trace shape) is the second fallback.
9. Print the wall time of every stage. Exit non-zero on a validate or contract failure.

## Spec: `docs/INJECT.md` (one page, written for the judges, no internal jargon)
- What the agent sees: the CSVs, one line each; what it never sees (`hidden/`).
- Way 1, the generator: `python scripts/demo_run.py --seed <any number> --schemes <efos,kickback,roundtrip,duplicate or clean> --serve`, with one sentence per scheme name describing what gets planted.
- Way 2, edit a generated dataset by hand, three worked recipes naming the exact columns: (a) put an existing supplier's `rfc` into `efos_69b.csv` with `situacion = Definitivo`; (b) add a second `out` row to `bank_transactions.csv` with an existing `invoice_uuid`, a new `txn_id` and a different `counterparty_clabe`; (c) set a supplier's `street`/`city` to an employee's `home_street`/`home_city` and add `counterparty_bank.csv` rows from that supplier's `clabe` to the employee's `personal_clabe`. Then `python scripts/demo_run.py --dataset <dir> --serve`. Say that hand-edited datasets have no ground truth, so no score is printed; the trace and the case file are the output.
- What the agent cannot do, said before they ask: prove a service was really delivered without contracts; see counterparties' banks beyond `counterparty_bank.csv`; the 69-B list is only as fresh as its download; synthetic data is not a real company; four scheme types, anything else lands in `not_pursued` as "suspicious, unproven" with what was noticed.

Add `demo` to the Makefile: `make demo SEED=7 SCHEMES=all` runs the script with `--serve`.

## Test: `tests/test_demo_run.py`
- `subprocess.run([sys.executable, "scripts/demo_run.py", "--seed", "101", "--schemes", "all", "--no-llm", "--runs", str(tmp_path)], cwd=repo_root)`: exit 0; the case JSON, the log, `latest.jsonl` and the markdown exist in `tmp_path`; stdout contains `"results_recall"`; nothing was created under `runs/` in the repo.
- `--seed 42` without `--dataset` → exit 2 and a message naming the frozen dataset.
- `--replay-from demo/sample_trace.jsonl --runs tmp --port 0`: hard to test end to end from a subprocess; instead unit-test the replay helper (`replay_log(src, dst, delay)`): after 1 s with delay 0.01 the destination has every line of the source.

## Definition of done
- [ ] `python scripts/demo_run.py --seed 7 --schemes all --serve` runs end to end with the frontend attached to port 8765
- [ ] `--no-llm` and `--replay-from` both work with the cluster unreachable (test with `LLM_BASE_URL=http://127.0.0.1:9` in the environment)
- [ ] `docs/INJECT.md` tried by a teammate who did not build the agent: they inject a scheme from the page alone
- [ ] `python -m pytest -q` green

## Judges' pack amendments (docs/SPEC_GAP.md, added 2026-09-12)
- Accept `--estate <path>` (a judges' SQLite `.db` or CSV dir per `estate_schema.sql`, #79) as an alternative to `--seed`/`--dataset`; skip generation and validation in that case and never look for `hidden/`.
- Scheme names for `--schemes`: `efos,kickback,roundtrip,duplicate,threshold,revenue` (#81); `all` means all six.
- After the run, also write `submission.json` (#88) and `report.html` (#90) next to the case file, run `scripts/judges/validate_format.py --submission ... --estate ...` when the input was a `.db`, and print its PASS/FAIL line.
- `--replay-from` delegates to `agent.investigate --replay` (#93) so the case file, submission and report are rebuilt offline, not only the log copied.
- `docs/INJECT.md` Way 2 recipes are written for the **judges' schema** (edit `vendors`, `invoices`, `bank_txns`, `purchase_orders`, `employees`, `efos_list` in the `.db` or CSVs), with the legacy CSV recipes kept in a short second list. The "cannot do" list becomes: five scheme types plus control observations; PO/contract stand in for proof of delivery; third-party bank legs only when the estate carries them; the 69-B list as fresh as its download; synthetic data.
- Print the three numbers at the end: LLM calls, MXN cost, wall-clock seconds (#89).

## #28 tests/test_no_hidden_access.py: mechanically enforce AGENTS.md rule 2  `hermes-ok`  CLOSED

## Goal
AGENTS.md rule 2 says `agent/` must never read `hidden/`. Today that is checked by eye. Make it a test that fails the PR. Two traps it must catch: (1) a string path to `hidden/ground_truth.json`; (2) the sneaky one: `from data_estate.validate import load` or `from data_estate.score import score`. Both of those read `hidden/ground_truth.json` internally, so an agent module importing them would see the ground truth without ever spelling "hidden".

## Spec: `tests/test_no_hidden_access.py`
Static part (always runs, no dependencies):
- For every `*.py` under `agent/` (recursive), parse the source with `ast`.
- Fail if any `Import` or `ImportFrom` node refers to a module starting with `data_estate`. The agent package must not import the generator, validator or scorer at all; they belong to the data side. The failure message names file and line.
- Fail if any `ast.Constant` string contains `hidden` or `ground_truth`, **except** docstrings: collect `ast.get_docstring(node)` for every `Module`, `ClassDef`, `FunctionDef` and `AsyncFunctionDef` first and skip those strings. (`agent/__init__.py`'s docstring mentions `hidden/` on purpose.)
- Fail if any call to `open`, `Path`, `read_text`, `read_bytes`, `read_csv`, `read_json` or `json.load` has a string-literal argument containing `hidden`.
- Apply the same rules to `scripts/check_llm.py` (it may import `agent.config`, nothing from the data side).

Runtime part, guarded with `pytest.importorskip("agent.data")` so it skips until #2 lands:
- `sys.addaudithook(hook)` where `hook(event, args)` appends `str(args[0])` to a module-level list when `event == "open"` and `"hidden" in str(args[0])`. Then `agent.data.load(<company_42 dir>)` and, if `agent.detectors.DETECTORS` is non-empty, `agent.detectors.run_all(ds)`. Assert the list is empty. Audit hooks cannot be removed, so the hook must only record and return fast.
- Copy company_42 to `tmp_path` **without** `hidden/`, `load` it, and assert `len(ds.invoices) == 597`. If #2's `tests/test_loader.py` already has this exact check, keep just one and mention the other in a comment.

Add one line to AGENTS.md rule 2: "`tests/test_no_hidden_access.py` enforces this." Change nothing else.

## Definition of done
- [ ] Test present and green on `master`; a temporary `from data_estate.validate import load` in any agent module makes it fail (try it locally, revert, do not commit the try)
- [ ] `python -m pytest -q` green

No dependencies for the static part. Small diff: one test file plus one line in AGENTS.md.

## #29 tests/test_detectors_batch.py: every planted entity hit on fresh seeds, no decoy on strong detectors  `hermes-ok`  CLOSED

## Goal
Every detector test so far runs against company_42 only. The judges score "records it has never seen". This test generates fresh datasets during the test run and checks that the scheme-defining detectors find every planted entity and nothing honest, and that every lead from every registered detector is well-formed. It catches threshold bugs that only show up on other seeds: the round-trip window and the fast-pay window were both tuned on one seed (see LEARNINGS.md), and seed 105 below has a return leg that a 10-day window misses.

## Spec: `tests/test_detectors_batch.py`
Fixed seeds and scheme sets (verified to generate and validate on current `master`; do not use random seeds here, #18 does that for the generator):

| seed | schemes |
|---|---|
| 101 | efos, kickback, roundtrip, duplicate |
| 102 | none: clean books, decoys only |
| 103 | efos |
| 104 | kickback, duplicate |
| 105 | roundtrip |

Session-scoped fixture: for each row, `Generator(seed).build(schemes)` → `write_estate(tmp_path_factory.mktemp("batch") / f"c{seed}")` → `assert check(path) == []` → `ds = agent.data.load(path)` and `truth = json.loads((path / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))` (tests may read hidden). Generation is about 50 ms per seed; loading is the slow part, so keep the fixture session-scoped.

Tests, each parametrised over the five datasets:
1. **Well-formed leads.** `leads = agent.detectors.run_all(ds)`; for every detector and every lead: `entity_id in ds.all_entity_ids()` (or `== ""`, allowed only for `detect_round_trip`), `evidence` is a non-empty list, every evidence ID is in `ds.all_record_ids()`, and `json.dumps(leads)` succeeds.
2. **EFOS.** `{r["entity_id"] for r in leads["detect_efos"]} == {e["supplier_id"] for s in truth["schemes"] if s["type"] == "efos_fake_supplier" for e in s["entities"]}` (the empty set on 102, 104, 105).
3. **Kickback.** `{r["entity_id"] for r in leads["detect_employee_address_match"]}` equals the set of planted shell supplier IDs, and every hit has `same_approver is True`.
4. **Duplicate.** `{r["invoice_uuid"] for r in leads["detect_duplicate_payments"]}` equals the planted `payments[*].invoice_uuid`; `{r["txn_id"] for r in leads["detect_clabe_not_on_master"]}` equals the planted `duplicate_txn` set.
5. **Round trip.** `{(r["out_txn"], r["forward_record"], r["in_txn"])}` equals the planted legs. Seed 105 has a leg whose return arrives 11 days after the forward: the #9 defaults (`forward_days=7`, `return_days=14`) find it; document that by also asserting `len(detect_round_trip(ds, return_days=10)) < len(detect_round_trip(ds))` on seed 105.
6. **Decoys.** For the strong detectors `detect_efos`, `detect_employee_address_match`, `detect_duplicate_payments`, `detect_clabe_not_on_master`, `detect_round_trip`: no `entity_id` in `{d["supplier_id"] for d in truth["decoys"]}` on any seed. (`detect_no_receipt`, `detect_fast_pay_no_deliverable` and `detect_new_vendor_round_amounts` are allowed to list decoys; that is their documented behaviour.)
7. **Clean books (102).** All five strong detectors return `[]`.

Conventions: the fixtures in `tests/conftest.py` are for company_42; this file builds its own. Never write under `data_estate/out/`. Runtime target: under 10 s for the whole file.

## Definition of done
- [ ] Test green on `master` with the listed detectors merged; `python -m pytest -q` green
- [ ] If an assertion fails for a real reason (a detector misses a planted entity on some seed), do **not** loosen it: comment on this issue with the seed, the detector and the offending row, and leave the test red in the PR so a human sees it.

**Depends on #2, #4, #6, #7, #8, #9.** If any of them is still open, skip this issue.

## #30 scripts/sync_issues.py: regenerate docs/ISSUES.md from GitHub  `hermes-ok`  CLOSED

## Goal
`docs/ISSUES.md` is the offline mirror of the issue queue (README: "GitHub is the source of truth"). It was written by hand and is already stale: no state column, no PR links, and newer issues are missing. One script regenerates it, so the mirror is trustworthy for anyone reading the repo without network and the open/closed picture is visible in one file.

## Spec
`python scripts/sync_issues.py [--repo filip-rs/PU-HackMTY] [--out docs/ISSUES.md] [--check]`
- Runs `gh issue list -R <repo> --state all --limit 200 --json number,title,state,labels,body,url` and `gh pr list -R <repo> --state all --limit 200 --json number,title,state,headRefName,url` through `subprocess.run(..., capture_output=True, text=True, check=True)`. Stdlib only.
- Output, deterministic and sorted by issue number:
  1. Header: `# Issue queue — snapshot of the GitHub issues (regenerated <YYYY-MM-DD>). GitHub is the source of truth: \`gh issue view <n>\`.`
  2. Table `| # | State | Label | Title | PR |`, where `PR` lists pull requests whose `headRefName` ends with `/<n>` or whose title starts with `#<n> ` as `#19 (open)` / `#21 (merged)`, else blank.
  3. `---`, then per issue `## #<n> <title>  \`<label>\`  <STATE>` followed by the body verbatim. Trailing whitespace stripped, exactly one blank line between sections, file ends with a newline.
- `--check`: regenerate in memory and exit 1 if the result differs from the file (so a human can notice drift; not wired into CI because CI has no `gh` token).
- If `gh` is missing or not authenticated: print its stderr, exit 2, never write a partial file.

Structure the module as `fetch(repo) -> (issues, prs)`, `build_markdown(issues, prs, today: str) -> str`, and a `main()`.

## Test: `tests/test_sync_issues.py`
- Monkeypatch `subprocess.run` with a fake returning canned JSON for the two commands (two issues; one PR with `headRefName: "hermes/15"` and state `OPEN`); `build_markdown(issues, prs, today="2026-09-12")`: the table has two rows, the row for #15 shows `#19 (open)`, both bodies appear under their `## #` headings, the text ends with `\n`, and building twice gives identical text.
- `--check` against a tmp file that differs → exit code 1; identical → 0 (drive `main()` with `sys.argv` patched).

## Definition of done
- [ ] Script and test green; run it once and commit the regenerated `docs/ISSUES.md` in the same PR
- [ ] `python -m pytest -q` green

No dependencies. Lowest priority of the `hermes-ok` queue: take it only when nothing else is available.

## #31 Demo rehearsal pack: script, surprise-question answers, cannot-do slide, venue checks  `needs-human`  OPEN

## Goal
Hours 24–36 of docs/PLAN.md: everything that is not code. The three-minute script with measured timings, the rehearsed answers to the surprise questions, the "what it cannot do" slide, the learnings slide, and the venue checklist. A person owns this; agents may draft the markdown, humans decide what is said.

## Deliverables (all under `demo/`)
- `demo/SCRIPT.md`: the beat sheet from docs/PLAN.md §Demo with the exact words for 0:00–0:30 (Rodrigo's story, flagged as a composite case), the command typed at 0:30 (`python scripts/demo_run.py --seed <judge's> --schemes <judge's> --serve`, from #27), what to point at while the UI (#26) runs (a lead appearing, the round-trip hops, a decoy being dropped), and the close at 2:30. Timed with a stopwatch in three rehearsals; the measured times go into the file.
- `demo/QA.md`: one answer per likely question, each pointing at where the evidence is on screen or in the case file (#23):
  - "Why didn't you accuse <decoy>?" for each of the five decoys: the `not_pursued` reason and the record that clears it (receipt IDs, the RFC difference, the court case number in the description, the LISR 27-III cash cap).
  - "The duplicate payment, is the supplier guilty?" No; the payment is. Show the ledger line on account `6000` and the CLABE that is not on the master.
  - "What if the 69-B list is stale?" The no-receipt, fast-pay and round-amount evidence stands without it; show the EFOS finding's trail without the 69-B row.
  - "How do you know the model did not hallucinate?" The guard (#14): every ID re-checked, the amount recomputed, the rule from the catalog; show a guard rejection in the trace if one happened, otherwise the test.
  - "How much did you find and how sure are you?" Amount per finding plus the tax exposure; the batch-evaluation table (#25) for confidence.
  - "What would a real deployment need?" and "What can it not do?" (next item).
- `demo/CANNOT_DO.md`, one slide: only sees what is in the books plus the counterparty statements an auditor obtains; cannot prove materialidad of a service without contracts; the 69-B list lags reality; synthetic data is not a real company; four scheme types, anything else lands in `not_pursued` or `other` with what was noticed.
- Learnings slide: five entries from `LEARNINGS.md`, e.g. the two-of-eight impossible detector specs, the IVA ratio on the round trip, the generator crash on 1.5 % of seeds (#24), the tool-calling check from #22, and whatever the batch evaluation teaches.
- Venue checklist inside `demo/SCRIPT.md`: `python scripts/check_llm.py --tools` from the venue network the night before and again 30 minutes before; a good run's `runs/latest.jsonl` saved as `demo/fallback_trace.jsonl` for `--replay-from`; `--no-llm` tried once on the demo laptop; the UI checked at the projector's resolution; a teammate who did not build the agent injects a scheme blind from `docs/INJECT.md`, and the precision and recall of that run go into `LEARNINGS.md`.

## Definition of done
- [ ] Three consecutive clean rehearsals under 3:00 on a stopwatch, times written down
- [ ] Every question in `QA.md` is answered by pointing at something on screen, not from memory
- [ ] Fallback trace saved and its replay tested on the demo laptop

**Depends on #23, #25, #26, #27.** Owner: a human. Agents may draft the markdown from the docs.

## Judges' pack amendments (docs/SPEC_GAP.md, added 2026-09-12)
- `demo/QA.md` must answer the eight questions in `student-materials/forensic-auditor/README.md` verbatim, each from a page or a log line in under ten seconds: "What happens if I change this input?" (INJECT.md + a live re-run), "Why should I trust this number?" (the reconciliation section of the finding, #90), "What does it do when it's wrong, or when there's nothing to find?" (a clean-books run from the results table, #86; a challenger kill, #91), "Could a real audit team run this tomorrow?" (Method and limits + the three numbers), "What did you cut, and why?" (SPEC_GAP.md "What we cut"), "Why didn't you flag vendor X?" (Leads not pursued, with signal/tools/closer, #94), "How confident are you in finding 2?" (proven/probable + challenger arguments), "What if the employee just happens to bank at the same institution?" (the same-bank check, #94, and the kickback finding's `CP` leg).
- The artifact judges read is `report.html` (#90) opened from a file with Wi-Fi off, plus `submission.json` validated on stage with `scripts/judges/validate_format.py`. Rehearse the offline replay (#93) as the first fallback and `--no-llm` as the second.
- The results slide is `results_table.csv` from `scripts/eval_batch.py --report` on seeds 901–910 (#86, #72), with the tuning seeds named next to it.
- `demo/CANNOT_DO.md`: five scheme types plus control observations; proof of delivery is a PO or contract on judge estates; third-party bank legs only when the estate carries them; the 69-B list lags reality; synthetic data.
Depends additionally on #86, #88, #90, #93, #94.

## #42 detect_kickback_outflow(ds): supplier statement outflows to an employee's personal CLABE  `hermes-ok`  CLOSED

## Goal
The **proof** of the kickback scheme, not just its tell. `detect_employee_address_match` (#7) says a supplier is registered at an employee's home; that alone is a coincidence a defence lawyer can explain. What closes the case is the supplier's own bank statement (`counterparty_bank`) showing money going from the supplier's CLABE to that employee's personal CLABE. `data_estate/README.md` lists exactly this as the proof: "same-approver + counterparty statement outflows to employee CLABE". No detector produces it today, so the loop (#13) and the deterministic fallback would have to rediscover it through tool calls. This detector hands it over as a lead with the `CP*` record IDs attached.

## Spec
`agent/detectors/kickback_outflow.py` → `detect_kickback_outflow(ds) -> list[dict]`
1. Take `ds.counterparty_bank` rows with `direction == "out"`.
2. Join `entity_clabe` to `ds.suppliers.clabe` (exact string equality) to get the supplier whose statement it is. Rows whose `entity_clabe` is not a supplier CLABE are dropped (customer statements are not this detector's business).
3. Join `counterparty_clabe` to `ds.employees.personal_clabe` (exact string equality). Keep only rows that land on an employee's personal account.
4. Group by `(supplier_id, employee_id)`; one lead per pair, sorted by `(entity_id, employee_id)`:
   - `entity_id`: the supplier_id · `supplier_name` · `employee_id` · `employee_name` · `employee_role`
   - `same_approver`: `suppliers.approved_by == employee_id` (bool)
   - `n_outflows`, `outflow_total_mxn`: count and sum of `amount` over the matched rows
   - `first_outflow`, `last_outflow`: ISO dates
   - `supplier_invoice_total_mxn`: sum of `total` over `ds.invoices` rows with `tipo == "recibida"` and `counterparty_id == supplier_id`
   - `outflow_ratio`: `outflow_total_mxn / supplier_invoice_total_mxn` rounded to 4 decimals (`0.0` if the supplier has no invoices)
   - `evidence`: the matched `record_id`s (`CP*`), sorted. Only the counterparty rows: the supplier's invoices and our payments are already the evidence of #7, and the loop unions evidence per entity.
5. No thresholds. A single peso from a supplier's account to an employee's personal account is a lead.

## Data facts (company_42, verified with pandas)
- `counterparty_bank` has 22 rows (11 in, 11 out) for two entity CLABEs: the kickback shell `S00004` and the round-trip supplier `S00021`.
- Exactly **8** out rows go from `S00004`'s CLABE to employee `E00002`'s personal CLABE: `CP00002, CP00003, CP00007, CP00008, CP00010, CP00014, CP00016, CP00020`, dated 2025-03-27 … 2025-10-20, sum **230,144.00**.
- `S00004` has 8 `recibida` invoices totalling **575,360.00**, all approved by `E00002`, and `suppliers.approved_by == "E00002"`. `outflow_ratio` is therefore **0.4000** (the generator sends 40% back).
- `S00021`'s outflows go to a customer CLABE, not an employee: zero leads from it.
- No supplier CLABE equals an employee CLABE, and no `bank_transactions` out row with an invoice lands on an employee CLABE, so nothing else in this dataset can match. Result on company_42: exactly **one** lead.

## Test: `tests/test_detect_kickback_outflow.py`
- `result` has length 1; `result[0]["entity_id"] == scheme("kickback_shell")["entities"][0]["supplier_id"]` and `employee_id == ...["employee_id"]`.
- `set(result[0]["evidence"]) == set(scheme("kickback_shell")["entities"][0]["counterparty_record_ids"])` (8 IDs).
- `same_approver is True`, `n_outflows == 8`, `outflow_total_mxn == pytest.approx(230144.0)`, `outflow_ratio == pytest.approx(0.4)`.
- No `entity_id` in `decoy_ids`; `json.dumps(result)` works; result sorted by `(entity_id, employee_id)`.
- Synthetic negative: copy `ds` with `dataclasses.replace(ds, counterparty_bank=ds.counterparty_bank[ds.counterparty_bank.direction == "in"])` → `[]`.

## Definition of done
- [ ] Module + test as above, `python -m pytest -q` green, no other files touched
- [ ] Finds the planted shell with all 8 `CP*` IDs; nothing else on company_42

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file per detector.

**Depends on #2** (merged). Independent of #7; the loop combines both.

## #43 Decoy-surfacing detectors: detect_name_twin_69b, detect_shared_supplier_address, detect_cash_payments  `hermes-ok`  CLOSED

## Goal
Three of the five decoys never appear in any lead today. `run_all(ds)` on company_42 surfaces the new-vendor decoy (`S00009`, via round amounts) and the law-firm decoy (`S00036`, via fast-pay / no-receipt), but nothing points at the **name-twin** (`S00007`), the **shared-address** supplier (`S00026`) or the **cash-payments** supplier (`S00011`). The loop (#13) can only clear what it sees: its definition of done ("every decoy appears in `not_pursued` with a reason") and the demo line "why did you not accuse X?" both need every decoy to arrive as a lead carrying the facts that clear it. These three detectors are deliberately **weak signals**: they exist so the agent can show, on record, that it looked and why it walked away. Each lead carries the exonerating facts as plain data fields; the detector never decides.

Three modules, three tests, all in one PR (each is ~30 lines).

## Spec 1: `agent/detectors/name_twin_69b.py` → `detect_name_twin_69b(ds) -> list[dict]`
The trap in #4: 69-B is matched on RFC, never on name. This detector is the mirror image: suppliers whose **name** equals a 69-B entry's `nombre` but whose RFC differs.
1. Join `ds.suppliers` to `ds.efos_69b` on `name.str.strip() == nombre.str.strip()` (exact, case-sensitive). No fuzzy or suffix-normalised matching: normalising `SA de CV` / `SAPI de CV` / `S de RL de CV` matches 11 suppliers on company_42 because the generator draws names from a small vocabulary. Exact names only.
2. Keep `situacion in {"Presunto", "Definitivo"}` and `suppliers.rfc != efos_69b.rfc`. (Equal RFC is #4's job and must not be duplicated here.)
3. One lead per supplier (a supplier can match several list rows: take the row with the latest `fecha_publicacion`), sorted by `entity_id`:
   `entity_id`, `name`, `rfc`, `listed_rfc`, `listed_nombre`, `situacion`, `fecha_publicacion` (ISO), `rfc_listed: False` (constant, spelled out so the loop sees it), `n_invoices`, `total_mxn`, `n_with_receipt` (count of those invoices with a `goods_receipts` row), `evidence` = the supplier's `recibida` invoice UUIDs.

**Data facts (company_42):** exactly 3 leads: `S00007` (the decoy; list RFC `TAO890114RLQ`, Definitivo, 8 invoices, 105,356.46, 8 with receipt), `S00012` (Presunto, 10 invoices, 784,013.25, 10 with receipt), `S00024` (Presunto, 5 invoices, 336,474.01, 0 with receipt: it is a logistics supplier, receipts are not expected). The two real EFOS suppliers `S00020`/`S00030` also match by name but their RFC matches too, so they must **not** appear.

## Spec 2: `agent/detectors/shared_supplier_address.py` → `detect_shared_supplier_address(ds) -> list[dict]`
Decoy 3 in `data_estate/README.md`: two suppliers at one address, a commercial building. #7 deliberately never compares supplier to supplier; this one does.
1. Group `ds.suppliers` by `(street.str.strip(), city.str.strip())`; keep groups with ≥ 2 suppliers.
2. One lead per supplier in such a group, sorted by `entity_id`: `entity_id`, `name`, `street`, `city`, `shares_with: [other supplier_ids in the group, sorted]`, `employee_home_match: bool` (True when the address also equals some employee's `(home_street, home_city)`; on company_42 this is False for every lead because #7 covers that case), `n_invoices`, `total_mxn`, `n_with_receipt`, `evidence` = the supplier's `recibida` invoice UUIDs.

**Data facts (company_42):** exactly one group, `Av. Garza Sada 337 / San Nicolás de los Garza, NL`, suppliers `S00024` and `S00026` (both `categoria == logistica`). Two leads. `S00026` is the decoy; `S00024` is its honest neighbour. Neither is at an employee's home.

## Spec 3: `agent/detectors/cash_payments.py` → `detect_cash_payments(ds, *, cap_mxn: float = 2000.0) -> list[dict]`
Decoy 5: cash invoices (`forma_pago == "01"`). Deductible only up to MXN 2,000 each (LISR Art. 27-III); the decoy stays under the cap on every invoice.
1. `ds.invoices` rows with `tipo == "recibida"` and `forma_pago == "01"`.
2. One lead per supplier, sorted by `entity_id`: `entity_id`, `name`, `n_cash_invoices`, `cash_total_mxn`, `max_cash_invoice_mxn`, `n_over_cap` (invoices with `total > cap_mxn`), `all_under_cap: bool`, `n_with_receipt`, `evidence` = the cash invoice UUIDs + the `txn_id` of every `bank_transactions` row whose `invoice_uuid` is one of them.

**Data facts (company_42):** `forma_pago` is `"03"` on 438 purchase invoices and `"01"` on 3, all from `S00011`: totals 1,821.72 / 1,793.00 / 1,733.25 (sum 5,347.97, max 1,821.72), paid by `TX00190`, `TX00365`, `TX00437`; all 3 have receipts. One lead, `n_over_cap == 0`, `all_under_cap is True`. With `cap_mxn=1800.0` the same lead has `n_over_cap == 1`.

## Tests (one file per detector)
`tests/test_detect_name_twin_69b.py`
- `{r["entity_id"]}` == `{"S00007", "S00012", "S00024"}`; the decoy from `truth["decoys"]` whose `looks_like` starts with `"Name almost"` is among them with `rfc_listed is False` and `listed_rfc == "TAO890114RLQ"`.
- No `entity_id` in `{e["supplier_id"] for e in scheme("efos_fake_supplier")["entities"]}`.
- `n_with_receipt == 8` on `S00007`. Sorted, `json.dumps` works.

`tests/test_detect_shared_supplier_address.py`
- Exactly 2 leads, entity IDs `{"S00024", "S00026"}`, each with `shares_with == [the other]` and `employee_home_match is False`.
- The decoy with `looks_like` starting `"Shares address"` is one of them. The kickback shell `S00004` is **not** (it shares with an employee, not a supplier). Sorted, `json.dumps` works.

`tests/test_detect_cash_payments.py`
- Exactly 1 lead; `entity_id` == the decoy with `looks_like` starting `"Cash payments"`; `n_cash_invoices == 3`, `cash_total_mxn == pytest.approx(5347.97)`, `all_under_cap is True`, `n_over_cap == 0`, `len(evidence) == 6`.
- `detect_cash_payments(ds, cap_mxn=1800.0)[0]["n_over_cap"] == 1` and `all_under_cap is False`.
- Every evidence ID in `ds.all_record_ids()`; `json.dumps` works.

## Definition of done
- [ ] Three modules + three tests, `python -m pytest -q` green, no other files touched
- [ ] After merge, `{r["entity_id"] for leads in run_all(ds).values() for r in leads}` on company_42 contains all five decoy IDs (add that one assertion to the cash-payments test file as `test_every_decoy_is_now_a_lead`, using the `decoy_ids` fixture)

### Conventions for every detector
- **Module:** `agent/detectors/<name>.py` with exactly one public function `detect_<name>(ds, **params) -> list[dict]`. The package `agent/detectors/__init__.py` discovers it on import (registry `DETECTORS`, runner `run_all`). Do not edit `__init__.py` or any other detector module.
- **`ds`** is `agent.data.Dataset` (#2): one pandas DataFrame per CSV, named after the file stem: `ds.suppliers`, `ds.customers`, `ds.employees`, `ds.invoices`, `ds.goods_receipts`, `ds.bank_transactions`, `ds.counterparty_bank`, `ds.ledger`, `ds.efos_69b`, plus `ds.company` (dict from `company.json`). Date columns are `datetime64`, money columns `float`, every ID / RFC / CLABE / folio / po_number / account_code is `str`, and empty cells are `""` (never NaN).
- **Pure function:** no I/O, no LLM, no network, never reads `hidden/`. Output must be deterministic: sort it.
- **Every returned dict is a lead, not an accusation.** It carries at least `entity_id` (the `S*`/`C*`/`E*` it points at) and `evidence` (list of record IDs that triggered it: invoice UUIDs, `TX*`, `CP*`, `GR*`), plus the fields listed below. Dates as ISO strings, money as float, everything `json.dumps`-able.
- **Test:** `tests/test_detect_<name>.py`. Fixtures from `tests/conftest.py`: `ds` (company_42 loaded), `scheme(type)` (that scheme's ground-truth dict), `decoy_ids` (set of the 5 decoy supplier IDs), `truth` (full dict). Only tests may read ground truth. Assert `json.dumps(result)` works.
- Run `python -m pytest -q` before opening the PR. No new dependencies. Small diff: one module + one test file per detector.

**Depends on #2** (merged). Does not depend on #4.

## #44 Lead aggregation and ranking agent/leads.py (docket per entity, scheme_hint, CLI)  `hermes-ok`  CLOSED

## Goal
Step 1 of the investigation loop (#13) says "group leads by `entity_id`; rank". That grouping is the agent's *docket*: which entities get investigated, in what order, and with what starting hypothesis. It is pure pandas, fully testable against ground truth, and it is also the deterministic core of the `--no-llm` fallback (which must pass the same scores on stage if the cluster is down). Splitting it out of #13 the way #22 split out the client: #13 then only orchestrates.

Also gives the team a one-command view of what the detectors see on any seed (`python -m agent.leads <dir>`), which is what we will stare at when a judge injects a fresh scheme.

## Spec: `agent/leads.py`
```python
STRONG: frozenset[str] = frozenset({
    "detect_efos", "detect_employee_address_match", "detect_kickback_outflow",
    "detect_round_trip", "detect_duplicate_payments", "detect_clabe_not_on_master",
})  # scheme-defining detectors (same list as #29); everything else is a weak signal

SIGNATURES: list[tuple[frozenset[str], str]] = [
    (frozenset({"detect_efos"}), "efos_fake_supplier"),
    (frozenset({"detect_employee_address_match", "detect_kickback_outflow"}), "kickback_shell"),
    (frozenset({"detect_round_trip"}), "round_trip_sales"),
    (frozenset({"detect_duplicate_payments", "detect_clabe_not_on_master"}), "duplicate_invoice_payment"),
]  # first signature whose detector set is a subset of the entity's detectors wins; else ""

def aggregate(ds: Dataset, leads: dict[str, list[dict]] | None = None) -> list[dict]:
    """leads defaults to agent.detectors.run_all(ds). Returns one dossier per entity, ranked."""

def scheme_hint(detectors: set[str]) -> str

def main(argv=None) -> int   # python -m agent.leads <dataset_dir> [--json] [--top N]
```
Dossier fields (all `json.dumps`-able, dates ISO, money float rounded to 2 decimals):
- `entity_id`, `kind` (`"supplier"` / `"customer"` / `"employee"` from the ID prefix `S`/`C`/`E`; a lead with `entity_id == ""` is skipped and counted in `n_orphan_leads` of the CLI summary), `name` (from the master table)
- `detectors`: sorted list of detector names that produced ≥ 1 lead for the entity; `n_detectors`; `n_strong` = `len(set(detectors) & STRONG)`
- `n_leads`: total lead dicts across detectors
- `total_mxn`: suppliers → sum of `total` over `recibida` invoices with `counterparty_id == entity_id`; customers → same over `emitida`; employees → 0.0
- `evidence`: sorted union of every lead's `evidence`, deduplicated; `n_evidence`
- `related`: sorted list of other entity IDs any lead mentions in `employee_id` or `customer_id` fields (e.g. the shell's approver, the round trip's customer)
- `scheme_hint`: `scheme_hint(set(detectors))`
- `leads`: `{detector_name: [lead dicts, unchanged]}`
- `rank`: 1-based position

Ranking key, descending: `(n_strong, n_detectors, total_mxn)`, ties broken by `entity_id` ascending. Strong evidence first, then breadth, then money. Never rank by `n_leads` (the no-receipt detector emits one row per invoice and would swamp everything).

CLI: prints `rank  entity_id  kind  n_strong/n_detectors  total_mxn  scheme_hint  detectors` one line per entity (`--top N` limits it), then a summary line `entities=<n> leads=<n> orphan_leads=<n> detectors=<n registered>`. `--json` prints the list of dossiers instead. Exit 0. Never writes anything.

## Data facts (company_42, verified with pandas; registry = #4–#11 + #42 + #43)
With every detector merged, `run_all` yields 130 leads over 19 entities (plus the round-trip detector's 3 leads, which name supplier `S00021` as `entity_id` and `C00005` in `customer_id`). Ranked dossiers:

| rank | entity | n_strong/n_detectors | total_mxn | scheme_hint |
|---|---|---|---|---|
| 1 | S00004 | 2/5 | 575,360.00 | kickback_shell |
| 2 | S00017 | 2/2 | 1,482,602.25 | duplicate_invoice_payment |
| 3 | S00021 | 1/4 | 1,218,000.00 | round_trip_sales |
| 4 | S00030 | 1/4 | 1,044,000.00 | efos_fake_supplier |
| 5 | S00020 | 1/4 | 1,026,600.00 | efos_fake_supplier |
| 6 | S00024 | 0/3 | 336,474.01 | "" |
| 7 | S00036 | 0/2 | 440,800.00 | "" |
| 8–19 | S00006, S00016, S00018, S00012, S00009, S00037, S00011, S00005, S00028, S00007, S00026, S00029 | 0/1 | | "" |

`S00004.evidence` has 24 IDs (8 invoices + 8 `TX` + 8 `CP`); `S00004.related == ["E00002"]`; `S00021.related == ["C00005"]`. The five decoys sit at ranks 7, 12, 14, 17, 18: every planted entity outranks every decoy, and no decoy gets a `scheme_hint`. If #42 is not merged yet, `S00004` has 1/4 and no hint (signature needs both kickback detectors); if #4 is not merged, `S00030`/`S00020` have 0/3. Wait for both.

## Test: `tests/test_leads.py`
- `d = aggregate(ds)`; `[x["entity_id"] for x in d[:5]] == ["S00004", "S00017", "S00021", "S00030", "S00020"]` and `rank` is `1..len(d)`.
- Every planted entity from `truth["schemes"]` (supplier IDs of every scheme's `entities`) has `n_strong >= 1`; every ID in `decoy_ids` has `n_strong == 0` and `scheme_hint == ""`; `max(rank of planted) < min(rank of decoys)`.
- `scheme_hint` per planted entity equals its scheme's `type`; for `S00004` it is `kickback_shell` and `related == ["E00002"]`.
- `S00004`: `n_evidence == 24`, `set(evidence) ⊇` its ground-truth `invoice_uuids | bank_txn_ids | counterparty_record_ids`.
- `scheme_hint({"detect_efos", "detect_no_receipt"}) == "efos_fake_supplier"`, `scheme_hint({"detect_employee_address_match"}) == ""`, `scheme_hint(set()) == ""`.
- Every `evidence` ID is in `ds.all_record_ids()`; every `entity_id` in `ds.all_entity_ids()`; `json.dumps(d)` works; calling `aggregate` twice gives equal output.
- `aggregate(ds, {"detect_efos": []})` → `[]`. Unknown detector names in `leads` are accepted (they are just not strong).
- CLI: `main([str(dataset_dir), "--top", "3"])` returns 0 and prints exactly 3 entity lines (capture with `capsys`); `--json` output parses and has 19 items.

## Definition of done
- [ ] `agent/leads.py`, `tests/test_leads.py` green; `python -m pytest -q` green; no other files touched
- [ ] `python -m agent.leads data_estate/out/company_42` prints the table above
- [ ] Comment on #13 that step 1 can call `agent.leads.aggregate` and that `scheme_hint` is the `--no-llm` signature

**Depends on #2, #4, #42, #43.** If any is still open, skip this issue.

## #45 ruff check in CI + fix the 3 existing lint errors  `hermes-ok`  CLOSED

## Goal
#16 configured ruff in `pyproject.toml` (`E4, E7, E9, F, I`) but nothing runs it: it is not in `.github/workflows/ci.yml`, not in `requirements.txt`, and `ruff check .` on current `master` already reports 3 errors (2× `I001` unsorted imports, 1× `F841` unused variable). Lint that is not enforced drifts. Make CI run it and fix what it finds.

## Spec
- `requirements.txt`: add `ruff`.
- `.github/workflows/ci.yml`: add a step `ruff check .` after the `pip install -r requirements.txt` step and before the validate/pytest steps, so a lint failure is reported before the (slower) tests.
- `Makefile`: add a `lint` target (`$(PYTHON) -m ruff check .`) and make `test` depend on it is **not** wanted; keep them separate so `make test` stays fast.
- Fix the 3 errors reported by `ruff check .` on `master` (`ruff check --fix` for the two import-order ones; remove or use the unused variable by hand; no `--unsafe-fixes`). No other code changes, no rule changes in `pyproject.toml`.

## Definition of done
- [ ] `ruff check .` exits 0 on the branch; CI runs it and is green
- [ ] `python -m pytest -q` green

## #65 agent/guard.py: ledger entry IDs in evidence are set aside, not a rejection  `hermes-ok`  CLOSED

## Goal
In LLM mode the model calls `query_ledger` a lot (35 of the 206 tool calls in the logged runs under `runs/`) and then cites the ledger `entry_id`s it saw (`GL00652`, `GL02894`, `GL03014`, ...) as evidence in `record_finding`. The case-file contract only accepts invoice UUIDs, `TX*`, `CP*` and `GR*` (`Dataset.all_record_ids()` in `agent/data.py`), so `validate_case_file` reports `findings[0].evidence: GL03014 not in dataset` and `agent/guard.py` rejects the whole finding. The lead is then dropped and recall on company_42 falls from 4/4 to 3/4 (see `runs/20260912T175005Z.jsonl`, entity S00017: the duplicate-payment finding was correct in every other respect).

Ledger rows are legitimate context (the duplicate payment is booked straight to an expense account, bypassing AP), they are just not evidence IDs under the contract. The guard should keep the finding, set the ledger refs aside, and keep them visible in the narrative.

Do not change `agent/contract.py`, `agent/data.py`, `data_estate/score.py` or `tests/test_case_file_contract.py` (AGENTS.md rules 3 and 5). This is a guard-only change.

## Spec (`agent/guard.py`)
1. New helper `_split_ledger_refs(evidence: list[str], ds: Dataset) -> tuple[list[str], list[str]]`: an ID is a ledger ref when it is in `set(ds.ledger["entry_id"])`. Returns `(evidence_without_ledger, ledger_ids)`, both in first-occurrence order, both deduped.
2. In `guard()`, right after the existing dedupe and BEFORE step 1 (the contract check): split the evidence. Every later check (contract, "belongs to accused", evidence kinds, invoice required, amount) runs on `evidence_without_ledger`.
3. If `evidence_without_ledger` is empty and `ledger_ids` is not: reject with the single reason `"evidence: only ledger entries were cited (GL...); cite invoice, TX, CP or GR records"` (list at most 3 IDs), and return early. Keep this reason first so the model (and the trace) sees the specific cause rather than the contract's generic "must be a non-empty list".
4. If the finding is otherwise accepted and `ledger_ids` is non-empty: `clean["narrative"]` gets a trailing sentence `" Ledger entries consulted: GL00652, GL02894."` (comma-separated, all of them, in order). Append to the existing narrative (separated by a space) or create the narrative from that sentence alone when there was none. Apply the `NARRATIVE_MAX` truncation AFTER appending.
5. IDs that are neither in `all_record_ids()` nor ledger entry IDs remain a rejection exactly as today (`test_fabricated_evidence_rejected` must not change).
6. `guard()` keeps its signature `(clean_finding | None, reasons)`; nothing in `agent/investigate.py` needs to change for this issue. Update the module docstring: one line saying ledger IDs are set aside, not rejected.

## Tests (add to `tests/test_guard.py`; use the existing `ds` fixture and `_ref_finding`)
Facts to rely on: `GL00652` exists in `data_estate/out/company_42/ledger.csv`; ledger IDs look like `GL00001`.
- `test_ledger_ids_moved_to_narrative`: take `_ref_finding(ds, "duplicate_invoice_payment")`, copy it, append `"GL00652"` to `evidence` → `guard` returns a clean finding with `reasons == []`; `clean["evidence"]` equals the reference evidence list (no `GL00652`); `"GL00652" in clean["narrative"]`; `clean["narrative"]` contains `"Ledger entries consulted"`.
- `test_only_ledger_ids_rejected`: same reference finding with `evidence = ["GL00652"]` → `clean is None` and `reasons[0]` contains `"only ledger entries"`.
- `test_ledger_ids_deduped_in_narrative`: `evidence = [<first reference evidence id>, "GL00652", "GL00652"]` → accepted; the narrative mentions `GL00652` exactly once.
- `test_ledger_plus_fabricated_still_rejected`: `evidence = reference + ["GL00652", "TX99999"]` → rejected; reasons mention `TX99999`.
- `test_narrative_truncated_after_ledger_append`: narrative of 1000 `"x"` plus one ledger id → `len(clean["narrative"]) == NARRATIVE_MAX`.

## Definition of done
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies
- [ ] `python -m agent.guard data_estate/out/company_42 /tmp/f.json` where `f.json` is the reference duplicate-payment finding plus `"GL00652"` prints `ACCEPTED` and the narrative shows the ledger id
- [ ] Every existing guard test passes unchanged

## #66 agent/investigate.py: feed guard rejections back to the model, then fall back to the deterministic finding  `hermes-ok`  CLOSED

## Goal
Today a `record_finding` that the guard rejects ends the lead: `_llm_loop` in `agent/investigate.py` sets `decision_made = True` and the entity lands in `not_pursued` with the guard's reasons as the drop reason. Across the seven logged LLM runs on company_42 (`runs/*.jsonl`) that turned a 4/4 dataset into 1/4, 1/4, 3/4, 3/4, 3/4, 4/4, 4/4, while `--no-llm` scores 4/4 every time (`test_no_llm_scores`). The guard's reasons are precise (`amount_mxn 1044000.00 is not within 25% of the recomputed 2070600.00`, `evidence GL03014 not in dataset`), which is exactly what the model needs to fix its call. And for a unit that carries a scheme signature, the deterministic builder `_build_finding` (the `--no-llm` path) already produces a guard-verified finding; when the model cannot, the loop should use that finding and say so in the log, not drop the lead.

This is "the LLM proposes, deterministic code proves" taken to its conclusion: the trace shows the model's attempt, the guard's verdict, and where the final finding came from.

Depends on #65 (ledger IDs in evidence no longer cause a rejection).

## Spec (`agent/investigate.py`, `_llm_loop` only; `_fallback_loop` and `--no-llm` output must stay byte-identical)
1. **Feedback on rejection.** When a `record_finding` tool call is rejected by the guard: emit the `guard` entry as today (`accepted: false`, `reasons`), then instead of ending the lead append a tool message for that tool call id: `tool_message(tc, {"accepted": False, "reasons": reasons, "hint": "Fix the finding using these reasons and call record_finding again, or call drop_lead."})` and continue the while loop. Do NOT `break` out of the for loop over the reply's tool calls on a rejection: any data-tool calls in the same reply still execute and get their tool messages (every tool call in an assistant message must receive a tool message, or the next request is invalid).
2. **Retry budget.** Module constant `MAX_GUARD_RETRIES = 2` (so at most 3 `record_finding` attempts per unit). Count rejections per unit; when the count exceeds the budget, stop calling the model for this unit and go to step 3. `max_steps` still bounds the total number of model calls per unit as today.
3. **Deterministic fallback for signature units.** Whenever the LLM path ends WITHOUT an accepted finding for a unit whose `scheme_hint` is non-empty and in `SCHEME_TO_RULE` (causes: retries exhausted, `max_steps` reached, the model called `drop_lead`, the model replied with no tool call), call `_build_finding(unit, ds, scheme_type, rule_id)`:
   - if it returns a finding: emit `decision` with payload `{"action": "record_finding", "finding": <payload>, "source": "deterministic_fallback", "llm_outcome": <"rejected"|"dropped"|"no_terminal"|"max_steps">, "llm_reason": <the model's drop reason, or the last guard reasons joined with "; ", or "">}`, then `guard` with `{"accepted": true, "reasons": [], "finding": <payload>, "source": "deterministic_fallback"}`; append to `findings`; do not add the entity to `dropped`.
   - if it returns `None`: drop as today with reason `"the aggregated scheme finding was rejected by the evidence guard"`, and keep the model's reason in the decision payload as `llm_reason`.
   The model's explicit `drop_lead` on a signature unit is therefore overridden, but its reason is preserved in the log and the `decision` entry for the drop is still emitted before the fallback decision, so the trace shows both.
4. **Provenance on the happy path.** Every `decision` with `action: "record_finding"` and every `guard` entry now carries `"source": "llm"` (or `"deterministic_fallback"`) and `"attempt": <1-based count of record_finding calls for this unit>`. `_fallback_loop` entries carry `"source": "deterministic"` and `"attempt": 1`. These are additive payload fields (readers ignore unknown fields).
5. Units without a signature behave as today (dropped by rule without a model call). #70 changes that later.
6. Update the module docstring (the two execution paths paragraph) to describe the retry and the fallback.

## Tests (`tests/test_investigate.py`; `FakeLLM`, no network; reuse the S00004 kickback finding from `test_fakellm_drives_one_lead`: accused `["S00004", "E00002"]`, rule `"R2"`, amount `575360.0`, evidence `["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"]`)
- `test_guard_rejection_is_fed_back_and_retry_succeeds`: replies = [record_finding with `amount_mxn: 1.0` (rejected on amount), the correct record_finding]. Assert the log kinds are exactly `run_start, lead, hypothesis, decision, guard, decision, guard, run_end`; first guard `accepted is False`; second guard `accepted is True`, `source == "llm"`, `attempt == 2`; `FakeLLM.calls[1]["messages"][-1]["role"] == "tool"` and its content contains `"not within 25%"`; one kickback finding with amount `575360.0`.
- `test_retries_exhausted_falls_back_to_deterministic`: three rejected record_findings (amount `1.0` each) → three rejected guards, then a `decision` with `source == "deterministic_fallback"`, `llm_outcome == "rejected"`, followed by an accepted `guard`; `FakeLLM.calls` has length 3; the case has the kickback finding with amount `575360.0`; `"S00004"` not in `not_pursued`.
- `test_model_drop_on_signature_unit_is_overridden_with_reason_kept`: one reply `drop_lead("S00004", "not enough")` → log has a `decision` `drop_lead` with reason `"not enough"` followed by a `decision` `record_finding` with `source == "deterministic_fallback"`, `llm_outcome == "dropped"`, `llm_reason == "not enough"`; the finding is in the case.
- `test_no_terminal_reply_falls_back`: one reply with `text="I am not sure"` and no tool calls → `llm_outcome == "no_terminal"`, finding present.
- `test_rejection_does_not_skip_sibling_tool_calls`: one reply with two tool calls in this order: `record_finding` (amount `1.0`) and `get_supplier({"supplier_id": "S00004"})`; second reply the correct finding. Assert `FakeLLM.calls[1]["messages"]` contains exactly two `role: "tool"` messages after the first assistant message, one per tool call id.
- `test_no_llm_scores` and `test_run_returns_same_dict_and_identical_files` unchanged and green.
- `test_llm_end_to_end_with_real_endpoint`: tighten `results_recall >= 0.75` to `== 1.0` (it skips without `.env`; with the fallback it is guaranteed on company_42).

## Definition of done
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies
- [ ] `python -m agent.investigate data_estate/out/company_42 --no-llm --out /tmp/a.json` produces the same case file as before this change
- [ ] A human with `.env` runs `python -m agent.investigate data_estate/out/company_42 --out /tmp/c.json` and `python -m data_estate.score data_estate/out/company_42 /tmp/c.json` shows `results_recall: 1.0` and `judgment_penalty: 0` (Hermes: note this in the PR body as "not run, no .env")

## #67 Streamed step log + docs/STEP_LOG.md contract + agent/steplog.py validator + agent/README.md refresh  `hermes-ok`  CLOSED

## Goal
A teammate is building the frontend separately, outside this repo, against the JSONL step log that `agent.investigate` writes. Today the only spec is the docstring of `agent/investigate.py` plus the superseded UI issue #26, `agent/README.md` still says "planned modules ... detectors.py", and, the real blocker, **the log is written only at the end of the run** (`_write_log` runs after `run_end`), so nothing can tail it live. This issue makes the log a stream, writes the contract down once, and adds a test that fails when the writer drifts from it.

## Deliverables
### 1. Streamed log (`agent/investigate.py`)
- `_Log.__init__(self, path: str | None)`: when `path` is given, create the parent directory, open the file with `open(path, "w", encoding="utf-8")` and keep the handle. `emit()` appends the entry to `self.entries` AND, when a handle is open, writes `json.dumps(entry, ensure_ascii=False, default=str) + "\n"` and calls `flush()` immediately. Add `close()`; `run()` calls it in a `finally` so a crash mid-run still leaves a readable file (without a `run_end` line, which is how a reader detects an aborted run).
- `run()` computes `log_path` before constructing `_Log(log_path)`; remove `_write_log` (or keep it as a no-op alias if something imports it; nothing in the repo does).
- Output must be byte-identical to today's files for the same run.

### 2. `agent/steplog.py` (the contract as code)
- `KINDS = ("run_start", "lead", "hypothesis", "tool_call", "tool_result", "decision", "guard", "run_end")` and `REQUIRED_PAYLOAD: dict[str, dict[str, type | tuple[type, ...]]]` listing, per kind, the payload fields that must be present and their JSON types. Take the fields from the writer:
  - `run_start`: `dataset: str, n_leads: int, mode: str ("llm"|"no-llm"), model: str`
  - `lead`: `entity_id: str, name: str, rank: int, detectors: list, n_detectors: int, total_mxn: number, leads: list`
  - `hypothesis`: `text: str, scheme_type: str`
  - `tool_call`: `name: str, args: dict`
  - `tool_result`: `name: str, n_rows: int, summary: str, ids: list, rows: list`
  - `decision`: `action: str ("record_finding"|"drop_lead")`; when `record_finding`: `finding: dict` with `scheme_type, accused, rule, amount_mxn, evidence`; when `drop_lead`: `reason: str`
  - `guard`: `accepted: bool, reasons: list, finding: dict`
  - `run_end`: `n_findings: int, n_not_pursued: int, wall_s: number, case_file: str, report: str`
  Extra payload fields are allowed (readers ignore unknown fields; #66 adds `source` and `attempt`).
- `parse_lines(text: str) -> tuple[list[dict], bool]`: parse a JSONL string, tolerating a partial last line (returns `(entries, complete)` where `complete` is False when the last line was cut off).
- `validate_entries(entries: list[dict]) -> list[str]`: one human-readable error per violation: envelope keys exactly `ts, entity_id, step, kind, payload`; `ts` parses with `datetime.fromisoformat`; `step` strictly increasing by 1 from 1; unknown kind is NOT an error (forward compatibility) but a known kind with a missing/mistyped required field is; first entry is `run_start`; if a `run_end` exists it is the last entry; every `guard` is immediately preceded by a `decision` with `action == "record_finding"` for the same `entity_id`; every `tool_result` is immediately preceded by a `tool_call` with the same `name` and `entity_id`; every `lead` entity is later the subject of at least one `decision`.
- CLI: `python -m agent.steplog runs/<file>.jsonl` prints `OK <n entries>` or the errors and exits 1.

### 3. `docs/STEP_LOG.md` (written for the frontend developer; no internal jargon without a definition)
- What the file is, where it lands (`--log` path, default `runs/<UTC ts>.jsonl`), that it is appended and flushed per event, and how to tail it (partial last line = writer mid-write, retry; `run_end` = finished; no `run_end` and no new lines for 60 s = aborted).
- The envelope, then one subsection per kind: the payload table (field, type, meaning) and **one real example line copied from `demo/sample_trace.jsonl`** (a real LLM run on company_42, committed by #73; if it is missing when you work, generate `python -m agent.investigate data_estate/out/company_42 --no-llm --log /tmp/t.jsonl` and use that, noting `tool_call`/`tool_result` only appear in LLM mode).
- Ordering guarantees per entity: `lead` → optional `hypothesis` → zero or more `tool_call`/`tool_result` pairs → `decision` (+ `guard` after `record_finding`, possibly several decision/guard pairs after #66) ; entities may interleave once runs are concurrent (#71), so group by `entity_id`, never assume contiguity.
- ID conventions: entities `S…` supplier, `C…` customer, `E…` employee, `""` for run-level events; records: 36-char UUID = invoice, `TX` = company bank transaction, `CP` = counterparty statement row, `GR` = goods receipt, `GL` = ledger entry (context only, never evidence).
- Where the names come from (`agent.data.load(...).suppliers/customers/employees`) and that the API server (#68) exposes them.
- The compatibility rule: writers add fields, never rename or remove; readers ignore unknown kinds and fields.

### 4. `agent/README.md` rewrite
Module table (`data`, `detectors/*`, `leads`, `tools`, `llm`, `config`, `rules`, `guard`, `contract`, `steplog`, `investigate`, `report`) with one line each; the CLI commands (`investigate`, `leads`, `guard`, `contract`, `report`, `steplog`); the two execution paths (`--no-llm` deterministic, LLM loop with guard); where outputs go; links to `docs/STEP_LOG.md` and the case-file contract in `data_estate/score.py`.

## Tests: `tests/test_step_log_contract.py`
- `test_no_llm_log_validates(tmp_path, dataset_dir)`: run `agent.investigate.run(dataset_dir, out=None, log=tmp, no_llm=True)`; `validate_entries(parse_lines(...)[0]) == []`.
- `test_fakellm_log_validates`: the two-reply FakeLLM script from `tests/test_investigate.py::test_fakellm_drives_one_lead` → `[]` errors, and the kinds include `tool_call` and `tool_result`.
- `test_log_is_streamed(tmp_path, dataset_dir)`: FakeLLM whose second reply is a callable that, when invoked, reads the log file and asserts it already contains a `lead` and a `hypothesis` line (the run has not ended yet).
- `test_partial_last_line_tolerated`: a valid log text with the last line cut in half → `parse_lines` returns all complete entries and `complete is False`.
- `test_validator_catches_drift`: hand-built entries with (a) a `guard` not preceded by a `record_finding` decision, (b) `step` skipping a number, (c) a `lead` without a required field → three distinct errors; an entry with an unknown kind → no error.
- `test_sample_trace_validates`: if `demo/sample_trace.jsonl` exists, it validates; otherwise skip.
- `test_steplog_cli(tmp_path)`: `python -m agent.steplog <valid file>` exits 0 and prints `OK`.

## Definition of done
- [ ] `tail -f runs/latest.jsonl` in one terminal shows lines appearing while `python -m agent.investigate ... --log runs/latest.jsonl --no-llm` runs in another (it is fast; use the FakeLLM test for the real proof)
- [ ] `docs/STEP_LOG.md` has an example line for every kind, `agent/README.md` no longer says "planned"
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies

## #68 api/server.py: stdlib HTTP + SSE server so the frontend can start runs and stream the step log  `hermes-ok`  OPEN

## Goal
The frontend (built separately, not in this repo) needs three things from the backend: start an investigation on a chosen dataset, receive the step-log events live, and fetch the finished case file, report and, when hidden truth exists, the score. There is no HTTP API today, only the CLI. Build one with the standard library (`http.server.ThreadingHTTPServer`, `json`, `threading`, `argparse`, `urllib.parse`), no FastAPI/uvicorn (AGENTS.md rule 4).

It lives OUTSIDE `agent/`, in a new package `api/`, because the score endpoint imports `data_estate.score`, which reads `hidden/`. AGENTS.md rule 2 and `tests/test_no_hidden_access.py` cover `agent/` only; `api/` may import `data_estate` the way `scripts/eval_batch.py` does. `api/` never copies anything from `hidden/` into a response except through the explicit `/score` endpoint.

Depends on #67 (the log must be streamed at emit time for `/events` to work).

## Spec
`python -m api.server [--host 127.0.0.1] [--port 8765] [--runs runs] [--out-root data_estate/out/live]`

Every response carries `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Headers: Content-Type`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`; any `OPTIONS` request returns 204 with those headers. Errors are JSON `{"error": "<message>"}` with 400/404/409/500. All JSON is UTF-8, `ensure_ascii=False`.

| Method & path | Body / query | Returns |
|---|---|---|
| `GET /health` | | `{"ok": true, "llm_configured": <agent.config.settings() is not None>, "model": "<LLM_MODEL or ''>"}` — never the key or URL |
| `GET /datasets` | | list of `{"name", "path", "has_truth": <hidden/ground_truth.json exists>, "n_suppliers", "n_customers", "n_invoices", "n_bank_txns"}` for every directory under `data_estate/out/` and `<out-root>` that contains `company.json`, sorted by name |
| `POST /datasets` | `{"seed": int, "schemes": "all" \| "clean" \| "efos,kickback,roundtrip,duplicate" (any subset)}` | 201 with that dataset's entry. Generates with `data_estate.generate.Generator(seed).build(list)` + `write_estate` into `<out-root>/company_<seed>/`, then `data_estate.validate.check` must return `[]` (else 500 with the errors). Seed 42 → 409 `company_42 is frozen`. Existing directory → regenerate (deterministic). Map `"all"` to the four names, `"clean"` to `[]` like `scripts/eval_batch.py::plan` |
| `GET /datasets/{name}/entities` | | `{"S00004": {"name", "kind": "supplier", "category"}, "C00005": {"name", "kind": "customer"}, "E00002": {"name", "kind": "employee", "role"}, ..., "COMPANY": {"name", "clabe"}}` from `agent.data.load` |
| `POST /runs` | `{"dataset": "company_42" \| "<path>", "no_llm": false, "max_leads": 12, "max_steps": 12}` | 202 `{"run_id", "dataset", "log", "case", "report"}`. Runs `agent.investigate.run(dataset, out=<runs>/<run_id>_case.json, log=<runs>/<run_id>.jsonl, ...)` in a background thread, then `agent.report.render` to `<runs>/<run_id>_case.md`. `run_id` = `<UTC %Y%m%dT%H%M%SZ>-<4 hex>`. One run at a time: while one is `running`, respond 409 `{"error": "a run is in progress", "run_id": "<that id>"}` |
| `GET /runs` | | newest-first list of `{"run_id", "dataset", "status": "running" \| "done" \| "failed", "started", "finished", "n_findings", "error"}`; includes runs from earlier server processes found in `<runs>/` (`*_case.json` exists → `done`; log without case → `failed`) |
| `GET /runs/{id}` | | one entry as above, 404 if unknown |
| `GET /runs/{id}/events` | `?after=<step>`; also honours the `Last-Event-ID` header | `text/event-stream`. For every log line with `step > after`: `id: <step>\nevent: <kind>\ndata: <the JSON line>\n\n`. While the run is `running`, tail the file (poll every 250 ms), send `: ping\n\n` every 15 s of silence. After the `run_end` line, or when status becomes `failed`, send `event: end\ndata: {"status": "<status>"}\n\n` and close. Parse lines with `agent.steplog.parse_lines` (partial last line tolerated) |
| `GET /runs/{id}/log` | | JSON array of every entry so far |
| `GET /runs/{id}/case` | | the case file (404 until `done`) |
| `GET /runs/{id}/report` | | the markdown as `text/markdown; charset=utf-8` (404 until `done`) |
| `GET /runs/{id}/score` | | `data_estate.score.score(dataset, case)` (404 when the dataset has no `hidden/ground_truth.json` or the run is not `done`). Document in the module docstring and README: for the team and for judges who ask; the frontend must not show it by default |

Implementation notes: a `RunRegistry` guarded by a `threading.Lock`; the investigation thread is a `threading.Thread(daemon=True)`; exceptions inside the thread set `status = "failed"` and `error = repr(exc)` and are also printed to stderr. Expose module-level `run_investigation = agent.investigate.run` and `render_report = agent.report.render` so tests can monkeypatch them. `serve(host, port, runs, out_root) -> ThreadingHTTPServer` returns the bound server (port 0 allowed) so tests can run it in a thread and read `server.server_address`. `main()` calls `serve_forever()`; Ctrl-C shuts down cleanly.

## Tests: `tests/test_api_server.py` (stdlib `urllib.request`, `threading`, `socket`; no `requests`)
- Fixture: server on `127.0.0.1:0` in a thread with `runs=tmp_path/"runs"`, `out_root=tmp_path/"out"`; shut down at teardown.
- `/health` → `ok true`, key `llm_configured` present, no `api_key`/`base_url` keys.
- `/datasets` contains `company_42` with `has_truth true` and `n_invoices > 0`; no value anywhere in the response mentions `ground_truth`.
- `POST /runs {"dataset": "company_42", "no_llm": true}` → 202; poll `/runs/{id}` until `done` (timeout 30 s); `/case` has 4 findings; `/score` has `results_recall == 1.0` and `judgment_penalty == 0`; `/report` body starts with `#`; `/log` kinds start with `run_start` and end with `run_end`; `/events?after=0` read with a 10 s socket timeout yields ≥ 34 `data:` lines and a final `event: end`; `Last-Event-ID: 30` yields only steps > 30.
- 409 on concurrent runs: monkeypatch `api.server.run_investigation` with a function that sleeps 1 s then calls the real one; start a run; a second `POST /runs` within that second → 409.
- `POST /datasets {"seed": 42}` → 409; `{"seed": 9001, "schemes": "clean"}` → 201, `tmp_path/out/company_9001/company.json` exists, `has_truth true`; `GET /datasets/company_9001/entities` has a `COMPANY` key.
- `/datasets/company_42/entities` maps `S00030` to a dict with `name` and `kind == "supplier"` and `E00002` to `kind == "employee"`.
- CORS: `Access-Control-Allow-Origin: *` on `/health`; `OPTIONS /runs` → 204.
- Unknown run id → 404 JSON.

## Definition of done
- [ ] `python -m api.server` in one terminal; `curl -s -X POST localhost:8765/runs -d '{"dataset":"company_42","no_llm":true}'` then `curl -N localhost:8765/runs/<id>/events` prints events and ends with `event: end`
- [ ] README.md "Everyday commands" gets the server line and a pointer to `docs/STEP_LOG.md`; a short `api/README.md` lists the endpoints (copy the table above)
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies

## #69 agent/clear.py: replace canned drop reasons with checks that cite records (or admit they cannot)  `hermes-ok`  OPEN

## Goal
`agent/investigate.py` drops every lead that has no scheme signature using `_DET_CLAUSES`: one fixed sentence per detector, written without looking at the data, e.g. `"the shared address is a commercial building, not an employee's home"`. On company_42 those sentences happen to be true. On a judge's hand-edited dataset they can be false (a supplier registered at an employee's home with no kickback outflow would still be "cleared" as a commercial building), and when a judge asks "how do you know?" the honest answer today is "it is hard-coded". The Judgment criterion is exactly that question, and `not_pursued` reasons are read aloud on stage.

Replace each clause with a check over the `Dataset` that returns a reason WITH record IDs when the innocent explanation actually holds, and `None` when it cannot be confirmed. A `None` becomes an honest `"unverified: ..."` reason (and, in #70, an escalation to the model).

## Spec: new module `agent/clear.py`
`clear_reason(detector: str, entity_id: str, leads: list[dict], ds: Dataset) -> str | None` dispatches on the detector name to one function each (`_clear_<detector without "detect_">`). Pure pandas over the Dataset; never reads `hidden/`; never raises (unknown detector → `None`). Each reason is one sentence a non-engineer can read, ends with record IDs, and lists at most 3 IDs followed by `"and N more"` when there are more. Amounts formatted `MXN 1,234.56`. Use `agent.tools.Tools(ds).check_69b(rfc)` and `agent.rules._active_69b_supplier_ids(ds)` rather than re-implementing 69-B logic.

Checks, with the facts on company_42 the tests rely on:

| Detector | Innocent iff | Reason shape (example entity on company_42) |
|---|---|---|
| `detect_new_vendor_round_amounts` | every `recibida` invoice of the supplier has ≥ 1 goods receipt AND the RFC is not live on 69-B | S00009: `"new vendor with round amounts, but all 5 invoices have warehouse-signed goods receipts (GR..., GR..., GR... and 2 more) and RFC JMK241214132 is not on the 69-B list"` |
| `detect_name_twin_69b` | `check_69b(rfc)["listed"]` is False | S00007: names the supplier's RFC `SZC9707063JK` and every twin's RFC and `situacion` from `name_matches` (here `TAO890114RLQ`); adds the receipt count when receipts exist (S00007 has 8/8) |
| `detect_shared_supplier_address` | the supplier's `street`+`city` matches no employee's `home_street`+`home_city` AND `counterparty_bank` shows no `out` row from the supplier's `clabe` to any employee `personal_clabe` | S00026: `"shares its address (Av. Garza Sada 337) with S00024 (Grupo del Norte SAPI de CV); it matches no employee's home and its bank statement shows no outflow to an employee account; 6 of 6 invoices have goods receipts (GR..., GR..., GR... and 3 more)"` |
| `detect_no_receipt` and `detect_fast_pay_no_deliverable` | the supplier's `category` is one that never carries goods receipts by construction (`servicios`, `logistica`, `renta_util`) AND the RFC is not live on 69-B AND the address matches no employee home AND no `counterparty_bank` outflow to an employee CLABE | S00036: `"one legal-services invoice (809BD813-4F13-823B-51F4-A72499503858, MXN 440,800.00) describing 'Honorarios — litigio mercantil exp. 412/2025', approved by E00001; services carry no goods receipt; RFC BNW120625NY2 is not on the 69-B list"`. Include the `descripcion` of the largest invoice and its `approved_by`. For a goods category (`consumibles`, `materia_prima`, `refacciones`) with missing receipts → `None` |
| `detect_cash_payments` | every `forma_pago == "01"` invoice has `total <= 2000` AND has a goods receipt | S00011: `"3 cash invoices, the largest MXN 1,821.72, all under the MXN 2,000 deductibility cap (LISR Art. 27-III), goods received (GR..., GR..., GR...)"` |
| strong detectors (`detect_efos`, `detect_employee_address_match`, `detect_kickback_outflow`, `detect_round_trip`, `detect_duplicate_payments`, `detect_clabe_not_on_master`) firing on a unit WITHOUT a complete signature | never cleared by rule | return `None` |

Integration in `agent/investigate.py`:
- `_drop_reason(dossier, ds)` calls `clear_reason` for each detector on the dossier. If every call returns a string: join them with `"; "` (dedupe identical sentences). If any returns `None`: the reason is `"unverified: <comma-separated detectors that returned None> fired and the innocent explanation could not be confirmed from the records; needs a human or a deeper investigation"`, and the `decision` payload gets `"verified": false` (`true` otherwise). Delete `_DET_CLAUSES`.
- `_build_not_pursued` unchanged apart from calling the new `_drop_reason`.
- Both `--no-llm` and LLM paths use it (the LLM path only for units without a signature, as today).

## Tests: `tests/test_clear.py` (fixtures `ds`, `decoy_ids`, `truth` from `tests/conftest.py`)
- One test per row of the table on the named entity: `test_clear_new_vendor_s00009` (contains `"5 invoices"`, three IDs that exist in `ds.goods_receipts["receipt_id"]`, `"JMK241214132"`); `test_clear_name_twin_s00007` (`"SZC9707063JK"` and `"TAO890114RLQ"`); `test_clear_shared_address_s00026` (`"S00024"`, `"Garza Sada 337"`); `test_clear_law_firm_s00036` (`"809BD813-4F13-823B-51F4-A72499503858"`, `"412/2025"`, `"E00001"`); `test_clear_cash_s00011` (`"1,821.72"`, `"2,000"`, ≥ 1 `GR` id).
- `test_strong_detector_never_cleared`: `clear_reason("detect_efos", "S00030", [], ds) is None` and the same for `detect_duplicate_payments` on `S00017`.
- `test_goods_category_without_receipt_is_none`: build an in-memory copy of `ds` (`dataclasses.replace` with copied DataFrames), drop every goods receipt of S00009, then `clear_reason("detect_no_receipt", "S00009", [], ds2) is None` and `clear_reason("detect_new_vendor_round_amounts", ...) is None`.
- `test_shared_address_at_employee_home_is_none`: copy `ds`, set S00026's `street`/`city` to E00002's `home_street`/`home_city` → `None`.
- `test_every_decoy_reason_cites_a_record`: `agent.investigate.run(company_42, out=None, log=None, no_llm=True)`; for each `decoy_ids` entry in `not_pursued` the reason contains at least one ID from `ds.all_record_ids()` or a supplier RFC from `ds.suppliers["rfc"]`, and does not start with `"unverified:"`.
- `test_every_not_pursued_reason_is_grounded_or_unverified`: for every `not_pursued` entry on company_42 (`--no-llm`): reason either starts with `"unverified:"` or contains a record ID / RFC / other entity ID.
- `test_unknown_detector_is_none`.
- `tests/test_investigate.py::test_no_llm_scores` must stay green (recall 1.0, penalty 0, every decoy in `not_pursued`).

## Definition of done
- [ ] `python -m agent.investigate data_estate/out/company_42 --no-llm --out /tmp/a.json` and every `not_pursued` reason names a record; `_DET_CLAUSES` is gone
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies
- [ ] A LEARNINGS.md entry (3 lines: tried / happened / changed) about replacing canned reasons with checks

## #70 agent/investigate.py: escalate unverified weak leads to the model; 'other' findings become a suspicious tier in not_pursued  `hermes-ok`  OPEN

## Goal
After #69, a weak lead (no scheme signature) whose innocent explanation cannot be confirmed from the records is marked `unverified`. Today such leads are dropped without the model ever looking at them. Two things should happen instead:

1. In LLM mode the model investigates them with the tools. This is also our only path to *notice* a scheme we did not plan for, which is what the judges do on stage ("hide a fresh scheme in the data").
2. Because the guard's R5 / `other` rule has no amount recomputation, an `other` finding must never become an accusation. It becomes a **"suspicious, unproven"** entry in `not_pursued` with the evidence the model gathered. That is the tiered output from `docs/STRATEGY.md` §3 (Proven / Suspicious / Cleared) expressed inside the frozen case-file contract. The scorer never penalises `not_pursued`, so a decoy that the model over-reads still costs nothing.

Depends on #66 (retry/fallback loop) and #69 (`clear_reason`).

## Spec (`agent/investigate.py`)
1. **Escalation.** In `_llm_loop`, for a unit with `scheme_hint == ""`: compute the reasons via `_drop_reason`. If it is verified (no detector returned `None`), drop as today with `decision` payload `{"action": "drop_lead", "reason", "verified": true, "escalated": false}`. Otherwise run the model investigation for the unit (same messages as a signature unit) with one extra line at the end of the user prompt:
   `"No scheme signature matched. The automatic clearing check could not confirm an innocent explanation for: <detectors that returned None>. Investigate with the tools. Call record_finding only if one of R1-R4 is fully evidenced with record IDs and the full amount; call record_finding with scheme_type 'other' and rule 'R5' if something is wrong but it is none of the four; otherwise call drop_lead with what you checked."`
   The `decision` entries for that unit carry `"escalated": true`.
2. **Escalation cap.** New CLI flag `--max-escalations` (default 4), threaded through `run(..., max_escalations=4)`. Units are already ordered signature-first; escalate the first N unverified units in rank order; the rest are dropped with the `"unverified: ..."` reason and `"escalated": false`.
3. **`other` is parked, never accused.** When the guard accepts a finding whose `scheme_type == "other"` (from any unit): do NOT append it to `findings`. Emit the `decision` (`record_finding`) and the accepted `guard` as usual, then emit `decision` with `{"action": "park_lead", "tier": "suspicious", "entity_id": <each accused id>, "reason": <see below>}` once per accused entity, and store the reason in a new `parked: dict[str, str]`. Reason text: `"suspicious, unproven: <narrative or 'the model flagged this entity'>. Evidence: <evidence ids, max 5, then 'and N more'>"`. `_build_not_pursued` uses `parked` first, then `dropped`, then `_drop_reason`.
4. The deterministic fallback of #66 applies only to units with a signature; escalated units never get a fallback finding. A rejected `other` finding after the retry budget → drop with the `"unverified: ..."` reason plus `" (model: <its last narrative or guard reasons>)"`.
5. `--no-llm`: unverified weak leads keep the `"unverified: ..."` reason, `"escalated": false`.
6. Add `park_lead` to `agent/steplog.py` (`REQUIRED_PAYLOAD["decision"]` gains the `park_lead` action with `tier: str, reason: str`) and to `docs/STEP_LOG.md`.
7. Docstring: describe the three outcomes for a weak lead (cleared with records / escalated / unverified).

## Tests (`tests/test_investigate.py`, FakeLLM, no network)
Helper for these tests: monkeypatch `agent.investigate._build_units` to wrap the real function and keep only the units whose `entity_id` is in a given set (so the FakeLLM script only has to cover one unit), and monkeypatch `agent.clear.clear_reason` to return `None` for `detect_shared_supplier_address`.
- `test_unverified_weak_lead_is_escalated`: units = {S00026}; replies: `get_supplier({"supplier_id": "S00026"})`, then `drop_lead("S00026", "freight company, carta porte on every invoice")`. Assert the log has a `tool_call` `get_supplier` for S00026, the `decision` is `drop_lead` with that reason and `escalated is True`, `not_pursued` has S00026 with that reason, `findings == []`.
- `test_verified_weak_lead_not_escalated`: units = {S00009} with the real `clear_reason` → `FakeLLM.calls == []`, decision `verified is True`, `escalated is False`.
- `test_other_finding_is_parked_not_accused`: units = {S00026}; reply: `record_finding` with `scheme_type "other"`, `rule "R5"`, `accused ["S00026"]`, `amount_mxn 1.0`, `evidence [<one recibida invoice uuid of S00026 taken from ds.invoices>]`, narrative `"odd freight pattern"`. Assert `findings == []`; `not_pursued` has S00026 with reason starting `"suspicious, unproven: odd freight pattern"` and containing that uuid; the log has `decision` `park_lead` with `tier == "suspicious"`; `data_estate.score.score` gives `judgment_penalty == 0` and `decoys_accused == []`.
- `test_escalation_cap`: `clear_reason` → `None` for everything; units = {S00026, S00009}; `max_escalations=1`; one `drop_lead` reply → `len(FakeLLM.calls) == 1`; S00009's reason starts with `"unverified:"` and its decision has `escalated is False`.
- `test_rejected_other_after_retries_is_unverified`: three rejected `other` findings (evidence `["TX99999"]`) → S00026 reason starts with `"unverified:"`, no fallback finding, `findings == []`.
- `test_no_llm_scores` and the #66 tests unchanged.

## Definition of done
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies
- [ ] `docs/STEP_LOG.md` documents `park_lead`
- [ ] LEARNINGS.md entry: why `other` is parked rather than accused (the R5 amount cannot be recomputed, and a decoy accused as `other` would still be a double penalty)

## #71 agent/investigate.py: investigate units concurrently (--workers) to keep a cold LLM run under 30 s  `hermes-ok`  OPEN

## Goal
A cold LLM run on company_42 takes 57–86 s (`wall_s` in `runs/20260912T171920Z.jsonl`, `...T173014Z`, `...T175005Z`, `debug_cold.jsonl`): four signature units investigated one after another, 6–10 tool calls each, one model round-trip per tool call. The stage budget is 90 s for the whole run and #70 adds up to four escalated units, so sequential no longer fits. Investigate units concurrently.

Depends on #66. Coordinate with #70 only through the log contract (the per-entity ordering guarantee in `docs/STEP_LOG.md` already tells readers to group by `entity_id`).

## Spec (`agent/investigate.py`, `agent/llm.py`)
1. `run(..., workers: int = 4)` and CLI `--workers 4`. `workers=1` must reproduce today's log byte-for-byte (same order, same steps).
2. `_Log.emit` takes a `threading.Lock`; `step` is assigned and the line written+flushed inside the lock, so steps are strictly increasing across threads and lines never interleave mid-write.
3. `_llm_loop` splits into a per-unit function `_investigate_unit(ds, unit, llm, rec, tools, max_steps) -> tuple[list[dict], dict[str, str], dict[str, str]]` (findings, dropped, parked) with NO shared mutable state except `rec`. The loop submits the first `max_leads` units to a `concurrent.futures.ThreadPoolExecutor(max_workers=workers)` and merges results in unit rank order (so `findings` and `not_pursued` are deterministic regardless of completion order; `findings` is sorted afterwards anyway). The escalation cap from #70 is decided BEFORE submission (the first N unverified units in rank order), so it is not a race.
4. `Tools(ds)` is built once and shared: it is read-only after construction (check `agent/tools.py`; if any method mutates instance state, give each worker its own instance).
5. `agent/llm.py`: the response cache write becomes atomic (write to `<key>.json.tmp` then `os.replace`) so two threads finishing the same key cannot leave a torn file; reading a missing/torn file falls back to a network call. `openai.OpenAI` is thread-safe; one client shared.
6. `run_end.wall_s` unchanged in meaning. Add `"workers": <n>` to the `run_start` payload (additive).
7. `_fallback_loop` stays sequential (it takes 0.13 s).

## Tests (`tests/test_investigate.py`)
- `test_parallel_matches_sequential_case_file`: a FakeLLM built from a callable reply that inspects the last user message to find the unit's entity id and returns, per entity, first a `get_supplier` call and then the deterministic finding for that unit (build it with `agent.investigate._build_finding` on the real units of company_42; the guard accepts it). Run with `workers=1` and `workers=3`, `max_leads=5`; the two case files are equal and both score recall 1.0, penalty 0.
- `test_parallel_log_is_well_formed`: with `workers=3` the log validates under `agent.steplog.validate_entries` (steps strictly increasing, every `tool_result` right after its `tool_call` for the same entity is NOT required across entities; the validator from #67 must therefore check the `tool_call`/`tool_result` pairing per entity subsequence, adjust it if it does not already), and for each entity the subsequence of kinds is `lead, hypothesis, tool_call, tool_result, decision, guard`.
- `test_workers_one_is_byte_identical_to_previous_behaviour`: `workers=1` on the two-reply script from `test_fakellm_drives_one_lead` produces exactly the kinds list that test asserts today.
- `tests/test_llm.py`: `test_cache_write_is_atomic` (no `.tmp` file left behind after `chat`; a torn cache file triggers a fresh request via a fake client).

## Definition of done
- [ ] A human with `.env` measures a cold run on a fresh seed (`LLM_CACHE=0 python -m agent.investigate data_estate/out/company_101 --workers 4`) and records `wall_s` in the PR; target under 30 s on company_42
- [ ] `python -m pytest -q` green, `ruff check .` clean, no new dependencies

## #72 LLM-mode batch evaluation on 10 unseen seeds: docs/eval tables + LEARNINGS entry  `cc`  OPEN

## Goal
The pitch needs the "on records it has never seen" number in LLM mode, and the go/no-go gate before the feature freeze is "mean recall ≥ 0.8, penalty 0 on every seed" (`docs/PLAN.md`). `scripts/eval_batch.py` (#25) exists, `docs/eval/` is empty. All logged LLM runs so far are on company_42, whose answers the model may have effectively memorised through the response cache. This needs `.env`, so it is a human/Claude Code task, not Hermes.

## Steps
1. Baseline now, before #66 lands:
   ```
   LLM_CACHE=0 python scripts/eval_batch.py --seeds 101-110 --schemes random --out docs/eval/2026-09-13-llm-baseline.md
   python scripts/eval_batch.py --seeds 101-110 --schemes random --no-llm --out docs/eval/2026-09-13-nollm.md
   ```
2. Repeat the LLM run after #66, #69 and #70 are merged → `docs/eval/<date>-llm.md`. Keep both tables; the diff is a slide.
3. Also run `--schemes clean` on 3 seeds (`--seeds 201-203`) in LLM mode: zero findings expected on honest books.
4. Add to `LEARNINGS.md`: what the baseline showed (which schemes the model loses, how often, why: guard rejections on amount/evidence) and what changed.
5. If any seed shows `penalty > 0` or a `clean` seed has a finding, open a follow-up issue with the seed number and the `not_pursued`/`findings` entries, labelled `hermes-ok` if the fix is a detector or guard rule, `needs-human` otherwise.

## Definition of done
- [ ] Both tables committed under `docs/eval/`, PR description quotes `mean_recall`, `seeds_with_penalty`, `wall_p50_s`, `wall_p95_s`
- [ ] LEARNINGS.md entry
- [ ] Gate met (mean recall ≥ 0.8, no penalties, no findings on clean seeds) or a follow-up issue filed for every failure

## #73 docs: PLAN.md refresh, HERMES_BRIEF.md for auto-merge, demo/sample_trace.jsonl, issue queue cleanup  `cc`  CLOSED

## Goal
The plan and the Hermes brief predate the investigation loop, the LLM runs and the decision to build the frontend outside this repo. Refresh them so the queue and the docs agree.

## Deliverables (docs only, plus one fixture)
- `docs/PLAN.md`: current status (what works, what the logged LLM runs showed), the refreshed architecture (streamed step log, API server, frontend external), the issue queue in Hermes pick-up order with dependencies, the auto-merge guardrails, the remaining timeline, and the demo plan.
- `docs/HERMES_BRIEF.md`: Hermes may work anywhere in the repo except the frozen dataset and the three protected tests; the merge step (wait for the `test` check, squash-merge, delete the branch) and what to do when CI is red; never weaken or delete tests to make CI pass.
- `demo/sample_trace.jsonl`: a real LLM run on company_42 with all four findings (`runs/20260912T174705Z.jsonl`), for the frontend developer and for #67's example lines.
- `LEARNINGS.md`: entry on the LLM-mode recall problem (truncated tool-call arguments before #64, ledger IDs after) and the fix plan.
- `docs/ISSUES.md` regenerated with `python scripts/sync_issues.py`.
- Issue queue: #28 closed (done in PR #61), #26 relabelled `needs-human` (frontend is external), #27 rewritten to depend on the API server.

## Definition of done
- [ ] `python -m pytest -q` green
- [ ] Every open issue is labelled and, where it depends on another, says `Depends on #n`

## #78 AGENTS.md + README: judges' estate as input contract, submission.json as output contract, five scheme types  `cc`  OPEN

## Goal
The judges' pack (`docs/SPEC_GAP.md`) changes three contracts at once: what we read, what we write, and the scheme enum. Every agent reads AGENTS.md first, so it must say so before the code changes land, or Hermes will refuse the schema work under rule 5.

## Spec
Edit `AGENTS.md`:
- **Layout:** add `data_estate/out/estate_42/` (frozen judge-shaped export, once #80 lands), `scripts/judges/` (vendored `validate_format.py`), `agent/submit.py`, `agent/challenge.py`.
- **Rule 5** becomes: "The *input* contract is the judges' `estate_schema.sql` (SQLite `.db` or CSV dir) **and** our legacy CSV layout; the *output* contract is the judges' `submission_schema.json` plus our internal case file. Changes to either need an issue labelled `needs-human`." Keep the rest.
- **Rule 2** adds: "the string `ground_truth` must not appear anywhere under `agent/` (judges grep for it)".
- **Scheme types:** two lists. Judges' (the only ones a submission may use): `phantom_vendor`, `kickback`, `round_tripping`, `threshold_splitting`, `revenue_inflation`. Internal (detectors, leads, rules): `efos_fake_supplier`, `kickback_shell`, `round_trip_sales`, `duplicate_invoice_payment`, `threshold_splitting`, `revenue_inflation`, `other`, with the mapping table from `docs/SPEC_GAP.md` and the note that `duplicate_invoice_payment` is reported as a control observation, never a finding.
- **How to run things:** add `python -m agent.investigate <estate.db|dir> --out case_file.json --submission submission.json --report report.html` (flags land in #88 and #90), `python scripts/judges/validate_format.py --submission submission.json --estate estate.db`, and `python -m data_estate.generate --seed 7 --format judges --out data_estate/out/estate_7`.
- **Entity ids:** on judge estates entity ids are `RFC:<rfc>` and `EMP:<id>`; on legacy datasets `S*/C*/E*`. Detectors must never assume a prefix.

Edit `README.md`: the "Setup" and "Everyday commands" blocks get the same commands; add a "Judges' pack" paragraph linking `docs/SPEC_GAP.md` and naming the tuning seeds (42, 101–110, 201–205, 301–306) and the reporting seeds (901–910, never run by hand before the eval).

Update `docs/HERMES_BRIEF.md` "Never" line: add "cite a scheme type outside the internal list".

## Definition of done
- [ ] AGENTS.md, README.md, docs/HERMES_BRIEF.md updated as above; `scripts/sync_issues.py --check` still passes
- [ ] No code changes in this PR

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #79 agent/data.py: load a judges' estate (SQLite .db or CSV dir per estate_schema.sql) into Dataset  `cc`  OPEN

## Goal
Judges score us on estates *they* generate to `estate_schema.sql`, handed to us as a path at run time. Today `agent.data.load` reads only our CSV layout, so on a judge estate every detector finds nothing. This issue makes `load(path)` accept three inputs and return the same `Dataset` the detectors, tools and guard already use, so the whole pipeline works on judge data without touching the detectors.

## Spec
`agent.data.load(path)` auto-detects:
1. **Legacy CSV dir** (has `suppliers.csv`): unchanged.
2. **Judges' SQLite** (`path` is a file, `sqlite3` opens it, table `vendors` exists).
3. **Judges' CSV dir** (has `vendors.csv`): same eight tables as CSVs.

Read with `sqlite3` (stdlib) into pandas via `pd.read_sql_query` with every column cast to `str` first (`keep_default_na` semantics: `None` → `""`), then apply the existing date/float conversions. Add to `Dataset`:
```python
purchase_orders: pd.DataFrame = <empty>   # po_id, vendor_rfc, date, amount, requester, approver, description
contracts: pd.DataFrame = <empty>         # contract_id, vendor_rfc, start_date, value, scope_text
record_table: dict[str, str] = {}         # record id -> judges' source_table name ("invoices", "bank_txns", "purchase_orders", "contracts", "ledger", "vendors", "employees", "efos_list")
source_format: str = "legacy" | "judges"
```
(dataclass fields with defaults go last; legacy loads leave them empty/`"legacy"`).

### Mapping (judges' table → our frame)
- **Company identity:** `company_rfc` = the `receiver_rfc` that appears on the most invoices whose issuer is a vendor; `company_clabe` = the most frequent `from_clabe` among `bank_txns` whose `to_clabe` is a vendor `bank_clabe`. `ds.company = {"name": company_rfc, "rfc": company_rfc, "clabe": company_clabe, "city": ""}`.
- **vendors → suppliers:** `supplier_id = "RFC:" + rfc`, `name = legal_name`, `rfc`, `street = address`, `city = ""`, `clabe = bank_clabe`, `account_holder = legal_name`, `category`, `onboarded = registered_date`, `approved_by` = `emp_id` of the employee whose `name` equals the most frequent `purchase_orders.approver` for that vendor (else `""`), `status = "activo"`.
- **invoices → invoices:** `uuid`, `tipo = "recibida" if receiver_rfc == company_rfc else "emitida"`, `serie = folio = ""`, `fecha = fecha_timbrado = issue_date`, `rfc_emisor = issuer_rfc`, `rfc_receptor = receiver_rfc`, `nombre_*` from vendors by rfc else `""`, `uso_cfdi`, `forma_pago`, `metodo_pago`, `clave_prod_serv = ""`, `descripcion = concepto_text`, `cantidad = 1.0`, `valor_unitario = subtotal`, `subtotal`, `iva`, `total`, `moneda = "MXN"`, `po_number` = matched PO id or `""`, `counterparty_id = "RFC:" + (issuer_rfc if recibida else receiver_rfc)`, `approved_by` = emp_id of the PO approver (else the `ledger.approver` on the invoice's GL rows, else `""`). Keep an extra column `status` (`vigente|cancelado`).
- **PO ↔ invoice match:** same `vendor_rfc`, `abs(po.amount - invoice.total) <= 0.01`, `po.date <= issue_date + 30 days`; earliest unmatched PO wins; one PO per invoice.
- **purchase_orders → goods_receipts (proxy):** one row per matched invoice: `receipt_id = po_id`, `po_number = po_id`, `supplier_id`, `invoice_uuid`, `fecha = po.date`, `descripcion = po.description`, `cantidad = 1.0`, `received_by` = approver's emp_id or name, `warehouse = ""`. Rationale: in the judges' schema a PO is the only deliverable trail; `record_table[po_id] = "purchase_orders"` so exhibits cite the right table. Document this proxy in the module docstring.
- **bank_txns → bank_transactions (company side) and counterparty_bank (third-party legs):** if `from_clabe == company_clabe`: `direction = "out"`, `counterparty_clabe = to_clabe`; if `to_clabe == company_clabe`: `direction = "in"`, `counterparty_clabe = from_clabe`; `account_clabe = company_clabe`, `counterparty_name` from vendors/employees by CLABE else `""`, `reference`, `invoice_uuid` recovered by (a) any invoice `uuid` substring in `reference`, else (b) the vendor/customer with that CLABE + exact `total == amount` + `date >= issue_date`, earliest unpaid invoice wins, else `""`. Keep an extra column `channel`. Rows where neither side is the company become `counterparty_bank` rows: `record_id = txn_id`, `entity_name`/`entity_clabe = from side`, `direction = "out"`, `amount`, `counterparty_name`/`counterparty_clabe = to side`, `fecha = date`, `reference`. `record_table[txn_id] = "bank_txns"` for both.
- **employees → employees:** `employee_id = emp_id` (already `EMP:0001`), `name`, `rfc = ""`, `role`, `home_street = home_city = ""`, `personal_clabe = bank_clabe`.
- **Customers:** distinct `receiver_rfc` on `emitida` invoices → `customer_id = "RFC:" + rfc`, `name` from vendors if the rfc is also a vendor else `""`, `clabe` = the `from_clabe` of inbound payments linked to that customer's invoices (most frequent) else `""`.
- **ledger → ledger:** `entry_id = str(entry_id)`, `fecha = date`, `account_code`, `account_name`, `debit`, `credit`, `descripcion = description`, `invoice_uuid`, `txn_id = ""`; keep extra columns `cost_center`, `approver`.
- **efos_list → efos_69b:** `rfc`, `nombre = legal_name`, `situacion = status.strip().capitalize()` (`definitivo` → `Definitivo`), `fecha_publicacion = publication_date`.
- **contracts → contracts:** as is; `record_table[contract_id] = "contracts"`; `all_record_ids()` includes contract ids and PO ids.

CLABEs are 18-digit strings with leading zeros; never cast to numbers. Dates that fail to parse become `NaT` and are logged once, never raise.

## Test: `tests/test_load_judges.py` with fixture `tests/fixtures/judges_mini/*.csv`
Hand-written mini estate (commit it): company RFC `EMP920101AB1`, CLABE `000000000000000099`; 2 vendors (`AAAA010101AA1` on efos_list as `definitivo`, `BBBB020202BB2` with a PO and a contract); 3 invoices (2 purchases, one per vendor, plus 1 sale from the company to `CCCC030303CC3`); 5 bank_txns: payment of each purchase (reference contains the invoice uuid for one, only the amount for the other), the sale's collection, one payroll transfer, and one **third-party** leg from vendor A's CLABE to employee `EMP:0001`'s CLABE; 1 PO matching vendor B's invoice; 1 contract for vendor B; 2 employees; 1 efos row. The test builds `mini.db` from the CSVs with `sqlite3` in `tmp_path` and loads both the dir and the db:
- both loads give identical frames (`DataFrame.equals` after sorting)
- `ds.company["rfc"] == "EMP920101AB1"`, `ds.company["clabe"] == "000000000000000099"`
- suppliers has 2 rows with ids `RFC:AAAA010101AA1`, `RFC:BBBB020202BB2`; customers has 1 row `RFC:CCCC030303CC3`
- both purchase payments carry the right `invoice_uuid` (one via reference, one via amount+CLABE); the payroll row has `invoice_uuid == ""`
- `counterparty_bank` has exactly 1 row (the vendor→employee leg) with `direction == "out"`; `bank_transactions` has 4
- `goods_receipts` has 1 row with `receipt_id == <po_id>`; `ds.record_table[<po_id>] == "purchase_orders"`, `ds.record_table[<txn_id>] == "bank_txns"`
- `efos_69b.situacion.iloc[0] == "Definitivo"`; `employees.personal_clabe` populated; `source_format == "judges"`
- `run_all(ds)` and `aggregate(ds)` run without error and `detect_efos` returns `RFC:AAAA010101AA1`
- legacy load of company_42 is byte-for-byte unchanged (`tests/test_loader.py` untouched and green)

## Definition of done
- [ ] `agent/data.py` as specified, fixture committed, `tests/test_load_judges.py` green, all existing tests green
- [ ] `python -m agent.investigate tests/fixtures/judges_mini --no-llm` runs and writes a case file
- [ ] Module docstring documents the PO-as-receipt proxy and the payment-link heuristic

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #80 generate.py --format judges: export estates to the judges' schema (SQLite + CSV) with judges'-shape ground truth; freeze estate_42  `codex`  OPEN

## Goal
Our held-out numbers must be measured on the same shape the judges use, and the judges' validator needs an `--estate my_estate.db`. Export our generator's richer estate to `estate_schema.sql`, write ground truth in `ground_truth_schema.json` shape, and freeze one export as `data_estate/out/estate_42`.

## Spec
`python -m data_estate.generate --seed 42 --format judges --out data_estate/out/estate_42` writes:
```
estate_42/estate.db          SQLite, the eight tables of estate_schema.sql, exact column names and order
estate_42/csv/<table>.csv    same content as CSV (vendors.csv, invoices.csv, ledger.csv, bank_txns.csv, purchase_orders.csv, contracts.csv, employees.csv, efos_list.csv)
estate_42/hidden/ground_truth.json   judges' shape (below)
estate_42/hidden/README
```
`--format legacy` (default) keeps today's output byte-identical (company_42 stays frozen).

### Table mapping (from `Estate`)
- **vendors:** one per supplier: `rfc`, `legal_name = name`, `registered_date = onboarded`, `address = f"{street}, {city}"`, `bank_clabe = clabe`, `category`, `contact_email = <slug>@<slug>.mx` (deterministic from name).
- **invoices:** `uuid`, `issuer_rfc = rfc_emisor`, `receiver_rfc = rfc_receptor`, `issue_date = fecha`, `subtotal`, `iva`, `total`, `concepto_text = descripcion`, `uso_cfdi`, `forma_pago`, `metodo_pago`, `status = "vigente"`.
- **ledger:** `entry_id` = integer (strip `GL` and leading zeros), `date = fecha`, `account_code`, `account_name`, `debit`, `credit`, `description = descripcion`, `invoice_uuid`, `cost_center` = `"CC-100 Produccion"` for materia_prima/refacciones/consumibles, `"CC-200 Administracion"` otherwise, `approver` = name of the invoice's `approved_by` employee on invoice rows, `""` on payment/payroll rows.
- **bank_txns:** company-side rows from `bank_transactions`: `txn_id`, `date = fecha`, `from_clabe/to_clabe` from `direction` (out: company → counterparty), `amount`, `reference = f"Pago factura {uuid}"` / `f"Cobro factura {uuid}"` / `"NOMINA QUINCENAL"` so the invoice link is recoverable, `channel = "efectivo"` when the invoice's `forma_pago == "01"` else `"SPEI"`. Third-party legs from `counterparty_bank` rows with `direction == "out"` only (the `in` rows mirror our own payments and would duplicate): `txn_id = record_id`, `from_clabe = entity_clabe`, `to_clabe = counterparty_clabe`, `reference`, `channel = "SPEI"`.
- **purchase_orders:** one per purchase invoice that has a goods receipt **or** whose supplier is honest (not in `truth["schemes"]`) and category is a service: `po_id = po_number`, `vendor_rfc`, `date = invoice fecha - rng(1..10) days`, `amount = invoice total`, `requester` = a random non-buyer employee name (seeded), `approver` = name of `approved_by`, `description = descripcion`. Planted phantom, kickback and round-trip invoices get **no PO**: that is their tell in the judges' world.
- **contracts:** one per `renta_util` supplier and one for the shared-address freight decoy: `contract_id = "CTR-" + supplier_id`, `vendor_rfc`, `start_date` = onboarded, `value` = 12 × mean invoice total, `scope_text` (`"Contrato marco, cuota mensual fija"` / `"Contrato de fletes, carta porte por viaje"`).
- **employees:** `emp_id = "EMP:" + employee_id[1:]` (`E00002` → `EMP:00002`), `name`, `role`, `bank_clabe = personal_clabe`, `hire_date` = seeded date in 2015–2024.
- **efos_list:** rows with `situacion in (Presunto, Definitivo)` only, `status` lowercased, `legal_name = nombre`, `publication_date`.

### Ground truth (judges' shape)
`{"seed", "company_rfc", "schemes": [{"scheme_id": "S<n>_<type>_<k>", "type": <judges' enum via SPEC_GAP mapping>, "entities": ["RFC:...", "EMP:..."], "supporting_invoices": [...], "supporting_txns": [...], "peso_amount", "difficulty": easy|medium|hard}], "decoys": [{"entity": "RFC:...", "signal": <detector name>, "why_innocent", "invoices": [...]}]}`. Mapping: `efos_fake_supplier→phantom_vendor` (easy), `kickback_shell→kickback` (medium), `round_trip_sales→round_tripping` (hard). `duplicate_invoice_payment` is **not** a judges' scheme: write it under an extra key `"control_observations": [...]` so `score.py` (#86) can still credit or ignore it. Also keep our internal truth at `hidden/ground_truth_internal.json` for the legacy scorer.

Kickback in this schema is provable only by the third-party leg (shell CLABE → buyer CLABE) and the approver on PO/ledger; the home-address tell is gone by construction. Nothing in the generator changes for that; the export simply does not carry addresses for employees.

### Freeze
`data_estate/out/estate_42/` committed; `tests/test_frozen_dataset.py` gains a second digest for it. `.gitignore` already keeps other exports out (`data_estate/out/*` minus the frozen ones: add `!data_estate/out/estate_42/`).

## Test: `tests/test_export_judges.py`
- Export seed 42 to `tmp_path`; open `estate.db` with `sqlite3`: the eight tables exist with exactly the columns of `estate_schema.sql` in order; every CSV has the same row count as its table.
- Referential integrity: every `invoices.issuer_rfc` that is not the company is in `vendors`; every `purchase_orders.vendor_rfc` and `contracts.vendor_rfc` in `vendors`; every `ledger.invoice_uuid` non-empty value in `invoices`; every `bank_txns` row has 18-digit CLABEs on both sides.
- Counts on seed 42: 42 vendors, 597 invoices, 16 employees, 34 efos rows (17 Presunto + 17 Definitivo), bank_txns = 612 + 11 third-party legs = 623, purchase_orders = 357 receipts + honest service invoices (compute in-test from the legacy estate), contracts ≥ 3.
- Ground truth: three schemes with judges' types, ids prefixed, `peso_amount` equal to the internal amounts, five decoys, `control_observations` has one entry.
- `--format legacy` output for seed 42 is byte-identical to `company_42` (diff in-test).

## Definition of done
- [ ] Export works for any seed and `--n`; `estate_42` frozen with digest; all tests green
- [ ] `data_estate/README.md` documents `--format judges` and the table mapping in one table

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #81 generate.py: plant threshold_splitting and revenue_inflation; add same-bank-institution and fixed-fee-contract decoys  `codex`  OPEN

## Goal
The judges' enum has five scheme types; we plant three. Judge estates can carry "up to all five with ten decoys". Add the two missing schemes and the two decoys that most directly target them, with ground truth, so detectors (#82, #83) have something to find and the eval can measure it.

## Spec
Approval limits are constants in code (`data_estate/generate.py` and mirrored in `agent/rules.py` by #82):
```python
APPROVAL_LIMIT_SUBTOTAL = {"Gerente de Compras": 250_000.0, "Director General": float("inf")}
```
Both schemes are selectable by name in `--schemes` (`threshold`, `revenue`) and included in the default list. Internal scheme types: `threshold_splitting`, `revenue_inflation` (same string as the judges' enum).

### `scheme_threshold_splitting`
- New vendor, category `refacciones`, onboarded in FY, approved by the buyer.
- 3 clusters at seeded dates ≥ 30 days apart. Each cluster: 3–4 purchase invoices dated within 2 business days, `subtotal` uniformly in `[0.80, 0.98] × 250_000`, descriptions of the same part, each with its own PO approved by the buyer (all under the limit), each paid normally (15–45 days). Goods receipts exist (the goods are real; the fraud is circumventing approval). Cluster sum is 2.4×–3.9× the limit.
- Ground truth: `type: threshold_splitting`, `entities: [RFC:vendor, EMP:buyer]`, `supporting_invoices` = all cluster invoices, `supporting_txns` = their payments, `peso_amount` = sum of cluster invoice totals, `difficulty: medium`.
- Legacy rule string for `agent/rules.py` (#82 adds it): `"Fraccionamiento de operaciones para evadir niveles de autorización; LGRA / política interna de compras; CFF Art. 83 (comprobantes) — approval-limit circumvention"`.

### `scheme_revenue_inflation`
- One fresh customer RFC (not a vendor, not in customers yet), name `Comercial <Last> SA de CV`.
- 3–5 sales invoices dated in the last 45 days of the FY, subtotals 150k–400k, revenue booked in the ledger (4000/2180/1200 as today), **no bank inflow ever**.
- 1–2 of them get `status = cancelado` in the export (#80 adds `status` support: an `Invoice.status` field defaulting to `vigente`) while the ledger keeps the revenue (no reversing entry).
- Ground truth: `type: revenue_inflation`, `entities: [RFC:customer]`, `supporting_invoices`, `supporting_txns: []`, `peso_amount` = sum of those sales totals, `difficulty: medium`.
- Rule string: `"Ingresos simulados / reconocimiento indebido de ingresos; CFF Art. 69-B / 113 Bis; NIF D-1 (ingresos)"`.

### Decoys (always present, like the existing five)
- **D6 same bank institution:** an honest goods supplier whose CLABE shares the first 3 digits (bank code) with the buyer's personal CLABE but nothing else; full PO and receipt trail. `signal: detect_kickback_outflow` (it must *not* fire; the decoy exists so the same-bank check in `agent/clear.py` has something to explain). `why_innocent`: "same bank code 0XX, different account; no transfer between the two accounts".
- **D7 fixed fee under contract:** an honest `servicios` supplier with 12 identical monthly invoices at `0.9 × 250_000` subtotal, a contract in `contracts` with `scope_text = "Contrato marco, cuota mensual fija"`, POs for each. Looks like threshold splitting (same amount just under the limit) but the invoices are one per month, not clustered, and the contract explains the amount. `signal: detect_threshold_splitting`.

Both decoys export with their contract/PO trail (#80). The `decoys()` method must keep the five existing decoys byte-identical on seed 42 when the new schemes are **not** selected, so `company_42` stays frozen; the new decoys are added *after* the existing ones and only consume RNG after them.

## Test: `tests/test_generate_new_schemes.py`
- `Generator(7).build(["threshold", "revenue"])`: truth has exactly those two schemes with the fields above; cluster invoices are within 2 business days per cluster and each `subtotal < 250_000`; every revenue-inflation invoice has no bank txn referencing it; at least one has `status == "cancelado"`.
- `Generator(42).build(["efos","kickback","roundtrip","duplicate"])` written with `--format legacy` is still byte-identical to `company_42`.
- Seeds 1–3 with all six schemes pass `data_estate.validate.check` (extend `validate.py`'s naive rules: threshold clusters findable by "≥3 invoices from one vendor within 2 days each ≥ 0.8 × limit"; revenue inflation by "sales invoice with no inbound txn"; decoys D6/D7 must not trip them).

## Definition of done
- [ ] Both schemes and both decoys generated, validated, exported; tests green; `company_42` unchanged

**Depends on #80** (the `status` column and the export of contracts/POs).

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #82 detect_threshold_splitting(ds): invoice clusters just under an approval limit  `hermes-ok`  OPEN

## Goal
The judges' `threshold_splitting` type: a vendor's purchases split into several invoices (and POs) each just below an approver's limit so nobody above that approver sees the total.

## Spec
`agent/detectors/threshold_splitting.py` → `detect_threshold_splitting(ds, *, window_days=2, min_cluster=3, min_ratio=0.80) -> list[dict]`
1. Limits live in `agent/rules.py` as `APPROVAL_LIMIT_SUBTOTAL = {"Gerente de Compras": 250_000.0, "Director General": float("inf")}` (add it there; a judge will ask to see the file). The limit for an invoice is the limit of the role of its `approved_by` employee (`ds.employees.role`); unknown role → the smallest finite limit.
2. Take `recibida` invoices; per supplier, sort by `fecha`; group into clusters where consecutive invoices are ≤ `window_days` apart.
3. Keep clusters with ≥ `min_cluster` invoices where **every** invoice has `subtotal >= min_ratio × limit` and `subtotal < limit`, and the cluster's summed subtotal ≥ limit.
4. One dict per cluster, sorted by `(entity_id, first_date)`: `entity_id` (supplier), `approver_id`, `approver_role`, `limit`, `n_invoices`, `first_date`, `last_date`, `cluster_subtotal`, `cluster_total_mxn`, `invoice_uuids`, `evidence` = invoice UUIDs + the `txn_id`s that paid them + their PO ids when present (`ds.goods_receipts.receipt_id` for those invoices on judge estates).
5. Also add the internal scheme to `agent/rules.py`: `R6` with `scheme_types={"threshold_splitting"}`, legal string from #81, `evidence_kinds={"invoice","txn","receipt"}`, amount = sum of `total` of the clustered invoices of the accused supplier (reuse the detector to find them), and add the signature `({"detect_threshold_splitting"}, "threshold_splitting")` to `agent/leads.py` `SIGNATURES` and `STRONG`.

## Data facts (from #81, seed 7 with `threshold`)
3 clusters of 3–4 invoices, subtotals in `[200k, 245k)`, ≥30 days apart. Decoy D7 has 12 monthly invoices at 225k: never ≥3 within 2 days, so it must not appear. Baseline suppliers have 4–24 invoices at random dates; two within 2 days both in `[200k, 250k)` is possible but a third is not expected; the test asserts no baseline supplier appears on seeds 7, 8, 9.

## Test: `tests/test_detect_threshold_splitting.py`
Generate seed 7 with `["threshold"]` into `tmp_path` (legacy format) and load it:
- `{r["entity_id"]}` == `{vendor}` from ground truth; number of rows == number of clusters (3); the union of `invoice_uuids` == `supporting_invoices`
- `approver_id` == the buyer; every `limit == 250_000.0`
- D7's supplier id not in the result; `detect_threshold_splitting(ds, min_cluster=99) == []`
- guard accepts a finding `{scheme_type: "threshold_splitting", accused: [vendor, buyer], rule: "R6", amount_mxn: <sum>, evidence: <all cluster uuids + txns>}`

## Definition of done
- [ ] Module, rule R6, signature, test green; docstring names the constant and the file it lives in

**Depends on #81.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #83 detect_revenue_inflation(ds): sales booked as revenue that were never collected or were cancelled without reversal  `hermes-ok`  OPEN

## Goal
The judges' `revenue_inflation` type: fictitious sales. In the books this looks like revenue in the ledger with no cash ever arriving, and invoices cancelled after the fact while the revenue entry stays.

## Spec
`agent/detectors/revenue_inflation.py` → `detect_revenue_inflation(ds, *, grace_days=60, period_end_days=45) -> list[dict]`
1. `emitida` invoices (`issuer == company`). For each: `collected` = there is a `bank_transactions` row with `direction == "in"` and `invoice_uuid == uuid` (or, when `invoice_uuid` is empty on judge estates, an inbound txn from the customer's CLABE with `amount == total` after `fecha`); `cancelled` = `status == "cancelado"` when the column exists; `revenue_booked` = a ledger row with `invoice_uuid == uuid` and `account_code == "4000"` and `credit > 0`; `reversed` = a ledger row for the uuid with `account_code == "4000"` and `debit > 0`.
2. Flag an invoice when `revenue_booked` and ((not `collected` and `fecha <= fiscal_year_end - ... `: use "not collected and at least `grace_days` after `fecha` within the data's last date, or issued within `period_end_days` of the last invoice date") or (`cancelled` and not `reversed`)).
3. Aggregate per customer (`counterparty_id`), one dict per customer sorted by `entity_id`: `entity_id`, `n_invoices`, `n_uncollected`, `n_cancelled_not_reversed`, `first_date`, `last_date`, `total_mxn` (sum of flagged totals), `customer_history` = number of *collected* invoices for that customer (0 for a fresh customer), `invoice_uuids`, `evidence` = flagged invoice UUIDs (no txns exist; that is the point).
4. `agent/rules.py`: `R7` with `scheme_types={"revenue_inflation"}`, legal string from #81, `evidence_kinds={"invoice"}`, amount = sum of the flagged invoices' `total` for the accused customer. `agent/leads.py`: signature `({"detect_revenue_inflation"}, "revenue_inflation")`, add to `STRONG` **only** when `customer_history == 0 or n_cancelled_not_reversed > 0` (implement as a second detector field the signature can read, or emit the lead only in those cases and a weaker `detect_uncollected_sales` otherwise; pick the simpler and say which).

## Data facts (from #81, seed 7 with `revenue`)
One fresh customer, 3–5 sales in the last 45 days, none collected, 1–2 cancelled without reversal. Honest customers pay 20–60 days after invoice; sales in the last ~50 days of the FY may legitimately be uncollected at year end (`pay_delay` capped at FY_END means they *are* paid on 12-31 in our generator; on judge estates they may not be). The `customer_history` field is what separates "new customer, nothing ever paid, cancellations" from "regular customer, last invoice still open".

## Test: `tests/test_detect_revenue_inflation.py`
Generate seed 7 with `["revenue"]` (legacy format, plus `status` column per #80/#81):
- exactly one row, `entity_id` == the planted customer, `invoice_uuids` ⊇ `supporting_invoices`, `customer_history == 0`, `n_cancelled_not_reversed >= 1`
- no honest customer appears; `detect_revenue_inflation(ds, grace_days=10_000) ` still returns the cancelled-not-reversed case
- guard accepts `{scheme_type: "revenue_inflation", accused: [customer], rule: "R7", amount_mxn: <sum>, evidence: <uuids>}`

## Definition of done
- [ ] Module, rule R7, signature, test green

**Depends on #81.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #84 Judge-shape signatures: kickback without address, round-trip 2-hop fallback, scheme_hints as a list  `hermes-ok`  OPEN

## Goal
On judge estates employees have no address, `bank_txns` may or may not carry third-party legs, and an entity may sit in two schemes ("entangled"). Three small changes so the existing detectors and the docket keep working on that shape.

## Spec
1. **Kickback signature.** `agent/leads.py` `SIGNATURES`: `kickback_shell` fires on `{"detect_kickback_outflow"}` alone; `detect_employee_address_match` becomes corroboration (keep it in `STRONG`). Add to `detect_kickback_outflow` a field `approver_link: bool` = the supplier's `approved_by` equals the employee receiving the money, and `same_bank_only: bool` = False when a real transfer exists (the same-institution decoy never reaches this detector because it needs a transfer; the check that *explains* the decoy lives in `agent/clear.py`, #94).
2. **Round-trip 2-hop fallback.** `agent/detectors/round_trip.py`: after the existing 3-hop search, a second pass for outgoing payment `O` with no forward leg: inbound `I` with `direction == "in"`, `I.fecha` within `return_days` of `O.fecha`, `I.amount >= return_min_ratio × O.amount`, and (`I.counterparty_clabe == O.counterparty_clabe` **or** the customer of `I` has the same RFC as the supplier of `O`). Emit the same dict shape with `forward_record = ""`, `via = "direct"` (3-hop rows get `via = "counterparty"`), evidence without the empty id. Deterministic order unchanged.
3. **Multiple hints.** `agent/leads.py`: `scheme_hints(detectors) -> list[str]` returning every matching signature in `SIGNATURES` order; dossiers carry `scheme_hints: [...]` and keep `scheme_hint = scheme_hints[0] if any else ""` for compatibility. `agent/investigate.py` `_build_units` groups by each hint, so an entity in two schemes yields two units (this is the mechanism #92 completes on the output side; here only the docket changes).

## Test
- `tests/test_leads.py`: a detector set `{"detect_kickback_outflow"}` → `kickback_shell`; `{"detect_round_trip", "detect_efos"}` → `["efos_fake_supplier", "round_trip_sales"]` from `scheme_hints`; `scheme_hint` still returns the first.
- `tests/test_detect_round_trip.py`: on company_42 results unchanged (3 rows, all `via == "counterparty"`); on a copy of company_42 with `counterparty_bank.csv` emptied, the 2-hop pass finds the 3 legs with `via == "direct"` (the pipe's CLABE is not the customer's, so this relies on the RFC rule: assert the generator's pipe/customer are different RFCs and therefore expect **0** rows there, and instead build a 3-row synthetic case in the test where the inbound CLABE equals the outbound CLABE).
- `tests/test_detect_kickback_outflow.py`: `approver_link is True` on company_42.
- `tests/test_investigate.py`: a dossier with two hints produces two units; company_42 scores unchanged (`1.0 / 0 / 1.0`).

## Definition of done
- [ ] Three changes, tests green, company_42 and the 10-seed batch unchanged (`scripts/eval_batch.py --seeds 101-105 --no-llm`)

No dependencies: everything here is testable on company_42 plus synthetic frames. When #79 lands, its `tests/fixtures/judges_mini` becomes an extra fixture for these tests (follow-up, not part of this issue).

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #85 agent/tools.py: judge-estate aware tools (RFC ids, purchase orders, contracts, trace_flow over third-party legs)  `cc`  OPEN

## Goal
The model's tools must answer the questions the judges will ask on their estates: is there a PO, a contract, what did the approver sign, where did the money go after it left us. Today the tools assume `S*/C*/E*` ids and receipts.

## Spec (add, do not break)
- Every lookup accepts `RFC:<rfc>` / `EMP:<id>` ids **and** legacy ids; `get_supplier` also accepts a bare RFC.
- `get_purchase_orders(*, vendor_id: str = "", invoice_uuid: str = "", limit: int = 50) -> list[dict]` from `ds.purchase_orders` (empty list with `note: "no purchase_orders table in this estate"` on legacy datasets).
- `get_contracts(vendor_id: str) -> list[dict]` from `ds.contracts`, same fallback.
- `get_supplier(...)` adds `deliverable_trail: {n_invoices, n_with_po, n_with_receipt, n_contracts}` and `approvers: [{employee_id, role, n_invoices}]`; `employee_links` gains `kind = "same_bank"` (first 3 CLABE digits equal, full CLABE different) so the model can *see* and dismiss it.
- `get_employee(...)` adds `bank_code` (first 3 digits) and `n_transfers_received_from_vendors` (count of `counterparty_bank` rows landing on the employee's CLABE).
- `trace_flow(clabe, ...)` walks `counterparty_bank` (third-party legs) **and** `bank_transactions`; each hop carries `record_id`, `source_table` from `ds.record_table`, and `returns_to_company`.
- `get_invoices(...)` rows add `status` (when present), `po_id`, `contract_id` (when a contract covers the vendor), `collected` (for sales) and `days_to_collect`.
- `TOOL_SCHEMAS` updated; descriptions mention judge ids (`RFC:...`).

## Test: `tests/test_tools.py` additions on `tests/fixtures/judges_mini` (#79) and on company_42
- `get_supplier("RFC:BBBB020202BB2")["deliverable_trail"]["n_with_po"] == 1`; `get_contracts("RFC:BBBB020202BB2")` has 1 row; `get_purchase_orders(invoice_uuid=<B's invoice>)` has 1 row
- `get_employee("EMP:0001")["n_transfers_received_from_vendors"] == 1`; `trace_flow(<vendor A clabe>)` returns the vendor→employee hop with `source_table == "bank_txns"`
- legacy results for existing assertions unchanged; `json.dumps` on every result

## Definition of done
- [ ] Tools and schemas extended, tests green; the LLM prompt in `agent/investigate.py` lists the two new tools

**Depends on #79.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #86 score.py + eval_batch.py: judges' ground-truth shape, false-accusation rate, 2% peso reconciliation, results_table.csv  `codex`  OPEN

## Goal
Our scorer reads our internal truth and prints our metrics. The judges' pack defines the answer-key shape, the two numbers that matter (recall and false-accusation rate), a 2% peso rule, and a results table with fixed columns. Make our harness speak that language so the slide is a direct export.

## Spec
`data_estate/score.py`:
- Accept both truth shapes: internal (`meta` key) and judges' (`company_rfc` key). Normalise to: schemes `[{type (judges' enum), entities (prefixed), supporting_invoices, supporting_txns, peso_amount}]`, decoys `[{entity, signal}]`, `control_observations`.
- Score a **submission.json** (#88) when given one (detect by `run_metadata` key); keep scoring legacy case files for the old tests. Entity matching on prefixed ids; legacy ids are mapped through the masters when the truth is internal.
- Output: `schemes_planted`, `schemes_found`, `recall_pct`, `decoys_planted`, `decoys_accused`, `false_accusations` (accused entities in no scheme), `false_accusation_rate_pct` = `100 × (false + decoys_accused) / max(1, n_accused_entities)`, `peso_claimed` (sum of finding amounts), `peso_actual` (sum of found schemes' `peso_amount`), `peso_reconciles` (every finding within 2% of its per-table exhibit sum, computed like `validate_format.py`), `llm_calls`, `mxn_cost`, `wall_clock_s` (from `run_metadata`), plus the old fields for compatibility.
- A finding counts as found when `scheme_type` matches and ≥1 planted entity is accused and `peso_amount` is within 25% (unchanged tolerance for *recall*; the 2% rule is a separate boolean).

`scripts/eval_batch.py`:
- `--format judges` generates with `--format judges` (#80), runs the agent on `estate.db`, scores the submission.
- Writes `results_table.csv` in the exact columns of `student-materials/forensic-auditor/results_table_template.csv` (copy the header verbatim into the script as a constant) plus a `TOTAL` row; `--out` markdown keeps the current table.
- Refuses seeds 42 and any seed in the tuning list `TUNING_SEEDS = {42, *range(101, 111), *range(201, 206), *range(301, 307)}` when `--report` is passed; `--report` is what produces the slide table on `901-910`.

## Test: `tests/test_score_judges.py`, `tests/test_eval_batch.py` additions
- Score the frozen `estate_42` (#80) against a hand-built submission that accuses the phantom vendor with correct exhibits: `recall_pct == 100/3` … (one of three), `false_accusation_rate_pct == 0`, `peso_reconciles is True`; add a decoy to `entities` → rate 50, `decoys_accused == 1`.
- A finding whose exhibits sum to 1.5× its `peso_amount` → `peso_reconciles is False`.
- `eval_batch --seeds 901-902 --report --no-llm --format judges` writes a CSV whose header equals the template header and has 3 rows (2 seeds + TOTAL); `--seeds 42 --report` exits non-zero.

## Definition of done
- [ ] Scorer and batch script as above, tests green, `docs/eval/README.md` explains tuning vs reporting seeds

**Depends on #80** and, for scoring submissions, **#88** (score legacy case files until then).

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #87 guard: 2% per-table reconciliation to cited exhibits, exhibit policy per rule, confidence tier  `cc`  OPEN

## Goal
The judges reconcile `peso_amount` to the **cited** exhibits, per table, within 2%. Our guard checks 25% against a recomputed aggregate, so a finding can pass us and fail them. Move the guard to their rule, and decide per rule which table "carries" the amount.

## Spec
`agent/rules.py`: each `Rule` gains `counted_table: str` (`"invoices"` for R1, R2, R6, R7; `"invoices"` for R3 counting the **purchase** invoices only; `"bank_txns"` for R4 counting the duplicate payments) and `exhibit_policy: Callable[[finding, ds], list[str]]` that returns the record ids the finding must cite for the amount to reconcile (R1/R2/R6: every counted invoice of the accused suppliers; R3: purchase invoices, and the sales legs are cited through their revenue ledger rows and inbound txns; R4: the second-and-later payments; R7: the flagged sales invoices).

`agent/guard.py`:
- Replace step 5: compute `per_table` sums over the finding's evidence exactly like `validate_format.py` (`invoices.total`, `bank_txns.amount` for both `bank_transactions` and `counterparty_bank`, `purchase_orders.amount`, `contracts.value`, using `ds.record_table` on judge estates and the record kind on legacy data). `best` = the table sum closest to `amount_mxn`; reject unless `abs(amount - best) <= 0.02 × max(best, 1)` **and** that table is the rule's `counted_table`. Reasons name both numbers and the table.
- If the evidence is missing counted records, do not reject blindly: when `finding.get("auto_complete_exhibits", True)`, add the ids from `exhibit_policy` to the evidence first (the loop always allows this; the LLM's proposal is preserved in the step log). Log what was added.
- Add `confidence`: `"proven"` when every evidence kind in `rule.evidence_kinds` is present and reconciliation holds; `"probable"` when reconciliation holds but a kind is missing (e.g. kickback with the approver link but no third-party leg). The clean finding carries `confidence`; `agent/contract.py` accepts the optional field.
- Keep `AMOUNT_TOLERANCE = 0.02` as the named constant (a judge will ask to see it).

## Test: `tests/test_guard.py` additions
- The four example findings on company_42 still pass (their amounts equal the cited invoice sums).
- A finding citing only half of the phantom vendor's invoices with the full amount: accepted **with** auto-completed exhibits, and the log entry lists the added ids; with `auto_complete_exhibits: False` it is rejected with "does not reconcile".
- Amount 5% off → rejected; amount matching `bank_txns` sum but rule R1 → rejected because the counted table is `invoices`.
- A kickback finding with no `cp` evidence → accepted as `probable`; with it → `proven`.
- Run the vendored validator (#88) on a submission built from the cleaned findings on `estate_42`: exit 0 with `--estate`.

## Definition of done
- [ ] Guard, rules, contract updated; all tests green; the no-LLM run on company_42 still scores 1.0 / 0 / 1.0

**Depends on #79.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #88 agent/submit.py: write submission.json per submission_schema.json; vendor validate_format.py; run it in CI  `cc`  OPEN

## Goal
The JSON the judges machine-check. Every finding becomes a judges' finding with prefixed entities, ≥3 exhibits naming their source table, a money trail, a confidence tier; every declined lead carries signal, reason, tools and closer; `run_metadata` carries the three numbers.

## Spec
`agent/submit.py` → `build_submission(case: dict, ds: Dataset, log: list[dict], meta: dict) -> dict` and CLI `python -m agent.submit <estate> <case_file.json> --log <run.jsonl> --out submission.json`.
- `seed`: from `meta` (the estate dir name `estate_<n>` / `company_<n>`, or `--seed`), else 0.
- `findings[]`: `scheme_type` via the mapping in `docs/SPEC_GAP.md` (internal → judges'); a finding whose internal type has no judges' type (`duplicate_invoice_payment`, `other`) is **moved** to `leads_not_pursued` with `closed_by: "validator"` and a reason that says it is a control observation outside the five types, keeping its evidence ids in the reason text. `entities` = accused ids (already prefixed on judge estates; legacy ids mapped `S→RFC:<rfc>`, `C→RFC:<rfc>`, `E→EMP:<digits>`). `rule_broken` = the rule's legal string. `narrative` ≤ 150 words (truncate at a sentence boundary). `peso_amount`. `confidence` from the guard (#87). `exhibits`: one per evidence id, `exhibit_id = "EX-<nn>"`, `source_table` from `ds.record_table` (legacy: invoice→`invoices`, TX/CP→`bank_txns`, GR→`purchase_orders`), `record_id` (**bank/ledger ids as they appear in the judges' estate**: on legacy data keep ours), `note` from a per-kind template with the amount and date ("Invoice from <vendor> to the company for MXN 98,600.00 on 2025-02-12, no purchase order"); then append master-table exhibits for each accused entity: `vendors`/`employees` row, and `efos_list` row when listed. `money_trail`: the bank rows among the exhibits ordered by date, `from`/`to` as entity names (company name, vendor, employee), each step citing its exhibit id; must connect (each step's `to` equals the next step's `from` where the data supports it).
- `leads_not_pursued[]`: from `not_pursued` + the step log: `entity`, `signal` = comma-joined detector names from the dossier, `reason` (from #94/#69), `tool_calls_made` = tool names called for that entity in the log, `closed_by` = `"investigator"` (LLM or fallback decision), `"challenger"` (#91), or `"validator"` (guard rejection / type outside enum).
- `run_metadata`: `llm_calls`, `mxn_cost`, `wall_clock_seconds`, `cost_by_role` (#89), `deterministic: true`.
- `agent/investigate.py` gains `--submission <path>` (default `submission.json` next to `--out`) and calls this after the case file is written.

`scripts/judges/validate_format.py`: the judges' file, verbatim, with a one-line header comment naming its origin. `tests/test_submission_format.py`: build the submission for `tests/fixtures/judges_mini` (no-LLM) and for `data_estate/out/estate_42/estate.db` when present; call `validate_structure` → `[]` and `validate_against_estate(sub, db)` → `[]`.

## Definition of done
- [ ] `python -m agent.investigate data_estate/out/estate_42/estate.db --no-llm --submission s.json` then `python scripts/judges/validate_format.py --submission s.json --estate data_estate/out/estate_42/estate.db` prints PASS
- [ ] Tests green; CI runs the validator test

**Depends on #79 and #87.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #89 run_metadata: count LLM calls and tokens in agent/llm.py, price constants, cost in the step log  `hermes-ok`  OPEN

## Goal
"Have three numbers ready: LLM call count, MXN cost, wall-clock seconds. 'We don't know' scores low on Feasibility." We know wall-clock; the other two are not counted anywhere.

## Spec
- `agent/llm.py` `LLM`: counters `calls`, `cached_calls`, `prompt_tokens`, `completion_tokens` (from `Reply.usage`), `by_role: dict[str, dict]` keyed by an optional `role` kwarg on `chat(...)` (`"investigator"`, `"challenger"`); `FakeLLM` mirrors them. A `stats()` method returns the dict.
- `agent/config.py`: `MXN_PER_1K_PROMPT_TOKENS` and `MXN_PER_1K_COMPLETION_TOKENS` constants with a comment: reference price of a hosted API for a comparable open-weight model in MXN (state the source and date); the cluster's marginal cost is 0, and both figures go in the report header. `settings()` exposes them; `.env` may override with `LLM_MXN_PER_1K_PROMPT` / `..._COMPLETION`.
- `agent/investigate.py`: `run_end` payload gains `llm_calls`, `cached_calls`, `prompt_tokens`, `completion_tokens`, `mxn_cost` (computed from the constants, cached calls cost 0), `cost_by_role`; the case file gets a top-level `run_metadata` with the same fields plus `wall_clock_seconds` and `deterministic` (`true` in no-LLM mode; in LLM mode `true` when every call was cached, else `false` with a note "replay from cache is deterministic").
- `--no-llm` reports `llm_calls: 0`, `mxn_cost: 0.0`.

## Test: `tests/test_llm.py`, `tests/test_investigate.py` additions
- `FakeLLM` with 3 scripted replies carrying `usage` → `stats()["calls"] == 3`, tokens summed, `by_role["investigator"]["calls"] == 3` when called with `role="investigator"`.
- A run with `FakeLLM` writes `run_metadata.llm_calls == <n>` and `mxn_cost == tokens × constants / 1000` within 1e-6; `--no-llm` writes zeros.

## Definition of done
- [ ] Counters, constants, `run_metadata` in case file and log; tests green

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #90 agent/report.py: the judges' five-section case file with a rendered money-trail diagram (Markdown + self-contained HTML)  `hermes-ok`  OPEN

## Goal
`case_file_structure.md` fixes the sections and says: "Money trail: a rendered diagram, not prose. Prose-only caps Clarity at 3." Our report is good prose and a table. Produce the required structure in Markdown (Mermaid block) and in a self-contained HTML file with an inline SVG that opens anywhere with no network and no JavaScript.

## Spec
`python -m agent.report <estate> <case_file.json> --submission submission.json --log run.jsonl --out report.md --html report.html`

Sections, in this order, headings verbatim:
1. **Header**: company name/RFC, audit period (min–max invoice date), estate seed, LLM calls, MXN cost, wall-clock seconds, "Deterministic: yes/no (why)". All from `run_metadata` (#89).
2. **Executive summary**: 2–4 plain sentences + the table `Findings (count, with confidence levels) / Total exposure (pesos) / Leads investigated and closed (count)`.
3. **One section per finding**: heading `<entity name> (<id>) — <judges' scheme type>`; **Rule broken**; **Amount and confidence**; **What happened** (≤150 words, the submission narrative); **Money trail**: a diagram, then nothing else in that subsection; **Exhibits table** (`exhibit id | source table | record id | what it proves`); **Reconciliation**: the arithmetic (`EX-01 98,600.00 + EX-02 … = 2,070,600.00 = claimed`), naming the counted table; **Challenge** (when #91 ran): what was argued and why the finding survived.
4. **Leads not pursued** (in the body): one entry per declined lead: entity name and id, signal (detector), specific reason, tools called, closed by.
5. **Method and limits**: architecture in ≤5 sentences; out of scope for this run; what the system cannot detect (from a constant list in code, e.g. "collusion with no money movement in the books"); reproducibility: the exact command line that regenerates this file, and "runs with the network disabled from the cached run".

**Diagram.** Markdown: a `mermaid` block `flowchart LR` with one node per entity (company, vendor, employee, customer) and one edge per money-trail step labelled `EX-nn · MXN amount · date`. HTML: the same graph drawn as inline SVG by a small pure-Python layout (nodes on a horizontal line in trail order, deduplicated; edges as arrows with labels; no external assets, no `<script>`), plus the rest of the report as HTML. The HTML must render in a browser opened from a file path with Wi-Fi off; the test checks for `<svg`, no `http`/`https` URLs, and no `<script>`.

Keep today's tax-exposure lines in section 2 as "Tax exposure (bonus estimate)"; never in `peso_amount`.

## Test: `tests/test_report.py` rewrite
- On company_42 (no-LLM run + submission from #88): the five `## ` headings in order; each finding section has the seven sub-elements in order; the reconciliation line sums to the claimed amount within 0.01; the Markdown contains one `mermaid` block per finding with as many edges as money-trail steps.
- HTML: contains `<svg` once per finding, no `<script>`, no `http`; file size < 2 MB.
- Every declined lead prints signal, reason, tools, closer.
- Rendering with the network unavailable: monkeypatch `socket.socket` to raise; render still succeeds.

## Definition of done
- [ ] Both outputs, tests green, `docs/PLAN.md` demo section points at `report.html`

**Depends on #88** (submission fields) and **#89** (header numbers).

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #91 agent/challenge.py: adversarial review that tries to break every finding before it is printed  `hermes-ok`  OPEN

## Goal
"If your system runs an adversarial review, include what it argued and why the finding survived. A finding that no one tried to break is weaker than one that was attacked and held." Also the judges' question "what if the employee just happens to bank at the same institution?". Give every finding a challenger whose arguments are deterministic record checks, recorded in the log and the case file.

## Spec
`agent/challenge.py` → `challenge(finding: dict, ds: Dataset) -> dict` returning `{"arguments": [{"claim", "records", "outcome": "survived"|"killed"|"weakened"}], "verdict": "survived"|"killed", "confidence": "proven"|"probable"}`. Arguments per scheme type (all pure pandas over `ds`, no LLM):
- **phantom_vendor / efos:** "a PO or contract exists for ≥ 50% of the invoices" (killed if true); "the 69-B status is `presunto` and publication is after every invoice" (weakened → `probable`); "the vendor has invoices to *other* receivers" (n/a in our data; skip when no data).
- **kickback:** "the employee link is same-bank-code only, no transfer between the accounts" (killed if no `counterparty_bank` leg lands on the employee's CLABE **and** the CLABE prefix is the only match); "the transfer references payroll or a loan" (weakened); "the approver is not the linked employee" (weakened).
- **round_tripping:** "the inbound payer has trading history with us before the first outbound" (weakened); "the forward leg is more than `forward_days` after our payment" (killed if every leg fails).
- **threshold_splitting:** "a contract with a fixed fee explains the repeated amount" (killed if a contract exists for the vendor and the invoices are ≥ 20 days apart); "the invoices are different parts/descriptions" (weakened).
- **revenue_inflation:** "the cancelled invoice was reversed in the ledger" (killed for that invoice; finding survives if any remain); "the customer paid other invoices" (weakened).
- **duplicate payment (observation):** "the second payment was refunded" (killed if an inbound txn from the alternate CLABE with the same amount exists).

`agent/investigate.py`: after the guard accepts a finding, run `challenge`; `killed` → the finding becomes a declined lead with `closed_by: "challenger"` and the claim as reason; `weakened` → `confidence = "probable"`; log `kind: "challenge"` with the arguments. The submission (#88) and report (#90) carry the arguments.

## Test: `tests/test_challenge.py`
- company_42 no-LLM: all four findings survive; the EFOS finding has the "presunto publication after invoices" argument marked `weakened` for the presunto supplier only if you implement per-entity, else `survived`; the kickback finding's same-bank argument is `survived` because a real `CP*` leg exists.
- Synthetic: remove the `CP*` legs from a copy of company_42 → kickback finding is `killed` with the same-bank argument; add a contract for the threshold vendor on seed 7 (#81) and spread its invoices → `killed`.
- The step log contains one `challenge` entry per finding.

## Definition of done
- [ ] Module, loop integration, tests green; company_42 scores unchanged

**Depends on #88** and **#87**.

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #92 Entangled schemes: one entity in two findings, no double-counting, declined-leads bookkeeping  `hermes-ok`  OPEN

## Goal
"Schemes may be entangled — two schemes sharing an entity, so a money trail crosses scheme boundaries." After #84 the docket can carry two hints per entity; finish the output side.

## Spec
- `agent/investigate.py`: units keyed by `(scheme_hint, frozenset(entity_ids))`; the same entity may appear in two findings with different `scheme_type`. `not_pursued` excludes an entity only for the schemes it was accused under: an entity accused of `kickback` but whose `round_tripping` hint was dropped gets a declined-lead entry for the dropped hint with `signal` naming the detectors of that hint.
- Evidence must not be shared between the two findings when the rule's `counted_table` sums would double count: the exhibit policy (#87) assigns each counted invoice to exactly one finding (the first in `SIGNATURES` order); shared bank legs may be cited by both.
- `agent/submit.py` and `agent/report.py`: nothing structural; verify they handle two findings with a common entity.
- `scripts/eval_batch.py`: `--schemes entangled` generates `kickback + roundtrip` with the round-trip pipe registered at the buyer's home and approved by him (the generator change is small: add an `entangle=True` flag to `scheme_round_trip` that reuses the kickback buyer; #81 owner reviews).

## Test: `tests/test_investigate.py` addition
- Synthetic dossiers: entity `X` with hints `[kickback_shell, round_trip_sales]` → two units, two findings when both guards pass, no invoice cited as counted evidence in both; `X` appears in `not_pursued` for neither.
- Generated entangled seed (if the generator flag lands; otherwise skip with reason): recall 1.0 for both schemes, penalty 0.

## Definition of done
- [ ] Loop, policy, tests green

**Depends on #84** and **#87**.

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #93 --replay: rebuild case file, submission and report from a stored run with the network disabled  `hermes-ok`  OPEN

## Goal
"Replay without a network. Your system must be able to reproduce a completed run with connectivity disabled." Judges may ask for it live. Today a re-run hits the cache, which works only if nothing in the prompt changed; a true replay must not depend on the model at all.

## Spec
- `agent/investigate.py --replay runs/<ts>.jsonl`: rebuilds `findings` and `not_pursued` from the log's `decision`/`guard`/`challenge` entries (the guard re-validates every finding against the estate; nothing is trusted blindly), writes the case file, submission (#88) and report (#90), and never constructs an `LLM`. `run_metadata` copies the original numbers and adds `"replayed_from": "<path>"`.
- Every run writes its log path into the case file (`run_metadata.log`), so `--replay` can be invoked with the case file alone.
- `scripts/demo_run.py` (#27) gets a `--replay` passthrough (comment on #27; do not implement there).

## Test: `tests/test_replay.py`
- Run company_42 with `FakeLLM` (log to `tmp_path`), then replay with `LLM_BASE_URL=http://127.0.0.1:9` in the environment and `socket.socket` monkeypatched to raise: replay succeeds; the case file equals the original (`json` equality ignoring `run_metadata.replayed_from`); the submission validates (#88).
- Tamper with the log (change an evidence id to `TX99999`) → replay drops that finding with a guard reason and exits 0 with a warning line.

## Definition of done
- [ ] Replay path, test green, `README.md` shows the two commands (run, then replay with Wi-Fi off)

**Depends on #88** and **#90**.

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #94 agent/clear.py on judge estates: PO, contract, same-bank-institution and cancelled-invoice checks; tool_calls_made and closed_by  `hermes-ok`  OPEN

## Goal
#69 replaces canned drop reasons with record checks on our schema. On judge estates the documents that clear a lead are POs, contracts, and the bank code, not goods receipts and home addresses. Extend the checks and make every declined lead carry what the judges' schema asks for.

## Spec (extends `agent/clear.py` from #69)
- New checks, each returning `(verified: bool, reason: str, records: list[str])`:
  - `po_trail(entity)`: share of the vendor's invoices with a PO (`ds.goods_receipts` proxy or `ds.purchase_orders`); clears `detect_no_receipt`/`detect_fast_pay_no_deliverable` when ≥ 80%: "8/8 invoices have purchase orders PO-0012…, approved by <name>".
  - `contract_on_file(entity)`: clears `detect_new_vendor_round_amounts` and `detect_threshold_splitting` leads when a contract covers the vendor and the invoice amounts match `value / 12` within 5%: "contract CTR-… (fixed monthly fee MXN 225,000.00) explains 12 equal invoices".
  - `same_bank_only(entity)`: for `detect_kickback_outflow`-adjacent leads and any vendor whose CLABE shares a bank code with an employee: "bank code 012 shared with EMP:0002, accounts differ, no transfer between them in bank_txns".
  - `cancelled_reversed(entity)`: clears `detect_revenue_inflation` leads when every cancelled invoice has a reversing 4000 debit.
  - `presunto_only(entity)` stays a *lead* (never clears) but the reason says the status and date.
- Every declined lead gets `signal` (detector names), `tool_calls_made` (the check names run, plus LLM tool calls from the log when in LLM mode), and `closed_by` (`investigator` | `challenger` | `validator`); `agent/investigate.py` writes them into `not_pursued` entries (extra keys are allowed by `agent/contract.py`; add them to its schema as optional).
- Reasons must name records. A reason that would contain no record id is rewritten to "could not verify from the records: <what was checked>" and the lead is marked `unverified` (#70 escalates those to the model).

## Test: `tests/test_clear.py` additions
- On `tests/fixtures/judges_mini` (#79): vendor B is cleared by `po_trail` and `contract_on_file` with the PO and contract ids in the reason; vendor A is **not** cleared.
- On seed 7 with the D6/D7 decoys (#81): D6 cleared by `same_bank_only` naming the bank code and the employee; D7 by `contract_on_file` naming the contract.
- Every `not_pursued` entry from a company_42 run has non-empty `signal`, `tool_calls_made`, `closed_by`.

## Definition of done
- [ ] Checks, bookkeeping, tests green; no declined lead on company_42 or estate_42 has a reason without a record id

**Depends on #69, #79, #81.**

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #95 Leak hygiene: ground_truth string check under agent/, hypothesis log line names its detectors  `hermes-ok`  OPEN

## Goal
Two cheap protections against the "Results caps at 2" rule: judges grep `ground_truth` under the source tree, and they read the trace for a scheme type named "before investigating".

## Spec
- `tests/test_no_hidden_access.py`: add a test that no file under `agent/` and `scripts/` (excluding `scripts/judges/` and `scripts/eval_batch.py`, which are harness) contains the string `ground_truth` (case-insensitive), and that `agent/` never imports `data_estate` (the harness package).
- `agent/investigate.py`: the `hypothesis` log entry's `text` must start with `"Detectors <a>, <b> match the <scheme> signature; investigating"` in fallback mode, and in LLM mode the entry gains `derived_from: [detector names]`. Never emit a hypothesis for a unit with no detector hits.
- `docs/STEP_LOG.md` (#67) gets the field; `demo/sample_trace.jsonl` (#73) regenerated if it exists.

## Test
- The grep test; a fallback run on company_42 has every `hypothesis.text` starting with `Detectors ` and listing ≥1 detector that actually fired for that entity.

## Definition of done
- [ ] Tests green; `grep -rn ground_truth agent/ scripts/` returns only harness files

### Conventions
- Read `docs/SPEC_GAP.md` first: it maps the judges' schema, scheme enum and output format onto our build. The spec files live in `student-materials/forensic-auditor/` (a sibling of the repo on Sondre's machine; ask for the pack if you do not have it).
- This issue is the approval AGENTS.md rule 5 requires for the schema or contract change it describes. Do exactly what is written here, nothing more.
- Tests may read `hidden/`; nothing under `agent/` may, and the string `ground_truth` must never appear under `agent/` (judges grep for it).
- Run `python -m pytest -q` and `ruff check .` before the PR. No new dependencies unless this issue names one.

## #96 api/server.py: judge-estate datasets and the submission / report.html / validate endpoints (follow-up to #68)  `hermes-ok`  OPEN

## Goal
#68 builds the API against our legacy CSV datasets. Judges hand us an estate in their schema (SQLite `.db` or CSV dir per `estate_schema.sql`, loaded by #79), and the frontend must be able to start a run on it and fetch the judges' artifacts. Follow-up to #68; do not change #68's endpoints, only add.

## Spec (`api/server.py`)
- `GET /datasets` also lists: every directory under the roots that contains `estate.db` or `vendors.csv` (`"format": "judges"`, `has_truth` from `hidden/ground_truth.json`), and every `*.db` file directly under a root (`name` = file stem). Legacy entries get `"format": "legacy"`.
- `POST /datasets` accepts `"format": "judges"` and calls the generator with `--format judges` (#80); `schemes` accepts the six names (#81).
- `POST /runs` accepts `"dataset"` as a path to a `.db` file or a judges' dir; `agent.investigate.run` handles it (#79). The run also writes `submission.json` (#88) and `report.html` (#90) next to the case file; the 202 body gains `"submission"` and `"report_html"`.
- New: `GET /runs/{id}/submission` (JSON, 404 until done), `GET /runs/{id}/report.html` (`text/html`, 404 until done), `GET /runs/{id}/validate` (runs `scripts/judges/validate_format.py` logic in-process: `{"ok": bool, "errors": [...]}`; uses `--estate` when the dataset is a `.db`).
- `GET /datasets/{name}/entities` on a judges' estate keys entities by `RFC:...`/`EMP:...` and includes `"COMPANY": {"rfc", "clabe"}`.
- `api/README.md` and `docs/STEP_LOG.md` (if it lists artifacts) updated.

## Tests (`tests/test_api_server.py` additions)
- With `tests/fixtures/judges_mini` (#79) copied under `out_root`: it appears in `/datasets` with `format == "judges"`; `POST /runs {"dataset": <that path>, "no_llm": true}` → done; `/submission` validates (`validate_structure` → `[]`); `/report.html` body contains `<svg`; `/validate` → `ok true`.
- Legacy assertions from #68 unchanged.

## Definition of done
- [ ] Endpoints added, tests green, ruff clean, no new dependencies; frontend teammate told about the two new artifact endpoints

**Depends on #68, #79, #88, #90.**
