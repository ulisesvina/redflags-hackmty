"""Investigation loop (#13) — the agent's brain.

Detectors produce *leads*, the LLM forms a hypothesis per lead and calls tools
to prove it or drop it, the evidence guard (#14) keeps invented evidence out,
and the result is a case file ``data_estate/score.py`` can score. The step log
is what the demo (#26) renders on screen, so its kinds/payloads are kept stable.

Two execution paths share the same investigation units:

- ``--no-llm`` (or no ``.env``): a deterministic fallback that turns the four
  known scheme signatures into findings through the *same* guard. This is the
  demo's safety net on stage and the path CI exercises.
- LLM loop: the model proposes via the tool layer (#12); every
  ``record_finding`` goes through the guard (#14). A *rejected* finding is fed
  back to the model (as a tool message with the guard's reasons and a hint) so
  it can fix and retry, up to ``MAX_GUARD_RETRIES`` rejections. If the LLM
  path ends without an accepted finding for a unit that carries a scheme
  signature, the loop falls back to the deterministic ``_build_finding`` (so
  ``--no-llm`` and LLM mode agree on the four known schemes) and labels the
  provenance in the step log. Every ``record_finding`` decision and every
  ``guard`` entry carries ``source`` (``llm`` | ``deterministic_fallback`` |
  ``deterministic``) and ``attempt``.

Amounts are the *full scheme aggregate* (the scorer's 25 % tolerance is on the
whole scheme, not a single entity), so EFOS suppliers that share a signature are
grouped into one finding. LLM access is only through ``agent.llm.LLM`` built from
``agent.config.settings()`` (#22) — never an HTTP client here.

Weak leads (no scheme signature) have three outcomes (#70): they are *cleared*
when the records support an innocent explanation, *escalated* to the model (up to
``max_escalations``) so a scheme we did not plan for can still be found, or
*unverified* and dropped. An ``other`` finding the guard accepts is never an
accusation — it is parked as a "suspicious, unproven" entry in ``not_pursued``
(the R5 rule has no amount recomputation, so it cannot be proven).

CLI: ``python -m agent.investigate <dataset_dir> [--out case_file.json] [--log runs/T.jsonl] [--max-leads 12] [--max-steps 12] [--max-escalations 4] [--workers 4] [--no-llm]``
or ``python -m agent.investigate --replay <log.jsonl|case_file.json> [--out ...]`` to rebuild a
run offline from its step log (never constructs an LLM, works with Wi-Fi off; #93).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .challenge import challenge as _challenge
from .clear import clear_reason
from .config import MXN_PER_1K_COMPLETION_TOKENS, MXN_PER_1K_PROMPT_TOKENS, settings
from .contract import SCHEME_TYPES, validate_case_file
from .data import Dataset, load
from .detectors import run_all
from .guard import _acceptable_evidence, _evidence_kind, guard
from .leads import STRONG, aggregate
from .llm import LLM, assistant_message, tool_message
from .report import render_html
from .rules import RULES
from .steplog import parse_lines
from .submit import build_submission, write_submission
from .tools import TOOL_SCHEMAS, Tools

# --- scheme signature -> evidence-guard rule --------------------------------
SCHEME_TO_RULE: dict[str, str] = {
    "efos_fake_supplier": "R1",
    "kickback_shell": "R2",
    "round_trip_sales": "R3",
    "duplicate_invoice_payment": "R4",
    "threshold_splitting": "R6",
}

_DATA_TOOL_NAMES = {
    "get_supplier",
    "get_customer",
    "get_employee",
    "get_invoices",
    "get_receipts",
    "get_bank_txns",
    "check_69b",
    "trace_flow",
    "query_ledger",
    "get_purchase_orders",
    "get_contracts",
}

# Guard-rejection retry budget (#66): the LLM may attempt ``record_finding``
# this many extra times after the first rejection; past that the loop falls
# back to the deterministic ``_build_finding`` for a signature unit. So at most
# ``MAX_GUARD_RETRIES + 1`` = 3 attempts per unit.
MAX_GUARD_RETRIES = 2


# --- step log ---------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _log_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class _Log:
    """One JSON object per line, the demo UI's data source (#26).

    When a ``path`` is given the file is opened immediately and every ``emit``
    appends and flushes the line, so a reader can tail it live mid-run (a
    partial last line means the writer is mid-write; no ``run_end`` after 60 s
    of silence means the run was aborted). :func:`run` calls :meth:`close` in a
    ``finally`` so a crash still leaves a readable file. Without a path it only
    buffers in memory.
    """

    def __init__(self, path: str | None = None) -> None:
        self.entries: list[dict[str, Any]] = []
        self._step = 0
        self._lock = threading.Lock()
        self._fh = None
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "w", encoding="utf-8")

    def emit(self, kind: str, entity_id: str = "", payload: dict | None = None) -> dict:
        # #71: step assignment + append + flush are atomic across worker threads,
        # so steps stay strictly increasing and lines never interleave mid-write.
        with self._lock:
            self._step += 1
            entry = {
                "ts": _now_iso(),
                "entity_id": entity_id or "",
                "step": self._step,
                "kind": kind,
                "payload": payload or {},
            }
            self.entries.append(entry)
            if self._fh is not None:
                self._fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
                self._fh.flush()
        return entry

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def _write_case_file(case: dict, out: str | None) -> None:
    if not out:
        return
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(case, fh, ensure_ascii=False, indent=2)


# --- investigation units -----------------------------------------------------
def _build_units(dossiers: list[dict]) -> list[dict]:
    """Group dossiers that share a non-empty scheme signature into one unit.

    An EFOS scheme spans *all* 69-B suppliers (S00030 + S00020 = 2,070,600 on
    company_42); a per-entity finding is rejected by the guard (its recompute is
    the whole scheme total under R1). Grouping by signature is how the loop
    produces the aggregate the scorer demands. Dossiers with no signature stay
    single-unit weak leads that are dropped.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    singles: list[dict] = []
    for d in dossiers:
        # A dossier may carry several scheme hints (an entity can sit in two
        # entangled schemes); it contributes a unit to *each* matching group.
        hints = d.get("scheme_hints")
        if hints is None:
            hints = [d.get("scheme_hint")] if d.get("scheme_hint") else []
        hints = [h for h in hints if h]
        if hints:
            for hint in hints:
                groups[hint].append(d)
        else:
            singles.append(d)

    units: list[dict] = []
    for hint, members in groups.items():
        members = sorted(members, key=lambda m: m["rank"])
        primary = members[0]
        entity_ids = sorted(str(m["entity_id"]) for m in members)
        detectors = sorted({x for m in members for x in m["detectors"]})
        related = sorted({x for m in members for x in m["related"]})
        evidence = sorted({x for m in members for x in m["evidence"]})
        leads: dict[str, dict] = {str(m["entity_id"]): m["leads"] for m in members}
        lead_list = [row for m in members for rows in m["leads"].values() for row in rows]
        units.append(
            {
                "entity_id": primary["entity_id"],
                "entity_ids": entity_ids,
                "kind": primary["kind"],
                "name": primary["name"],
                "detectors": detectors,
                "n_detectors": len(detectors),
                "n_strong": sum(1 for x in detectors if x in STRONG),
                "total_mxn": round(sum(float(m["total_mxn"]) for m in members), 2),
                "scheme_hint": hint,
                "related": related,
                "evidence": evidence,
                "leads": leads,
                "lead_list": lead_list,
                "members": members,
                "rank": primary["rank"],
            }
        )
    for d in singles:
        units.append(
            {
                "entity_id": d["entity_id"],
                "entity_ids": [d["entity_id"]],
                "kind": d["kind"],
                "name": d["name"],
                "detectors": d["detectors"],
                "n_detectors": d["n_detectors"],
                "n_strong": d["n_strong"],
                "total_mxn": d["total_mxn"],
                "scheme_hint": "",
                "related": d["related"],
                "evidence": d["evidence"],
                "leads": {str(d["entity_id"]): d["leads"]},
                "lead_list": [row for rows in d["leads"].values() for row in rows],
                "members": [d],
                "rank": d["rank"],
            }
        )

    # Scheme-bearing units first, then weak leads; stable within each class.
    units.sort(key=lambda u: (0 if u["scheme_hint"] else 1, u["rank"]))
    for i, u in enumerate(units, 1):
        u["rank"] = i
    return units


# --- fallback building ------------------------------------------------------
def _gather_evidence(unit: dict, ds: Dataset, accused: list[str], rule) -> list[str]:
    """Record IDs from the unit's leads that belong to the accused AND the rule's kinds."""
    acceptable = _acceptable_evidence(accused, ds)
    kinds = set(rule.evidence_kinds)
    pool: set[str] = set()
    for row in unit["lead_list"]:
        for e in row.get("evidence", []) or []:
            pool.add(str(e))
    evidence: list[str] = []
    for e in sorted(pool):
        if e not in acceptable:
            continue
        kind = _evidence_kind(e, ds)
        if kind is None or (kinds and kind not in kinds):
            continue
        evidence.append(e)
    # R1..R4 require at least one invoice.
    if not any(_evidence_kind(e, ds) == "invoice" for e in evidence):
        for e in sorted(acceptable):
            if _evidence_kind(e, ds) == "invoice" and e not in evidence:
                evidence.append(e)
                break
    return evidence


def _scheme_narrative(unit: dict, scheme_type: str, rule, ds: Dataset) -> str:
    names = ", ".join(
        str(m["name"]) for m in unit["members"] if m.get("name")
    ) or ", ".join(unit["entity_ids"])
    return (
        f"{scheme_type.replace('_', ' ')}: {names} — {rule.id}. "
        f"Records show MXN {unit['total_mxn']:,.2f} moved against these counterparties; "
        f"the scheme amount is the full aggregate across the accused entities."
    )


def _build_finding(unit: dict, ds: Dataset, scheme_type: str, rule_id: str) -> dict | None:
    """Assemble one aggregate finding for the unit and pass it through the guard."""
    rule = RULES[rule_id]
    accused = sorted(set(unit["entity_ids"]) | set(unit["related"]))
    if not accused:
        return None
    evidence = _gather_evidence(unit, ds, accused, rule)
    if not evidence:
        return None
    finding = {
        "scheme_type": scheme_type,
        "accused": accused,
        "rule": rule.legal,
        "amount_mxn": rule.recompute_amount({"accused": accused}, ds),
        "evidence": evidence,
        "narrative": _scheme_narrative(unit, scheme_type, rule, ds),
    }
    clean, _reasons = guard(finding, ds)
    return clean


# --- not-pursued reasons ----------------------------------------------------
# (#69) A weak lead is cleared only when the records support the innocent
# explanation; otherwise the reason is an honest "unverified".


def _drop_reason(dossier: dict, ds: Dataset) -> tuple[str, bool, list[str]]:
    """Why this entity was not pursued, from checks that cite records (#69).

    For each detector on the dossier, :func:`agent.clear.clear_reason` returns a
    grounded innocent explanation when the records support it and ``None`` when
    it cannot be confirmed. Returns ``(reason, verified, unverified_dets)`` —
    ``verified`` is False exactly when at least one detector fired and the
    innocent explanation could not be confirmed, which becomes an honest
    "unverified: ..." reason; ``unverified_dets`` is the list of detectors
    that returned ``None`` (used by #70's escalation prompt).
    """
    eid = str(dossier.get("entity_id") or "")
    dets = sorted(set(dossier.get("detectors", [])))
    reasons: list[str] = []
    unverified: list[str] = []
    for det in dets:
        r = clear_reason(det, eid, dossier.get("leads", {}).get(det, []) or [], ds)
        if r is None:
            unverified.append(det)
        elif r and r not in reasons:
            reasons.append(r)
    if unverified:
        reason = (
            f"unverified: {', '.join(unverified)} fired and the innocent explanation "
            "could not be confirmed from the records; needs a human or a deeper investigation"
        )
        return reason, False, unverified
    if not reasons:
        return "no corroborating scheme signature matched", True, []
    return "; ".join(reasons), True, []


def _build_not_pursued(
    dossiers: list[dict],
    ds: Dataset,
    findings: list[dict],
    dropped: dict[str, str],
    parked: dict[str, str] | None = None,
    challenged: dict[str, str] | None = None,
) -> list[dict]:
    """Why the remaining leads were not pursued, in the case-file contract.

    ``parked`` (#70) comes first — an ``other`` finding the guard accepted is
    recorded as a "suspicious, unproven" entry, never an accusation. Then
    ``challenged`` (#91) — a finding the adversarial review killed, closed by the
    challenger with the argument that destroyed it. Then ``dropped`` (the
    per-unit reason the loop already decided), then the per-dossier grounded
    ``_drop_reason``. Every parked/challenged entry carries ``closed_by`` so
    #88/#94 can export it exactly as the judges' schema wants.
    """
    parked = parked or {}
    challenged = challenged or {}
    accused: set[str] = set()
    for f in findings:
        accused.update(f.get("accused", []))
    out: list[dict] = []
    for d in dossiers:
        eid = str(d["entity_id"])
        if eid in accused:
            continue
        if eid in challenged:
            # A killed finding's entity is not accused in a surviving finding,
            # so it is a declined lead closed by the challenger (#91). An entity
            # caught by both a killed and a surviving finding stays accused only
            # in the surviving one (the ``accused`` check above already skipped it).
            out.append({"entity": eid, "reason": challenged[eid], "closed_by": "challenger"})
            continue
        if eid in parked:
            out.append({"entity": eid, "reason": parked[eid], "closed_by": "investigator"})
            continue
        reason = dropped.get(eid)
        if reason is None:
            reason, _verified, _dets = _drop_reason(d, ds)
        out.append({"entity": eid, "reason": reason})
    out.sort(key=lambda x: x["entity"])
    return out


# --- tool execution ---------------------------------------------------------
def _run_data_tool(tools: Tools, name: str, args: dict) -> Any:
    fn = getattr(tools, name, None)
    if fn is None:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(**args)
    except TypeError:
        return {"error": f"bad arguments for {name}: {args}"}


def _summarize(result: Any, ds: Dataset) -> tuple[int, str, list[str], list]:
    record_ids = ds.all_record_ids()
    if isinstance(result, list):
        rows = result
        n_rows = len(rows)
    elif isinstance(result, dict) and "error" in result:
        rows = [result]
        n_rows = 0
    elif isinstance(result, dict):
        rows = [result] if result else []
        n_rows = 1 if result else 0
    else:
        rows = []
        n_rows = 0

    ids: list[str] = []
    for r in rows[:50]:
        if isinstance(r, dict):
            for v in r.values():
                if isinstance(v, str) and v in record_ids:
                    ids.append(v)
    ids = list(dict.fromkeys(ids))[:50]
    return n_rows, f"{n_rows} rows", ids, rows[:5]


def _llm_finding_payload(finding: dict) -> dict:
    return {
        "scheme_type": finding.get("scheme_type"),
        "accused": finding.get("accused", []),
        "rule": finding.get("rule"),
        "amount_mxn": finding.get("amount_mxn"),
        "evidence": finding.get("evidence", []),
        "narrative": finding.get("narrative", ""),
    }


# --- prompts ----------------------------------------------------------------
def _system_prompt() -> str:
    lines = [
        "You are a forensic auditor examining a Mexican company's books for invoice fraud.",
        "Your job is to decide, per lead, whether to record an accusation or drop the lead.",
        "An accusation needs all three: a rule from the catalog below, a peso amount, and evidence",
        "record IDs that exist in the dataset. Never accuse someone you cannot back with those.",
        "",
        "Scheme types: " + ", ".join(sorted(SCHEME_TYPES)),
        "Rules:",
    ]
    for rid in sorted(RULES):
        rule = RULES[rid]
        lines.append(f"  {rid} [{', '.join(sorted(rule.scheme_types))}]: {rule.legal}")
    lines += [
        "",
        "Case-file contract: findings[] = {scheme_type, accused[entity ids], rule, amount_mxn, evidence[record ids]}.",
        "The amount must be the FULL scheme total (the sum over every entity in the scheme),",
        "not a single entity's subtotal. Evidence must be record IDs (invoice UUIDs, TX*, CP*, GR*)",
        "belonging to the accused entities.",
        "",
        "Use the data tools to gather proof. When confident, call record_finding with the full scheme",
        "aggregate; otherwise call drop_lead with a clear, non-technical reason.",
    ]
    return "\n".join(lines)


def _unit_prompt(unit: dict) -> str:
    lines = [
        f"Scheme hint: {unit['scheme_hint'] or 'none'}",
        f"Entities in this scheme: {', '.join(unit['entity_ids'])}",
    ]
    if unit["related"]:
        lines.append(f"Related counterparties: {', '.join(unit['related'])}")
    lines.append(f"Money moved through these counterparties: MXN {unit['total_mxn']:,.2f}")
    lines.append("Leads:")
    for eid, det_leads in unit["leads"].items():
        for det, rows in det_leads.items():
            for row in rows[:12]:
                lines.append(f"  {eid} [{det}] {json.dumps(row, ensure_ascii=False)}")
    return "\n".join(lines)


def _build_messages(unit: dict) -> list[dict]:
    return [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": _unit_prompt(unit)},
    ]


# --- terminal tool schemas --------------------------------------------------
def _schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


RECORD_FINDING_SCHEMA = _schema(
    "record_finding",
    "Record an accusation. scheme_type must be one of the legal types; accused are entity IDs; "
    "rule is a rule id (R1-R5) or its legal string; amount_mxn is the full scheme total; "
    "evidence are record IDs belonging to the accused; narrative is a short justification.",
    {
        "scheme_type": {"type": "string"},
        "accused": {"type": "array", "items": {"type": "string"}},
        "rule": {"type": "string"},
        "amount_mxn": {"type": "number"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "narrative": {"type": "string"},
    },
    ["scheme_type", "accused", "rule", "amount_mxn", "evidence"],
)

DROP_LEAD_SCHEMA = _schema(
    "drop_lead",
    "Drop a lead: you could not prove an accusation (state why).",
    {"entity_id": {"type": "string"}, "reason": {"type": "string"}},
    ["entity_id", "reason"],
)

TERMINAL_TOOLS = [RECORD_FINDING_SCHEMA, DROP_LEAD_SCHEMA]


# --- the two execution paths -------------------------------------------------
def _fallback_loop(
    ds: Dataset, units: list[dict], rec: _Log, max_leads: int
) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """Deterministic no-LLM path: scheme signatures -> findings via the guard."""
    findings: list[dict] = []
    dropped: dict[str, str] = {}
    for unit in units[:max_leads]:
        eid = unit["entity_id"]
        rec.emit(
            "lead",
            eid,
            {
                "entity_id": eid,
                "name": unit["name"],
                "rank": unit["rank"],
                "detectors": unit["detectors"],
                "n_detectors": unit["n_detectors"],
                "total_mxn": unit["total_mxn"],
                "leads": unit["lead_list"],
            },
        )
        hint = unit["scheme_hint"]
        if not hint:
            reason, verified, _dets = _drop_reason(unit["members"][0], ds)
            rec.emit("decision", eid, {"action": "drop_lead", "reason": reason, "verified": verified, "escalated": False})
            dropped[eid] = reason
            continue
        rule_id = SCHEME_TO_RULE.get(hint)
        if rule_id is None:
            reason, verified, _dets = _drop_reason(unit["members"][0], ds)
            rec.emit("decision", eid, {"action": "drop_lead", "reason": reason, "verified": verified})
            dropped[eid] = reason
            continue
        scheme_type = hint
        # The trace names the detectors that actually fired (the signature) so a
        # judge reading the log sees *why* this lead became a hypothesis (#95).
        det_names = unit["detectors"]
        rec.emit(
            "hypothesis",
            eid,
            {
                "text": f"Detectors {', '.join(det_names)} match the {scheme_type} signature; investigating.",
                "scheme_type": scheme_type,
            },
        )
        finding = _build_finding(unit, ds, scheme_type, rule_id)
        if finding is None:
            reason = "the aggregated scheme finding was rejected by the evidence guard"
            rec.emit("decision", eid, {"action": "drop_lead", "reason": reason})
            dropped[eid] = reason
            continue
        rec.emit(
            "decision",
            eid,
            {"action": "record_finding", "finding": _llm_finding_payload(finding), "source": "deterministic", "attempt": 1},
        )
        rec.emit(
            "guard",
            eid,
            {"accepted": True, "reasons": [], "finding": _llm_finding_payload(finding), "source": "deterministic", "attempt": 1},
        )
        findings.append(finding)
    return findings, dropped, {}


def _escalation_prompt(unverified_dets: list[str]) -> str:
    """The line appended to a weak lead's prompt when it is escalated (#70).

    The rule list is generated from ``RULES`` (SondreTH's note) so that R6/R7
    (arriving with #82/#83) are named automatically, and only the real rules
    (scheme types other than ``other``/R5) are listed for the model to claim.
    """
    rule_ids = ", ".join(sorted(rid for rid, r in RULES.items() if "other" not in r.scheme_types))
    dets = ", ".join(unverified_dets) or "the fired detectors"
    return (
        "No scheme signature matched. The automatic clearing check could not confirm an "
        f"innocent explanation for: {dets}. Investigate with the tools. Call record_finding "
        f"only if one of {rule_ids} is fully evidenced with record IDs and the full amount; call "
        "record_finding with scheme_type 'other' and rule 'R5' if something is wrong but it is "
        "none of those; otherwise call drop_lead with what you checked."
    )


def _park_finding(clean: dict, rec, parked: dict[str, str]) -> None:
    """Record an accepted ``other`` finding as a "suspicious, unproven" declined lead (#70).

    An ``other`` finding has no amount recomputation (R5), so it must never become
    an accusation; instead it enters ``not_pursued`` as a suspicious tier. One
    ``park_lead`` decision is emitted per accused entity, and the reason is stored
    in ``parked`` so ``_build_not_pursued`` can emit it with ``closed_by``.
    """
    narr = clean.get("narrative") or "the model flagged this entity"
    ev = [str(e) for e in clean.get("evidence", [])]
    ev_txt = ", ".join(ev[:5])
    if len(ev) > 5:
        ev_txt += f" and {len(ev) - 5} more"
    reason = f"suspicious, unproven: {narr}." + (f" Evidence: {ev_txt}" if ev_txt else "")
    for a in clean["accused"]:
        rec.emit("decision", a, {"action": "park_lead", "tier": "suspicious", "entity_id": a, "reason": reason})
        parked[str(a)] = reason


def _challenge_findings(
    findings: list[dict], ds: Dataset, rec: _Log | None
) -> tuple[list[dict], dict[str, str]]:
    """Run the adversarial review (#91) on every accepted finding.

    For each finding, ``:func:`agent.challenge.challenge``` returns the
    arguments a defender would raise plus a verdict. The finding keeps its
    challenge result (``challenge`` and the possibly-downgraded ``confidence``).
    A ``killed`` finding leaves the findings list and becomes a declined lead
    closed by the challenger, with the argument that destroyed it as the reason.
    A ``weakened`` finding stays but its confidence is downgraded to ``probable``.
    A ``challenge`` step-log entry is emitted per finding (run-level, so the
    per-entity adjacency in :func:`agent.steplog.validate_entries` is unaffected).
    Deterministic, pure pandas; ``rec`` may be ``None`` (replay never writes a log).
    """
    kept: list[dict] = []
    challenged: dict[str, str] = {}
    for f in findings:
        result = _challenge(f, ds)
        f["challenge"] = {
            "arguments": result["arguments"],
            "verdict": result["verdict"],
            "confidence": result["confidence"],
        }
        if result["confidence"] == "probable" and f.get("confidence") != "probable":
            f["confidence"] = "probable"
        if rec is not None:
            rec.emit(
                "challenge",
                "",
                {
                    "scheme_type": str(f.get("scheme_type", "")),
                    "verdict": result["verdict"],
                    "confidence": result["confidence"],
                    "arguments": result["arguments"],
                },
            )
        if result["verdict"] == "killed":
            kill_claims = [a["claim"] for a in result["arguments"] if a["outcome"] == "killed"]
            kill_records = [str(r) for a in result["arguments"] for r in a.get("records", [])]
            reason = "challenged and killed: " + "; ".join(kill_claims)
            if kill_records:
                reason += " [" + ", ".join(kill_records[:5]) + "]"
            for a in f.get("accused", []):
                challenged[str(a)] = reason
        else:
            kept.append(f)
    return kept, challenged


def _llm_loop(
    ds: Dataset,
    units: list[dict],
    llm: Any,
    rec: _Log,
    max_leads: int,
    max_steps: int,
    max_escalations: int,
    workers: int = 1,
) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """Run the model investigation per unit and return ``(findings, dropped, parked)``.

    #71: units are investigated concurrently. A signature unit is investigated as
    usual; a rejected ``record_finding`` is fed back and, past the retry budget, the
    deterministic finding is used (#66). A weak lead (no scheme signature) has three
    outcomes (#70): *cleared* (the records confirm an innocent explanation and it is
    dropped, ``escalated: false``), *escalated* (unverified, and the first
    ``max_escalations`` in rank order are investigated by the model so an unplanned
    scheme can still be found), or *unverified* (dropped past the cap). An accepted
    ``other`` finding is parked, not accused.

    The escalation cap is decided *before* any worker starts (the first N unverified
    weak units in rank order), so it is not a race. Each unit's plan is computed
    deterministically, then the units run on a ``ThreadPoolExecutor(max_workers=
    workers)`` when ``workers > 1``; results are merged in unit rank order (so
    ``findings`` / ``not_pursued`` are deterministic regardless of completion order).
    ``workers=1`` runs the units sequentially and reproduces the pre-#71 log exactly.
    """
    tools = Tools(ds)
    all_tools = TOOL_SCHEMAS + TERMINAL_TOOLS
    selected = units[:max_leads]

    # Decide each unit's plan before submission (#70's escalation cap is not a race).
    plans: list[dict] = []
    escalated_count = 0  # weak leads already escalated this run
    for unit in selected:
        if unit["scheme_hint"]:
            plans.append({"action": "investigate"})
            continue
        reason, verified, unverified_dets = _drop_reason(unit["members"][0], ds)
        if verified:
            plans.append({"action": "clear", "reason": reason})
        elif escalated_count < max_escalations:
            escalated_count += 1
            plans.append({"action": "escalate", "unverified_dets": unverified_dets})
        else:
            plans.append({"action": "unverified", "reason": reason})

    def _run(unit: dict, plan: dict):
        return _investigate_unit(unit, ds, llm, rec, tools, max_steps, plan, all_tools)

    if workers <= 1:
        results = [_run(u, p) for u, p in zip(selected, plans)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_run, u, p) for u, p in zip(selected, plans)]
            results = [f.result() for f in futures]

    findings: list[dict] = []
    dropped: dict[str, str] = {}
    parked: dict[str, str] = {}
    for new_findings, new_dropped, new_parked in results:
        findings.extend(new_findings)
        dropped.update(new_dropped)
        parked.update(new_parked)
    return findings, dropped, parked


def _investigate_unit(
    unit: dict,
    ds: Dataset,
    llm: Any,
    rec: _Log,
    tools: "Tools",
    max_steps: int,
    plan: dict,
    all_tools: list,
) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """Investigate one unit; return ``(new_findings, new_dropped, new_parked)``.

    All of a unit's conversation and ``rec.emit`` calls happen here. The only shared
    state is ``rec`` (thread-safe via :class:`_Log`) and the read-only ``tools`` /
    ``llm`` / ``ds``. ``plan`` is decided before submission in :func:`_llm_loop`. One
    of::

        {"action": "investigate"}                     # signature unit -> model
        {"action": "clear", "reason": <str>}          # weak, records clear it
        {"action": "escalate", "unverified_dets": [...]}  # weak, within the cap
        {"action": "unverified", "reason": <str>}     # weak, past the cap
    """
    eid = unit["entity_id"]
    rec.emit(
        "lead",
        eid,
        {
            "entity_id": eid,
            "name": unit["name"],
            "rank": unit["rank"],
            "detectors": unit["detectors"],
            "n_detectors": unit["n_detectors"],
            "total_mxn": unit["total_mxn"],
            "leads": unit["lead_list"],
        },
    )
    hint = unit["scheme_hint"]
    action = plan["action"]

    if action == "clear":
        rec.emit("decision", eid, {"action": "drop_lead", "reason": plan["reason"], "verified": True, "escalated": False})
        return [], {eid: plan["reason"]}, {}
    if action == "unverified":
        rec.emit("decision", eid, {"action": "drop_lead", "reason": plan["reason"], "verified": False, "escalated": False})
        return [], {eid: plan["reason"]}, {}

    escalated = action == "escalate"
    unverified_dets = plan.get("unverified_dets") or []

    messages = _build_messages(unit)
    if escalated:
        # The model investigates an unverified weak lead with an extra line naming
        # what the automatic check could not clear and when to call record_finding
        # vs. drop_lead.
        u = messages[1]
        messages[1] = {"role": "user", "content": u["content"] + "\n" + _escalation_prompt(unverified_dets)}
    first = True
    steps = 0
    terminal = False
    llm_outcome = ""  # "accepted" | "rejected" | "dropped" | "no_terminal" | "max_steps"
    llm_reason = ""  # model's drop reason / last guard reasons / model text
    rf_attempts = 0  # 1-based count of record_finding calls for this unit
    rejections = 0  # count of record_finding calls rejected by the guard
    accepted: dict | None = None
    new_parked: dict[str, str] = {}

    while not terminal and steps < max_steps:
        # generous completion budget: reasoning models burn tokens on
        # reasoning_content first, and a truncated record_finding call loses
        # scheme_type/rule and gets rejected by the guard
        reply = llm.chat(messages, tools=all_tools, tool_choice="auto", max_tokens=8192, role="investigator")
        if first:
            rec.emit(
                "hypothesis",
                eid,
                {
                    "text": reply.text or (f"{hint} suspected." if hint else "weak lead escalated to the model; investigating."),
                    "scheme_type": hint or "unconfirmed",
                    "derived_from": unit["detectors"],
                },
            )
            first = False
        messages.append(assistant_message(reply))
        steps += 1

        if not reply.tool_calls:
            # The model replied with text and no terminal tool call.
            llm_outcome = "no_terminal"
            llm_reason = (reply.text or "").strip() or "no terminal tool call"
            terminal = True
            break

        for tc in reply.tool_calls:
            if tc.name in _DATA_TOOL_NAMES:
                result = _run_data_tool(tools, tc.name, tc.args)
                n_rows, summary, ids, rows = _summarize(result, ds)
                rec.emit("tool_call", eid, {"name": tc.name, "args": tc.args})
                rec.emit(
                    "tool_result",
                    eid,
                    {"name": tc.name, "n_rows": n_rows, "summary": summary, "ids": ids, "rows": rows},
                )
                messages.append(tool_message(tc, result))
            elif tc.name == "record_finding":
                finding = dict(tc.args)
                rf_attempts += 1
                rec.emit(
                    "decision",
                    eid,
                    {"action": "record_finding", "finding": finding, "source": "llm", "attempt": rf_attempts, "escalated": escalated},
                )
                clean, reasons = guard(finding, ds)
                rec.emit(
                    "guard",
                    eid,
                    {
                        "accepted": clean is not None,
                        "reasons": reasons,
                        "finding": _llm_finding_payload(clean) if clean else finding,
                        "source": "llm",
                        "attempt": rf_attempts,
                        "escalated": escalated,
                    },
                )
                if clean is not None:
                    if clean["scheme_type"] == "other":
                        # An `other` finding has no amount recomputation, so it is
                        # parked as suspicious, never an accusation (#70).
                        _park_finding(clean, rec, new_parked)
                        llm_outcome = "parked"
                        terminal = True
                        break
                    accepted = clean
                    llm_outcome = "accepted"
                    terminal = True
                    break
                # Rejected: keep going. Feed the guard's reasons back as a tool
                # message so the model can fix the finding and retry, and still
                # execute any sibling data-tool calls in the reply.
                rejections += 1
                llm_reason = "; ".join(reasons) if reasons else "finding rejected by the evidence guard"
                messages.append(
                    tool_message(
                        tc,
                        {
                            "accepted": False,
                            "reasons": reasons,
                            "hint": "Fix the finding using these reasons and call record_finding again, or call drop_lead.",
                        },
                    )
                )
                if rejections > MAX_GUARD_RETRIES:
                    llm_outcome = "rejected"
                    terminal = True
                    break
            elif tc.name == "drop_lead":
                reason = str(tc.args.get("reason", "dropped"))
                rec.emit("decision", eid, {"action": "drop_lead", "reason": reason, "escalated": escalated})
                llm_outcome = "dropped"
                llm_reason = reason
                terminal = True
                break

    if not terminal and steps >= max_steps:
        llm_outcome = "max_steps"
        llm_reason = f"reached {max_steps} tool calls without a terminal decision"

    if accepted is not None:
        return [accepted], {}, {}

    # An escalated weak lead gets no deterministic fallback (#70): the model either
    # proved a scheme, parked an `other`, or we drop it here.
    if escalated:
        if llm_outcome == "parked":
            return [], {}, new_parked
        dets = ", ".join(unverified_dets) or "unknown detectors"
        if llm_outcome == "rejected":
            final_reason = f"unverified: {dets} (model: {llm_reason or 'no narrative'})"
            rec.emit("decision", eid, {"action": "drop_lead", "reason": final_reason, "escalated": True})
            return [], {eid: final_reason}, {}
        if llm_outcome == "dropped":
            # the drop_lead decision was already emitted with the model reason
            return [], {eid: llm_reason}, {}
        # no_terminal / max_steps: no terminal decision was emitted yet
        final_reason = llm_reason or f"unverified: {dets}"
        rec.emit("decision", eid, {"action": "drop_lead", "reason": final_reason, "escalated": True})
        return [], {eid: final_reason}, {}

    # A signature unit whose LLM path ended without an accepted finding gets the
    # deterministic finding, so LLM and --no-llm agree on the four known schemes.
    # The model's own terminal decision (drop_lead) and its reasons are preserved in
    # the log; the fallback is labelled as such.
    rule_id = SCHEME_TO_RULE.get(hint)
    if rule_id is not None:
        scheme_type = hint
        finding = _build_finding(unit, ds, scheme_type, rule_id)
        if finding is None:
            reason = "the aggregated scheme finding was rejected by the evidence guard"
            rec.emit("decision", eid, {"action": "drop_lead", "reason": reason, "llm_reason": llm_reason})
            return [], {eid: reason}, {}
        rec.emit(
            "decision",
            eid,
            {
                "action": "record_finding",
                "finding": _llm_finding_payload(finding),
                "source": "deterministic_fallback",
                "llm_outcome": llm_outcome,
                "llm_reason": llm_reason,
            },
        )
        rec.emit(
            "guard",
            eid,
            {"accepted": True, "reasons": [], "finding": _llm_finding_payload(finding), "source": "deterministic_fallback"},
        )
        return [finding], {}, {}

    # Keep a safe drop for a hint that is not in SCHEME_TO_RULE (an unplanned scheme
    # the model found but no rule covers); known signatures all map to a rule.
    reason, verified, _dets = _drop_reason(unit["members"][0], ds)
    rec.emit("decision", eid, {"action": "drop_lead", "reason": reason, "verified": verified})
    return [], {eid: reason}, {}


# --- entry points -----------------------------------------------------------
def _make_llm() -> LLM | None:
    s = settings()
    if s is None:
        return None
    return LLM(s)


def _compute_run_metadata(use_llm: bool, llm: Any, wall: float) -> dict:
    """#89: the run-metadata block written to the case file and the step log.

    ``prompt_tokens`` / ``completion_tokens`` / ``cost_by_role`` count only
    *uncached* calls (a cached call cost 0), so ``mxn_cost`` is exactly the token
    counts times the reference rate (config, .env-overridable) divided by 1000.
    ``--no-llm`` reports zero calls and zero cost; ``deterministic`` is true in
    no-LLM mode, and in LLM mode only when every call came from the cache.
    """
    if use_llm and llm is not None and hasattr(llm, "stats"):
        stats = llm.stats()
        llm_calls = stats["calls"]
        cached_calls = stats["cached_calls"]
        prompt_tokens = stats["prompt_tokens"]
        completion_tokens = stats["completion_tokens"]
        by_role = stats["by_role"]
    else:
        llm_calls = 0
        cached_calls = 0
        prompt_tokens = 0
        completion_tokens = 0
        by_role = {}

    s = settings()
    p_rate = s.mxn_per_1k_prompt if s is not None else MXN_PER_1K_PROMPT_TOKENS
    c_rate = s.mxn_per_1k_completion if s is not None else MXN_PER_1K_COMPLETION_TOKENS

    def _cost(p: int, c: int) -> float:
        return (p * p_rate + c * c_rate) / 1000.0

    mxn_cost = _cost(prompt_tokens, completion_tokens)
    cost_by_role = {role: _cost(r["prompt_tokens"], r["completion_tokens"]) for role, r in by_role.items()}

    if not use_llm:
        deterministic = True
        note = ""
    elif llm_calls > 0 and cached_calls == llm_calls:
        deterministic = True
        note = "replay from cache is deterministic"
    else:
        deterministic = False
        note = ""

    return {
        "llm_calls": llm_calls,
        "cached_calls": cached_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "mxn_cost": mxn_cost,
        "cost_by_role": cost_by_role,
        "wall_clock_seconds": wall,
        "deterministic": deterministic,
        "deterministic_note": note,
    }


def _artifact_path(requested: str | None, out: str | None, default_name: str) -> str:
    """Where a run's extra artifact goes: as asked, else next to the case file. "" disables it."""
    if requested == "":
        return ""
    if requested:
        return requested
    return str(Path(out).with_name(default_name)) if out else ""


def run(
    dataset_dir: str | Path,
    *,
    out: str | None = "case_file.json",
    log: str | None = None,
    no_llm: bool = False,
    max_leads: int = 12,
    max_steps: int = 12,
    max_escalations: int = 4,
    workers: int = 4,
    llm: Any = None,
    submission: str | None = None,
    report: str | None = None,
    seed: int | None = None,
) -> dict:
    """Run the investigation; returns the case-file dict after writing it and the log.

    ``submission`` writes the judges' ``submission.json`` (#88) next to the case file and
    ``report`` the five-section ``report.html`` (#90); pass ``""`` to skip either. Both are
    built from the case file, the estate and the step log, so the three artifacts of a run
    can never disagree with each other.
    """
    ds = load(dataset_dir)
    effective_llm = llm
    if effective_llm is None and not no_llm:
        effective_llm = _make_llm()
    use_llm = effective_llm is not None and not no_llm
    mode = "llm" if use_llm else "no-llm"
    model = ""
    if effective_llm is not None:
        _s = getattr(effective_llm, "settings", None)
        model = _s.model if _s is not None else ""

    dossiers = aggregate(ds, run_all(ds))
    units = _build_units(dossiers)
    log_path = log or f"runs/{_log_timestamp()}.jsonl"

    rec = _Log(log_path)
    try:
        rec.emit(
            "run_start",
            "",
            {"dataset": str(dataset_dir), "n_leads": len(dossiers), "mode": mode, "model": model, "workers": workers},
        )
        t0 = time.time()

        if use_llm and effective_llm is not None:
            findings, dropped, parked = _llm_loop(ds, units, effective_llm, rec, max_leads, max_steps, max_escalations, workers)
        else:
            findings, dropped, parked = _fallback_loop(ds, units, rec, max_leads)

        findings.sort(key=lambda f: (f["scheme_type"], f["accused"]))
        # #91: attack every finding before it is printed. A killed finding leaves
        # the list and becomes a declined lead closed by the challenger.
        findings, challenged = _challenge_findings(findings, ds, rec)
        not_pursued = _build_not_pursued(dossiers, ds, findings, dropped, parked, challenged)
        case: dict = {"findings": findings, "not_pursued": not_pursued}

        errors = validate_case_file(case, ds)
        if errors:
            raise RuntimeError("case file failed the contract: " + "; ".join(errors))

        wall = round(time.time() - t0, 3)
        run_metadata = _compute_run_metadata(use_llm, effective_llm, wall)
        # #93: the case file records the path of the log that produced it, so a
        # later ``--replay`` can be invoked with the case file alone.
        run_metadata["log"] = log_path
        # The artifact paths are known before they are written, so the log's last line can
        # tell a reader (and the API's event stream) where every output of this run landed.
        submission_path = _artifact_path(submission, out, "submission.json")
        report_path = _artifact_path(report, out, "report.html")
        case["run_metadata"] = run_metadata
        rec.emit(
            "run_end",
            "",
            {
                "n_findings": len(findings),
                "n_not_pursued": len(not_pursued),
                "wall_s": wall,
                "llm_calls": run_metadata["llm_calls"],
                "cached_calls": run_metadata["cached_calls"],
                "prompt_tokens": run_metadata["prompt_tokens"],
                "completion_tokens": run_metadata["completion_tokens"],
                "mxn_cost": run_metadata["mxn_cost"],
                "cost_by_role": run_metadata["cost_by_role"],
                "case_file": str(out),
                "report": report_path,
                "submission": submission_path,
                # #93: the full block, so ``--replay`` can rebuild the run's metadata
                # numbers offline (it is the source of truth for a replay).
                "run_metadata": run_metadata,
            },
        )

        _write_case_file(case, out)
        # rec.entries is the log this run just wrote, already parsed.
        meta = {"seed": seed} if seed is not None else {}
        built: dict | None = None
        if submission_path:
            built = write_submission(case, ds, submission_path, rec.entries, meta)
        if report_path:
            if built is None:
                built = build_submission(case, ds, rec.entries, meta)
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            Path(report_path).write_text(
                render_html(case, ds, submission=built, log=rec.entries), encoding="utf-8"
            )
        return case
    finally:
        rec.close()


def replay(
    source: str | Path,
    *,
    out: str | None = "case_file.json",
    submission: str | None = None,
    report: str | None = None,
    seed: int | None = None,
) -> dict:
    """Rebuild a case file (and submission/report) from a stored run's step log, offline.

    ``source`` is either a step-log ``.jsonl`` written by :func:`run`, or a case
    file ``.json`` whose ``run_metadata.log`` names that log — so ``--replay`` can
    be invoked with the case file alone. ``findings`` are taken from the log's
    *accepted* ``guard`` entries and re-validated through the evidence guard, so
    nothing is trusted blindly: a finding the guard now rejects (e.g. a tampered
    evidence id) is dropped, a warning line is printed, and the run still exits 0.
    ``not_pursued`` is rebuilt with the same deterministic machinery the run used.
    ``run_metadata`` copies the original numbers and adds ``replayed_from``.

    No ``LLM`` is ever constructed and no network is touched, so this works with
    Wi-Fi off and ``LLM_BASE_URL`` pointing at a dead port.
    """
    src = Path(source)
    original_meta: dict = {}
    if src.suffix == ".json":
        case_ref = json.loads(src.read_text(encoding="utf-8"))
        original_meta = dict(case_ref.get("run_metadata") or {})
        log_path = original_meta.get("log")
        if not log_path:
            raise ValueError(f"{src}: no run_metadata.log to replay")
    else:
        log_path = str(src)

    text = Path(log_path).read_text(encoding="utf-8")
    entries, complete = parse_lines(text)
    if not entries:
        raise ValueError(f"{log_path}: empty step log")
    if not complete:
        print(f"WARNING: {log_path}: last line was partial (run was interrupted)", file=sys.stderr)

    run_start = next((e for e in entries if e["kind"] == "run_start"), None)
    if run_start is None:
        raise ValueError(f"{log_path}: no run_start entry")
    dataset = (run_start.get("payload") or {}).get("dataset")
    if not dataset:
        raise ValueError(f"{log_path}: run_start has no dataset path")
    ds = load(dataset)

    # findings: accepted guard entries, re-validated through the guard.
    raw: list[dict] = []
    for e in entries:
        if e["kind"] != "guard":
            continue
        payload = e["payload"] or {}
        if payload.get("accepted") is not True:
            continue
        finding = payload.get("finding")
        if not isinstance(finding, dict) or not finding.get("scheme_type"):
            continue
        clean, reasons = guard(dict(finding), ds)
        if clean is not None:
            raw.append(clean)
        else:
            print(
                "WARNING: dropped a "
                f"{finding.get('scheme_type')!r} finding on replay: " + "; ".join(reasons),
                file=sys.stderr,
            )
    # Dedupe by (scheme_type, accused) — the run emits one accepted guard per unit.
    seen: set[tuple[str, tuple]] = set()
    findings: list[dict] = []
    for f in raw:
        key = (f["scheme_type"], tuple(f["accused"]))
        if key in seen:
            continue
        seen.add(key)
        findings.append(f)
    findings.sort(key=lambda f: (f["scheme_type"], f["accused"]))

    # dropped map from the log's drop_lead decisions (last one wins, matching the loop).
    dropped: dict[str, str] = {}
    for e in entries:
        if e["kind"] != "decision":
            continue
        payload = e["payload"] or {}
        if payload.get("action") != "drop_lead":
            continue
        eid = str(e.get("entity_id") or "")
        if eid:
            dropped[eid] = str(payload.get("reason") or "dropped")

    # parked map from the log's park_lead decisions (#70) — an `other` finding
    # the guard accepted, rebuilt as a "suspicious, unproven" not_pursued entry.
    parked: dict[str, str] = {}
    for e in entries:
        if e["kind"] != "decision":
            continue
        payload = e["payload"] or {}
        if payload.get("action") != "park_lead":
            continue
        pid = str(payload.get("entity_id") or e.get("entity_id") or "")
        if pid:
            parked[pid] = str(payload.get("reason") or "suspicious, unproven")

    dossiers = aggregate(ds, run_all(ds))
    # #91: apply the same adversarial review the run did, so a replayed case file
    # cannot resurrect a finding the challenger killed on the way out. Deterministic,
    # so run/replay agree; the original challenge results are recomputed and attached.
    findings, challenged = _challenge_findings(findings, ds, None)
    not_pursued = _build_not_pursued(dossiers, ds, findings, dropped, parked, challenged)
    case: dict = {"findings": findings, "not_pursued": not_pursued}

    errors = validate_case_file(case, ds)
    if errors:
        raise RuntimeError("replayed case file failed the contract: " + "; ".join(errors))

    # run_metadata: the original numbers, plus where it was replayed from.
    if not original_meta:
        run_end = next((e for e in entries if e["kind"] == "run_end"), None)
        run_end_payload = (run_end or {}).get("payload") or {}
        original_meta = dict(run_end_payload.get("run_metadata") or {})
    meta = dict(original_meta)
    meta["replayed_from"] = str(src)
    meta.setdefault("log", log_path)
    case["run_metadata"] = meta

    submission_path = _artifact_path(submission, out, "submission.json")
    report_path = _artifact_path(report, out, "report.html")
    _write_case_file(case, out)
    meta_for_sub = {"seed": seed} if seed is not None else {}
    built: dict | None = None
    if submission_path:
        built = write_submission(case, ds, submission_path, entries, meta_for_sub)
    if report_path:
        if built is None:
            built = build_submission(case, ds, entries, meta_for_sub)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(
            render_html(case, ds, submission=built, log=entries), encoding="utf-8"
        )
    return case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agent.investigate")
    parser.add_argument("dataset_dir", nargs="?", default=None,
                        help="dataset dir (not needed with --replay)")
    parser.add_argument("--out", default="case_file.json")
    parser.add_argument("--log", default=None)
    parser.add_argument("--max-leads", type=int, default=12)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--max-escalations", type=int, default=4,
                        help="how many weak leads (no scheme signature) the model may investigate (#70)")
    parser.add_argument("--workers", type=int, default=4,
                        help="investigate units concurrently (#71); workers=1 is byte-identical to sequential")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument(
        "--submission",
        default=None,
        help="path for the judges' submission.json (default: next to --out; \"\" to skip)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="path for the five-section report.html (default: next to --out; \"\" to skip)",
    )
    parser.add_argument("--seed", type=int, default=None, help="estate seed recorded in the submission")
    parser.add_argument(
        "--replay",
        default=None,
        help="rebuild a case file from a stored run's step log (.jsonl) or case file "
        "(.json) without the network; never constructs an LLM",
    )
    args = parser.parse_args(argv)
    if args.replay:
        case = replay(
            args.replay,
            out=args.out,
            submission=args.submission,
            report=args.report,
            seed=args.seed,
        )
    else:
        if not args.dataset_dir:
            parser.error("a dataset_dir is required unless --replay is given")
        case = run(
            args.dataset_dir,
            out=args.out,
            log=args.log,
            no_llm=args.no_llm,
            max_leads=args.max_leads,
            max_steps=args.max_steps,
            max_escalations=args.max_escalations,
            workers=args.workers,
            submission=args.submission,
            report=args.report,
            seed=args.seed,
        )
    print(json.dumps(case, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
