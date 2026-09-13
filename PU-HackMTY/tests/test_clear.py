"""Tests for agent/clear.py (#69): not_pursued reasons are grounded in the records.

Every ``clear_reason`` returns either a readable innocent explanation *with
record IDs* or ``None`` when the records cannot confirm it. These tests exercise
the per-detector checks on company_42, the strong-detector never-cleared rule,
the two defensive None paths, and the end-to-end guarantee that a decoy's
``not_pursued`` reason names a record.
"""
from __future__ import annotations

import re
from dataclasses import replace

from agent.clear import clear_reason


# --- per-detector checks on company_42 ---------------------------------------
def test_clear_new_vendor_s00009(ds):
    r = clear_reason("detect_new_vendor_round_amounts", "S00009", [], ds)
    assert r is not None
    assert "5 invoices" in r
    ids = set(ds.goods_receipts["receipt_id"].astype(str))
    gr_in_text = re.findall(r"GR\d+", r)
    assert len([g for g in gr_in_text if g in ids]) >= 3
    assert "JMK241214132" in r


def test_clear_name_twin_s00007(ds):
    r = clear_reason("detect_name_twin_69b", "S00007", [], ds)
    assert r is not None
    assert "SZC9707063JK" in r
    assert "TAO890114RLQ" in r


def test_clear_shared_address_s00026(ds):
    r = clear_reason("detect_shared_supplier_address", "S00026", [], ds)
    assert r is not None
    assert "S00024" in r
    assert "Garza Sada 337" in r


def test_clear_law_firm_s00036(ds):
    r = clear_reason("detect_fast_pay_no_deliverable", "S00036", [], ds)
    assert r is not None
    assert "809BD813-4F13-823B-51F4-A72499503858" in r
    assert "412/2025" in r
    assert "E00001" in r


def test_clear_cash_s00011(ds):
    r = clear_reason("detect_cash_payments", "S00011", [], ds)
    assert r is not None
    assert "1,821.72" in r
    assert "2,000" in r
    assert any(t.startswith("GR") for t in re.findall(r"GR\d+", r))


# --- strong detectors are never cleared -------------------------------------
def test_strong_detector_never_cleared(ds):
    assert clear_reason("detect_efos", "S00030", [], ds) is None
    assert clear_reason("detect_duplicate_payments", "S00017", [], ds) is None


# --- defensive None paths ------------------------------------------------------
def test_goods_category_without_receipt_is_none(ds):
    s00009_uuids = set(
        ds.invoices[
            (ds.invoices["tipo"] == "recibida")
            & (ds.invoices["counterparty_id"].astype(str) == "S00009")
        ]["uuid"].astype(str)
    )
    gr2 = ds.goods_receipts[~ds.goods_receipts["invoice_uuid"].astype(str).isin(s00009_uuids)].copy()
    ds2 = replace(ds, goods_receipts=gr2)
    assert clear_reason("detect_no_receipt", "S00009", [], ds2) is None
    assert clear_reason("detect_new_vendor_round_amounts", "S00009", [], ds2) is None


def test_shared_address_at_employee_home_is_none(ds):
    e = ds.employees[ds.employees["employee_id"].astype(str) == "E00002"].iloc[0]
    sup2 = ds.suppliers.copy()
    mask = sup2["supplier_id"].astype(str) == "S00026"
    sup2.loc[mask, "street"] = e["home_street"]
    sup2.loc[mask, "city"] = e["home_city"]
    ds2 = replace(ds, suppliers=sup2)
    assert clear_reason("detect_shared_supplier_address", "S00026", [], ds2) is None


# --- end-to-end: decoys carry a grounded reason -------------------------------
def _entity_tokens(ds):
    ids = set(ds.all_record_ids())
    rfcs = set(ds.suppliers["rfc"].astype(str))
    ents = (
        set(ds.suppliers["supplier_id"].astype(str))
        | set(ds.customers["customer_id"].astype(str))
        | set(ds.employees["employee_id"].astype(str))
    )
    return ids, rfcs, ents


def test_every_decoy_reason_cites_a_record(dataset_dir, ds, decoy_ids):
    from agent.investigate import run

    case = run(str(dataset_dir), out=None, log=None, no_llm=True)
    reasons = {e["entity"]: e["reason"] for e in case["not_pursued"]}
    assert decoy_ids <= set(reasons)
    ids, rfcs, ents = _entity_tokens(ds)
    for dec in decoy_ids:
        r = reasons[dec]
        assert not r.startswith("unverified:")
        assert any(x in r for x in ids) or any(x in r for x in rfcs) or any(x in r for x in ents)


def test_every_not_pursued_reason_is_grounded_or_unverified(dataset_dir, ds):
    from agent.investigate import run

    case = run(str(dataset_dir), out=None, log=None, no_llm=True)
    ids, rfcs, ents = _entity_tokens(ds)
    for e in case["not_pursued"]:
        r = e["reason"]
        assert r.startswith("unverified:") or any(x in r for x in ids) or any(x in r for x in rfcs) or any(x in r for x in ents)


def test_unknown_detector_is_none(ds):
    assert clear_reason("detect_does_not_exist", "S00009", [], ds) is None
