"""Upload, investigation, and case presentation API."""

from __future__ import annotations

import csv
import io
import json
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:
    from .mlx_extractor import extract_with_mlx
    from .pu_adapter import CASE_ROOT, REQUIRED_BOOKS, assess_books, classify_run, company_name_from_books, prepare_books
    from .presenter import build_presentation
    from .integrations import answer_question, anchor_manifest, finalize_case, integration_status
except ImportError:
    from mlx_extractor import extract_with_mlx
    from pu_adapter import CASE_ROOT, REQUIRED_BOOKS, assess_books, classify_run, company_name_from_books, prepare_books
    from presenter import build_presentation
    from integrations import answer_question, anchor_manifest, finalize_case, integration_status

app = FastAPI(title="RedFlags Forensic Auditor", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".csv", ".json", ".pdf", ".xlsx", ".xls", ".zip"}
MAX_BOOK_BYTES = int(os.getenv("MAX_BOOK_BYTES", str(25 * 1024 * 1024)))


def read_structured(data: bytes, filename: str) -> list[dict[str, Any]]:
    """Read the formats that can be normalized without a vision model."""
    lower_name = filename.lower()
    if lower_name.endswith(".json"):
        payload = json.loads(data.decode("utf-8-sig"))
        if isinstance(payload, dict):
            payload = payload.get("entries", payload.get("rows", [payload]))
        return payload if isinstance(payload, list) else []
    if lower_name.endswith(".csv"):
        return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    return []


def normalize_entries(rows: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for row in rows:
        normalized = {str(key).lower().strip(): value for key, value in row.items()}
        amount = next((normalized[key] for key in ("amount", "total", "importe", "debit", "credit") if key in normalized), None)
        try:
            amount = float(str(amount).replace(",", "")) if amount not in (None, "") else None
        except ValueError:
            amount = None
        entries.append(
            {
                "date": normalized.get("date", normalized.get("fecha")),
                "description": normalized.get("description", normalized.get("concept", normalized.get("descripcion"))),
                "amount": amount,
                "currency": normalized.get("currency", normalized.get("moneda", "MXN")),
                "source": source,
            }
        )
    return entries


def infer_company(rows: list[dict[str, Any]]) -> str | None:
    for row in rows:
        normalized = {str(key).lower().strip(): value for key, value in row.items()}
        candidate = normalized.get("company") or normalized.get("company_name") or normalized.get("empresa")
        if candidate:
            return str(candidate)
    return None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "product": "RedFlags", "mode": "forensic-auditor", "version": "1.0.0"}


@app.get("/integrations/status")
def integrations() -> dict[str, Any]:
    """Report capabilities without ever returning a credential."""
    return {"integrations": integration_status()}


@app.get("/demo-books/{scenario}")
def demo_books(scenario: str) -> FileResponse:
    filename = "redflags-fraud-demo.zip" if scenario == "fraud" else "redflags-demo.zip" if scenario == "clean" else ""
    download_name = "fraud-case.zip" if scenario == "fraud" else "clean-case.zip" if scenario == "clean" else ""
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    if not filename or not path.is_file():
        raise HTTPException(status_code=404, detail="Demo scenario not found")
    return FileResponse(path, media_type="application/zip", filename=download_name)


def _load_completed_run(run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    if not run_id or Path(run_id).name != run_id:
        raise HTTPException(status_code=400, detail="A valid runId is required")
    run_dir = CASE_ROOT / run_id
    dataset = run_dir / "dataset"
    case_path = run_dir / "case.json"
    if not dataset.is_dir() or not case_path.is_file():
        raise HTTPException(status_code=404, detail="Completed case not found")
    try:
        case = json.loads(case_path.read_text(encoding="utf-8"))
        events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if (run_dir / "events.jsonl").is_file() else []
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=f"Case file could not be read: {error}") from error
    return run_dir, case, build_presentation(dataset, case, events)


@app.post("/investigate/start")
async def start_investigation(
    payload: dict[str, Any],
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing session")
    run_id = str(payload.get("runId", ""))
    if not run_id or Path(run_id).name != run_id:
        raise HTTPException(status_code=400, detail="A valid classification runId is required")
    dataset_path = CASE_ROOT / run_id / "dataset"
    if not dataset_path.is_dir():
        raise HTTPException(status_code=404, detail="Classification run not found")
    intake_path = CASE_ROOT / run_id / "intake.json"
    try:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        missing = list(intake.get("readiness", {}).get("missingFiles", []))
    except (OSError, json.JSONDecodeError):
        missing = sorted(name for name in REQUIRED_BOOKS if not (dataset_path / name).is_file())
    if missing:
        raise HTTPException(status_code=409, detail={"message": "More source books are required", "missingFiles": missing})
    classification = classify_run(run_id)
    if classification["status"] != "complete":
        raise HTTPException(
            status_code=500,
            detail={
                "message": classification.get("error", "Investigation failed"),
                "reason": classification.get("reason", "The investigation engine did not complete."),
            },
        )
    presentation = build_presentation(dataset_path, classification["case"], classification["log"])
    integrity = finalize_case(CASE_ROOT / run_id, classification["case"], presentation)
    return {
        "investigationId": run_id,
        "status": "complete",
        "case": classification["case"],
        "presentation": presentation,
        "integrity": integrity,
        "log": classification["log"],
    }


@app.post("/cases/{run_id}/ask")
def ask_case(run_id: str, payload: dict[str, Any]) -> dict[str, str]:
    _, _, presentation = _load_completed_run(run_id)
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Ask a question about the evidence or reasoning")
    answer, provider = answer_question(presentation, question)
    return {"answer": answer, "provider": provider}


@app.post("/cases/{run_id}/anchor")
def anchor_case(run_id: str) -> dict[str, Any]:
    run_dir, case, presentation = _load_completed_run(run_id)
    integrity = finalize_case(run_dir, case, presentation)
    result = anchor_manifest(integrity["hash"])
    if result.get("status") == "anchored":
        manifest_path = run_dir / "evidence_manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["integrity"] = result
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass
    return result


@app.post("/extract-books")
async def extract_books(
    books: list[UploadFile] = File(...),
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing session")
    if not books:
        raise HTTPException(status_code=400, detail="Attach at least one book")

    file_payloads: list[tuple[str, bytes]] = []
    structured_entries: list[dict[str, Any]] = []
    structured_company: str | None = None
    for book in books:
        content = await book.read()
        filename = book.filename or "book"
        if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported book format: {filename}")
        if len(content) > MAX_BOOK_BYTES:
            raise HTTPException(status_code=413, detail=f"Book exceeds the {MAX_BOOK_BYTES} byte limit: {filename}")
        file_payloads.append((filename, content))
        try:
            rows = read_structured(content, filename)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=400, detail=f"Could not parse {filename}: {error}") from error
        if filename.lower() == "company.json":
            metadata = json.loads(content.decode("utf-8-sig"))
            if isinstance(metadata, dict) and metadata.get("name"):
                structured_company = structured_company or str(metadata["name"])
            rows = []
        structured_company = structured_company or infer_company(rows)
        structured_entries.extend(normalize_entries(rows, filename))

    structured_company = structured_company or company_name_from_books(file_payloads)
    ai_result = await extract_with_mlx(file_payloads)
    company_name = ai_result.get("companyName") or structured_company
    if ai_result.get("entries"):
        structured_entries.extend(ai_result["entries"])
    prepared = prepare_books(file_payloads)

    return {
        "caseId": f"CASE-{uuid.uuid4().hex[:8].upper()}",
        "companyName": company_name,
        "filesReceived": len(books),
        "entries": structured_entries,
        "readiness": prepared["readiness"],
        "runId": prepared["runId"],
        "classification": {"status": "ready" if prepared["readiness"]["ready"] else "insufficient_data", "runId": prepared["runId"], "readiness": prepared["readiness"]},
    }
