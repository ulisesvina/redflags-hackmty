"""Tests for the tool layer (issue #12).

Tests may read hidden/ground_truth.json via the fixtures; the tools may not.
The whole point of the tool layer is that every number it returns traces back to
a record ID, so the model can cite it and the evidence guard can re-check it.
"""
from __future__ import annotations

import json

import pytest

from agent.data import load as _data_load
from agent.tools import TOOL_SCHEMAS, Tools

SCHEMA_NAMES = {
    "get_supplier", "get_customer", "get_employee", "get_invoices",
    "get_bank_txns", "get_receipts", "check_69b", "trace_flow", "query_ledger",
    "get_purchase_orders", "get_contracts",
}


@pytest.fixture()
def tools(ds):
    return Tools(ds)


# ---- get_supplier --------------------------------------------------------

def test_get_supplier_efos_listed_no_receipts(ds, scheme, tools):
    ent = scheme("efos_fake_supplier")["entities"][0]
    res = tools.get_supplier(ent["supplier_id"])
    assert res["efos"]["listed"] is True
    assert res["stats"]["n_with_receipt"] == 0
    assert res["stats"]["n_invoices"] == len(ent["invoice_uuids"])
    assert res["rfc"] == ent["rfc"]


def test_get_supplier_kickback_employee_links(ds, scheme, tools):
    ent = scheme("kickback_shell")["entities"][0]
    res = tools.get_supplier(ent["supplier_id"])
    kinds = {link["kind"] for link in res["employee_links"]}
    assert "address" in kinds
    assert "approver" in kinds
    # Both links point at the same insider (the buyer).
    emp = {link["employee_id"] for link in res["employee_links"]}
    assert ent["employee_id"] in emp


def test_get_supplier_unknown_id_errors(tools):
    res = tools.get_supplier("NOPE")
    assert "error" in res


def test_get_customer_and_employee(tools):
    cust = tools.get_customer("C00005")
    assert cust["customer_id"] == "C00005"
    assert "stats" in cust
    emp = tools.get_employee("E00002")
    assert emp["employee_id"] == "E00002"
    assert "linked_suppliers" in emp


# ---- check_69b -----------------------------------------------------------

def test_check_69b_name_twin_decoy(ds, truth, tools):
    # The decoy whose name is almost identical to a 69-B entry but RFC differs.
    twins = {
        d["supplier_id"]: d
        for d in truth["decoys"]
        if d["looks_like"].startswith("Name almost")
    }
    assert twins
    d2 = next(iter(twins.values()))
    res = tools.check_69b(d2["rfc"])
    assert res["listed"] is False
    assert res["name_matches"]  # lets the model SEE the trap
    # The match is by name-stem only; the RFCs differ.
    assert all(m["rfc"] != d2["rfc"] for m in res["name_matches"])


def test_check_69b_real_efos_listed(ds, scheme, tools):
    ent = scheme("efos_fake_supplier")["entities"][0]
    res = tools.check_69b(ent["rfc"])
    assert res["listed"] is True
    assert res["rfc"] == ent["rfc"]


# ---- trace_flow ----------------------------------------------------------

def test_trace_flow_round_trip_returns_to_company(ds, scheme, tools):
    ent = scheme("round_trip_sales")["entities"][0]
    supplier_id = ent["supplier_id"]
    clabe = ds.suppliers[ds.suppliers["supplier_id"] == supplier_id]["clabe"].iloc[0]
    hops = tools.trace_flow(clabe)
    assert any(h["returns_to_company"] for h in hops)
    # Each hop carries a real record ID and an ISO date.
    record_ids = ds.all_record_ids()
    for h in hops:
        assert h["record_id"] in record_ids
        assert h["fecha"]


def test_trace_flow_unknown_clabe_empty(tools):
    assert tools.trace_flow("NOPE") == []


# ---- duplicate invoice payment ------------------------------------------

def test_get_bank_txns_duplicate_invoice_two_rows(ds, scheme, tools):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    pay = ent["payments"][0]
    rows = tools.get_bank_txns(invoice_uuid=pay["invoice_uuid"])
    assert len(rows) == 2
    # The two txns are the original and the duplicate, and the duplicate went
    # to a CLABE that is not on the supplier master.
    got = {r["txn_id"] for r in rows}
    assert got == {pay["original_txn"], pay["duplicate_txn"]}
    dups = [r for r in rows if r["txn_id"] == pay["duplicate_txn"]]
    assert dups and dups[0]["counterparty_clabe"] == ent["alternate_clabe"]


def test_query_ledger_duplicate_to_expense(ds, scheme, tools):
    ent = scheme("duplicate_invoice_payment")["entities"][0]
    pay = ent["payments"][0]
    rows = tools.query_ledger(txn_id=pay["duplicate_txn"])
    assert rows
    assert any(r["account_code"] == "6000" for r in rows)
    # The original was booked to AP (2100).
    orig = tools.query_ledger(txn_id=pay["original_txn"])
    assert any(r["account_code"] == "2100" for r in orig)


# ---- receipts / invoices -------------------------------------------------

def test_get_receipts_present_and_absent(ds, scheme, tools):
    ent = scheme("efos_fake_supplier")["entities"][0]
    # EFOS invoices have no deliverable.
    for uuid in ent["invoice_uuids"]:
        assert tools.get_receipts(uuid) == []
    # A decoy supplier (real goods) has receipts on every invoice.
    rec = tools.get_invoices("S00007")
    assert rec
    for inv in rec:
        assert inv["uuid"] in ds.all_record_ids()
        if tools.get_receipts(inv["uuid"]):
            assert inv["has_receipt"] is True


# ---- limits / serialisation ---------------------------------------------

def test_results_json_dumpable_and_bounded(ds, scheme, tools):
    ent = scheme("round_trip_sales")["entities"][0]
    supplier_id = ent["supplier_id"]
    clabe = ds.suppliers[ds.suppliers["supplier_id"] == supplier_id]["clabe"].iloc[0]

    small = tools.get_invoices(supplier_id, limit=3)
    assert len(small) <= 3

    for result in [
        tools.get_supplier(supplier_id),
        tools.get_customer("C00005"),
        tools.get_employee("E00002"),
        small,
        tools.get_bank_txns(limit=5),
        tools.get_receipts(small[0]["uuid"]) if small else [],
        tools.check_69b("TAO890114RLQ"),
        tools.trace_flow(clabe),
        tools.query_ledger(limit=5),
    ]:
        assert json.dumps(result)


def test_unknown_id_returns_error_key(ds, tools):
    assert "error" in tools.get_supplier("NOPE")
    assert "error" in tools.get_customer("NOPE")
    assert "error" in tools.get_employee("NOPE")


# ---- schemas -------------------------------------------------------------

def test_tool_schema_names_match_methods(tools):
    methods = {m for m in dir(Tools) if not m.startswith("_")}
    assert methods >= SCHEMA_NAMES
    schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert schema_names == SCHEMA_NAMES


def test_tool_schemas_are_object_params():
    for s in TOOL_SCHEMAS:
        assert s["type"] == "function"
        assert s["function"]["parameters"]["type"] == "object"
        assert s["function"]["description"]


# ---- judge-estate aware tools (#85) ----------------------------------------

@pytest.fixture()
def judge_tools(judges_mini_dir):
    """tools over tests/fixtures/judges_mini, the judges' schema (RFC ids, PO/contracts)."""
    return Tools(_data_load(judges_mini_dir))


def test_judge_get_supplier_deliverable_trail(judge_tools):
    res = judge_tools.get_supplier("RFC:BBBB020202BB2")
    assert res["deliverable_trail"]["n_invoices"] == 1
    assert res["deliverable_trail"]["n_with_po"] == 1
    assert res["deliverable_trail"]["n_with_receipt"] == 1
    assert res["deliverable_trail"]["n_contracts"] == 1
    # a bare RFC resolves to the same supplier.
    assert judge_tools.get_supplier("BBBB020202BB2")["supplier_id"] == "RFC:BBBB020202BB2"


def test_judge_get_supplier_approvers(judge_tools):
    res = judge_tools.get_supplier("RFC:BBBB020202BB2")
    assert res["approvers"] == [
        {"employee_id": "EMP:0001", "role": "Gerente de Compras", "n_invoices": 1}
    ]
    # same-bank link lets the model SEE the same-bank-institution decoy.
    kinds = {link["kind"] for link in judge_tools.get_supplier("RFC:AAAA010101AA1")["employee_links"]}
    assert "same_bank" in kinds


def test_judge_get_contracts(judge_tools):
    rows = judge_tools.get_contracts("RFC:BBBB020202BB2")
    assert len(rows) == 1
    assert rows[0]["contract_id"] == "CTR-0001"
    assert rows[0]["vendor_id"] == "RFC:BBBB020202BB2"
    # a vendor with no contract is an empty list, not an error.
    assert judge_tools.get_contracts("RFC:AAAA010101AA1") == []


def test_judge_get_purchase_orders(judge_tools):
    rows = judge_tools.get_purchase_orders(invoice_uuid="INV-0002")
    assert len(rows) == 1
    assert rows[0]["po_id"] == "PO-0001"
    assert rows[0]["vendor_id"] == "RFC:BBBB020202BB2"
    # an invoice with no PO, and a vendor with no PO, both come back empty.
    assert judge_tools.get_purchase_orders(invoice_uuid="INV-0001") == []
    assert judge_tools.get_purchase_orders(vendor_id="RFC:AAAA010101AA1") == []
    assert judge_tools.get_purchase_orders(vendor_id="BBBB020202BB2")[0]["po_id"] == "PO-0001"


def test_judge_get_employee_bank_and_transfers(judge_tools):
    res = judge_tools.get_employee("EMP:0001")
    assert res["employee_id"] == "EMP:0001"
    assert res["bank_code"] == "000"
    assert res["n_transfers_received_from_vendors"] == 1
    # a bare employee id resolves too.
    assert judge_tools.get_employee("0001")["employee_id"] == "EMP:0001"
    assert judge_tools.get_employee("EMP:0002")["n_transfers_received_from_vendors"] == 0


def test_judge_get_invoices_extras(judge_tools):
    rows = judge_tools.get_invoices("RFC:BBBB020202BB2")
    assert len(rows) == 1
    inv = rows[0]
    assert inv["status"] == "vigente"
    assert inv["po_id"] == "PO-0001"
    assert inv["contract_id"] == "CTR-0001"
    assert inv["collected"] is False
    # the sale invoice is collected; a bare RFC also resolves.
    sale = judge_tools.get_invoices("CCCC030303CC3")
    assert sale and sale[0]["collected"] is True
    assert sale[0]["days_to_collect"] == 15
    assert sale[0]["contract_id"] == ""


def test_judge_trace_flow_source_table(judge_tools, judges_mini_dir):
    ds = _data_load(judges_mini_dir)
    clabe = ds.suppliers[ds.suppliers["rfc"] == "AAAA010101AA1"]["clabe"].iloc[0]
    hops = judge_tools.trace_flow(clabe)
    emp_hop = [h for h in hops if h["record_id"] == "BNK-0005"]
    assert emp_hop and emp_hop[0]["source_table"] == "bank_txns"
    assert emp_hop[0]["to_clabe"] == "000000000000000501"
    # every hop carries a real record id + its source table.
    for h in hops:
        assert h["record_id"] in ds.all_record_ids()
        assert h["source_table"]


def test_judge_trace_flow_company_legs(judge_tools, judges_mini_dir):
    ds = _data_load(judges_mini_dir)
    hops = judge_tools.trace_flow(ds.company["clabe"])
    recs = {h["record_id"] for h in hops}
    assert "BNK-0001" in recs and "BNK-0002" in recs
    assert all(h["source_table"] == "bank_txns" for h in hops)


def test_judge_legacy_tools_note(judges_mini_dir, tools):
    # On a legacy company_42 dataset, PO/contract tables do not exist.
    pos = tools.get_purchase_orders(invoice_uuid="anything")
    assert pos and pos[0]["note"] == "no purchase_orders table in this estate"
    cnts = tools.get_contracts("S00004")
    assert cnts and cnts[0]["note"] == "no contracts table in this estate"


def test_judge_results_json_dumpable(tools, judge_tools, ds):
    # both estates' results serialise.
    for res in [
        judge_tools.get_supplier("RFC:BBBB020202BB2"),
        judge_tools.get_employee("EMP:0001"),
        judge_tools.get_invoices("RFC:BBBB020202BB2"),
        judge_tools.get_purchase_orders(invoice_uuid="INV-0002"),
        judge_tools.get_contracts("RFC:BBBB020202BB2"),
        judge_tools.trace_flow(ds.suppliers[ds.suppliers["supplier_id"] == "S00004"]["clabe"].iloc[0]),
    ]:
        assert json.dumps(res)
    # legacy get_supplier still has all the fields the model relied on.
    legacy = tools.get_supplier("S00004")
    assert "deliverable_trail" in legacy and "approvers" in legacy
    assert json.dumps(legacy)
