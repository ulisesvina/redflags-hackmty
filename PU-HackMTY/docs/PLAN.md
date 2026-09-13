# PLAN.md — HackMTY 2026 · Infosys "Forensic Auditor"

Updated 2026-09-12 evening. Supersedes the hour-zero plan; the judging table, scope and demo story are unchanged.

## Goal
An agent that, given a company's books and only the hint that something is wrong, finds the fraud,
follows the money, proves it with record IDs and a peso amount — and refuses to accuse anyone it
can't back up. Deliverable: working code + a 3-minute live demo where judges inject a fresh scheme.

## Where we are

**Working, merged, tested (232 tests, CI green):**
- `data_estate/`: generator (`--seed`, `--schemes`, `--n`), validator, scorer; company_42 frozen behind a checksum.
- `agent/`: loader, 12 detectors, lead docket (`leads.py`), tool layer (9 tools, every row carries record IDs),
  LLM client with disk cache and `FakeLLM`, rule catalog + evidence guard, investigation loop with two paths
  (`--no-llm` deterministic, LLM tool-calling), human-readable report with money trail and tax exposure.
- `scripts/eval_batch.py`: recall / penalty / evidence over N fresh seeds. `scripts/check_llm.py --tools`.

**Scores today:**

| Path | Dataset | Recall | Penalty | Wall |
|---|---|---|---|---|
| `--no-llm` | company_42, seed 7 | 1.0 | 0 | 0.1 s |
| LLM (GLM-5.3-Flash on the cluster) | company_42, 7 logged runs | 1/4, 1/4, 3/4, 3/4, 3/4, 4/4, 4/4 | 0 | 57–86 s cold |

> The LLM row is **not a reportable result**: company_42 is a tuning seed, its answer file is committed here,
> and the response cache may be replaying earlier answers. It is also not reproducible on this machine (`.env`
> holds the placeholders from `.env.example` and those seven logs are not in `runs/`). The measured, reproducible numbers are in [`docs/eval/`](eval/README.md), deterministic path,
> reporting seeds 901–910. Re-run the LLM tables with the commands in `docs/eval/README.md` once the cluster
> credentials are in `.env` (#72).


The LLM path loses findings for two reasons, both diagnosed from `runs/*.jsonl`: tool-call arguments truncated
by a small completion budget (fixed in PR #64), and ledger `GL*` IDs cited as evidence, which the contract does
not accept, so the guard rejects the finding and the loop drops the lead instead of retrying (#65, #66).
Precision has been perfect on every run: no decoy accused, ever.

**Not there yet:** live-tailable step log (#67), an HTTP API for the frontend (#68), drop reasons that cite
records instead of canned sentences (#69), a path for schemes we did not plan for (#70), concurrency to fit the
90-second stage budget (#71), LLM-mode numbers on unseen seeds (#72), the one-command demo (#27) and the
rehearsal pack (#31).

**Frontend:** built by a teammate outside this repo. The backend's contract to it is the step log
(`docs/STEP_LOG.md`, #67) and the API server (#68). `demo/sample_trace.jsonl` is a real run on company_42 with
all four findings, for building against before the API lands. Its `run_start` says `"mode": "no-llm"`: it is a
deterministic run, so it has the right log *shape* but no `tool_call` events. Regenerate it in LLM mode once
`.env` is filled in, so the frontend is built against a trace that has tool calls in it.

## How we win (judging criteria → what we build)

| Criterion | What scores it |
|---|---|
| Results | Recall on unseen data. Detectors produce leads; the loop confirms them; the deterministic fallback (#66) guarantees a signature unit is never lost to a bad model call. Measured by `scripts/eval_batch.py` (#72). |
| Judgment | Zero decoy accusations. `not_pursued` reasons that cite the clearing record (#69). `other` findings parked as "suspicious, unproven", never accused (#70). Guard verdicts visible in the trace. |
| Feasibility | Case file a real auditor could act on: rule cited, amount recomputed, IDs verified, tax exposure. Runs on an open-weight model on our own cluster; `--no-llm` if the cluster is down. |
| Clarity | Money trail on screen as the agent traces it (frontend over the step log). Rodrigo's story frames it in 30 seconds. Report in plain words. |

## Scope — fixed
- Four scheme types: `efos_fake_supplier`, `kickback_shell`, `round_trip_sales`, `duplicate_invoice_payment`.
  Anything else is `other` → parked as suspicious in `not_pursued` (#70), never an accusation.
- Five decoys (see `data_estate/README.md`). The agent must clear all five with a reason that names a record.
- Dataset schema and case-file contract are frozen. Changes go through a `needs-human` issue.

## Team & ownership

| Who | Owns | How |
|---|---|---|
| Sondre | `agent/` design decisions, LLM-mode runs (`.env`), #72 | Claude Code |
| Filip | `data_estate/`, queue hygiene, PLAN, merges that need a human | Codex / Claude Code |
| Hermes (server, unattended) | every `hermes-ok` issue, anywhere in the repo except the frozen dataset and the protected tests; opens the PR and merges it when CI is green | GitHub queue, see `docs/HERMES_BRIEF.md` |
| Frontend teammate | the UI, outside this repo, against `docs/STEP_LOG.md` and the API (#68) | — |
| Whoever is free | `demo/` script, Q&A, rehearsal (#31) | — |

## Architecture

```
data_estate/out/<seed>/          CSVs the agent sees (hidden/ never read by agent/)
        │
agent/data.py                    load → pandas Dataset
        │
agent/detectors/*.py             12 cheap rules → leads (auto-registered)
        │
agent/leads.py                   one dossier per entity, ranked; scheme signature → hint
        │
agent/investigate.py             per unit: hypothesis → tool calls → record_finding | drop_lead
        │   ├─ agent/tools.py       9 deterministic tools; every row carries record IDs
        │   ├─ agent/llm.py         OpenAI-compatible client → cluster (.env); cache; FakeLLM for tests
        │   ├─ agent/guard.py       every ID exists & belongs to the accused; rule in catalog; amount recomputed
        │   │                       rejection → fed back to the model → retry → deterministic fallback (#66)
        │   └─ agent/clear.py       drop reasons that cite records, or "unverified" → escalate (#69, #70)
        │
runs/<id>.jsonl                  step log, streamed line by line (#67) ── docs/STEP_LOG.md
case_file.json                   findings[] + not_pursued[] → data_estate/score.py
submission.json (#88)            the judges' machine-checked JSON; their validate_format.py runs in CI
report.html / .md (#90)          the five required sections; money trail as a diagram; opens offline
        │
api/server.py (#68)              POST /runs · GET /runs/{id}/events (SSE) · /case · /report · /score
        │
frontend (external)              live trace + money graph + case file
```

## The queue, in the order Hermes will take it

Hermes picks the lowest open `hermes-ok` number whose `Depends on` issues are closed and that has no open PR.
Numbers were filed in priority order on purpose.

| # | What | Depends on | Why it is in this position |
|---|---|---|---|
| 65 | guard: ledger IDs set aside, not rejected | — | 20-line change, removes the last known LLM-mode rejection cause |
| 66 | loop: guard feedback → retry → deterministic fallback | 65 | makes LLM-mode recall 1.0 on any signature unit; the trace shows provenance |
| 67 | streamed log + `docs/STEP_LOG.md` + `agent/steplog.py` validator + README | — | the frontend is blocked on a live-tailable log and a written contract |
| 68 | `api/server.py`: stdlib HTTP + SSE | 67 | the frontend's backend; one run at a time; score behind an explicit endpoint |
| 69 | `agent/clear.py`: drop reasons that cite records | — | Judgment criterion; "how do you know?" gets a record ID |
| 70 | escalate unverified weak leads; `other` → suspicious tier | 66, 69 | the judges' surprise scheme lands somewhere honest |
| 71 | concurrent units, `--workers` | 66 | 57–86 s cold → target < 30 s |
| 27 | `scripts/demo_run.py` + `docs/INJECT.md` | 68 | one command on stage; judge's injection guide |
| 72 | LLM-mode batch eval on unseen seeds (`cc`, needs `.env`) | 66, 69, 70 | the "records it has never seen" number for the pitch |
| 73 | this plan refresh (`cc`) | — | — |
| 31 | rehearsal pack (`needs-human`) | 27, 72 | script, Q&A, cannot-do slide, venue checklist |
| 26 | trace UI in this repo (`needs-human`) | — | superseded by the external frontend; keep open only if that falls through |

Filing rule (from LEARNINGS): a spec for an unattended agent must name the number it should find, the test file,
and the exact strings the test asserts, or it is not a spec.

## Hermes auto-merge: setup and guardrails

What is in place on `filip-rs/PU-HackMTY`:
- Branch protection on `master`: required status check `test` (the CI job), 0 required reviews, no force pushes.
  A PR cannot merge until CI is green; that is the gate Hermes' merge relies on.
- CI (`.github/workflows/ci.yml`): `ruff check .`, `validate company_42`, `pytest -q` on Python 3.12.
- Tests that must never be weakened or deleted (a PR that touches them without an issue saying so is reverted):
  `tests/test_case_file_contract.py`, `tests/test_frozen_dataset.py`, `tests/test_no_hidden_access.py`.
- Hermes has no `.env`; every `@pytest.mark.llm` test skips in CI and on the Hermes host. Consequence: **an
  LLM-mode regression is invisible to auto-merge.** The FakeLLM tests carry the loop's logic; a human runs #72
  after each batch of merges to the loop.

Recommended repo settings (owner action, five minutes): enable *Allow auto-merge* so `gh pr merge --auto --squash`
works without polling; enable *Automatically delete head branches*; set the required check to *strict* (branch
must be up to date with `master`) so two Hermes PRs merged minutes apart cannot combine into a red `master`.

Morning routine for a human: `gh pr list -s merged --limit 20`, skim each diff, `python scripts/sync_issues.py`,
re-run `python -m pytest -q` and, with `.env`, `python -m agent.investigate data_estate/out/company_42 --out /tmp/c.json`
followed by `python -m data_estate.score data_estate/out/company_42 /tmp/c.json`.

## Timeline (remaining)

| When | Milestone | Done when |
|---|---|---|
| Tonight | #65, #66, #67 merged by Hermes; frontend teammate builds against `demo/sample_trace.jsonl` and `docs/STEP_LOG.md` | LLM run on company_42 scores 4/4 three times in a row; `tail -f` shows a live log |
| Tomorrow morning | #68, #69 merged; frontend talks to `api/server.py`; #72 baseline run | frontend shows a live run end to end; eval table in `docs/eval/` |
| Tomorrow midday | #70, #71, #27; #72 final run | blind injection by a teammate investigated inside 90 s with the UI live |
| **Feature freeze** | after #27 and #72 | nothing merges to `master` except doc fixes; Hermes queue emptied of `hermes-ok` labels |
| Last 6 h | #31: three timed rehearsals, Q&A, cannot-do slide, learnings slide | three clean rehearsals in a row, times written down |

## Demo (3 minutes)

1. **0:00–0:30** Story. Rodrigo, a machine-shop owner in Monterrey, deducted invoices from three
   "consultants" a contact set him up with. Each looked fine alone. Two years later SAT listed them
   under 69-B and he was on the hook — treated as a participant, not a victim. His accountant never
   connected them. (Composite case, say so.)
2. **0:30–2:30** Live. A judge picks a seed and a scheme subset (or edits CSVs per `docs/INJECT.md`); we start
   the run from the frontend (`POST /runs`) and the trace streams: lead → hypothesis → records pulled → money
   followed → accusation with rule + amount, or drop with a reason that names a record. Make sure at least one
   decoy is visibly cleared and, if it happens, one guard rejection followed by a corrected finding.
3. **2:30–3:00** Surprise question. Rehearsed answers live in `demo/QA.md` (#31); the trace stays on screen.
   Hand the judges `report.html` from that run: five sections, the money trail drawn as a diagram, every peso
   reconciled to the exhibits beneath it. It is a single file with no script and no URL in it, so it opens on
   their laptop with the Wi-Fi off — which is exactly what `case_file_structure.md` asks us to be able to show.

Fallbacks, in order: cluster down → `no_llm: true` (same trace shape, deterministic findings); laptop trouble →
replay `demo/sample_trace.jsonl` through the API.

## Risks

| Risk | Mitigation |
|---|---|
| Cluster unreachable on demo day | `python scripts/check_llm.py --tools` from the venue the night before and 30 min before; `--no-llm` path is a first-class fallback and scores 1.0; response cache. |
| Model proposes a wrong finding | Guard rejects, feeds the reasons back, model retries, deterministic fallback on signature units (#66). Provenance is in the trace. |
| Accuses a decoy on stage | Never happened in any run. `other` cannot become an accusation (#70). Batch eval must show penalty 0 across 10 seeds before freeze (#72). |
| Hermes PR breaks something | CI-gated merges; protected tests; morning review; `git revert` of the squash commit is one command. |
| Demo runs long | `--workers` (#71), `--max-leads`, `--max-escalations`, `max_steps`; pre-warm with one run; rehearse with a timer. |
| Judges inject a scheme type we don't have | Escalation puts the model on it (#70); it lands in `not_pursued` as "suspicious, unproven" with the evidence it gathered. Say so honestly. Never fake a finding. |
| Frontend and backend drift | `docs/STEP_LOG.md` is the contract, `tests/test_step_log_contract.py` fails on writer drift, the API returns the same lines. |

## Definition of done
- `python -m data_estate.generate --seed <any>` → `validate` passes → agent runs (LLM mode) → `score.py` recall ≥ 0.8
  on 10 unseen seeds, penalty 0 on every one, no findings on honest books.
- Every `not_pursued` reason names a record or says "unverified".
- Case file and report readable by a non-engineer.
- Demo rehearsed three times end to end with the frontend live.
