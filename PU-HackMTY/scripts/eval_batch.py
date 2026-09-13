#!/usr/bin/env python3
"""Batch evaluation (#25): run the agent on N fresh datasets and score each run.

  python scripts/eval_batch.py --seeds 101-110 [--schemes all|clean|random|efos,kickback]
        [--no-llm] [--out docs/eval/<YYYY-MM-DD>.md] [--workdir data_estate/out/batch]
        [--max-leads 12] [--min-recall 0.8] [--max-penalty 0]
        [--format legacy|judges] [--report] [--csv results_table.csv]

This is the "on records it has never seen" number for the pitch and the go/no-go
gate before the feature freeze (docs/PLAN.md hours 12-24: mean recall >= 0.8 and
judgment penalty 0 on every seed). One command generates N fresh datasets, runs the
agent on each, scores every run, and prints a table plus a markdown file for slides.

``--format judges`` (#86) generates each estate to the judges' schema (#80,
``estate.db`` + ``csv/``), runs the agent on ``estate.db``, builds the judges'
``submission.json`` (#88) and scores *that* — so the number is on the same shape the
judges use. ``--report`` refuses the tuning seeds (the judges' rule: reporting seeds
must be disjoint from tuning) and writes ``results_table.csv`` in the exact columns of
the pack's ``results_table_template.csv``, with a ``TOTAL`` row, for the slide.

The CLI and the test share the same functions: run_batch, parse_seeds, plan,
to_markdown, to_results_csv. Stdlib only (argparse, statistics, time, traceback) plus
the existing ``data_estate`` and ``agent`` packages. No new dependencies.

Seed 42 is refused: company_42 is frozen and its answer file is in the repo, so it is
not "unseen". CI does not run this (it needs the whole agent and, in LLM mode, .env);
it is a manual gate a human runs before the freeze.

Exit code 1 when mean_recall < --min-recall, or any seed's penalty > --max-penalty,
or any clean seed produced a finding; 0 otherwise.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALL_SCHEMES = ["efos", "kickback", "roundtrip", "duplicate"]

# Judges' results-table columns, copied verbatim from the pack's
# student-materials/forensic-auditor/results_table_template.csv (#86).
RESULTS_TABLE_COLUMNS = [
    "seed", "schemes_planted", "schemes_found", "recall_pct", "decoys_planted",
    "decoys_accused", "false_accusation_rate_pct", "peso_claimed", "peso_actual",
    "peso_reconciles", "llm_calls", "mxn_cost", "wall_clock_s",
]
RESULTS_TABLE_HEADER = ",".join(RESULTS_TABLE_COLUMNS)

# Seeds a team tunes on; the judges' rule says the reporting seeds must be disjoint
# (#86, docs/eval/README.md). ``--report`` refuses these so the slide table cannot
# accidentally quote a seed whose answer key is sitting in the repo.
TUNING_SEEDS = {42, *range(101, 111), *range(201, 206), *range(301, 307)}


def parse_seeds(text: str) -> list[int]:
    """Parse "101-103,200" -> [101, 102, 103, 200].

    Refuses seed 42 (frozen company_42 is not "unseen").
    """
    out: list[int] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            lo, hi = int(a), int(b)
            if lo > hi:
                lo, hi = hi, lo
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(token))
    if 42 in out:
        print(
            "error: seed 42 is the frozen company_42 and its answer file is in the repo; "
            "not 'unseen'. Choose a different range.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return out


def plan(seeds: list[int], schemes_arg: str) -> list[tuple[int, list[str]]]:
    """Map each seed to its scheme list based on the --schemes argument.

    "all" (default) plants the four schemes; "clean" plants none; "random" picks,
    per seed, a deterministic subset via ``random.Random(seed).sample(...)`` of
    random size 0-4; an explicit comma list plants exactly those names.
    """
    arg = (schemes_arg or "all").strip().lower()
    if arg == "all":
        per_seed: list[str] = list(ALL_SCHEMES)
        randomized = False
    elif arg == "clean":
        per_seed = []
        randomized = False
    elif arg == "random":
        per_seed = []
        randomized = True
    else:
        names = [x.strip() for x in arg.split(",") if x.strip()]
        bad = [n for n in names if n not in ALL_SCHEMES]
        if bad:
            print("error: unknown scheme(s): " + ", ".join(bad), file=sys.stderr)
            raise SystemExit(2)
        per_seed = names
        randomized = False

    out: list[tuple[int, list[str]]] = []
    for seed in seeds:
        if randomized:
            r = random.Random(seed)
            k = r.randint(0, len(ALL_SCHEMES))
            ss = r.sample(ALL_SCHEMES, k)
        else:
            ss = list(per_seed)
        out.append((seed, ss))
    return out


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    srt = sorted(values)
    if len(srt) == 1:
        return srt[0]
    idx = min(len(srt) - 1, max(0, round(0.95 * (len(srt) - 1))))
    return srt[idx]


def _row(seed: int, schemes: list[str]) -> dict:
    return {
        "seed": seed,
        "schemes": list(schemes),
        "recall": 0.0,
        "found": [],
        "missed": [],
        "penalty": 0,
        "false_acc": [],
        "decoys_acc": [],
        "evidence_validity": 0.0,
        "not_pursued": 0,
        "contract_errors": 0,
        "llm_calls": 0,
        "cached_calls": 0,
        "tokens": 0,
        "mxn_cost": 0.0,
        "wall_s": 0.0,
        # #86 judges' results-table columns (one row per seed in results_table.csv)
        "schemes_planted": 0,
        "schemes_found": 0,
        "recall_pct": 0.0,
        "decoys_planted": 0,
        "decoys_accused_count": 0,
        "false_accusations_count": 0,
        "n_accused_entities": 0,
        "false_accusation_rate_pct": 0.0,
        "peso_claimed": 0.0,
        "peso_actual": 0.0,
        "peso_reconciles": False,
        "wall_clock_s": 0.0,
        "error": "",
    }


def run_batch(
    seed_plan: list[tuple[int, list[str]]],
    *,
    no_llm: bool,
    workdir: str | Path,
    max_leads: int = 12,
    format: str = "legacy",
) -> tuple[list[dict], dict]:
    """Run the agent on each (seed, schemes) pair and score it.

    ``format`` is ``legacy`` (our CSV layout, as before) or ``judges`` (#86): the
    estate is written to the judges' schema (#80, ``estate.db`` + ``csv/`` + the
    judges' ``hidden/ground_truth.json``), the agent runs on ``estate.db``, a
    ``submission.json`` is built (#88), and that submission is scored.

    Returns ``(rows, summary)``. An exception inside any per-seed step is caught,
    printed with its traceback, and recorded as recall 0 / penalty 0 with ``error``
    set so the batch always finishes. Rows and the summary keep the seed/schemes
    fields so the markdown output is self-describing.
    """
    from agent.config import settings
    from agent.contract import validate_case_file
    from agent.data import load as load_ds
    from agent.investigate import run
    from data_estate import validate
    from data_estate.export_judges import write_judges_estate
    from data_estate.generate import COMPANY, Generator, write_estate
    from data_estate.score import score

    if format not in ("legacy", "judges"):
        raise ValueError(f"unknown format {format!r} (expected 'legacy' or 'judges')")

    out_root = Path(workdir)
    out_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    wall_times: list[float] = []
    for seed, schemes in seed_plan:
        t0 = time.time()
        row = _row(seed, schemes)
        dataset_dir: Path
        try:
            estate = Generator(seed).build(list(schemes))
            if format == "judges":
                dataset_dir = out_root / f"estate_{seed}"
                write_judges_estate(estate, dataset_dir, seed=seed, company=COMPANY)
                dataset_path = dataset_dir / "estate.db"
                submission_path = out_root / f"submission_{seed}.json"
                case = run(
                    dataset_path,
                    out=str(out_root / f"case_{seed}.json"),
                    log=str(out_root / f"log_{seed}.jsonl"),
                    no_llm=no_llm,
                    max_leads=max_leads,
                    submission=str(submission_path),
                )
                submission = json.loads(submission_path.read_text(encoding="utf-8")) \
                    if submission_path.exists() else case
                scored = score(dataset_dir, submission)
                row["contract_errors"] = len(validate_case_file(case, load_ds(dataset_path)))
            else:
                dataset_dir = out_root / f"company_{seed}"
                write_estate(estate, dataset_dir)
                check_errs = validate.check(dataset_dir)
                if check_errs:
                    raise RuntimeError("dataset failed validation: " + "; ".join(check_errs))
                case = run(
                    dataset_dir,
                    out=str(out_root / f"case_{seed}.json"),
                    log=str(out_root / f"log_{seed}.jsonl"),
                    no_llm=no_llm,
                    max_leads=max_leads,
                )
                scored = score(dataset_dir, case)
                row["contract_errors"] = len(validate_case_file(case, load_ds(dataset_dir)))

            row["recall"] = float(scored["results_recall"])
            row["found"] = sorted(scored["found"])
            row["missed"] = sorted(scored["missed"])
            row["penalty"] = int(scored["judgment_penalty"])
            row["false_acc"] = sorted(scored["false_accusations"])
            row["decoys_acc"] = sorted(scored["decoys_accused"])
            row["evidence_validity"] = float(scored["evidence_validity"])
            row["not_pursued"] = int(scored["not_pursued_listed"])
            # #86 judges' results-table fields, straight from the scorer.
            row["schemes_planted"] = int(scored.get("schemes_planted", 0))
            row["schemes_found"] = int(scored.get("schemes_found", 0))
            row["recall_pct"] = float(scored.get("recall_pct", 0.0))
            row["decoys_planted"] = int(scored.get("decoys_planted", 0))
            row["decoys_accused_count"] = int(scored.get("decoys_accused_count", 0))
            row["false_accusations_count"] = int(scored.get("false_accusations_count", 0))
            row["n_accused_entities"] = int(scored.get("n_accused_entities", 0))
            row["false_accusation_rate_pct"] = float(scored.get("false_accusation_rate_pct", 0.0))
            row["peso_claimed"] = float(scored.get("peso_claimed", 0.0))
            row["peso_actual"] = float(scored.get("peso_actual", 0.0))
            row["peso_reconciles"] = bool(scored.get("peso_reconciles", True))
            # #89 writes run_metadata into the case file; these are the three
            # numbers the judges ask every team for (calls, cost, wall clock).
            meta = case.get("run_metadata", {}) or {}
            row["llm_calls"] = int(meta.get("llm_calls", 0) or 0)
            row["cached_calls"] = int(meta.get("cached_calls", 0) or 0)
            row["tokens"] = int(meta.get("prompt_tokens", 0) or 0) + int(meta.get("completion_tokens", 0) or 0)
            row["mxn_cost"] = float(meta.get("mxn_cost", 0.0) or 0.0)
            row["wall_clock_s"] = float(scored.get("wall_clock_s", 0.0))
        except Exception as exc:  # noqa: BLE001 - batch must always finish
            row["error"] = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        row["wall_s"] = round(time.time() - t0, 3)
        wall_times.append(row["wall_s"])
        rows.append(row)

    s = settings()
    if no_llm or s is None:
        mode = "no-llm"
        model = ""
    else:
        mode = "llm"
        model = str(s.model)
    mode_label = f"{mode} ({model})" if model else mode

    recall_vals = [r["recall"] for r in rows]
    ev_vals = [r["evidence_validity"] for r in rows]
    # Seeds generated with an empty scheme list are honest books: there is nothing
    # to recall and no evidence to validate, so score.py reports recall 1.0
    # (vacuously, n == 0) and evidence_validity 0.0 (ev_total == 0). Averaging those
    # in flatters recall and understates evidence validity, so the headline numbers
    # are computed over the seeds that actually had a scheme planted, and the clean
    # seeds are reported separately as the "nothing to find" control.
    scheme_rows = [r for r in rows if r["schemes"]]
    clean_rows = [r for r in rows if not r["schemes"]]
    s_recall = [r["recall"] for r in scheme_rows]
    s_ev = [r["evidence_validity"] for r in scheme_rows]
    summary = {
        "seeds": [r["seed"] for r in rows],
        "mode": mode_label,
        "model": model,
        "mean_recall": sum(recall_vals) / len(recall_vals) if recall_vals else 0.0,
        "min_recall": min(recall_vals) if recall_vals else 0.0,
        "seeds_with_penalty": [r["seed"] for r in rows if r["penalty"] > 0],
        "clean_seeds_with_findings": [r["seed"] for r in rows if not r["schemes"] and r["found"]],
        "mean_evidence_validity": sum(ev_vals) / len(ev_vals) if ev_vals else 0.0,
        "wall_p50_s": statistics.median(wall_times) if wall_times else 0.0,
        "wall_p95_s": _p95(wall_times),
        "seeds_with_schemes": [r["seed"] for r in scheme_rows],
        "clean_seeds": [r["seed"] for r in clean_rows],
        "mean_recall_scheme_seeds": sum(s_recall) / len(s_recall) if s_recall else 0.0,
        "min_recall_scheme_seeds": min(s_recall) if s_recall else 0.0,
        "mean_evidence_validity_scheme_seeds": sum(s_ev) / len(s_ev) if s_ev else 0.0,
        "total_llm_calls": sum(r["llm_calls"] for r in rows),
        "total_mxn_cost": round(sum(r["mxn_cost"] for r in rows), 4),
        "mxn_per_seed": round(sum(r["mxn_cost"] for r in rows) / len(rows), 4) if rows else 0.0,
        "n_errors": len([r for r in rows if r["error"]]),
    }
    return rows, summary


_COLUMNS = [
    "seed",
    "schemes",
    "recall",
    "found",
    "missed",
    "penalty",
    "false_acc",
    "decoys_acc",
    "evidence_validity",
    "not_pursued",
    "contract_errors",
    "llm_calls",
    "mxn_cost",
    "wall_s",
    "error",
]


def _cell(key: str, value) -> str:
    if key in ("schemes", "found", "missed", "false_acc", "decoys_acc"):
        return ",".join(str(v) for v in value) if isinstance(value, (list, tuple)) else str(value)
    if key in ("recall", "evidence_validity"):
        return f"{float(value):.3f}" if isinstance(value, (int, float)) else str(value)
    if key == "wall_s":
        return f"{float(value):.2f}" if isinstance(value, (int, float)) else str(value)
    if key == "mxn_cost":
        return f"{float(value):.4f}" if isinstance(value, (int, float)) else str(value)
    return str(value)


def to_markdown(rows: list[dict], summary: dict, argv: list[str]) -> str:
    """Render the rows as a markdown table plus a summary block."""
    header = "| " + " | ".join(_COLUMNS) + " |"
    sep = "| " + " | ".join(["---"] * len(_COLUMNS)) + " |"
    lines = [header, sep]
    for row in rows:
        cells = [_cell(c, row.get(c)) for c in _COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- seeds: {summary['seeds']}")
    lines.append(f"- mode: {summary['mode']}")
    lines.append(f"- seeds_with_schemes: {summary.get('seeds_with_schemes', [])}")
    lines.append(f"- clean_seeds (nothing to find): {summary.get('clean_seeds', [])}")
    lines.append(f"- **mean_recall (scheme seeds): {summary.get('mean_recall_scheme_seeds', 0.0):.3f}**")
    lines.append(f"- min_recall (scheme seeds): {summary.get('min_recall_scheme_seeds', 0.0):.3f}")
    lines.append(
        "- **mean_evidence_validity (scheme seeds): "
        f"{summary.get('mean_evidence_validity_scheme_seeds', 0.0):.3f}**"
    )
    lines.append(f"- mean_recall (all seeds, clean counted as 1.0): {summary['mean_recall']:.3f}")
    lines.append(f"- min_recall (all seeds): {summary['min_recall']:.3f}")
    lines.append(f"- seeds_with_penalty: {summary['seeds_with_penalty']}")
    lines.append(f"- clean_seeds_with_findings: {summary['clean_seeds_with_findings']}")
    lines.append(
        "- mean_evidence_validity (all seeds, clean scored 0.0 because there is nothing to validate): "
        f"{summary['mean_evidence_validity']:.3f}"
    )
    lines.append(f"- wall_p50_s: {summary['wall_p50_s']:.2f}")
    lines.append(f"- wall_p95_s: {summary['wall_p95_s']:.2f}")
    lines.append(f"- total_llm_calls: {summary.get('total_llm_calls', 0)}")
    lines.append(f"- total_mxn_cost: {summary.get('total_mxn_cost', 0.0):.4f}")
    lines.append(f"- mxn_per_seed: {summary.get('mxn_per_seed', 0.0):.4f}")
    if summary.get("n_errors"):
        lines.append(f"- errors: {summary['n_errors']}")
    lines.append(f"- command: {' '.join(argv)}")
    return "\n".join(lines) + "\n"


def _num_cell(value) -> str:
    """A results-table cell, the way a reader (and a judge) expects the number."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _results_row(row: dict) -> list[str]:
    """One seed as a row in the judges' exact column order (#86)."""
    values = [
        row.get("seed", ""),
        row.get("schemes_planted", 0),
        row.get("schemes_found", 0),
        row.get("recall_pct", 0.0),
        row.get("decoys_planted", 0),
        row.get("decoys_accused_count", 0),
        row.get("false_accusation_rate_pct", 0.0),
        row.get("peso_claimed", 0.0),
        row.get("peso_actual", 0.0),
        row.get("peso_reconciles", False),
        row.get("llm_calls", 0),
        row.get("mxn_cost", 0.0),
        row.get("wall_clock_s", 0.0),
    ]
    return [_num_cell(v) for v in values]


def _results_total_row(rows: list[dict]) -> list[str]:
    """The aggregate TOTAL row. Recall and false-accusation rate are re-derived from
    the pooled counts so the row is the true over-all figure, not a mean of means."""
    if not rows:
        return ["TOTAL"] + [""] * (len(RESULTS_TABLE_COLUMNS) - 1)
    planted = sum(r.get("schemes_planted", 0) for r in rows)
    found = sum(r.get("schemes_found", 0) for r in rows)
    recall_pct = 100.0 * found / planted if planted else 0.0
    decoys_planted = sum(r.get("decoys_planted", 0) for r in rows)
    decoys_accused = sum(r.get("decoys_accused_count", 0) for r in rows)
    false_acc = sum(r.get("false_accusations_count", 0) for r in rows)
    n_accused = sum(r.get("n_accused_entities", 0) for r in rows)
    far = 100.0 * (false_acc + decoys_accused) / max(1, n_accused)
    reconcile = all(bool(r.get("peso_reconciles", True)) for r in rows)
    values = [
        "TOTAL",
        planted,
        found,
        recall_pct,
        decoys_planted,
        decoys_accused,
        far,
        round(sum(r.get("peso_claimed", 0.0) for r in rows), 2),
        round(sum(r.get("peso_actual", 0.0) for r in rows), 2),
        reconcile,
        sum(r.get("llm_calls", 0) for r in rows),
        round(sum(r.get("mxn_cost", 0.0) for r in rows), 4),
        round(sum(r.get("wall_clock_s", 0.0) for r in rows), 2),
    ]
    return [_num_cell(v) for v in values]


def to_results_csv(rows: list[dict]) -> str:
    """The judges' results table in their exact columns, plus a TOTAL row (#86)."""
    lines = [RESULTS_TABLE_HEADER]
    for row in rows:
        lines.append(",".join(_results_row(row)))
    lines.append(",".join(_results_total_row(rows)))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python scripts/eval_batch.py")
    parser.add_argument("--seeds", required=True, help="range 'a-b', comma list, or both, e.g. 101-105,200")
    parser.add_argument("--schemes", default="all", help="all|clean|random|comma list of scheme names")
    parser.add_argument("--no-llm", action="store_true", help="use the deterministic fallback path")
    parser.add_argument("--out", default=None, help="also write a markdown table to this path")
    parser.add_argument("--workdir", default="data_estate/out/batch", help="dir for generated datasets")
    parser.add_argument("--max-leads", type=int, default=12)
    parser.add_argument("--min-recall", type=float, default=0.8)
    parser.add_argument("--max-penalty", type=int, default=0)
    parser.add_argument("--format", choices=("legacy", "judges"), default="legacy",
                        help="legacy (default) or judges (#80/#86): generate to estate_schema.sql "
                             "(estate.db + csv/), run the agent on estate.db and score the submission.json")
    parser.add_argument("--report", action="store_true",
                        help="#86: refuse tuning seeds and write the judges' results_table.csv (the slide table)")
    parser.add_argument("--csv", default=None,
                        help="path for the judges' results_table.csv (default: --workdir/results_table.csv)")
    args = parser.parse_args(argv)

    seeds = parse_seeds(args.seeds)
    if args.report:
        tuning_hits = sorted(s for s in seeds if s in TUNING_SEEDS)
        if tuning_hits:
            print(
                "error: --report must not use tuning seeds "
                f"(got {tuning_hits}, tuning set is {sorted(TUNING_SEEDS)}). The judges' rule requires "
                "reporting seeds and tuning seeds to be disjoint (docs/eval/README.md).",
                file=sys.stderr,
            )
            raise SystemExit(1)

    seed_plan = plan(seeds, args.schemes)
    rows, summary = run_batch(
        seed_plan, no_llm=args.no_llm, workdir=args.workdir,
        max_leads=args.max_leads, format=args.format,
    )
    summary["command_line"] = " ".join(sys.argv)

    # Print an aligned table on stdout.
    cells = [[_cell(c, r.get(c)) for c in _COLUMNS] for r in rows]
    widths = [len(_COLUMNS[i]) for i in range(len(_COLUMNS))]
    for c in cells:
        for i, val in enumerate(c):
            widths[i] = max(widths[i], len(val))

    def pad(items):
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(items))

    print(pad(_COLUMNS))
    print(pad(["-" * w for w in widths]))
    for c in cells:
        print(pad(c))

    print("\nSummary")
    for key in ("seeds", "mode", "seeds_with_schemes", "clean_seeds",
                "mean_recall_scheme_seeds", "min_recall_scheme_seeds",
                "mean_evidence_validity_scheme_seeds", "mean_recall", "min_recall",
                "seeds_with_penalty", "clean_seeds_with_findings", "mean_evidence_validity",
                "wall_p50_s", "wall_p95_s", "total_llm_calls", "total_mxn_cost", "mxn_per_seed"):
        print(f"  {key}: {summary[key]}")
    print(f"  command_line: {summary.get('command_line', '')}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(to_markdown(rows, summary, sys.argv), encoding="utf-8")
        print(f"\nwrote {out_path}")

    if args.report:
        csv_path = Path(args.csv) if args.csv else Path(args.workdir) / "results_table.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(to_results_csv(rows), encoding="utf-8")
        print(f"\nwrote {csv_path}")

    # A batch of only clean books has no recall to measure; the gate for it is
    # "produced no findings", which the third clause below already checks.
    recall_gate = bool(summary["seeds_with_schemes"]) and (
        summary["mean_recall_scheme_seeds"] < args.min_recall
    )
    gate_fail = (
        recall_gate
        or any(r["penalty"] > args.max_penalty for r in rows)
        or bool(summary["clean_seeds_with_findings"])
    )
    return 1 if gate_fail else 0


if __name__ == "__main__":
    sys.exit(main())
