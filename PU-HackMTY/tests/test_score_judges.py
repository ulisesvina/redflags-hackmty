"""data_estate/score.py on a judges' estate (#86): recall, false-accusation rate,
and the 2% peso reconciliation, against the frozen estate_42 (#80).

Tests may read ``hidden/``; nothing under ``agent/`` may. estate_42 is frozen, so
these assert against its committed ground truth.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_estate.score import score

ROOT = Path(__file__).resolve().parents[1]
ESTATE = ROOT / "data_estate" / "out" / "estate_42"

PHANTOM = "phantom_vendor"


def _truth() -> dict:
    return json.loads((ESTATE / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))


def _phantom() -> dict:
    return next(s for s in _truth()["schemes"] if s["type"] == PHANTOM)


def _exhibits(uuids: list[str]) -> list[dict]:
    return [
        {"exhibit_id": f"E{i}", "source_table": "invoices", "record_id": u, "note": "invoice"}
        for i, u in enumerate(uuids)
    ]


def _submission(findings: list[dict]) -> dict:
    return {
        "seed": 42,
        "findings": findings,
        "leads_not_pursued": [],
        "run_metadata": {"llm_calls": 3, "mxn_cost": 0.15, "wall_clock_seconds": 1.2},
    }


def _finding(entities: list[str], peso: float, uuids: list[str]) -> dict:
    return {
        "scheme_type": PHANTOM,
        "entities": entities,
        "narrative": "Invoices for consulting with no deliverables.",
        "rule_broken": "CFF Art. 69-B",
        "peso_amount": peso,
        "exhibits": _exhibits(uuids),
        "confidence": "proven",
    }


def test_phantom_vendor_recall_and_clean_rate():
    """Accusing the phantom vendor (1 of the 3 judges' schemes) gives recall 100/3,
    no false accusations, and a reconciling peso figure."""
    ph = _phantom()
    res = score(ESTATE, _submission([_finding([ph["entities"][0]], ph["peso_amount"], ph["supporting_invoices"])]))

    assert res["schemes_planted"] == 3
    assert res["schemes_found"] == 1
    assert res["recall_pct"] == pytest.approx(100 * 1 / 3)
    assert res["false_accusation_rate_pct"] == 0.0
    assert res["false_accusations"] == []
    assert res["decoys_accused"] == []
    assert res["peso_reconciles"] is True
    assert res["peso_actual"] == pytest.approx(ph["peso_amount"])
    assert res["decoys_planted"] == 5


def test_adding_a_decoy_doubles_the_rate():
    """Adding a decoy to the accused entities: 1 of 2 accused is a decoy -> rate 50."""
    ph = _phantom()
    decoy = _truth()["decoys"][0]["entity"]
    res = score(
        ESTATE,
        _submission([_finding([ph["entities"][0], decoy], ph["peso_amount"], ph["supporting_invoices"])]),
    )

    assert res["decoys_accused"] == [decoy]
    assert res["decoys_accused_count"] == 1
    assert res["false_accusation_rate_pct"] == pytest.approx(50.0)
    assert res["false_accusation_rate_pct"] == pytest.approx(100.0 * (0 + 1) / 2)


def test_exhibits_overstating_claim_fail_reconciliation():
    """A finding whose exhibits sum to 1.5x its peso_amount must not reconcile."""
    ph = _phantom()
    res = score(
        ESTATE,
        _submission([_finding([ph["entities"][0]], round(ph["peso_amount"] / 1.5, 2), ph["supporting_invoices"])]),
    )

    assert res["peso_reconciles"] is False
