"""Tests for detect_revenue_inflation (issue #83).

Tests may read ``hidden/``; under ``agent/`` nothing may. Here the ground truth
comes from the generator's in-memory ``truth`` (a test may read it), not ``hidden/``.

The scheme is generated in the judges' format (``--format judges``) because the
judges' schema carries an ``invoices.status`` column, which is the only place a
``cancelado`` invoice is observable. The legacy CSV layout has no ``status``
column (#81 deliberately did not add one), so the cancelled-not-reversed tell is
only testable on a judges estate.
"""
from __future__ import annotations

import pytest

from agent.data import load
from agent.detectors.revenue_inflation import detect_revenue_inflation
from agent.guard import guard
from agent.rules import RULES
from data_estate.export_judges import write_judges_estate
from data_estate.generate import COMPANY, Generator


def _load_revenue_seed(tmp_path, seed=7):
    """Generate a judges-format seed with only the revenue scheme, write it, load it."""
    estate = Generator(seed).build(["revenue"])
    out = tmp_path / f"estate{seed}"
    write_judges_estate(estate, out, seed=seed, company=COMPANY)
    return estate, load(out / "estate.db")


def _scheme(estate, scheme_type):
    return next(s for s in estate.truth["schemes"] if s["type"] == scheme_type)


def _planted_customer(estate):
    return "RFC:" + _scheme(estate, "revenue_inflation")["entities"][0]["rfc"]


def test_finds_the_planted_customer(tmp_path):
    estate, ds = _load_revenue_seed(tmp_path)
    ent = _scheme(estate, "revenue_inflation")["entities"][0]
    result = detect_revenue_inflation(ds)
    assert result
    assert len(result) == 1
    r = result[0]
    assert r["entity_id"] == "RFC:" + ent["rfc"]
    # every planted sales invoice is on the lead
    assert set(r["invoice_uuids"]) >= set(ent["invoice_uuids"])
    # a fresh customer: nothing ever collected
    assert r["customer_history"] == 0
    # at least one cancelled-not-reversed invoice
    assert r["n_cancelled_not_reversed"] >= 1
    assert r["total_mxn"] == pytest.approx(
        _scheme(estate, "revenue_inflation")["amount_mxn"]
    )


def test_no_honest_customer_appears(tmp_path):
    estate, ds = _load_revenue_seed(tmp_path)
    result = detect_revenue_inflation(ds)
    # The only customer reported is the planted revenue one; honest customers
    # whose sales were all collected are not flagged.
    assert {r["entity_id"] for r in result} == {_planted_customer(estate)}


def test_large_grace_days_still_returns_cancelled_case(tmp_path):
    estate, ds = _load_revenue_seed(tmp_path)
    # grace_days=10_000 takes the whole window out of the "not collected and
    # recent" trigger; the cancelled-not-reversed case must survive on its own.
    result = detect_revenue_inflation(ds, grace_days=10_000)
    assert result
    assert {r["entity_id"] for r in result} == {_planted_customer(estate)}
    assert all(r["n_cancelled_not_reversed"] >= 1 for r in result)


def test_well_formed_and_sorted(tmp_path):
    estate, ds = _load_revenue_seed(tmp_path)
    result = detect_revenue_inflation(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert all(u in record_ids for u in r["invoice_uuids"])
        assert isinstance(r["n_invoices"], int)
        assert isinstance(r["customer_history"], int)
    assert result == sorted(result, key=lambda r: r["entity_id"])


def test_no_revenue_scheme_returns_empty(tmp_path):
    # A seed planted with a different scheme never reports a revenue customer.
    estate = Generator(8).build(["efos"])
    out = tmp_path / "estate8"
    write_judges_estate(estate, out, seed=8, company=COMPANY)
    ds = load(out / "estate.db")
    assert detect_revenue_inflation(ds) == []


def test_guard_accepts_revenue_finding(tmp_path):
    estate, ds = _load_revenue_seed(tmp_path)
    scheme = _scheme(estate, "revenue_inflation")
    cust = _planted_customer(estate)
    result = detect_revenue_inflation(ds)
    uuids = [u for r in result for u in r["evidence"]]
    finding = {
        "scheme_type": "revenue_inflation",
        "accused": [cust],
        "rule": "R7",
        "amount_mxn": scheme["amount_mxn"],
        "evidence": uuids,
    }
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert clean["scheme_type"] == "revenue_inflation"
    assert clean["accused"] == [cust]
    assert clean["amount_mxn"] == pytest.approx(scheme["amount_mxn"])
    assert clean["rule"] == RULES["R7"].legal
    assert clean["confidence"] in ("proven", "probable")
