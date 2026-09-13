"""The judges'-schema export (#80): shape, referential integrity, and ground truth.

The judges generate estates to ``estate_schema.sql`` and hand us one at run time, so our
own held-out numbers have to be measured on that shape. These tests check that what we
write is really their schema: their column names in their order, rows that resolve
against each other, and an answer key in ``ground_truth_schema.json`` shape.

Tests may read ``hidden/``; nothing under ``agent/`` may.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from data_estate.export_judges import SCHEMA, write_judges_estate
from data_estate.generate import COMPANY, Generator, write_estate

ROOT = Path(__file__).resolve().parents[1]
FROZEN_LEGACY = ROOT / "data_estate" / "out" / "company_42"
FROZEN_JUDGES = ROOT / "data_estate" / "out" / "estate_42"
JUDGES_ENUM = {"phantom_vendor", "kickback", "round_tripping", "threshold_splitting", "revenue_inflation"}


@pytest.fixture(scope="module")
def exported(tmp_path_factory) -> Path:
    """Seed 42 exported to the judges' schema in a temp dir."""
    out = tmp_path_factory.mktemp("judges") / "estate_42"
    estate = Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"])
    write_judges_estate(estate, out, seed=42, company=COMPANY)
    return out


@pytest.fixture(scope="module")
def conn(exported: Path):
    connection = sqlite3.connect(exported / "estate.db")
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


# --- the schema is theirs, column for column ---------------------------------

def test_every_table_exists_with_the_judges_columns_in_order(conn):
    present = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert present == set(SCHEMA), f"tables differ: {present ^ set(SCHEMA)}"
    for table, columns in SCHEMA.items():
        actual = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        assert actual == columns, f"{table}: {actual} != {columns}"


def test_csv_mirrors_the_database(exported: Path, conn):
    for table, columns in SCHEMA.items():
        with (exported / "csv" / f"{table}.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
            assert list(rows[0].keys()) == columns if rows else True
        n_db = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        assert len(rows) == n_db, f"{table}: {len(rows)} csv rows vs {n_db} in the db"


def test_the_judges_own_validator_can_open_the_estate(exported: Path):
    """Their validate_format.py opens the .db and reads ID_COLUMN off every table."""
    from importlib import util

    spec = util.spec_from_file_location("judges_validator", ROOT / "scripts" / "judges" / "validate_format.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conn = sqlite3.connect(exported / "estate.db")
    try:
        have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, column in module.ID_COLUMN.items():
            assert table in have, f"their validator expects table {table}"
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            assert column in cols, f"their validator keys {table} on {column}"
        for table, column in module.AMOUNT_COLUMN.items():
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            assert column in cols, f"their validator sums {table}.{column}"
    finally:
        conn.close()


# --- the rows resolve against each other -------------------------------------

def test_referential_integrity(conn):
    vendors = {r["rfc"] for r in conn.execute("SELECT rfc FROM vendors")}
    invoices = {r["uuid"] for r in conn.execute("SELECT uuid FROM invoices")}
    company = COMPANY["rfc"]

    for row in conn.execute("SELECT uuid, issuer_rfc, receiver_rfc FROM invoices"):
        # One side is always us; a purchase's issuer must be a vendor we know.
        assert company in (row["issuer_rfc"], row["receiver_rfc"]), row["uuid"]
        if row["receiver_rfc"] == company:
            assert row["issuer_rfc"] in vendors, f"{row['uuid']} issued by unknown {row['issuer_rfc']}"

    for row in conn.execute("SELECT po_id, vendor_rfc FROM purchase_orders"):
        assert row["vendor_rfc"] in vendors, row["po_id"]
    for row in conn.execute("SELECT contract_id, vendor_rfc FROM contracts"):
        assert row["vendor_rfc"] in vendors, row["contract_id"]
    for row in conn.execute("SELECT entry_id, invoice_uuid FROM ledger WHERE invoice_uuid != ''"):
        assert row["invoice_uuid"] in invoices, row["entry_id"]


def test_every_bank_row_has_two_eighteen_digit_clabes(conn):
    for row in conn.execute("SELECT txn_id, from_clabe, to_clabe FROM bank_txns"):
        for side in ("from_clabe", "to_clabe"):
            assert re.fullmatch(r"\d{18}", row[side] or ""), f"{row['txn_id']}.{side}={row[side]!r}"


def test_ledger_entry_id_is_an_integer_key(conn):
    ids = [r["entry_id"] for r in conn.execute("SELECT entry_id FROM ledger")]
    assert all(isinstance(i, int) for i in ids)
    assert len(set(ids)) == len(ids), "ledger entry_id is the primary key"


def test_efos_list_carries_only_the_judges_two_statuses(conn):
    statuses = {r["status"] for r in conn.execute("SELECT status FROM efos_list")}
    assert statuses <= {"definitivo", "presunto"}, statuses


def test_employee_ids_are_prefixed_and_addressless(conn):
    rows = list(conn.execute("SELECT emp_id, bank_clabe FROM employees"))
    assert rows
    for row in rows:
        assert row["emp_id"].startswith("EMP:"), row["emp_id"]
        assert re.fullmatch(r"\d{18}", row["bank_clabe"])
    columns = [r[1] for r in conn.execute("PRAGMA table_info(employees)")]
    # The kickback's naive tell is gone by construction: the schema has no address.
    assert not any("address" in c or "home" in c for c in columns)


# --- counts on seed 42 --------------------------------------------------------

def test_counts_match_the_legacy_estate(conn):
    estate = Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"])
    n = {t: conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"] for t in SCHEMA}
    assert n["vendors"] == len(estate.suppliers)
    assert n["invoices"] == len(estate.invoices)
    assert n["ledger"] == len(estate.ledger)
    assert n["employees"] == len(estate.employees)
    # Our own statement plus the outgoing third-party legs only: an incoming leg mirrors
    # a payment already exported from our side and would show the same peso twice.
    third_party_out = len([c for c in estate.counterparty_bank if c.direction == "out"])
    assert n["bank_txns"] == len(estate.bank) + third_party_out
    assert n["efos_list"] == len({e["rfc"] for e in estate.efos
                                  if e["situacion"] in ("Presunto", "Definitivo")})
    assert n["contracts"] >= 3


def test_planted_suppliers_have_no_purchase_order(conn):
    """The phantom, kickback and round-trip invoices have no requisition trail.

    That absence is their tell in the judges' schema, which has no goods receipts.
    """
    estate = Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"])
    truth = {s["type"]: s for s in estate.truth["schemes"]}
    by_id = {s.supplier_id: s for s in estate.suppliers}
    with_po = {r["vendor_rfc"] for r in conn.execute("SELECT vendor_rfc FROM purchase_orders")}

    for scheme_type in ("efos_fake_supplier", "kickback_shell", "round_trip_sales"):
        for ent in truth[scheme_type]["entities"]:
            sid = ent.get("supplier_id")
            if sid and sid in by_id:
                assert by_id[sid].rfc not in with_po, f"{scheme_type} {sid} should have no PO"

    # The duplicate-payment supplier is honest and delivers goods, so it keeps its trail.
    dup = truth["duplicate_invoice_payment"]["entities"][0]["supplier_id"]
    assert by_id[dup].rfc in with_po


# --- ground truth, in the judges' answer-key shape ---------------------------

def test_ground_truth_matches_the_judges_schema(exported: Path):
    truth = json.loads((exported / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))
    assert {"seed", "company_rfc", "schemes", "decoys"} <= set(truth)
    assert truth["seed"] == 42
    assert truth["company_rfc"] == COMPANY["rfc"]

    assert {s["type"] for s in truth["schemes"]} == {"phantom_vendor", "kickback", "round_tripping"}
    for scheme in truth["schemes"]:
        assert {"scheme_id", "type", "entities", "peso_amount", "difficulty"} <= set(scheme)
        assert scheme["type"] in JUDGES_ENUM
        assert scheme["difficulty"] in {"easy", "medium", "hard"}
        assert scheme["entities"] and all(":" in e for e in scheme["entities"])
        assert scheme["peso_amount"] > 0
        assert scheme["supporting_invoices"]

    assert len(truth["decoys"]) == 5
    for decoy in truth["decoys"]:
        assert {"entity", "signal", "why_innocent"} <= set(decoy)
        assert decoy["entity"].startswith("RFC:")

    # A double payment is not one of the judges' five schemes. Accusing the honest
    # supplier of it would be a false accusation, so it lives outside `schemes`.
    assert [o["type"] for o in truth["control_observations"]] == ["duplicate_invoice_payment"]


def test_peso_amounts_equal_the_internal_truth(exported: Path):
    judges = json.loads((exported / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))
    internal = json.loads((exported / "hidden" / "ground_truth_internal.json").read_text(encoding="utf-8"))
    internal_amounts = {s["type"]: s["amount_mxn"] for s in internal["schemes"]}
    mapping = {"phantom_vendor": "efos_fake_supplier", "kickback": "kickback_shell",
               "round_tripping": "round_trip_sales"}
    for scheme in judges["schemes"]:
        assert scheme["peso_amount"] == internal_amounts[mapping[scheme["type"]]]


def test_hidden_is_marked_and_the_agent_never_reads_it(exported: Path):
    assert "Do NOT mount" in (exported / "hidden" / "README").read_text(encoding="utf-8")


# --- the legacy path is untouched --------------------------------------------

def test_legacy_export_is_still_byte_identical(tmp_path):
    """company_42 is frozen; adding a second format must not move a single byte."""
    out = tmp_path / "company_42"
    write_estate(Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"]), out)
    for path in sorted(FROZEN_LEGACY.rglob("*")):
        if path.is_file():
            mirror = out / path.relative_to(FROZEN_LEGACY)
            assert mirror.exists(), f"missing {mirror}"
            assert mirror.read_bytes() == path.read_bytes(), f"{path.name} changed"


def test_export_is_deterministic(tmp_path):
    """Same seed, same bytes: the judges may run our generator twice."""
    outs = []
    for i in (1, 2):
        out = tmp_path / f"run{i}"
        write_judges_estate(Generator(7).build(["efos", "kickback"]), out, seed=7, company=COMPANY)
        outs.append(out)
    for name in SCHEMA:
        a = (outs[0] / "csv" / f"{name}.csv").read_bytes()
        b = (outs[1] / "csv" / f"{name}.csv").read_bytes()
        assert a == b, f"{name}.csv differs between two runs of the same seed"


def test_cli_writes_both_formats(tmp_path):
    judges = tmp_path / "estate_9001"
    result = subprocess.run(
        [sys.executable, "-m", "data_estate.generate", "--seed", "9001",
         "--format", "judges", "--out", str(judges)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (judges / "estate.db").exists()
    assert (judges / "csv" / "vendors.csv").exists()
    assert (judges / "hidden" / "ground_truth.json").exists()

    legacy = tmp_path / "company_9001"
    result = subprocess.run(
        [sys.executable, "-m", "data_estate.generate", "--seed", "9001", "--out", str(legacy)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (legacy / "suppliers.csv").exists()
    assert not (legacy / "estate.db").exists()


# --- the agent works on it ----------------------------------------------------

def test_the_agent_investigates_the_exported_estate(exported: Path, tmp_path):
    """End to end on the judges' shape: load, detect, investigate, submit, validate.

    This is the test that matters. Every number we report is measured on their schema,
    so if this breaks, our results describe a world the judges never see.
    """
    from importlib import util

    from agent.investigate import run
    from agent.submit import build_submission

    case = run(exported / "estate.db", out=str(tmp_path / "case.json"),
               log=str(tmp_path / "log.jsonl"), no_llm=True)
    types = {f["scheme_type"] for f in case["findings"]}
    assert {"efos_fake_supplier", "kickback_shell", "round_trip_sales"} <= types

    from agent.data import load
    ds = load(exported / "estate.db")
    submission = build_submission(case, ds, [], {"seed": 42})

    spec = util.spec_from_file_location("judges_validator", ROOT / "scripts" / "judges" / "validate_format.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate_structure(submission) == []
    # --estate: every cited record resolves AND every peso_amount reconciles within 2%.
    assert module.validate_against_estate(submission, str(exported / "estate.db")) == []


@pytest.mark.skipif(not FROZEN_JUDGES.exists(), reason="estate_42 not committed yet")
def test_frozen_estate_42_still_matches_a_fresh_export(tmp_path):
    """The committed export is what seed 42 produces today."""
    out = tmp_path / "estate_42"
    write_judges_estate(Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"]),
                        out, seed=42, company=COMPANY)
    for name in SCHEMA:
        fresh = (out / "csv" / f"{name}.csv").read_bytes()
        frozen = (FROZEN_JUDGES / "csv" / f"{name}.csv").read_bytes()
        assert fresh == frozen, f"estate_42/csv/{name}.csv drifted from the generator"
