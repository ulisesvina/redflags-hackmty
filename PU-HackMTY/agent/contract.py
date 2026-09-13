"""Mechanical case-file contract check (#3), reused by the evidence guard (#14).

A case file that names an ID which does not exist in the dataset is invalid,
full stop (AGENTS.md rule 3). Full contract: docstring of data_estate/score.py.

CLI: python -m agent.contract <dataset_dir> <case_file.json>
     prints the errors and exits 1, or prints OK and exits 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .data import Dataset, load

SCHEME_TYPES = {
    "efos_fake_supplier",
    "kickback_shell",
    "round_trip_sales",
    "duplicate_invoice_payment",
    "threshold_splitting",
    "revenue_inflation",
    "other",
}


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_case_file(case: dict, ds: Dataset) -> list[str]:
    """Return [] when valid, else one human-readable error per problem."""
    errors: list[str] = []

    if not isinstance(case, dict):
        return ["case file: expected a JSON object"]
    findings = case.get("findings")
    if not isinstance(findings, list):
        errors.append("case file: 'findings' must be a list")
    not_pursued = case.get("not_pursued")
    if not isinstance(not_pursued, list):
        errors.append("case file: 'not_pursued' must be a list")
    if errors:
        return errors

    entity_ids = ds.all_entity_ids()
    record_ids = ds.all_record_ids()
    not_pursued_entities: set[str] = set()

    for i, row in enumerate(not_pursued):
        if not isinstance(row, dict):
            errors.append(f"not_pursued[{i}]: expected an object")
            continue
        entity = row.get("entity")
        if entity not in entity_ids:
            errors.append(f"not_pursued[{i}].entity: {entity} not in dataset")
        not_pursued_entities.add(entity)
        if not isinstance(row.get("reason"), str) or not row.get("reason"):
            errors.append(f"not_pursued[{i}].reason: must be a non-empty string")

    accused_entities: set[str] = set()
    for i, finding in enumerate(findings):
        prefix = f"findings[{i}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix}: expected an object")
            continue

        if finding.get("scheme_type") not in SCHEME_TYPES:
            errors.append(f"{prefix}.scheme_type: {finding.get('scheme_type')!r} not in {sorted(SCHEME_TYPES)}")

        accused = finding.get("accused")
        if not isinstance(accused, list) or not accused or not all(isinstance(a, str) for a in accused):
            errors.append(f"{prefix}.accused: must be a non-empty list of strings")
        else:
            if len(set(accused)) != len(accused):
                errors.append(f"{prefix}.accused: duplicate IDs")
            for a in set(accused):
                accused_entities.add(a)
                if a not in entity_ids:
                    errors.append(f"{prefix}.accused: {a} not in dataset")

        rule = finding.get("rule")
        if not isinstance(rule, str) or not rule:
            errors.append(f"{prefix}.rule: must be a non-empty string")

        amount = finding.get("amount_mxn")
        if not _is_number(amount) or amount <= 0:
            errors.append(f"{prefix}.amount_mxn: {amount!r} must be a number > 0")

        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(e, str) for e in evidence):
            errors.append(f"{prefix}.evidence: must be a non-empty list of strings")
        else:
            if len(set(evidence)) != len(evidence):
                errors.append(f"{prefix}.evidence: duplicate IDs")
            for e in set(evidence):
                if e not in record_ids:
                    errors.append(f"{prefix}.evidence: {e} not in dataset")

    double_booked = accused_entities & not_pursued_entities
    for entity in sorted(double_booked):
        errors.append(f"{entity}: accused in a finding but also listed in not_pursued")

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python -m agent.contract <dataset_dir> <case_file.json>", file=sys.stderr)
        return 2
    ds = load(argv[0])
    try:
        case = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{argv[1]}: invalid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_case_file(case, ds)
    if errors:
        for err in errors:
            print(err)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
