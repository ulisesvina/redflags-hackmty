"""Adapter from uploaded books to the investigation engine."""

from __future__ import annotations

import json
import io
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _configured_path(name: str, fallback: Path) -> Path:
    value = Path(os.getenv(name, str(fallback))).expanduser()
    return value.resolve() if value.is_absolute() else (REPOSITORY_ROOT / value).resolve()


ENGINE_ROOT = _configured_path("FORENSIC_ENGINE_ROOT", REPOSITORY_ROOT / "PU-HackMTY")
CASE_ROOT = _configured_path("CASE_STORAGE_ROOT", REPOSITORY_ROOT / "backend" / "runtime" / "cases")

LEGACY_COLUMNS: dict[str, list[str]] = {
    "suppliers.csv": ["supplier_id", "name", "rfc", "street", "city", "clabe", "account_holder", "category", "onboarded", "approved_by", "status"],
    "customers.csv": ["customer_id", "name", "rfc", "street", "city", "clabe"],
    "employees.csv": ["employee_id", "name", "rfc", "role", "home_street", "home_city", "personal_clabe"],
    "invoices.csv": ["uuid", "tipo", "serie", "folio", "fecha", "fecha_timbrado", "rfc_emisor", "nombre_emisor", "rfc_receptor", "nombre_receptor", "uso_cfdi", "forma_pago", "metodo_pago", "clave_prod_serv", "descripcion", "cantidad", "valor_unitario", "subtotal", "iva", "total", "moneda", "po_number", "counterparty_id", "approved_by", "status"],
    "goods_receipts.csv": ["receipt_id", "po_number", "supplier_id", "invoice_uuid", "fecha", "descripcion", "cantidad", "received_by", "warehouse"],
    "bank_transactions.csv": ["txn_id", "fecha", "account_clabe", "direction", "amount", "counterparty_name", "counterparty_clabe", "reference", "invoice_uuid", "channel"],
    "counterparty_bank.csv": ["record_id", "entity_name", "entity_clabe", "fecha", "direction", "amount", "counterparty_name", "counterparty_clabe", "reference"],
    "ledger.csv": ["entry_id", "fecha", "account_code", "account_name", "debit", "credit", "descripcion", "invoice_uuid", "txn_id", "cost_center", "approver"],
    "efos_69b.csv": ["rfc", "nombre", "situacion", "fecha_publicacion"],
}


def _empty_dataset(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "company.json").write_text(json.dumps({"name": "Uploaded company", "rfc": "", "clabe": "", "city": ""}), encoding="utf-8")
    for filename, columns in LEGACY_COLUMNS.items():
        (destination / filename).write_text(",".join(columns) + "\n", encoding="utf-8")


def _safe_extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if target != destination.resolve() and destination.resolve() not in target.parents:
                raise ValueError("archive contains an unsafe path")
        bundle.extractall(destination)
    candidates = [path for path in destination.rglob("company.json") if path.parent.is_dir()]
    return next((path.parent for path in candidates if (path.parent / "suppliers.csv").exists()), destination)


def _materialize(files: list[tuple[str, bytes]], destination: Path) -> Path:
    _empty_dataset(destination)
    for filename, content in files:
        lower_name = Path(filename).name.lower()
        if lower_name.endswith(".zip"):
            archive = destination / "books.zip"
            archive.write_bytes(content)
            source = _safe_extract(archive, destination / "archive")
            if source != destination:
                for path in source.iterdir():
                    target = destination / path.name
                    if path.is_file() and path.name in (*LEGACY_COLUMNS, "company.json"):
                        shutil.copyfile(path, target)
            continue
        if lower_name == "company.json":
            (destination / lower_name).write_bytes(content)
            continue
        target_name = {
            "supplier_list.csv": "suppliers.csv",
            "suppliers.csv": "suppliers.csv",
            "bank.csv": "bank_transactions.csv",
            "bank_records.csv": "bank_transactions.csv",
            "bank_transactions.csv": "bank_transactions.csv",
            "ledger.csv": "ledger.csv",
            "invoices.csv": "invoices.csv",
            "customers.csv": "customers.csv",
            "employees.csv": "employees.csv",
            "goods_receipts.csv": "goods_receipts.csv",
            "counterparty_bank.csv": "counterparty_bank.csv",
            "efos_69b.csv": "efos_69b.csv",
        }.get(lower_name)
        if target_name:
            (destination / target_name).write_bytes(content)
    return destination


def company_name_from_books(files: list[tuple[str, bytes]]) -> str | None:
    for filename, content in files:
        if Path(filename).name.lower() == "company.json":
            try:
                return json.loads(content.decode("utf-8-sig")).get("name")
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                return None
        if filename.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    company_files = [name for name in archive.namelist() if Path(name).name.lower() == "company.json"]
                    if company_files:
                        return json.loads(archive.read(company_files[0]).decode("utf-8-sig")).get("name")
            except (OSError, zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                return None
    return None


def _python_command() -> str:
    configured = os.getenv("FORENSIC_ENGINE_PYTHON")
    if configured:
        path = Path(configured).expanduser()
        # Preserve the virtualenv launcher symlink; resolving it selects the system Python.
        return str(path if path.is_absolute() else REPOSITORY_ROOT / path)
    bundled = ENGINE_ROOT / ".venv" / "bin" / "python"
    return str(bundled) if bundled.is_file() else sys.executable


REQUIRED_BOOKS = {"company.json", *LEGACY_COLUMNS}


def _dataset_files(files: list[tuple[str, bytes]]) -> set[str]:
    names: set[str] = set()
    for filename, content in files:
        if filename.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    names.update(Path(name).name.lower() for name in archive.namelist())
            except zipfile.BadZipFile:
                continue
        else:
            names.add(Path(filename).name.lower())
    return names


def assess_books(files: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Report whether the engine has every required source table."""
    present = _dataset_files(files)
    missing = sorted(REQUIRED_BOOKS - present)
    return {
        "ready": not missing,
        "requiredFiles": sorted(REQUIRED_BOOKS),
        "presentFiles": sorted(REQUIRED_BOOKS & present),
        "missingFiles": missing,
    }


def prepare_books(files: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Persist an upload without invoking investigation."""
    run_id = uuid.uuid4().hex
    run_dir = CASE_ROOT / run_id
    dataset_dir = run_dir / "dataset"
    run_dir.mkdir(parents=True, exist_ok=True)
    _materialize(files, dataset_dir)
    readiness = assess_books(files)
    # Persist the upload-time gate separately from the normalized dataset.  The
    # latter intentionally contains empty compatibility tables and must never be
    # mistaken for a complete evidence estate by a direct API call.
    (run_dir / "intake.json").write_text(
        json.dumps({"readiness": readiness}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"runId": run_id, "dataset": str(dataset_dir), "readiness": readiness}


def classify_run(run_id: str) -> dict[str, Any]:
    """Classify a previously prepared upload."""
    run_dir = CASE_ROOT / run_id
    dataset = run_dir / "dataset"
    if not dataset.is_dir() or not (dataset / "company.json").is_file():
        return {"status": "failed", "runId": run_id, "error": "Prepared upload not found"}
    try:
        case_path = run_dir / "case.json"
        log_path = run_dir / "events.jsonl"
        command = [
            _python_command(), "-m", "agent.investigate", str(dataset), "--no-llm",
            "--out", str(case_path), "--log", str(log_path), "--submission", "", "--report", "",
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ENGINE_ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
        result = subprocess.run(command, cwd=ENGINE_ROOT, env=environment, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            return {
                "status": "failed",
                "runId": run_id,
                "error": "Investigation failed",
                "reason": detail[-2000:] if detail else f"Engine exited with code {result.returncode}",
            }
        return {"status": "complete", "runId": run_id, "case": json.loads(case_path.read_text(encoding="utf-8")), "log": log_path.read_text(encoding="utf-8").splitlines()}
    except subprocess.TimeoutExpired:
        return {"status": "failed", "runId": run_id, "error": "Investigation failed", "reason": "The investigation exceeded the 5-minute limit."}
    except json.JSONDecodeError:
        return {"status": "failed", "runId": run_id, "error": "Investigation failed", "reason": "The engine produced an invalid case.json file."}
    except (OSError, ValueError) as error:
        return {"status": "failed", "runId": run_id, "error": "Investigation failed", "reason": str(error)}


def classify_books(files: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Compatibility helper for callers that need prepare + classify together."""
    prepared = prepare_books(files)
    if not prepared["readiness"]["ready"]:
        return {"status": "insufficient_data", "runId": prepared["runId"], "readiness": prepared["readiness"]}
    return classify_run(prepared["runId"])
