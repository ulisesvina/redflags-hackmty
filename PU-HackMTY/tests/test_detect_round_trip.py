"""Tests for detect_round_trip (issue #9).

Tests may read hidden/ground_truth.json via the fixtures; the detector may not.
"""
from __future__ import annotations

import json

from agent.detectors.round_trip import detect_round_trip


def test_counts_match_ground_truth(ds, scheme):
    ent = scheme("round_trip_sales")["entities"][0]
    result = detect_round_trip(ds)
    assert len(result) == len(ent["legs"]) == 3


def test_legs_are_the_planted_chains(ds, scheme):
    ent = scheme("round_trip_sales")["entities"][0]
    result = detect_round_trip(ds)
    found = {(r["out_txn"], r["forward_record"], r["in_txn"]) for r in result}
    expected = {(leg["out_txn"], leg["forward_record"], leg["in_txn"]) for leg in ent["legs"]}
    assert found == expected


def test_row_fields_match_leg(ds, scheme):
    ent = scheme("round_trip_sales")["entities"][0]
    legs_by_key = {
        (leg["out_txn"], leg["forward_record"], leg["in_txn"]): leg for leg in ent["legs"]
    }
    result = detect_round_trip(ds)
    for r in result:
        leg = legs_by_key[(r["out_txn"], r["forward_record"], r["in_txn"])]
        assert r["purchase_invoice"] == leg["purchase_invoice"]
        assert r["sales_invoice"] == leg["sales_invoice"]
        assert r["entity_id"] == ent["supplier_id"]
        assert r["customer_id"] == ent["customer_id"]
        assert 0.8 <= r["amount_in"] / r["amount_forward"] <= 1.0
        assert 0 <= r["days_forward_to_in"] <= 14
        assert 0 <= r["days_out_to_forward"] <= 7


def test_iva_effect_0_90_finds_nothing(ds):
    # Documents the IVA effect so nobody "fixes" the threshold back to 0.90.
    assert detect_round_trip(ds, return_min_ratio=0.90) == []


def test_no_decoys(ds, decoy_ids):
    result = detect_round_trip(ds)
    assert all(r["entity_id"] not in decoy_ids for r in result)
    assert all(r["customer_id"] not in decoy_ids for r in result)


def test_well_formed_leads_and_serializable(ds):
    result = detect_round_trip(ds)
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    for r in result:
        assert r["entity_id"] in entity_ids
        assert r["customer_id"] in entity_ids
        assert r["out_txn"] in record_ids
        assert r["forward_record"] in record_ids
        assert r["in_txn"] in record_ids
        assert r["evidence"] and all(e in record_ids for e in r["evidence"])
        assert isinstance(r["amount_out"], float)
        assert isinstance(r["amount_forward"], float)
        assert isinstance(r["amount_in"], float)
        assert isinstance(r["days_out_to_forward"], int)
        assert isinstance(r["days_forward_to_in"], int)
        assert isinstance(r["purchase_invoice"], str)
        assert isinstance(r["sales_invoice"], str)
    assert json.dumps(result)


def test_sorted_deterministically(ds):
    result = detect_round_trip(ds)
    assert result == sorted(
        result, key=lambda r: (r["out_txn"], r["forward_record"], r["in_txn"])
    )


# --- #84: judge-shape round trip ---------------------------------------------

def test_all_company_42_rows_are_counterparty_via(ds):
    """On company_42 the 3-hop search finds the planted chains; all via counterp."""
    result = detect_round_trip(ds)
    assert len(result) == 3
    assert all(r["via"] == "counterparty" for r in result)
    assert all(r["forward_record"] for r in result)


def test_2hop_emptied_counterparty_bank_finds_nothing(ds, scheme):
    """With the third-party legs gone, the 2-hop fallback still finds nothing on
    company_42: the round-trip pipe and customer carry different RFCs and the
    inbound does not come from the very account we paid (so neither the CLABE
    nor the RFC rule fires)."""
    import dataclasses

    emptied = dataclasses.replace(ds, counterparty_bank=ds.counterparty_bank.iloc[0:0])
    assert detect_round_trip(emptied) == []

    # The generator's pipe and customer genuinely have different RFCs, which is
    # why the RFC rule cannot bridge this copy.
    ent = scheme("round_trip_sales")["entities"][0]
    sup_rfc = str(ds.suppliers.loc[ds.suppliers["supplier_id"] == ent["supplier_id"], "rfc"].iloc[0])
    cus_rfc = str(ds.customers.loc[ds.customers["customer_id"] == ent["customer_id"], "rfc"].iloc[0])
    assert sup_rfc != cus_rfc


def test_2hop_direct_synthetic_case():
    """A 2-hop round trip is caught when the inbound payment comes from the very
    account we paid (same CLABE): 3 pairs -> 3 'direct' rows, no forward hop."""
    import dataclasses
    from datetime import date

    import pandas as pd

    from agent.data import load

    ds = load("data_estate/out/company_42")

    invs = pd.DataFrame(
        {
            "uuid": [f"INV-P{i}" for i in range(3)] + [f"INV-S{i}" for i in range(3)],
            "counterparty_id": [f"S0{i}" for i in range(3)] + [f"C0{i}" for i in range(3)],
        }
    )
    rows_o = []
    rows_i = []
    for i in range(3):
        clabe = f"CLABE{i}"
        rows_o.append(
            {
                "txn_id": f"TX-O{i}",
                "fecha": date(2025, 6, 1 + i),
                "direction": "out",
                "amount": 1000.0 * (i + 1),
                "counterparty_clabe": clabe,
                "invoice_uuid": f"INV-P{i}",
            }
        )
        rows_i.append(
            {
                "txn_id": f"TX-I{i}",
                "fecha": date(2025, 6, 3 + i),
                "direction": "in",
                "amount": 900.0 * (i + 1),
                "counterparty_clabe": clabe,
                "invoice_uuid": f"INV-S{i}",
            }
        )
    txs = pd.DataFrame(rows_o + rows_i)
    txs["fecha"] = pd.to_datetime(txs["fecha"])
    cb = pd.DataFrame(columns=["record_id", "entity_clabe", "direction", "fecha", "amount", "counterparty_clabe"])
    ds2 = dataclasses.replace(ds, invoices=invs, bank_transactions=txs, counterparty_bank=cb)

    result = detect_round_trip(ds2)
    assert len(result) == 3
    assert sorted(r["out_txn"] for r in result) == ["TX-O0", "TX-O1", "TX-O2"]
    assert all(r["via"] == "direct" for r in result)
    assert all(r["forward_record"] == "" for r in result)
    assert all(r["amount_forward"] == 0.0 for r in result)
    assert all(0 <= r["days_forward_to_in"] <= 14 for r in result)
    # evidence must not carry the empty forward id
    assert all("" not in r["evidence"] for r in result)
    assert {r["entity_id"] for r in result} == {"S00", "S01", "S02"}
    assert {r["customer_id"] for r in result} == {"C00", "C01", "C02"}
