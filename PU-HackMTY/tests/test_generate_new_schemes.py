"""threshold_splitting and revenue_inflation, and the two decoys that target them (#81).

The judges' enum has five scheme types and we planted three. These two complete the set.
Neither moves money in a way a bank rule can see: threshold splitting is a real purchase
broken up to stay under an approval limit, and revenue inflation is money that never
arrives at all. Both are caught in the books or not at all.

Tests may read ``hidden/``; nothing under ``agent/`` may.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from data_estate.export_judges import write_judges_estate
from data_estate.generate import (
    APPROVAL_LIMIT_SUBTOTAL,
    COMPANY,
    Generator,
    write_estate,
)
from data_estate.validate import check

ROOT = Path(__file__).resolve().parents[1]
FROZEN_LEGACY = ROOT / "data_estate" / "out" / "company_42"
FROZEN_JUDGES = ROOT / "data_estate" / "out" / "estate_42"
LIMIT = APPROVAL_LIMIT_SUBTOTAL["Gerente de Compras"]
ALL_SIX = ["efos", "kickback", "roundtrip", "duplicate", "threshold", "revenue"]


@pytest.fixture(scope="module")
def estate():
    return Generator(7).build(["threshold", "revenue"])


def _scheme(estate, scheme_type: str) -> dict:
    return next(s for s in estate.truth["schemes"] if s["type"] == scheme_type)


# --- threshold splitting ------------------------------------------------------

def test_threshold_scheme_is_planted_with_its_entities(estate):
    scheme = _scheme(estate, "threshold_splitting")
    entity = scheme["entities"][0]
    assert entity["supplier_id"].startswith("S")
    assert entity["employee_id"].startswith("E")
    assert entity["approval_limit"] == LIMIT
    assert scheme["amount_mxn"] > 0
    assert "Fraccionamiento" in scheme["rule"]


def test_every_split_invoice_sits_just_under_the_approval_limit(estate):
    scheme = _scheme(estate, "threshold_splitting")
    by_uuid = {i.uuid: i for i in estate.invoices}
    for uuid_ in scheme["entities"][0]["invoice_uuids"]:
        subtotal = by_uuid[uuid_].subtotal
        # Under the limit, but close enough that splitting is obviously deliberate.
        assert subtotal < LIMIT, f"{uuid_} subtotal {subtotal} is not under the limit"
        assert subtotal >= 0.80 * LIMIT, f"{uuid_} subtotal {subtotal} is not near the limit"


def test_clusters_are_tight_in_time_and_sum_well_above_the_limit(estate):
    scheme = _scheme(estate, "threshold_splitting")
    by_uuid = {i.uuid: i for i in estate.invoices}
    clusters = scheme["entities"][0]["clusters"]
    assert len(clusters) == 3
    starts = []
    for cluster in clusters:
        assert len(cluster) >= 3, "a cluster of two is not a pattern"
        days = sorted(date.fromisoformat(by_uuid[u].fecha) for u in cluster)
        assert (days[-1] - days[0]).days <= 2, "cluster spans more than two days"
        assert sum(by_uuid[u].subtotal for u in cluster) > LIMIT, "cluster does not exceed the limit"
        starts.append(days[0])
    starts.sort()
    for earlier, later in zip(starts, starts[1:]):
        assert (later - earlier).days >= 30, "clusters must be well separated in time"


def test_split_invoices_have_receipts_and_the_buyers_approval(estate):
    """The goods are real. The fraud is against the company's own control, not the vendor."""
    scheme = _scheme(estate, "threshold_splitting")
    entity = scheme["entities"][0]
    receipted = {r.invoice_uuid for r in estate.receipts}
    by_uuid = {i.uuid: i for i in estate.invoices}
    for uuid_ in entity["invoice_uuids"]:
        assert uuid_ in receipted, f"{uuid_} has no goods receipt"
        assert by_uuid[uuid_].approved_by == entity["employee_id"]


# --- revenue inflation --------------------------------------------------------

def test_revenue_scheme_is_planted_against_a_fresh_customer(estate):
    scheme = _scheme(estate, "revenue_inflation")
    entity = scheme["entities"][0]
    assert entity["customer_id"].startswith("C")
    assert 3 <= len(entity["invoice_uuids"]) <= 5
    assert entity["bank_txn_ids"] == []
    assert scheme["amount_mxn"] > 0
    assert "Ingresos simulados" in scheme["rule"]


def test_no_money_ever_arrives_for_the_inflated_sales(estate):
    """The whole point: a bank rule cannot see this, because no payment exists."""
    scheme = _scheme(estate, "revenue_inflation")
    paid = {t.invoice_uuid for t in estate.bank if t.invoice_uuid}
    for uuid_ in scheme["entities"][0]["invoice_uuids"]:
        assert uuid_ not in paid, f"{uuid_} was collected; the scheme is not inflated revenue"


def test_the_revenue_is_booked_anyway(estate):
    """Revenue credited to 4000 Ventas with no cash behind it is the tell in the books."""
    scheme = _scheme(estate, "revenue_inflation")
    uuids = set(scheme["entities"][0]["invoice_uuids"])
    credited = {g.invoice_uuid for g in estate.ledger
                if g.account_code == "4000" and g.credit > 0 and g.invoice_uuid in uuids}
    assert credited == uuids, "every inflated sale must still be booked as revenue"
    reversed_ = {g.invoice_uuid for g in estate.ledger
                 if g.account_code == "4000" and g.debit > 0 and g.invoice_uuid in uuids}
    assert not reversed_, "no reversing entry: that is what makes the cancellation a finding"


def test_some_invoices_are_cancelled_without_reversal(estate):
    scheme = _scheme(estate, "revenue_inflation")
    cancelled = set(scheme["entities"][0]["cancelled_uuids"])
    assert 1 <= len(cancelled) <= 2
    assert cancelled <= set(scheme["entities"][0]["invoice_uuids"])
    assert cancelled <= estate.cancelled


def test_cancellation_reaches_the_judges_export(tmp_path):
    """Our CSV layout has no status column; the judges' schema does, so it shows there."""
    import sqlite3

    estate = Generator(7).build(["revenue"])
    out = tmp_path / "estate_7"
    write_judges_estate(estate, out, seed=7, company=COMPANY)
    conn = sqlite3.connect(out / "estate.db")
    try:
        cancelled = {r[0] for r in conn.execute("SELECT uuid FROM invoices WHERE status = 'cancelado'")}
    finally:
        conn.close()
    assert cancelled == estate.cancelled
    assert cancelled, "the export lost the cancellations"


# --- the two new decoys -------------------------------------------------------

def test_both_new_decoys_are_present_with_the_new_schemes(estate):
    looks = [d["looks_like"] for d in estate.truth["decoys"]]
    assert len(estate.truth["decoys"]) == 7
    assert any("same institution" in x for x in looks), "D6 (same bank code) missing"
    assert any("just under the" in x for x in looks), "D7 (fixed monthly fee) missing"


def test_same_bank_decoy_shares_only_the_bank_code(estate):
    decoy = next(d for d in estate.truth["decoys"] if "same institution" in d["looks_like"])
    supplier = next(s for s in estate.suppliers if s.supplier_id == decoy["supplier_id"])
    buyer = next(e for e in estate.employees if e.role == "Gerente de Compras")
    assert supplier.clabe[:3] == buyer.personal_clabe[:3], "the decoy must share the bank code"
    assert supplier.clabe != buyer.personal_clabe, "sharing the account would make it guilty"
    # And no money ever passes between the two accounts, which is what clears them.
    for row in estate.counterparty_bank:
        assert not (row.entity_clabe == supplier.clabe
                    and row.counterparty_clabe == buyer.personal_clabe)


def test_fixed_fee_decoy_is_monthly_not_clustered(estate):
    """Same amount just under the limit, but spread one per month, and under contract."""
    decoy = next(d for d in estate.truth["decoys"] if "just under the" in d["looks_like"])
    invoices = sorted((i for i in estate.invoices if i.counterparty_id == decoy["supplier_id"]),
                      key=lambda i: i.fecha)
    assert len(invoices) == 12
    assert len({i.subtotal for i in invoices}) == 1, "the fee is fixed"
    assert invoices[0].subtotal < LIMIT
    days = [date.fromisoformat(i.fecha) for i in invoices]
    for earlier, later in zip(days, days[1:]):
        assert (later - earlier).days >= 20, "a monthly fee is never a same-week cluster"
    assert len({d.month for d in days}) == 12


def test_the_fixed_fee_decoy_gets_a_contract_in_the_export(tmp_path):
    import sqlite3

    estate = Generator(7).build(["threshold"])
    decoy = next(d for d in estate.truth["decoys"] if "just under the" in d["looks_like"])
    supplier = next(s for s in estate.suppliers if s.supplier_id == decoy["supplier_id"])
    out = tmp_path / "estate_7"
    write_judges_estate(estate, out, seed=7, company=COMPANY)
    conn = sqlite3.connect(out / "estate.db")
    try:
        rfcs = {r[0] for r in conn.execute("SELECT vendor_rfc FROM contracts")}
        pos = {r[0] for r in conn.execute("SELECT vendor_rfc FROM purchase_orders")}
    finally:
        conn.close()
    # It is honest, so it keeps the paperwork that explains it: a framework contract
    # fixing the fee, and a purchase order per invoice.
    assert supplier.rfc in rfcs or supplier.category != "renta_util"
    assert supplier.rfc in pos, "an honest service supplier keeps its requisition trail"


# --- nothing else moved -------------------------------------------------------

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_all_six_schemes_validate(seed, tmp_path):
    estate = Generator(seed).build(ALL_SIX)
    out = tmp_path / f"c{seed}"
    write_estate(estate, out)
    assert {s["type"] for s in estate.truth["schemes"]} == {
        "efos_fake_supplier", "kickback_shell", "round_trip_sales",
        "duplicate_invoice_payment", "threshold_splitting", "revenue_inflation",
    }
    assert check(out) == []


def test_new_decoys_are_absent_without_a_new_scheme():
    """They add suppliers, and renumber() shuffles ids, so they must stay opt-in.

    Adding them to every estate would change every supplier id in the frozen
    company_42 and estate_42.
    """
    estate = Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"])
    assert len(estate.truth["decoys"]) == 5


def test_company_42_is_still_byte_identical(tmp_path):
    out = tmp_path / "company_42"
    write_estate(Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"]), out)
    for path in sorted(FROZEN_LEGACY.rglob("*")):
        if path.is_file():
            assert (out / path.relative_to(FROZEN_LEGACY)).read_bytes() == path.read_bytes(), path.name


def _db_content(path: Path) -> str:
    """A deterministic text signature of a SQLite estate: every table (in name
    order), every column, every row in insertion order.

    estate.db is not byte-portable: bytes 96-99 of the header hold the version
    of the SQLite library that wrote the file, so the same rows hash differently
    on a different SQLite build. The rows are what a judge reads and what scoring
    depends on, so we compare the database by content and everything else by bytes.
    """
    conn = sqlite3.connect(path)
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        parts = []
        for t in tables:
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")')]
            select = ",".join(f'"{c}"' for c in cols)
            rows = [tuple(r) for r in conn.execute(f'SELECT {select} FROM "{t}" ORDER BY rowid')]
            parts.append((t, tuple(cols), tuple(rows)))
        return repr(parts)
    finally:
        conn.close()


def test_estate_42_is_still_byte_identical(tmp_path):
    out = tmp_path / "estate_42"
    write_judges_estate(Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"]),
                        out, seed=42, company=COMPANY)
    for path in sorted(FROZEN_JUDGES.rglob("*")):
        if path.is_file():
            fresh = out / path.relative_to(FROZEN_JUDGES)
            if path.suffix == ".db":
                assert _db_content(fresh) == _db_content(path), path.name
            else:
                assert fresh.read_bytes() == path.read_bytes(), path.name
