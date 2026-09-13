"""tests/test_challenge.py (#91): the adversarial review that tries to break every finding.

"If your system runs an adversarial review, include what it argued and why the
finding survived. A finding that no one tried to break is weaker than one that
was attacked and held." These tests pin the challenge module and its integration
into the investigation loop:

- On company_42 (no LLM) all four real findings *survive* — the challenger must
  not knock out a true scheme.
- The kickback's same-bank argument survives because a real CP* leg exists.
- Removing the one transfer between a same-bank vendor and employee *kills* the
  kickback (the "same bank code, no transfer" argument).
- A threshold-splitting finding with a fixed-fee contract and invoices spaced
  >= 20 days apart is *killed*.
- The step log carries one ``challenge`` entry per finding.

Tests may read ``hidden/``; nothing here does.
"""
from __future__ import annotations

from pathlib import Path

from agent.challenge import challenge
from agent.data import load

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "tests" / "fixtures" / "judges_mini"


def _read_log(path: Path) -> list[dict]:
    from agent.steplog import parse_lines

    entries, complete = parse_lines(path.read_text(encoding="utf-8"))
    assert complete
    return entries


def _finding(case: dict, scheme_type: str) -> dict:
    for f in case["findings"]:
        if f["scheme_type"] == scheme_type:
            return f
    raise AssertionError(f"no {scheme_type} finding")


# -------------------------------------------------------- company_42 (real data)
def test_company42_all_findings_survive(tmp_path, dataset_dir):
    """The challenger must not knock out a true scheme; every argument is recorded."""
    from agent.investigate import run

    log = tmp_path / "run.jsonl"
    case = run(str(dataset_dir), out=str(tmp_path / "case.json"), log=str(log), no_llm=True)
    assert {f["scheme_type"] for f in case["findings"]} == {
        "efos_fake_supplier", "kickback_shell", "round_trip_sales", "duplicate_invoice_payment",
    }
    for f in case["findings"]:
        ch = f["challenge"]
        assert ch["verdict"] == "survived", (f["scheme_type"], ch)
        assert ch["arguments"], f["scheme_type"]
        assert f["confidence"] in ("proven", "probable")

    # the step log carries one challenge entry per finding
    entries = _read_log(log)
    challenge_entries = [e for e in entries if e["kind"] == "challenge"]
    assert len(challenge_entries) == len(case["findings"])
    assert {e["payload"]["scheme_type"] for e in challenge_entries} == {f["scheme_type"] for f in case["findings"]}

    # and the log still validates under the step-log contract
    from agent.steplog import validate_entries

    assert validate_entries(entries) == []


def test_kickback_same_bank_argument_survives_because_of_a_real_leg(tmp_path, dataset_dir, ds):
    from agent.investigate import run

    case = run(str(dataset_dir), out=str(tmp_path / "c.json"), no_llm=True)
    kick = _finding(case, "kickback_shell")
    ch = challenge(kick, ds)
    same_bank = next(a for a in ch["arguments"] if "same-bank" in a["claim"])
    assert same_bank["outcome"] == "survived"
    # a real counterparty-statement leg reaches the employee's account
    assert any(rec.startswith("CP") for rec in same_bank["records"])


def test_efos_presunto_argument_is_recorded_and_survives(tmp_path, dataset_dir, ds):
    """On company_42 the presunto supplier has invoices AFTER its publication, so
    the 'published after every invoice' argument does not hold and survives."""
    from agent.investigate import run

    case = run(str(dataset_dir), out=str(tmp_path / "c.json"), no_llm=True)
    efos = _finding(case, "efos_fake_supplier")
    ch = challenge(efos, ds)
    presunto = next(a for a in ch["arguments"] if "69-B status is presunto" in a["claim"])
    assert presunto["outcome"] == "survived"


# --------------------------------------------------------------- kill cases
def test_kickback_killed_when_same_bank_with_no_transfer(tmp_path, judges_mini_db):
    """Remove the one transfer vendor->employee from a same-bank pair and the
    kickback is killed by the 'same-bank-code only, no transfer' argument."""
    from agent.investigate import run

    ds = load(judges_mini_db)
    case = run(str(judges_mini_db), out=str(tmp_path / "c.json"), no_llm=True)
    kick = _finding(case, "kickback_shell")

    import copy

    ds2 = copy.copy(ds)
    ds2.counterparty_bank = ds2.counterparty_bank[
        ds2.counterparty_bank["record_id"] != "BNK-0005"
    ]
    ch = challenge(kick, ds2)
    assert ch["verdict"] == "killed"
    assert any(
        a["outcome"] == "killed" and "same-bank" in a["claim"] for a in ch["arguments"]
    )


def _write(estate: str, rows: str) -> None:
    with open(estate, "w", encoding="utf-8") as fh:
        fh.write(rows)


def _threshold_estate(tmp_path) -> Path:
    """A judge-shaped estate with one vendor, three invoices 30 days apart and a
    fixed-fee contract — the profile of a threshold-splitting decoy."""
    vdir = tmp_path / "thresh"
    vdir.mkdir()
    _write(vdir / "vendors.csv",
           "rfc,legal_name,registered_date,address,bank_clabe,category,contact_email\n"
           "VVV010101AA1,Proveedor Falso SA,2024-01-01,Av 1,111000000000000001,Otros,v@e.mx\n")
    _write(vdir / "invoices.csv",
           "uuid,issuer_rfc,receiver_rfc,issue_date,subtotal,iva,total,concepto_text,uso_cfdi,forma_pago,metodo_pago,status\n"
           "INV-1,VVV010101AA1,EMP920101AB1,2026-01-05,200000,32000,232000,servicio,G03,03,PUE,vigente\n"
           "INV-2,VVV010101AA1,EMP920101AB1,2026-02-05,200000,32000,232000,servicio,G03,03,PUE,vigente\n"
           "INV-3,VVV010101AA1,EMP920101AB1,2026-03-05,200000,32000,232000,servicio,G03,03,PUE,vigente\n")
    _write(vdir / "contracts.csv",
           "contract_id,vendor_rfc,start_date,value,scope_text\n"
           "CTR-9,VVV010101AA1,2026-01-01,2784000.00,cuota mensual fija\n")
    _write(vdir / "employees.csv",
           "emp_id,name,role,bank_clabe,hire_date\nEMP:0001,Ana,Gerente,000000000000000501,2021-01-01\n")
    _write(vdir / "bank_txns.csv",
           "txn_id,date,from_clabe,to_clabe,amount,reference,channel\n"
           "BNK-1,2026-01-06,000000000000000099,111000000000000001,232000.0,Pago INV-1,SPEI\n")
    return vdir


def test_threshold_killed_by_fixed_fee_contract(tmp_path):
    ds = load(_threshold_estate(tmp_path))
    finding = {
        "scheme_type": "threshold_splitting",
        "accused": ["RFC:VVV010101AA1"],
        "rule": "R6",
        "amount_mxn": 696000.0,
        "evidence": ["INV-1", "INV-2", "INV-3"],
    }
    ch = challenge(finding, ds)
    assert ch["verdict"] == "killed"
    assert any(
        a["outcome"] == "killed" and "fixed fee" in a["claim"] for a in ch["arguments"]
    )


def test_threshold_survives_without_a_contract(tmp_path):
    """Without a contract the repeated amount has no innocent explanation, so it holds."""
    ds = load(_threshold_estate(tmp_path))
    ds.contracts = ds.contracts[ds.contracts["contract_id"] != "CTR-9"]
    finding = {
        "scheme_type": "threshold_splitting",
        "accused": ["RFC:VVV010101AA1"],
        "rule": "R6",
        "amount_mxn": 696000.0,
        "evidence": ["INV-1", "INV-2", "INV-3"],
    }
    ch = challenge(finding, ds)
    assert ch["verdict"] == "survived"


def test_a_weakened_argument_downgrades_confidence(ds):
    """A payroll/loan reference on the supplier->employee transfer weakens the kickback."""
    import copy

    ds2 = copy.copy(ds)
    cp = ds2.counterparty_bank.copy()
    idx = cp.index[cp["counterparty_name"] == "Diego Zambrano"][0]
    cp.at[idx, "reference"] = "prestamo personal"
    ds2.counterparty_bank = cp
    finding = {
        "scheme_type": "kickback_shell",
        "accused": ["S00004", "E00002"],
        "rule": "R2",
        "amount_mxn": 575360.0,
        "evidence": ["BFEEB533-ACF5-9149-B1C9-D0DCA38CC35F", "EAC97D37-B587-8D33-1D5B-D8B04027B283"],
    }
    ch = challenge(finding, ds2)
    # The bite (payroll reference) weakens it, but a real transfer still exists, so it is
    # not killed: confidence drops to probable.
    assert ch["verdict"] == "survived"
    assert ch["confidence"] == "probable"
    assert any(a["outcome"] == "weakened" for a in ch["arguments"])
