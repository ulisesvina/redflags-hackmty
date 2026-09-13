"""Optional service adapters with credential-free fallbacks."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def integration_status() -> list[dict[str, Any]]:
    mongo_ready = bool(os.getenv("MONGODB_URI")) and importlib.util.find_spec("pymongo") is not None
    solana_ready = bool(os.getenv("SOLANA_SECRET_KEY")) and importlib.util.find_spec("solana") is not None
    return [
        {
            "id": "gemini", "name": "Gemini", "configured": bool(os.getenv("GEMINI_API_KEY")),
            "state": "live" if os.getenv("GEMINI_API_KEY") else "fallback",
            "role": "Case Q&A",
            "fallback": "Local answers",
        },
        {
            "id": "mongodb", "name": "MongoDB", "configured": mongo_ready,
            "state": "live" if mongo_ready else "fallback",
            "role": "Case storage",
            "fallback": "Local storage",
        },
        {
            "id": "vultr", "name": "Vultr", "configured": bool(os.getenv("VULTR_PUBLIC_URL")),
            "state": "live" if os.getenv("VULTR_PUBLIC_URL") else "deploy-ready",
            "role": "Cloud deployment",
            "fallback": "Runs locally",
        },
        {
            "id": "solana", "name": "Solana", "configured": solana_ready,
            "state": "live" if solana_ready else "fallback",
            "role": "Evidence timestamp",
            "fallback": "Local SHA-256",
        },
    ]


def canonical_hash(case: dict[str, Any], presentation: dict[str, Any]) -> str:
    manifest = {
        "findings": case.get("findings", []),
        "not_pursued": case.get("not_pursued", []),
        "status": presentation.get("status"),
        "totalExposureMxn": presentation.get("totalExposureMxn", 0),
        "moneyFlow": presentation.get("moneyFlow", {}),
    }
    body = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def finalize_case(run_dir: Path, case: dict[str, Any], presentation: dict[str, Any]) -> dict[str, Any]:
    fingerprint = canonical_hash(case, presentation)
    integrity = {"algorithm": "SHA-256", "hash": fingerprint, "status": "local"}
    manifest = {
        "runId": run_dir.name,
        "finalizedAt": datetime.now(timezone.utc).isoformat(),
        "integrity": integrity,
        "case": case,
        "presentation": presentation,
    }
    try:
        (run_dir / "evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    _persist_atlas(manifest)
    return integrity


def _persist_atlas(manifest: dict[str, Any]) -> bool:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return False
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi

        client = MongoClient(uri, server_api=ServerApi("1"), serverSelectionTimeoutMS=3000, appname="redflags-forensic-auditor")
        database = client[os.getenv("MONGODB_DATABASE", "redflags")]
        database.cases.replace_one({"runId": manifest["runId"]}, manifest, upsert=True)
        client.close()
        return True
    except Exception:
        return False


def _safe_gemini_case(presentation: dict[str, Any]) -> dict[str, Any]:
    """Exclude entity names, RFCs, CLABEs and evidence IDs from hosted-model prompts."""
    return {
        "status": presentation.get("status"),
        "totalExposureMxn": presentation.get("totalExposureMxn"),
        "confidence": presentation.get("confidence"),
        "findings": [
            {
                "scheme": item.get("schemeType"), "title": item.get("title"),
                "rule": item.get("rule"), "amountMxn": item.get("amountMxn"),
                "confidence": item.get("confidence"), "evidenceCount": len(item.get("evidenceIds", [])),
            }
            for item in presentation.get("findings", [])
        ],
        "notPursuedCount": len(presentation.get("leadsNotPursued", [])),
    }


def answer_question(presentation: dict[str, Any], question: str) -> tuple[str, str]:
    key = os.getenv("GEMINI_API_KEY")
    if key:
        answer = _gemini_answer(_safe_gemini_case(presentation), _redact_question(presentation, question), key)
        if answer:
            return answer, "Gemini"
    return _local_answer(presentation, question), "Case engine"


def _redact_question(presentation: dict[str, Any], question: str) -> str:
    """Remove known case identifiers before optional hosted-model Q&A."""
    sensitive: set[str] = set()
    company = presentation.get("company", {})
    sensitive.update(str(company.get(key, "")) for key in ("name", "rfc"))
    for item in presentation.get("affectedSuppliers", []):
        sensitive.update(str(item.get(key, "")) for key in ("id", "name", "rfc", "account"))
    for item in presentation.get("evidence", []):
        sensitive.add(str(item.get("id", "")))
    for node in presentation.get("moneyFlow", {}).get("nodes", []):
        sensitive.update(str(node.get(key, "")) for key in ("id", "label", "detail"))
    redacted = question
    for value in sorted((value for value in sensitive if len(value.strip()) >= 3), key=len, reverse=True):
        redacted = re.sub(re.escape(value), "[REDACTED CASE IDENTIFIER]", redacted, flags=re.IGNORECASE)
    return redacted


def _gemini_answer(safe_case: dict[str, Any], question: str, key: str) -> str | None:
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = (
        "You explain a completed financial investigation. Answer in at most "
        "90 words using only the aggregate finalized case below. Never invent a party, record, claim or amount. "
        "If the case cannot answer, say that explicitly.\n"
        f"Question: {question}\nFinalized aggregate case: {json.dumps(safe_case, ensure_ascii=False)}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 220},
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
        return "".join(part.get("text", "") for part in body["candidates"][0]["content"]["parts"]).strip() or None
    except (OSError, urllib.error.URLError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None


def _local_answer(presentation: dict[str, Any], question: str) -> str:
    query = question.lower()
    status = presentation.get("status")
    exposure = float(presentation.get("totalExposureMxn", 0))
    findings = presentation.get("findings", [])
    leads = presentation.get("leadsNotPursued", [])
    if any(word in query for word in ("amount", "monto", "peso", "exposure", "exposición")):
        return (
            f"The supported exposure is MXN {exposure:,.2f}. It is the sum of validated findings whose evidence IDs exist in the estate; anomalies that did not cross that bar are excluded."
            if status == "fraud_found" else
            "Supported fraud exposure is MXN 0.00. The agent reviewed anomalies, but none met the joint rule, record-ID and paid-peso threshold."
        )
    if any(word in query for word in ("why", "proof", "evidence", "prueba", "evidencia", "confiden")):
        if findings:
            count = sum(len(item.get("evidenceIds", [])) for item in findings)
            return f"The conclusion rests on {count} cited records across {len(findings)} validated finding(s). Each survived the evidence guard and adversarial challenge. Confidence is {presentation.get('confidence')}%; no one-off anomaly was treated as proof."
        return f"Confidence is {presentation.get('confidence')}% that no provable scheme appears in the supplied estate. That means the accusation threshold was not met, not that future evidence could never change the conclusion."
    if any(word in query for word in ("supplier", "proveedor", "who", "quién")):
        affected = presentation.get("affectedSuppliers", [])
        if not affected:
            return "No supplier is accused. No party had both a verified rule breach and a supported peso trail."
        return "The case names only " + ", ".join(item.get("name", item.get("id", "the supported supplier")) for item in affected) + ". Other unusual suppliers remain in the non-pursued log."
    if any(word in query for word in ("lead", "abandon", "dead end", "descart")):
        return f"The case records {len(leads)} leads it did not pursue. An anomaly is not enough to accuse; each lead requires corroborating records and a defensible peso amount."
    return str(presentation.get("summary", "The finalized case does not contain enough evidence to answer that question.")) + " I cannot infer facts beyond the finalized evidence."


def anchor_manifest(fingerprint: str) -> dict[str, Any]:
    if not os.getenv("SOLANA_SECRET_KEY") or importlib.util.find_spec("solana") is None:
        return {"algorithm": "SHA-256", "hash": fingerprint, "status": "local"}
    try:
        from solana.rpc.api import Client
        from solders.hash import Hash
        from solders.instruction import AccountMeta, Instruction
        from solders.keypair import Keypair
        from solders.message import Message
        from solders.pubkey import Pubkey
        from solders.transaction import Transaction

        raw_secret = os.environ["SOLANA_SECRET_KEY"].strip()
        payer = Keypair.from_bytes(bytes(json.loads(raw_secret))) if raw_secret.startswith("[") else Keypair.from_base58_string(raw_secret)
        network = os.getenv("SOLANA_NETWORK", "devnet")
        client = Client(os.getenv("SOLANA_RPC_URL", f"https://api.{network}.solana.com"))
        blockhash: Hash = client.get_latest_blockhash().value.blockhash
        memo = Instruction(
            Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
            f"redflags:v1:{fingerprint}".encode("utf-8"),
            [AccountMeta(payer.pubkey(), True, False)],
        )
        message = Message.new_with_blockhash([memo], payer.pubkey(), blockhash)
        transaction = Transaction([payer], message, blockhash)
        signature = str(client.send_transaction(transaction).value)
        return {
            "algorithm": "SHA-256", "hash": fingerprint, "status": "anchored", "network": network,
            "signature": signature, "explorerUrl": f"https://explorer.solana.com/tx/{signature}?cluster={network}",
        }
    except Exception as error:
        return {"algorithm": "SHA-256", "hash": fingerprint, "status": "local", "error": f"Solana anchoring failed: {error}"}
