"""Step-log contract as code (#67).

``agent.investigate`` writes one JSON object per line to the ``--log`` path.
This module is the single description of that line format: the kinds, the
payload fields each kind must carry, a tolerant parser, a validator that fails
when the writer drifts from the contract, and a small CLI.

The contract here is the source of truth for the frontend and for the API
server (#68). Writers may add fields, never rename or remove them; readers must
ignore unknown kinds and unknown fields (forward compatibility).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# `load` of a run's step names; ``""`` is the run-level entity id.
KINDS: tuple[str, ...] = (
    "run_start",
    "lead",
    "hypothesis",
    "tool_call",
    "tool_result",
    "decision",
    "guard",
    "challenge",
    "run_end",
)

# A JSON number is an int or a float; bool is deliberately excluded.
_NUMBER = (int, float)


def _is_type(value: Any, spec: type | tuple[type, ...]) -> bool:
    """Return whether ``value`` satisfies a contract type spec."""
    if spec is str:
        return isinstance(value, str)
    if spec is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if spec is float:
        return isinstance(value, float) and not isinstance(value, bool)
    if spec is bool:
        return isinstance(value, bool)
    if spec is list:
        return isinstance(value, list)
    if spec is dict:
        return isinstance(value, dict)
    if isinstance(spec, tuple):
        return isinstance(value, spec) and not isinstance(value, bool)
    return True


# Per-kind required payload fields, with the JSON type each must have. Extra
# payload fields are allowed. ``decision`` is conditional on ``action`` and is
# validated separately in ``validate_entries``.
REQUIRED_PAYLOAD: dict[str, dict[str, type | tuple[type, ...]]] = {
    "run_start": {"dataset": str, "n_leads": int, "mode": str, "model": str},
    "lead": {
        "entity_id": str,
        "name": str,
        "rank": int,
        "detectors": list,
        "n_detectors": int,
        "total_mxn": _NUMBER,
        "leads": list,
    },
    "hypothesis": {"text": str, "scheme_type": str},
    "tool_call": {"name": str, "args": dict},
    "tool_result": {"name": str, "n_rows": int, "summary": str, "ids": list, "rows": list},
    "decision": {"action": str},
    "guard": {"accepted": bool, "reasons": list, "finding": dict},
    "challenge": {"scheme_type": str, "verdict": str, "arguments": list},
    "run_end": {
        "n_findings": int,
        "n_not_pursued": int,
        "wall_s": _NUMBER,
        "case_file": str,
        "report": str,
    },
}

# finding fields a ``record_finding`` decision / accepted guard must carry.
_FINDING_FIELDS: tuple[str, ...] = ("scheme_type", "accused", "rule", "amount_mxn", "evidence")


def parse_lines(text: str) -> tuple[list[dict], bool]:
    """Parse a JSONL step-log string; tolerate a partial last line.

    Returns ``(entries, complete)`` where ``complete`` is False when the final
    line was cut off mid-write (the writer is still going). Blank lines are
    skipped.
    """
    entries: list[dict] = []
    complete = True
    for line in text.split("\n"):
        if line.strip() == "":
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            complete = False
            break
    return entries, complete


def _err(msg: str) -> list[str]:
    return [msg]


def validate_entries(entries: list[dict]) -> list[str]:
    """Validate a list of step-log entries; return one message per violation.

    Envelope keys must be exactly ``ts, entity_id, step, kind, payload``; ``ts``
    must parse with ``datetime.fromisoformat``; ``step`` must be strictly
    increasing by 1 from 1; the first entry must be ``run_start``; a ``run_end``
    (if present) must be the last entry; every ``guard`` must be immediately
    preceded by a ``record_finding`` decision for the same entity; every
    ``tool_result`` must be immediately preceded by a ``tool_call`` with the
    same ``name`` and ``entity_id``; and every ``lead`` entity must later be the
    subject of at least one ``decision``. Unknown kinds are allowed (forward
    compatibility) but a known kind with a missing/mistyped required field is an
    error.
    """
    errors: list[str] = []
    if not entries:
        return errors

    # Envelope shape, timestamps and strictly-increasing steps.
    for i, e in enumerate(entries):
        label = f"entry {e.get('step', '?')}"
        if set(e.keys()) != {"ts", "entity_id", "step", "kind", "payload"}:
            errors.append(f"{label}: envelope keys must be exactly ts, entity_id, step, kind, payload")
            continue
        try:
            datetime.fromisoformat(e["ts"])
        except (ValueError, TypeError):
            errors.append(f"{label}: ts is not an ISO timestamp")
        if i == 0:
            if e["step"] != 1:
                errors.append(f"{label}: step must start at 1")
        elif e["step"] != entries[i - 1]["step"] + 1:
            errors.append(f"{label}: step must be the previous step + 1 (got {e['step']})")

    if entries[0].get("kind") != "run_start":
        errors.append("entry 1: first entry must be run_start")

    run_end_idx = [i for i, e in enumerate(entries) if e.get("kind") == "run_end"]
    if run_end_idx and run_end_idx[-1] != len(entries) - 1:
        errors.append(f"entry {entries[-1].get('step', '?')}: a run_end must be the last entry")

    # Known-kind payload requirements; unknown kinds are ignored.
    for e in entries:
        kind = e.get("kind")
        payload = e.get("payload", {})
        if not isinstance(payload, dict):
            continue
        req = REQUIRED_PAYLOAD.get(kind)
        if req is None:
            continue
        for field, spec in req.items():
            if field not in payload:
                errors.append(f"entry {e.get('step', '?')}: payload missing required field '{field}' for kind '{kind}'")
            elif not _is_type(payload[field], spec):
                errors.append(
                    f"entry {e.get('step', '?')}: payload field '{field}' for kind '{kind}' should be a JSON {_spec_name(spec)}"
                )
        if kind == "decision":
            action = payload.get("action")
            if action == "record_finding":
                find = payload.get("finding")
                if not isinstance(find, dict):
                    errors.append(f"entry {e.get('step', '?')}: decision record_finding requires a 'finding' object")
                else:
                    for f in _FINDING_FIELDS:
                        if f not in find:
                            errors.append(f"entry {e.get('step', '?')}: finding missing required field '{f}'")
            elif action == "drop_lead":
                if not isinstance(payload.get("reason"), str):
                    errors.append(f"entry {e.get('step', '?')}: decision drop_lead requires a 'reason' string")
            elif action == "park_lead":
                if not isinstance(payload.get("tier"), str) or not isinstance(payload.get("reason"), str):
                    errors.append(
                        f"entry {e.get('step', '?')}: decision park_lead requires 'tier' and 'reason' strings "
                        "(the 'suspicious' tier; the reason is the declined-lead narrative)"
                    )

    # Ordering relationships, checked per entity subsequence. A concurrent
    # writer (#71) may interleave *other* entities' entries between one unit's
    # own tool_call and tool_result, or between its decision and guard, so the
    # adjacency contract holds within an entity's own subsequence, not globally.
    by_entity: dict[str, list[dict]] = {}
    for e in entries:
        by_entity.setdefault(str(e.get("entity_id", "")), []).append(e)
    for eid, sub in by_entity.items():
        for j, e in enumerate(sub):
            kind = e.get("kind")
            label = f"entry {e.get('step', '?')} (entity {eid or '(run)'})"
            if kind == "guard":
                if (
                    j == 0
                    or sub[j - 1].get("kind") != "decision"
                    or sub[j - 1].get("payload", {}).get("action") != "record_finding"
                ):
                    errors.append(
                        f"{label}: a guard must immediately follow a record_finding decision in the same entity's sequence"
                    )
            if kind == "tool_result":
                if (
                    j == 0
                    or sub[j - 1].get("kind") != "tool_call"
                    or sub[j - 1].get("payload", {}).get("name") != e.get("payload", {}).get("name")
                ):
                    errors.append(
                        f"{label}: a tool_result must immediately follow a matching tool_call (same name) in the same entity's sequence"
                    )

    # Every lead must later be the subject of at least one decision.
    decision_entities: set[str] = set()
    for e in entries:
        if e.get("kind") == "decision":
            decision_entities.add(e.get("entity_id", ""))
    for i, e in enumerate(entries):
        if e.get("kind") != "lead":
            continue
        eid = str(e.get("entity_id", "")) or ""
        if not any(
            later.get("kind") == "decision" and later.get("entity_id") == eid for later in entries[i + 1 :]
        ):
            errors.append(f"entry {e.get('step', '?')}: lead entity '{eid}' is never the subject of a later decision")

    return errors


def _spec_name(spec: type | tuple[type, ...]) -> str:
    if isinstance(spec, tuple):
        return "number"
    return getattr(spec, "__name__", str(spec))


def main(argv: list[str] | None = None) -> int:
    parser = __import__("argparse").ArgumentParser(prog="python -m agent.steplog")
    parser.add_argument("log_file", help="path to a step-log .jsonl file")
    args = parser.parse_args(argv)
    text = Path(args.log_file).read_text(encoding="utf-8")
    entries, complete = parse_lines(text)
    errors = validate_entries(entries)
    if errors:
        for err in errors:
            print(err)
        return 1
    print(f"OK {len(entries)} entries" + ("" if complete else " (partial last line ignored)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
