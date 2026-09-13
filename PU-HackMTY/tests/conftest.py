"""Shared fixtures. Tests MAY read hidden/ground_truth.json; agent/ code must never (AGENTS.md rule 2)."""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPANY_42 = ROOT / "data_estate" / "out" / "company_42"
JUDGES_MINI = ROOT / "tests" / "fixtures" / "judges_mini"
ESTATE_42 = ROOT / "data_estate" / "out" / "estate_42" / "estate.db"


@pytest.fixture(scope="session")
def dataset_dir() -> Path:
    return COMPANY_42


@pytest.fixture(scope="session")
def ds(dataset_dir):
    from agent.data import load

    return load(dataset_dir)


@pytest.fixture(scope="session")
def truth() -> dict:
    """Ground truth for company_42: {"schemes": [...], "decoys": [...], "meta": {...}}."""
    return json.loads((COMPANY_42 / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def scheme(truth):
    """scheme("efos_fake_supplier") -> that scheme's ground-truth dict."""
    by_type = {s["type"]: s for s in truth["schemes"]}
    return lambda t: by_type[t]


@pytest.fixture(scope="session")
def decoy_ids(truth) -> set[str]:
    return {d["supplier_id"] for d in truth["decoys"]}


# --------------------------------------------------------- judges' estate (#79, #88)
# The column types estate_schema.sql declares, so a fixture .db exercises the same
# str/REAL/INTEGER path a judge-generated estate would.
SQL_TYPES = {
    "vendors": "rfc TEXT PRIMARY KEY, legal_name TEXT, registered_date TEXT, address TEXT, bank_clabe TEXT, category TEXT, contact_email TEXT",
    "invoices": "uuid TEXT PRIMARY KEY, issuer_rfc TEXT, receiver_rfc TEXT, issue_date TEXT, subtotal REAL, iva REAL, total REAL, concepto_text TEXT, uso_cfdi TEXT, forma_pago TEXT, metodo_pago TEXT, status TEXT",
    "ledger": "entry_id INTEGER PRIMARY KEY, date TEXT, account_code TEXT, account_name TEXT, debit REAL, credit REAL, description TEXT, invoice_uuid TEXT, cost_center TEXT, approver TEXT",
    "bank_txns": "txn_id TEXT PRIMARY KEY, date TEXT, from_clabe TEXT, to_clabe TEXT, amount REAL, reference TEXT, channel TEXT",
    "purchase_orders": "po_id TEXT PRIMARY KEY, vendor_rfc TEXT, date TEXT, amount REAL, requester TEXT, approver TEXT, description TEXT",
    "contracts": "contract_id TEXT PRIMARY KEY, vendor_rfc TEXT, start_date TEXT, value REAL, scope_text TEXT",
    "employees": "emp_id TEXT PRIMARY KEY, name TEXT, role TEXT, bank_clabe TEXT, hire_date TEXT",
    "efos_list": "rfc TEXT PRIMARY KEY, legal_name TEXT, status TEXT, publication_date TEXT",
}
REAL_COLUMNS = {"subtotal", "iva", "total", "debit", "credit", "amount", "value"}
INT_COLUMNS = {"entry_id"}


def build_db(csv_dir: Path, db_path: Path) -> Path:
    """Write a judges' CSV estate into a SQLite file with the schema's own column types."""
    from agent.data import JUDGE_COLUMNS

    conn = sqlite3.connect(db_path)
    try:
        for table, columns in JUDGE_COLUMNS.items():
            conn.execute(f"CREATE TABLE {table} ({SQL_TYPES[table]})")
            with (csv_dir / f"{table}.csv").open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            for row in rows:
                values = [
                    float(row[c]) if c in REAL_COLUMNS else int(row[c]) if c in INT_COLUMNS else row[c]
                    for c in columns
                ]
                conn.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(columns))})", values)
        conn.commit()
    finally:
        conn.close()
    return db_path


@pytest.fixture(scope="session")
def judges_mini_dir() -> Path:
    return JUDGES_MINI


@pytest.fixture(scope="session")
def judges_mini_db(tmp_path_factory) -> Path:
    """tests/fixtures/judges_mini as a SQLite estate, the shape judges hand over."""
    return build_db(JUDGES_MINI, tmp_path_factory.mktemp("estate") / "mini.db")
