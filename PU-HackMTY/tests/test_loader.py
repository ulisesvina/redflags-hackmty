"""Tests for agent/data.py (#2)."""
from __future__ import annotations

import csv
import json
import shutil

from agent.data import load

CSV_STEMS = (
    "suppliers",
    "customers",
    "employees",
    "invoices",
    "goods_receipts",
    "bank_transactions",
    "counterparty_bank",
    "ledger",
    "efos_69b",
)


def _dictreader_rows(directory, stem):
    with open(directory / f"{stem}.csv", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def test_row_counts_match_csv(ds, dataset_dir):
    for stem in CSV_STEMS:
        df = getattr(ds, stem)
        assert len(df) == _dictreader_rows(dataset_dir, stem), stem


def test_dtypes(ds):
    assert str(ds.invoices["fecha"].dtype) == "datetime64[ns]"
    assert str(ds.invoices["fecha_timbrado"].dtype) == "datetime64[ns]"
    assert str(ds.suppliers["onboarded"].dtype) == "datetime64[ns]"
    assert str(ds.efos_69b["fecha_publicacion"].dtype) == "datetime64[ns]"
    assert str(ds.invoices["total"].dtype) == "float64"
    assert str(ds.bank_transactions["amount"].dtype) == "float64"
    assert str(ds.ledger["debit"].dtype) == "float64"
    assert str(ds.suppliers["clabe"].dtype) in ("object", "str")
    assert str(ds.invoices["folio"].dtype) in ("object", "str")
    assert str(ds.invoices["po_number"].dtype) in ("object", "str")
    assert str(ds.ledger["account_code"].dtype) in ("object", "str")


def test_company_clabe_leading_zero(ds):
    assert ds.company["clabe"] in set(ds.bank_transactions["account_clabe"])


def test_no_nan_and_empty_cells_preserved(ds):
    for stem in CSV_STEMS:
        df = getattr(ds, stem)
        assert df.isna().sum().sum() == 0, stem
    assert int((ds.bank_transactions["invoice_uuid"] == "").sum()) == 12
    assert int((ds.invoices["po_number"] == "").sum()) == 156
    assert int((ds.ledger["txn_id"] == "").sum()) == 1791


def test_all_record_ids(ds, dataset_dir):
    ids = ds.all_record_ids()
    assert {"TX00001", "GR00001", "CP00001"} <= ids
    case = json.loads((dataset_dir / ".." / "example_case_file_for_seed42.json").read_text(encoding="utf-8"))
    for finding in case["findings"]:
        assert set(finding["evidence"]) <= ids


def test_all_entity_ids(ds, dataset_dir):
    ids = ds.all_entity_ids()
    case = json.loads((dataset_dir / ".." / "example_case_file_for_seed42.json").read_text(encoding="utf-8"))
    for finding in case["findings"]:
        assert set(finding["accused"]) <= ids
    for row in case["not_pursued"]:
        assert row["entity"] in ids


def test_load_without_hidden(ds, dataset_dir, tmp_path):
    # Copy company_42 without hidden/ and load: same row counts.
    for stem in CSV_STEMS:
        shutil.copy(dataset_dir / f"{stem}.csv", tmp_path / f"{stem}.csv")
    shutil.copy(dataset_dir / "company.json", tmp_path / "company.json")
    assert not (tmp_path / "hidden").exists()
    ds2 = load(tmp_path)
    for stem in CSV_STEMS:
        assert len(getattr(ds2, stem)) == len(getattr(ds, stem)), stem
