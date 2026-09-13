from __future__ import annotations

from pathlib import Path

from backend.app.integrations import _redact_question, answer_question, canonical_hash, finalize_case, integration_status


def test_canonical_hash_is_stable_and_manifest_is_written(tmp_path: Path, monkeypatch) -> None:
    for name in ("GEMINI_API_KEY", "MONGODB_URI", "SOLANA_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    case = {"findings": [], "not_pursued": [{"entity": "S1", "reason": "cleared"}]}
    presentation = {"status": "clean", "totalExposureMxn": 0, "moneyFlow": {"nodes": [], "edges": []}}
    assert canonical_hash(case, presentation) == canonical_hash(dict(reversed(list(case.items()))), presentation)
    result = finalize_case(tmp_path, case, presentation)
    assert result["status"] == "local"
    assert len(result["hash"]) == 64
    assert (tmp_path / "evidence_manifest.json").is_file()


def test_all_integrations_report_truthful_fallbacks_without_credentials(monkeypatch) -> None:
    for name in ("GEMINI_API_KEY", "MONGODB_URI", "SOLANA_SECRET_KEY", "VULTR_PUBLIC_URL"):
        monkeypatch.delenv(name, raising=False)
    status = integration_status()
    assert len(status) == 4
    assert all(item["state"] in {"fallback", "deploy-ready"} for item in status)
    assert all(item["configured"] is False for item in status)


def test_local_answer_never_invents_a_supported_amount(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    presentation = {
        "status": "clean",
        "totalExposureMxn": 0,
        "confidence": 93,
        "findings": [],
        "leadsNotPursued": [{"entity": "S1", "reason": "not corroborated"}],
        "summary": "No provable fraud found.",
    }
    answer, provider = answer_question(presentation, "What amount did the agent prove?")
    assert "MXN 0.00" in answer
    assert provider == "Case engine"


def test_hosted_question_redacts_known_case_identifiers() -> None:
    presentation = {
        "company": {"name": "Empresa Secreta SA", "rfc": "ESE010101AA1"},
        "affectedSuppliers": [{"id": "S00042", "name": "Proveedor Privado", "rfc": "PPR010101AA2", "account": "012345"}],
        "evidence": [{"id": "TXN-SECRET-1"}],
        "moneyFlow": {"nodes": []},
    }
    redacted = _redact_question(presentation, "Why did Empresa Secreta SA pay Proveedor Privado in TXN-SECRET-1?")
    assert "Empresa Secreta" not in redacted
    assert "Proveedor Privado" not in redacted
    assert "TXN-SECRET-1" not in redacted
    assert "[REDACTED CASE IDENTIFIER]" in redacted
