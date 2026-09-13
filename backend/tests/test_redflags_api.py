from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import main, pu_adapter


ROOT = Path(__file__).resolve().parents[2]
AUTH = {"Authorization": "Bearer redflags-test-session"}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runs = tmp_path / "runs"
    monkeypatch.setattr(main, "CASE_ROOT", runs)
    monkeypatch.setattr(pu_adapter, "CASE_ROOT", runs)
    pu_python = ROOT / "PU-HackMTY" / ".venv" / "bin" / "python"
    if pu_python.is_file():
        monkeypatch.setenv("FORENSIC_ENGINE_PYTHON", str(pu_python))
    for name in ("GEMINI_API_KEY", "MONGODB_URI", "SOLANA_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    return TestClient(main.app)


def upload_demo(client: TestClient, scenario: str) -> dict:
    filename = "redflags-fraud-demo.zip" if scenario == "fraud" else "redflags-demo.zip"
    payload = (ROOT / "backend" / "examples" / filename).read_bytes()
    response = client.post(
        "/extract-books",
        headers=AUTH,
        files=[("books", (filename, payload, "application/zip"))],
    )
    assert response.status_code == 200
    return response.json()


def test_health_and_integration_status_are_safe(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["product"] == "RedFlags"

    response = client.get("/integrations/status")
    assert response.status_code == 200
    integrations = response.json()["integrations"]
    assert {item["id"] for item in integrations} == {"gemini", "mongodb", "vultr", "solana"}
    assert all("key" not in str(item).lower() for item in integrations)


def test_partial_estate_is_rejected_by_the_server_gate(client: TestClient) -> None:
    response = client.post(
        "/extract-books",
        headers=AUTH,
        files=[("books", ("company.json", b'{"name":"Partial Company"}', "application/json"))],
    )
    assert response.status_code == 200
    extraction = response.json()
    assert extraction["readiness"]["ready"] is False

    start = client.post("/investigate/start", headers=AUTH, json={"runId": extraction["runId"]})
    assert start.status_code == 409
    assert start.json()["detail"]["missingFiles"]


@pytest.mark.parametrize(("scenario", "expected_status"), [("fraud", "fraud_found"), ("clean", "clean")])
def test_demo_estates_complete_the_real_api_contract(client: TestClient, scenario: str, expected_status: str) -> None:
    extraction = upload_demo(client, scenario)
    assert extraction["readiness"]["ready"] is True
    assert extraction["readiness"]["missingFiles"] == []

    response = client.post("/investigate/start", headers=AUTH, json={"runId": extraction["runId"]})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "complete"
    assert body["presentation"]["status"] == expected_status
    assert body["integrity"]["algorithm"] == "SHA-256"
    assert len(body["integrity"]["hash"]) == 64
    assert isinstance(body["presentation"]["leadsNotPursued"], list)

    if scenario == "fraud":
        assert body["presentation"]["totalExposureMxn"] > 0
        assert body["presentation"]["findings"]
        assert body["presentation"]["evidence"]
        assert body["presentation"]["moneyFlow"]["edges"]
        assert round(sum(item["exposureMxn"] for item in body["presentation"]["affectedSuppliers"]), 2) == body["presentation"]["totalExposureMxn"]
    else:
        assert body["presentation"]["totalExposureMxn"] == 0
        assert body["presentation"]["findings"] == []
        assert body["presentation"]["affectedSuppliers"] == []


def test_case_q_and_a_falls_back_without_gemini(client: TestClient) -> None:
    extraction = upload_demo(client, "clean")
    started = client.post("/investigate/start", headers=AUTH, json={"runId": extraction["runId"]})
    assert started.status_code == 200
    response = client.post(
        f"/cases/{extraction['runId']}/ask",
        json={"question": "What exact amount can you prove?"},
    )
    assert response.status_code == 200
    assert "MXN 0.00" in response.json()["answer"]
    assert response.json()["provider"] == "Case engine"
