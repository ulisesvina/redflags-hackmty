# Evaluation — what we measured, on which seeds, and what is still missing

The judges' rule (`student-materials/forensic-auditor/README.md`): *"Report on seeds you did not tune on.
Name both sets in the pitch. They must be disjoint."* And: *"Recall is half the measure. False accusations
against decoys are weighted at least as heavily."*

## The two seed sets

| Set | Seeds | Used for |
|---|---|---|
| **Tuning** | 42 (frozen `company_42`), 101–110, 201–205, 301–306 | Every detector threshold, every guard rule, every debugging run during the build |
| **Reporting** | **901–910** | Never run until the evaluation below. This is the "records it has never seen" number |

The two sets are disjoint. `scripts/eval_batch.py` refuses seed 42 outright, because its answer file is
committed in the repo and it is therefore not unseen. And `--report` (the only flag that produces the
slide table) refuses the whole tuning set `TUNING_SEEDS = {42, 101–110, 201–205, 301–306}` (#86) — a hard
guard, so a reporting table cannot silently quote a seed we tuned on. The set is a named constant in the
script, so it stays in sync with this table.

## Results, deterministic path (`--no-llm`), 2026-09-12

Ten estates generated from the reporting seeds, each investigated end to end and scored against its own
hidden ground truth, which the agent never reads (`tests/test_no_hidden_access.py` enforces that, and the
string `ground_truth` appears nowhere under `agent/`).

| Table | Seeds | Schemes | Recall | Decoys accused | False accusations | Evidence validity | Wall clock (median) |
|---|---|---|---|---|---|---|---|
| [`2026-09-12-nollm-reporting.md`](2026-09-12-nollm-reporting.md) | 901–910 | random subset per seed | **1.000** on all 7 scheme seeds | **0** | **0** | **1.000** | 1.19 s |
| [`2026-09-12-nollm-reporting-all.md`](2026-09-12-nollm-reporting-all.md) | 901–910 | all four | **1.000** on all 10 | **0** | **0** | 0.994 | 1.25 s |
| [`2026-09-12-nollm-tuning.md`](2026-09-12-nollm-tuning.md) | 101–110 | random subset per seed | 1.000 on all 9 scheme seeds | 0 | 0 | 0.996 | 1.2 s |
| [`2026-09-12-nollm-clean.md`](2026-09-12-nollm-clean.md) | 201–205 | none (honest books) | n/a | **0** | **0** | n/a | 1.0 s |

**Nothing to find.** The random-subset draw gave seeds 903, 906 and 908 an empty scheme list, and the
dedicated clean run covers five more. On all eight honest estates the agent produced **zero findings**. That
is the answer to the judges' question *"what does it do when there's nothing to find?"*, measured rather
than asserted.

## Reading the two averages

A clean estate has no scheme to recall and no evidence to validate. `data_estate/score.py` reports
`results_recall = 1.0` for it (vacuously, the denominator is zero) and `evidence_validity = 0.0` (nothing
was cited, so nothing could be valid). Averaging clean seeds into either number is misleading in **both**
directions: it flatters recall and it understates evidence validity. So the summary block reports:

- `mean_recall_scheme_seeds` and `mean_evidence_validity_scheme_seeds` — the honest headline, over the
  seeds that actually had fraud planted. **These are the numbers for the slide.**
- `mean_recall` / `mean_evidence_validity` — the all-seeds figures, kept so the tables stay comparable
  with earlier runs.
- `clean_seeds` and `clean_seeds_with_findings` — the "nothing to find" control, which must stay empty.

## Not yet measured: LLM mode

Every table above is the **deterministic path**. It uses the detectors, the lead docket, the rule catalog
and the evidence guard, with no model call, and it is what runs on stage if the cluster is unreachable.

The LLM path has **not** been evaluated on unseen seeds. It has been run — seven times on company_42, with
GLM-5.3-Flash on the cluster, scoring 1/4 to 4/4 before the retry and fallback work of #65/#66/#70 landed
(`LEARNINGS.md`, 2026-09-12 19:00). But company_42 is a **tuning** seed: its answer file is committed in this
repo and the response cache may be replaying earlier answers, so under the judges' own rule that number is
not reportable. `.env` on this machine holds the placeholder values from `.env.example`
(`LLM_BASE_URL=https://cluster.example`, empty key and model), so every batch here fell back to the
deterministic path. The harness is ready; it needs credentials, not code. With a filled-in `.env`, these three commands produce the
LLM-mode tables:

```bash
python scripts/check_llm.py --tools                      # endpoint answers and returns structured tool calls
LLM_CACHE=0 python scripts/eval_batch.py --seeds 901-910 --schemes random \
    --out docs/eval/<date>-llm-reporting.md              # the headline "unseen" table
LLM_CACHE=0 python scripts/eval_batch.py --seeds 201-203 --schemes clean \
    --out docs/eval/<date>-llm-clean.md                  # honest books: expect zero findings
```

`LLM_CACHE=0` matters: with the cache on, a second run answers from disk and the call count, cost and wall
clock all collapse to a replay rather than a cold measurement.

The tables carry three columns the judges ask every team for, filled from `run_metadata` in the case file:
`llm_calls`, `mxn_cost` and `wall_s`, with `total_llm_calls`, `total_mxn_cost` and `mxn_per_seed` in the
summary. They are zero above because no model was called.

## Reproducing any table

```bash
python scripts/eval_batch.py --seeds 901-910 --schemes random --no-llm --out /tmp/check.md
```

The generator is deterministic, so the same seed rebuilds the same estate and the same case file. The
command line that produced each table is recorded at the bottom of that table.

## The judges' results table (#86)

The pack defines one answer-key shape, two numbers that matter (recall and false-accusation rate), a 2%
peso rule, and a results table with fixed columns (`results_table_template.csv`). Our harness now speaks
that shape directly instead of our internal metrics.

`--format judges` generates each estate to the judges' schema (`estate.db` + `csv/`, #80), runs the agent
on `estate.db`, builds the judges' `submission.json` (#88), and scores *that* submission — so the number is
measured on the same schema and same output shape the judges use, not on our CSV layout and case file.

`--report` writes `results_table.csv` (in the template's exact columns) plus a `TOTAL` row, and refuses
the tuning seeds so the reporting table cannot quote a seed we tuned on.

```bash
python scripts/eval_batch.py --seeds 901-902 --report --no-llm --format judges \
    --csv data_estate/out/results_table.csv
```

The columns are the template's verbatim:

```
seed,schemes_planted,schemes_found,recall_pct,decoys_planted,decoys_accused,
false_accusation_rate_pct,peso_claimed,peso_actual,peso_reconciles,llm_calls,mxn_cost,wall_clock_s
```

`peso_reconciles` is the judges' 2% per-table rule: every finding's `peso_amount` reconciles to the sum of
its cited exhibits' amounts, per table, within 2% (shared implementation in `agent/reconcile.py`, #87).

