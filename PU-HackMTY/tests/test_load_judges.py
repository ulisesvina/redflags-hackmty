"""tests/test_load_judges.py (#79): a judges' estate loads into the same Dataset.

Judges hand us an estate in *their* schema at a path given at run time. If the loader
only understood our own column names, every detector would find nothing and the score
would be zero however good the rest is. These tests pin the adapter with a hand-written
mini estate (`tests/fixtures/judges_mini/`) small enough to check by hand.

The same fixture is loaded twice — once as the CSV directory, once as a SQLite estate
built from those CSVs with the real column types (REAL amounts, an INTEGER entry_id, by
the ``judges_mini_db`` fixture in conftest) — and the two must produce identical frames.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agent.data import load

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "tests" / "fixtures" / "judges_mini"

@pytest.fixture(scope="module")
def mini():
    return load(MINI)


@pytest.fixture(scope="module")
def mini_db(judges_mini_db):
    """The same estate, read out of a SQLite file instead of the CSVs."""
    return load(judges_mini_db)


FRAMES = (
    "suppliers", "customers", "employees", "invoices", "goods_receipts",
    "bank_transactions", "counterparty_bank", "ledger", "efos_69b",
    "purchase_orders", "contracts",
)


def test_csv_and_sqlite_estates_load_identically(mini, mini_db):
    """The same estate in either container must give byte-identical frames."""
    for name in FRAMES:
        left = getattr(mini, name).sort_index(axis=0).reset_index(drop=True)
        right = getattr(mini_db, name).sort_index(axis=0).reset_index(drop=True)
        assert list(left.columns) == list(right.columns), name
        assert left.equals(right), f"{name} differs:\n{left}\n!=\n{right}"
    assert mini.company == mini_db.company
    assert mini.record_table == mini_db.record_table


def test_company_identity_is_derived_not_declared(mini):
    """No company.json in the judges' schema: the company is whoever the vendors invoice."""
    assert mini.company["rfc"] == "EMP920101AB1"
    assert mini.company["clabe"] == "000000000000000099"
    assert mini.source_format == "judges"


def test_vendors_and_customers_become_prefixed_entities(mini):
    assert sorted(mini.suppliers["supplier_id"]) == ["RFC:AAAA010101AA1", "RFC:BBBB020202BB2"]
    assert list(mini.customers["customer_id"]) == ["RFC:CCCC030303CC3"]
    assert mini.customers.iloc[0]["clabe"] == "000000000000000077"
    listed = mini.suppliers.set_index("supplier_id").loc["RFC:AAAA010101AA1"]
    assert listed["name"] == "Servicios Integrales del Bajio SA de CV"
    assert listed["clabe"] == "000000000000000001"  # leading zeros survive
    assert listed["status"] == "activo"


def test_supplier_approved_by_comes_from_the_purchase_order_approver(mini):
    by_id = mini.suppliers.set_index("supplier_id")
    assert by_id.loc["RFC:BBBB020202BB2", "approved_by"] == "EMP:0001"
    assert by_id.loc["RFC:AAAA010101AA1", "approved_by"] == ""  # no PO at all


def test_invoice_direction_counterparty_and_approver(mini):
    by_uuid = mini.invoices.set_index("uuid")
    assert by_uuid.loc["INV-0001", "tipo"] == "recibida"
    assert by_uuid.loc["INV-0003", "tipo"] == "emitida"
    assert by_uuid.loc["INV-0001", "counterparty_id"] == "RFC:AAAA010101AA1"
    assert by_uuid.loc["INV-0003", "counterparty_id"] == "RFC:CCCC030303CC3"
    assert by_uuid.loc["INV-0002", "po_number"] == "PO-0001"
    assert by_uuid.loc["INV-0001", "po_number"] == ""
    # INV-0002 via its PO approver, INV-0001 via the ledger approver fallback.
    assert by_uuid.loc["INV-0002", "approved_by"] == "EMP:0001"
    assert by_uuid.loc["INV-0001", "approved_by"] == "EMP:0001"
    assert by_uuid.loc["INV-0001", "status"] == "vigente"
    assert by_uuid.loc["INV-0001", "total"] == pytest.approx(92800.0)


def test_payments_link_to_invoices_by_reference_then_by_amount(mini):
    by_txn = mini.bank_transactions.set_index("txn_id")
    assert len(mini.bank_transactions) == 4
    assert by_txn.loc["BNK-0001", "invoice_uuid"] == "INV-0001"   # named in the reference
    assert by_txn.loc["BNK-0002", "invoice_uuid"] == "INV-0002"   # CLABE + exact amount
    assert by_txn.loc["BNK-0003", "invoice_uuid"] == "INV-0003"   # the collection
    assert by_txn.loc["BNK-0004", "invoice_uuid"] == ""           # payroll settles no invoice
    assert by_txn.loc["BNK-0001", "direction"] == "out"
    assert by_txn.loc["BNK-0003", "direction"] == "in"
    assert by_txn.loc["BNK-0001", "counterparty_name"] == "Servicios Integrales del Bajio SA de CV"
    assert by_txn.loc["BNK-0001", "account_clabe"] == "000000000000000099"
    assert by_txn.loc["BNK-0004", "channel"] == "SPEI"


def test_a_leg_the_company_is_not_part_of_becomes_a_counterparty_row(mini):
    assert len(mini.counterparty_bank) == 1
    leg = mini.counterparty_bank.iloc[0]
    assert leg["record_id"] == "BNK-0005"
    assert leg["direction"] == "out"
    assert leg["entity_clabe"] == "000000000000000001"          # vendor A pays out
    assert leg["counterparty_clabe"] == "000000000000000501"    # to the buyer's own account
    assert leg["counterparty_name"] == "Ana Ruiz Medina"
    assert leg["amount"] == pytest.approx(27840.0)


def test_a_purchase_order_stands_in_for_the_goods_receipt(mini):
    assert len(mini.goods_receipts) == 1
    receipt = mini.goods_receipts.iloc[0]
    assert receipt["receipt_id"] == "PO-0001"
    assert receipt["po_number"] == "PO-0001"
    assert receipt["invoice_uuid"] == "INV-0002"
    assert receipt["supplier_id"] == "RFC:BBBB020202BB2"
    assert receipt["received_by"] == "EMP:0001"
    assert mini.record_table["PO-0001"] == "purchase_orders"


def test_record_table_names_every_citable_table(mini):
    assert mini.record_table["BNK-0005"] == "bank_txns"
    assert mini.record_table["INV-0001"] == "invoices"
    assert mini.record_table["1"] == "ledger"
    assert mini.record_table["CTR-0001"] == "contracts"
    assert mini.record_table["EMP:0001"] == "employees"
    assert mini.record_table["AAAA010101AA1"] == "vendors"
    assert set(mini.record_table.values()) <= {
        "vendors", "invoices", "ledger", "bank_txns", "purchase_orders",
        "contracts", "employees", "efos_list",
    }
    ids = mini.all_record_ids()
    assert {"INV-0001", "BNK-0001", "BNK-0005", "PO-0001", "CTR-0001"} <= ids


def test_efos_employees_ledger_and_contracts(mini):
    assert mini.efos_69b.iloc[0]["situacion"] == "Definitivo"   # judges write it lowercase
    assert mini.efos_69b.iloc[0]["rfc"] == "AAAA010101AA1"
    assert list(mini.employees["employee_id"]) == ["EMP:0001", "EMP:0002"]
    assert list(mini.employees["personal_clabe"]) == ["000000000000000501", "000000000000000502"]
    assert (mini.employees["home_street"] == "").all()          # the schema has no address
    assert mini.ledger.iloc[0]["entry_id"] == "1"
    assert mini.ledger.iloc[0]["approver"] == "Ana Ruiz Medina"
    assert mini.ledger.iloc[0]["descripcion"] == "Registro factura INV-0001"
    assert mini.contracts.iloc[0]["contract_id"] == "CTR-0001"
    assert mini.contracts.iloc[0]["value"] == pytest.approx(556800.0)


def test_dates_and_money_are_typed(mini):
    assert pd.api.types.is_datetime64_any_dtype(mini.invoices["fecha"])
    assert pd.api.types.is_datetime64_any_dtype(mini.purchase_orders["date"])
    assert pd.api.types.is_float_dtype(mini.bank_transactions["amount"])
    assert pd.api.types.is_float_dtype(mini.contracts["value"])


def test_the_detectors_run_on_a_judge_estate_and_find_the_listed_vendor(mini):
    """The whole point of the adapter: our detectors work on someone else's schema."""
    from agent.detectors import run_all
    from agent.detectors.efos import detect_efos
    from agent.leads import aggregate

    hits = detect_efos(mini)
    assert [h["entity_id"] for h in hits] == ["RFC:AAAA010101AA1"]
    results = run_all(mini)
    dossiers = aggregate(mini, results)
    assert dossiers, "aggregate produced no dossier on a judge estate"
    assert dossiers[0]["entity_id"] == "RFC:AAAA010101AA1"


def test_an_unrecognisable_path_is_refused(tmp_path):
    (tmp_path / "notes.txt").write_text("not an estate", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load(tmp_path)


def test_a_file_that_is_not_sqlite_is_refused(tmp_path):
    junk = tmp_path / "estate.db"
    junk.write_bytes(b"this is not a database")
    with pytest.raises(FileNotFoundError):
        load(junk)


def test_legacy_datasets_still_have_empty_judges_frames(ds):
    """A legacy load must be untouched by #79: no POs, no contracts, no record table."""
    assert ds.source_format == "legacy"
    assert len(ds.purchase_orders) == 0
    assert len(ds.contracts) == 0
    assert ds.record_table == {}
    assert len(ds.invoices) == 597
