"""Batch detector tests over fresh, unseen seeds (issue #29).

Every other detector test runs against company_42 only. The judges score records a
detector has never seen, so this file generates fresh estates at test time and checks
that the scheme-defining detectors find every planted entity and nothing honest, and
that every lead from every registered detector is well-formed. It catches threshold
bugs that only show up on other seeds (the round-trip window and the fast-pay window
were both tuned on one seed; seed 105 below has an 11-day return leg).

Tests may read hidden/ground_truth.json; agent/ code must never (AGENTS.md rule 2).
"""

from __future__ import annotations

import json

import pytest

from agent import detectors
from agent.data import load
from data_estate.generate import Generator, write_estate
from data_estate.validate import check

# Fixed seeds and scheme sets, verified to generate and validate on current master.
# No random seeds here (#18 does that for the generator).
BATCH_ROWS: list[tuple[int, list[str]]] = [
    (101, ["efos", "kickback", "roundtrip", "duplicate"]),
    (102, []),  # clean books, decoys only
    (103, ["efos"]),
    (104, ["kickback", "duplicate"]),
    (105, ["roundtrip"]),
]

# Scheme-defining detectors (same list as #29). Anything else is a weak signal allowed
# to list decoys — that is its documented behaviour.
STRONG: tuple[str, ...] = (
    "detect_efos",
    "detect_employee_address_match",
    "detect_duplicate_payments",
    "detect_clabe_not_on_master",
    "detect_round_trip",
)

SEEDS = [seed for seed, _ in BATCH_ROWS]


@pytest.fixture(scope="session")
def batches(tmp_path_factory):
    """Generate each fresh estate once, load it, and read its hidden ground truth.

    Generation is ~50 ms a seed; loading is the slow part, so this is session-scoped.
    Never writes under data_estate/out/.
    """
    base = tmp_path_factory.mktemp("batch")
    result: dict[int, dict] = {}
    for seed, schemes in BATCH_ROWS:
        out = base / f"c{seed}"
        estate = Generator(seed).build(schemes)
        write_estate(estate, out)
        assert check(out) == [], f"seed {seed} schemes {schemes} did not validate"
        ds = load(out)
        truth = json.loads((out / "hidden" / "ground_truth.json").read_text(encoding="utf-8"))
        result[seed] = {"ds": ds, "truth": truth, "schemes": schemes}
    return result


@pytest.fixture(scope="session")
def leads_by_seed(batches):
    return {seed: detectors.run_all(info["ds"]) for seed, info in batches.items()}


@pytest.mark.parametrize("seed", SEEDS)
def test_well_formed_leads(seed, batches, leads_by_seed):
    """Every lead from every registered detector is well-formed and serializable."""
    ds = batches[seed]["ds"]
    record_ids = ds.all_record_ids()
    entity_ids = ds.all_entity_ids()
    leads = leads_by_seed[seed]
    for det_name, lead_list in leads.items():
        for r in lead_list:
            eid = r.get("entity_id", "")
            if det_name == "detect_round_trip":
                assert eid in entity_ids or eid == "", (
                    f"{det_name}: entity_id {eid!r} must be a known entity or ''"
                )
            else:
                assert eid in entity_ids, f"{det_name}: entity_id {eid!r} is not a known entity"
            evidence = r.get("evidence", [])
            assert evidence, f"{det_name}: empty evidence on {eid!r}"
            assert all(e in record_ids for e in evidence), (
                f"{det_name}: evidence not all record ids on {eid!r}"
            )
    assert json.dumps(leads)


@pytest.mark.parametrize("seed", SEEDS)
def test_efos_finds_every_planted_supplier(seed, batches, leads_by_seed):
    truth = batches[seed]["truth"]
    planted = {
        ent["supplier_id"]
        for s in truth["schemes"]
        if s["type"] == "efos_fake_supplier"
        for ent in s["entities"]
    }
    got = {r["entity_id"] for r in leads_by_seed[seed]["detect_efos"]}
    assert got == planted


@pytest.mark.parametrize("seed", SEEDS)
def test_kickback_shell_via_employee_address(seed, batches, leads_by_seed):
    truth = batches[seed]["truth"]
    planted = {
        ent["supplier_id"]
        for s in truth["schemes"]
        if s["type"] == "kickback_shell"
        for ent in s["entities"]
    }
    leads = leads_by_seed[seed]["detect_employee_address_match"]
    got = {r["entity_id"] for r in leads}
    assert got == planted
    assert all(r["same_approver"] is True for r in leads)


@pytest.mark.parametrize("seed", SEEDS)
def test_duplicate_payment_finds_planted_payments(seed, batches, leads_by_seed):
    truth = batches[seed]["truth"]
    plant_inv: set[str] = set()
    plant_txn: set[str] = set()
    for s in truth["schemes"]:
        if s["type"] == "duplicate_invoice_payment":
            for ent in s["entities"]:
                for p in ent["payments"]:
                    plant_inv.add(p["invoice_uuid"])
                    plant_txn.add(p["duplicate_txn"])
    leads = leads_by_seed[seed]
    assert {r["invoice_uuid"] for r in leads["detect_duplicate_payments"]} == plant_inv
    assert {r["txn_id"] for r in leads["detect_clabe_not_on_master"]} == plant_txn


@pytest.mark.parametrize("seed", SEEDS)
def test_round_trip_finds_planted_legs(seed, batches, leads_by_seed):
    truth = batches[seed]["truth"]
    plant_legs: set[tuple[str, str, str]] = set()
    for s in truth["schemes"]:
        if s["type"] == "round_trip_sales":
            for ent in s["entities"]:
                for leg in ent["legs"]:
                    plant_legs.add((leg["out_txn"], leg["forward_record"], leg["in_txn"]))
    got = {
        (r["out_txn"], r["forward_record"], r["in_txn"])
        for r in leads_by_seed[seed]["detect_round_trip"]
    }
    assert got == plant_legs


def test_seed_105_eleven_day_return_needs_14_day_window(batches):
    """Document that the #9 default (return_days=14) is what catches seed 105's 11-day leg."""
    from agent.detectors.round_trip import detect_round_trip

    ds = batches[105]["ds"]
    n_default = len(detect_round_trip(ds))
    n_ten = len(detect_round_trip(ds, return_days=10))
    assert n_ten < n_default


@pytest.mark.parametrize("seed", SEEDS)
def test_no_decoy_on_strong_detectors(seed, batches, leads_by_seed):
    truth = batches[seed]["truth"]
    decoy_ids = {dec["supplier_id"] for dec in truth["decoys"]}
    leads = leads_by_seed[seed]
    for det in STRONG:
        for r in leads[det]:
            entity = r.get("entity_id", "")
            assert entity not in decoy_ids, (
                f"{det} flagged decoy {entity} on seed {seed}"
            )


def test_clean_books_102_no_strong_detector_fires(leads_by_seed):
    leads = leads_by_seed[102]
    for det in STRONG:
        assert leads[det] == []
