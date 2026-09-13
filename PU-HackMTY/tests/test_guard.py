"""Tests for the evidence guard (#14): agent/rules.py + agent/guard.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.data import load
from agent.guard import NARRATIVE_MAX, guard
from agent.rules import LEGAL_TO_ID, RULES, Rule

ROOT = Path(__file__).resolve().parents[1]
COMPANY_42 = ROOT / "data_estate" / "out" / "company_42"
EXAMPLE = json.loads(
    (ROOT / "data_estate" / "out" / "example_case_file_for_seed42.json").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def ds():
    return load(COMPANY_42)


def _ref_finding(ds, scheme_type: str) -> dict:
    """The matching finding from the reference case file."""
    for f in EXAMPLE["findings"]:
        if f["scheme_type"] == scheme_type:
            return f
    raise AssertionError(f"no reference finding for {scheme_type}")


# --- rule catalog -------------------------------------------------------------

def test_rule_catalog_has_r1_to_r7():
    assert set(RULES) == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}
    for rule in RULES.values():
        assert isinstance(rule, Rule)
        assert rule.id == rule.id
        assert rule.legal
        assert rule.scheme_types
        assert isinstance(rule.scheme_types, frozenset)


def test_rule_scheme_types_match_contract():
    assert RULES["R1"].scheme_types == frozenset({"efos_fake_supplier"})
    assert RULES["R2"].scheme_types == frozenset({"kickback_shell"})
    assert RULES["R3"].scheme_types == frozenset({"round_trip_sales"})
    assert RULES["R4"].scheme_types == frozenset({"duplicate_invoice_payment"})
    assert RULES["R5"].scheme_types == frozenset({"other"})
    assert RULES["R6"].scheme_types == frozenset({"threshold_splitting"})
    assert RULES["R7"].scheme_types == frozenset({"revenue_inflation"})


def test_rule_legal_strings_match_reference_file():
    for f in EXAMPLE["findings"]:
        rule_id = next(rid for rid, r in RULES.items() if f["scheme_type"] in r.scheme_types)
        assert RULES[rule_id].legal == f["rule"], f"{rule_id} legal != reference"


def test_every_legal_string_is_recognised():
    for rid, rule in RULES.items():
        assert LEGAL_TO_ID[rule.legal] == rid


# --- the reference case file's findings pass the guard ------------------------

REFERENCE_TYPES = ["efos_fake_supplier", "kickback_shell",
                   "round_trip_sales", "duplicate_invoice_payment"]


@pytest.mark.parametrize("scheme_type", REFERENCE_TYPES)
def test_reference_findings_pass_unchanged(ds, scheme_type):
    """Every reference finding survives, with its citation completed, never trimmed.

    Since #87 the guard adds the records the rule's amount rests on (``exhibit_policy``)
    so the claim reconciles against the counted table the way the judges compute it. The
    finding's own evidence is never dropped.
    """
    finding = _ref_finding(ds, scheme_type)
    clean, reasons = guard(finding, ds)
    assert clean is not None, f"{scheme_type} rejected: {reasons}"
    assert clean["scheme_type"] == finding["scheme_type"]
    assert clean["accused"] == finding["accused"]
    assert set(clean["evidence"]) >= set(finding["evidence"]), "evidence was dropped"
    assert abs(clean["amount_mxn"] - finding["amount_mxn"]) < 0.005
    assert clean["rule"] == finding["rule"]
    assert clean["confidence"] in ("proven", "probable")


@pytest.mark.parametrize("scheme_type", REFERENCE_TYPES)
def test_counted_exhibits_reconcile_within_two_percent(ds, scheme_type):
    """The judges' arithmetic: the counted table's exhibits sum to the claim within 2%."""
    from agent.reconcile import per_table_sums, reconciles
    from agent.rules import LEGAL_TO_ID, RULES

    finding = _ref_finding(ds, scheme_type)
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    rule = RULES[LEGAL_TO_ID[clean["rule"]]]
    sums = per_table_sums(clean["counted_exhibits"], ds)
    assert list(sums) == [rule.counted_table], f"{scheme_type}: counted set spans {sums}"
    assert reconciles(sums[rule.counted_table], clean["amount_mxn"])


# --- cleaning: narrative truncation + unknown keys -----------------------------

def test_narrative_truncated_and_unknown_field_stripped(ds):
    finding = _ref_finding(ds, "kickback_shell")
    finding = {**finding, "narrative": "x" * 2000, "foo": "bar"}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert len(clean["narrative"]) == 1000
    assert "foo" not in clean


# --- rejections ---------------------------------------------------------------

def test_fabricated_evidence_rejected(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "evidence": finding["evidence"] + ["TX99999"]}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("TX99999" in r for r in reasons)


def test_evidence_from_another_supplier_rejected(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")  # accuses S00030
    other_inv = str(
        ds.invoices[ds.invoices["counterparty_id"] == "S00009"]["uuid"].iloc[0]
    )  # a decoy supplier's invoice
    finding = {**finding, "evidence": [other_inv]}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("does not belong to any accused entity" in r for r in reasons)


def test_made_up_rule_rejected(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "rule": "made up"}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("not a recognised rule" in r for r in reasons)


def test_rule_scheme_mismatch_rejected(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "scheme_type": "kickback_shell", "rule": "R1"}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("not valid for scheme_type" in r for r in reasons)


def test_amount_outside_tolerance_rejected_with_both_numbers(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "amount_mxn": finding["amount_mxn"] * 3}
    clean, reasons = guard(finding, ds)
    assert clean is None
    # rejected naming the claim and what the cited exhibits actually add up to
    assert any(f"{finding['amount_mxn']:.2f}" in r for r in reasons)
    assert any("2,070,600.00" in r for r in reasons)


def test_ten_percent_off_is_rejected_at_the_judges_tolerance(ds):
    """2% is the judges' rule. A 10% error passed the old 25% tolerance; it must not now."""
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "amount_mxn": round(finding["amount_mxn"] * 1.10, 2)}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("does not reconcile" in r for r in reasons)


def test_one_percent_off_is_accepted(ds):
    """Inside the tolerance the finding stands; the guard is not stricter than the judges."""
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "amount_mxn": round(finding["amount_mxn"] * 1.01, 2)}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons


def test_amount_matching_the_wrong_table_is_rejected(ds):
    """A claim that reconciles against bank rows cannot stand under an invoice rule."""
    from agent.reconcile import per_table_sums

    finding = _ref_finding(ds, "duplicate_invoice_payment")
    clean, _ = guard(finding, ds)
    assert clean is not None
    invoices_total = per_table_sums(
        [e for e in clean["evidence"] if e not in clean["counted_exhibits"]], ds
    ).get("invoices")
    assert invoices_total, "expected the duplicate finding to cite invoices as well"
    # R4 counts bank_txns; claiming the invoice total instead must be refused.
    bad = {**finding, "amount_mxn": invoices_total, "auto_complete_exhibits": False}
    clean, reasons = guard(bad, ds)
    assert clean is None
    assert any("counts its money in" in r or "does not reconcile" in r for r in reasons)


# --- rule id and reference acceptance ------------------------------------------

def test_rule_id_accepted_and_rewritten_to_legal(ds):
    finding = _ref_finding(ds, "efos_fake_supplier")
    finding = {**finding, "rule": "R1"}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert clean["rule"] == RULES["R1"].legal


def test_reference_amounts_match_recompute(ds):
    """The guard's recomputation reproduces each reference amount (per 25% tol)."""
    for f in EXAMPLE["findings"]:
        rule_id = next(rid for rid, r in RULES.items() if f["scheme_type"] in r.scheme_types)
        recompute = RULES[rule_id].recompute_amount(f, ds)
        assert abs(f["amount_mxn"] - recompute) <= 0.25 * recompute, f"{rule_id} recompute"


# --- edge cases ----------------------------------------------------------------

def test_r5_other_no_amount_recompute(ds):
    inv = str(ds.invoices[ds.invoices["counterparty_id"] == "S00011"]["uuid"].iloc[0])
    finding = {
        "scheme_type": "other",
        "accused": ["S00011"],
        "rule": "R5",
        "amount_mxn": 1234.56,
        "evidence": [inv],
    }
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert clean["amount_mxn"] == 1234.56


def test_guard_never_raises_on_garbage(ds):
    for bad in (None, "x", 42, [], {"findings": []}):
        clean, reasons = guard(bad, ds)
        assert clean is None
        assert reasons


def test_duplicate_evidence_deduped(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    dup = finding["evidence"][0]
    finding = {**finding, "accused": finding["accused"] + finding["accused"][:1],
               "evidence": finding["evidence"] + [dup]}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert len(clean["accused"]) == len(set(clean["accused"]))
    assert len(clean["evidence"]) == len(set(clean["evidence"]))
    assert clean["evidence"].count(dup) == 1


# --- ledger refs are context, not evidence (#65) -----------------------------

def test_ledger_ids_moved_to_narrative(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    original_evidence = _ref_finding(ds, "duplicate_invoice_payment")["evidence"]
    finding = {**finding, "evidence": original_evidence + ["GL00652"]}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert reasons == []
    # The ledger id is set aside, never cited; the finding's own records all survive.
    assert "GL00652" not in clean["evidence"]
    assert set(clean["evidence"]) >= set(original_evidence)
    assert "GL00652" in clean["narrative"]
    assert "Ledger entries consulted" in clean["narrative"]


def test_only_ledger_ids_rejected(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    finding = {**finding, "evidence": ["GL00652"]}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert "only ledger entries" in reasons[0]


def test_ledger_ids_deduped_in_narrative(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    first_id = finding["evidence"][0]
    finding = {**finding, "evidence": [first_id, "GL00652", "GL00652"]}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert clean["narrative"].count("GL00652") == 1


def test_ledger_plus_fabricated_still_rejected(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    finding = {**finding, "evidence": finding["evidence"] + ["GL00652", "TX99999"]}
    clean, reasons = guard(finding, ds)
    assert clean is None
    assert any("TX99999" in r for r in reasons)


def test_narrative_truncated_after_ledger_append(ds):
    finding = _ref_finding(ds, "duplicate_invoice_payment")
    finding = {**finding, "narrative": "x" * 1000,
               "evidence": finding["evidence"] + ["GL00652"]}
    clean, reasons = guard(finding, ds)
    assert clean is not None, reasons
    assert len(clean["narrative"]) == NARRATIVE_MAX
