"""Build a UI-safe, evidence-linked view of a case file.

This module never changes the forensic verdict. It resolves entity labels, looks up
cited records, and derives a money-flow view from the case file and uploaded estate.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


CONFIDENCE_SCORES = {"proven": 97, "probable": 86, "possible": 68, "low": 55}
SCHEME_LABELS = {
    "efos_fake_supplier": "Fake supplier on the SAT 69-B list",
    "kickback_shell": "Kickback through a related-party shell",
    "round_trip_sales": "Round-trip sales and fictitious revenue",
    "threshold_splitting": "Payments split below a control threshold",
    "revenue_inflation": "Revenue inflation",
    "duplicate_invoice_payment": "Duplicate invoice payment",
    "other": "Unsupported anomaly",
}


def _rows(dataset: Path, filename: str) -> list[dict[str, str]]:
    path = dataset / filename
    if not path.is_file():
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def _money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _company(dataset: Path) -> dict[str, str]:
    try:
        value = json.loads((dataset / "company.json").read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _entity_maps(dataset: Path) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    entities: dict[str, dict[str, str]] = {}
    account_owner: dict[str, str] = {}
    definitions = (
        ("suppliers.csv", "supplier_id", "supplier", "clabe"),
        ("customers.csv", "customer_id", "customer", "clabe"),
        ("employees.csv", "employee_id", "employee", "personal_clabe"),
    )
    for filename, id_key, kind, account_key in definitions:
        for row in _rows(dataset, filename):
            entity_id = str(row.get(id_key, ""))
            if not entity_id:
                continue
            entities[entity_id] = {
                "id": entity_id,
                "name": str(row.get("name", entity_id)),
                "rfc": str(row.get("rfc", "")),
                "kind": kind,
                "detail": str(row.get("category") or row.get("role") or row.get("city") or ""),
                "account": str(row.get(account_key, "")),
            }
            if row.get(account_key):
                account_owner[str(row[account_key])] = entity_id
    return entities, account_owner


def _record_index(dataset: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    specs = (
        ("invoices.csv", "uuid", "CFDI invoice", "total", "fecha"),
        ("bank_transactions.csv", "txn_id", "Company bank movement", "amount", "fecha"),
        ("counterparty_bank.csv", "record_id", "Counterparty bank movement", "amount", "fecha"),
        ("goods_receipts.csv", "receipt_id", "Goods receipt", "", "fecha"),
        ("ledger.csv", "entry_id", "Ledger entry", "debit", "fecha"),
        ("efos_69b.csv", "rfc", "SAT Article 69-B list", "", "fecha_publicacion"),
    )
    for filename, id_key, source, amount_key, date_key in specs:
        for row in _rows(dataset, filename):
            record_id = str(row.get(id_key, ""))
            if not record_id:
                continue
            description = (
                row.get("descripcion") or row.get("reference") or row.get("nombre")
                or row.get("counterparty_name") or row.get("account_name") or source
            )
            index[record_id] = {
                "id": record_id,
                "source": source,
                "file": filename,
                "date": str(row.get(date_key, "")),
                "amountMxn": _money(row.get(amount_key)) if amount_key else None,
                "description": str(description),
            }
    return index


def _supplier_allocations(
    dataset: Path,
    suppliers: list[dict[str, str]],
    finding_amount: float,
) -> dict[str, float]:
    """Allocate an aggregate finding without overstating any named supplier."""
    if not suppliers:
        return {}
    if len(suppliers) == 1:
        return {suppliers[0]["id"]: finding_amount}

    invoice_totals = {supplier["id"]: 0.0 for supplier in suppliers}
    for row in _rows(dataset, "invoices.csv"):
        supplier_id = str(row.get("counterparty_id", ""))
        if supplier_id in invoice_totals:
            invoice_totals[supplier_id] += _money(row.get("total"))
    weight_total = sum(invoice_totals.values())
    weights = invoice_totals if weight_total else {supplier["id"]: 1.0 for supplier in suppliers}
    weight_total = sum(weights.values())

    allocations: dict[str, float] = {}
    remaining = finding_amount
    for index, supplier in enumerate(suppliers):
        supplier_id = supplier["id"]
        amount = remaining if index == len(suppliers) - 1 else round(finding_amount * weights[supplier_id] / weight_total, 2)
        allocations[supplier_id] = amount
        remaining = round(remaining - amount, 2)
    return allocations


def _money_flow(
    company: dict[str, str],
    findings: list[dict[str, Any]],
    entities: dict[str, dict[str, str]],
    dataset: Path,
) -> dict[str, list[dict[str, Any]]]:
    company_id = "COMPANY"
    nodes: dict[str, dict[str, Any]] = {
        company_id: {
            "id": company_id,
            "label": company.get("name", "Audited company"),
            "detail": company.get("rfc", "Company operating account"),
            "kind": "company",
            "risk": False,
        }
    }
    edges: list[dict[str, Any]] = []
    counterparty_rows = _rows(dataset, "counterparty_bank.csv")

    for finding_index, finding in enumerate(findings):
        accused = [str(value) for value in finding.get("accused", [])]
        resolved = [entities[value] for value in accused if value in entities]
        suppliers = [entity for entity in resolved if entity["kind"] == "supplier"]
        employees = [entity for entity in resolved if entity["kind"] == "employee"]
        customers = [entity for entity in resolved if entity["kind"] == "customer"]
        amount = _money(finding.get("amount_mxn"))
        evidence = [str(value) for value in finding.get("evidence", [])]

        for entity in resolved:
            nodes[entity["id"]] = {
                "id": entity["id"], "label": entity["name"],
                "detail": " · ".join(filter(None, (entity["id"], entity["rfc"], entity["detail"]))),
                "kind": entity["kind"], "risk": True,
            }

        if finding.get("scheme_type") == "kickback_shell" and suppliers and employees:
            supplier, employee = suppliers[0], employees[0]
            edges.append({
                "from": company_id, "to": supplier["id"], "amountMxn": amount,
                "label": "Reconciled invoice payments", "evidenceIds": evidence,
            })
            linked = [row for row in counterparty_rows if str(row.get("counterparty_clabe")) == employee["account"]]
            downstream = sum((_money(row.get("amount")) for row in linked), 0.0)
            edges.append({
                "from": supplier["id"], "to": employee["id"], "amountMxn": round(downstream, 2),
                "label": f"{len(linked)} linked downstream transfers", "evidenceIds": [str(row.get("record_id")) for row in linked],
            })
        elif finding.get("scheme_type") in {"round_trip_sales", "revenue_inflation"} and customers:
            customer = customers[0]
            edges.append({"from": customer["id"], "to": company_id, "amountMxn": amount, "label": "Recorded revenue", "evidenceIds": evidence})
            edges.append({"from": company_id, "to": customer["id"], "amountMxn": amount, "label": "Funds returned", "evidenceIds": evidence})
        else:
            targets = suppliers or customers or employees
            share = round(amount / max(1, len(targets)), 2)
            for target in targets:
                edges.append({
                    "from": company_id, "to": target["id"], "amountMxn": share,
                    "label": SCHEME_LABELS.get(str(finding.get("scheme_type")), "Supported movement"),
                    "evidenceIds": evidence,
                })

        if not resolved:
            synthetic_id = f"FINDING-{finding_index + 1}"
            nodes[synthetic_id] = {"id": synthetic_id, "label": "Evidence-linked counterparty", "detail": ", ".join(accused), "kind": "supplier", "risk": True}
            edges.append({"from": company_id, "to": synthetic_id, "amountMxn": amount, "label": "Supported movement", "evidenceIds": evidence})

    if not findings:
        nodes["CLEARED"] = {"id": "CLEARED", "label": "Reconciled counterparties", "detail": "No entity crossed the accusation threshold", "kind": "supplier", "risk": False}
        edges.append({"from": company_id, "to": "CLEARED", "amountMxn": 0, "label": "Evidence tests completed", "evidenceIds": []})

    return {"nodes": list(nodes.values()), "edges": edges}


def build_presentation(dataset: Path, case: dict[str, Any], events: list[str] | None = None) -> dict[str, Any]:
    """Return a stable frontend contract derived from an already-validated case."""
    company = _company(dataset)
    entities, _ = _entity_maps(dataset)
    records = _record_index(dataset)
    findings = case.get("findings", []) if isinstance(case.get("findings"), list) else []
    not_pursued = case.get("not_pursued", []) if isinstance(case.get("not_pursued"), list) else []
    total_exposure = round(sum(_money(item.get("amount_mxn")) for item in findings), 2)
    confidence_values = [CONFIDENCE_SCORES.get(str(item.get("confidence", "")).lower(), 78) for item in findings]
    confidence = round(sum(confidence_values) / len(confidence_values)) if confidence_values else 93

    presentation_findings: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    seen_evidence: set[str] = set()
    affected: list[dict[str, Any]] = []
    for index, finding in enumerate(findings):
        accused_ids = [str(value) for value in finding.get("accused", [])]
        accused = [entities.get(value, {"id": value, "name": value, "rfc": "", "kind": "entity", "detail": ""}) for value in accused_ids]
        evidence_ids = [str(value) for value in finding.get("evidence", [])]
        supplier_allocations = _supplier_allocations(
            dataset,
            [entity for entity in accused if entity.get("kind") == "supplier"],
            _money(finding.get("amount_mxn")),
        )
        presentation_findings.append({
            "id": f"F-{index + 1:02d}",
            "schemeType": str(finding.get("scheme_type", "other")),
            "title": SCHEME_LABELS.get(str(finding.get("scheme_type")), str(finding.get("scheme_type", "Finding")).replace("_", " ").title()),
            "rule": str(finding.get("rule", "")),
            "amountMxn": _money(finding.get("amount_mxn")),
            "confidence": str(finding.get("confidence", "probable")),
            "confidenceScore": CONFIDENCE_SCORES.get(str(finding.get("confidence", "")).lower(), 78),
            "narrative": str(finding.get("narrative") or "The cited records support this finding."),
            "accused": accused,
            "evidenceIds": evidence_ids,
        })
        for entity in accused:
            if entity.get("kind") != "supplier":
                continue
            existing = next((item for item in affected if item["id"] == entity["id"]), None)
            allocated_exposure = supplier_allocations.get(entity["id"], _money(finding.get("amount_mxn")))
            if existing:
                existing["exposureMxn"] = round(existing["exposureMxn"] + allocated_exposure, 2)
                if str(finding.get("rule", "")) not in existing["basis"]:
                    existing["basis"] += f"; {finding.get('rule', '')}"
            else:
                affected.append({**entity, "exposureMxn": allocated_exposure, "basis": str(finding.get("rule", ""))})
        for record_id in evidence_ids:
            if record_id in seen_evidence:
                continue
            seen_evidence.add(record_id)
            evidence_items.append(records.get(record_id, {
                "id": record_id, "source": "Verified case record", "file": "case file",
                "date": "", "amountMxn": None, "description": "Cited by the validated forensic finding.",
            }))

    timeline = []
    for line in events or []:
        try:
            event = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            continue
        if event.get("kind") in {"run_start", "hypothesis", "guard", "challenge", "run_end"}:
            timeline.append({
                "step": event.get("step"), "kind": event.get("kind"), "entityId": event.get("entity_id", ""),
                "detail": _event_detail(event), "accepted": event.get("payload", {}).get("accepted"),
            })

    return {
        "company": company,
        "status": "fraud_found" if findings else "clean",
        "headline": "Supported fraud found" if findings else "No provable fraud found",
        "summary": (
            f"RedFlags proved {len(findings)} scheme{'s' if len(findings) != 1 else ''} totaling MXN {total_exposure:,.2f}. Every accusation carries a rule, a peso amount and source record IDs."
            if findings else
            "RedFlags completed the evidence tests without finding a supplier that met the accusation threshold. Reviewed anomalies remain documented as leads, not allegations."
        ),
        "totalExposureMxn": total_exposure,
        "confidence": confidence,
        "findings": presentation_findings,
        "evidence": evidence_items,
        "affectedSuppliers": affected,
        "leadsNotPursued": [
            {
                "entity": f"{entities.get(str(item.get('entity')), {}).get('name', item.get('entity', 'Unknown entity'))} ({item.get('entity', 'unknown')})",
                "entityId": str(item.get("entity", "")),
                "reason": str(item.get("reason", "Insufficient corroboration.")),
                "closedBy": item.get("closed_by"),
            }
            for item in not_pursued if isinstance(item, dict)
        ],
        "moneyFlow": _money_flow(company, findings, entities, dataset),
        "timeline": timeline,
        "recordCounts": {
            "invoices": len(_rows(dataset, "invoices.csv")),
            "bank": len(_rows(dataset, "bank_transactions.csv")) + len(_rows(dataset, "counterparty_bank.csv")),
            "suppliers": len(_rows(dataset, "suppliers.csv")),
            "evidence": len(evidence_items),
        },
    }


def _event_detail(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    kind = event.get("kind")
    if kind == "run_start":
        return f"Ranked {payload.get('n_leads', 0)} detector leads for investigation."
    if kind == "hypothesis":
        return str(payload.get("text", "Hypothesis formed."))
    if kind == "guard":
        return "Evidence guard accepted a finding." if payload.get("accepted") else "Evidence guard rejected an unsupported finding."
    if kind == "challenge":
        return f"Adversarial review {payload.get('verdict', 'completed')} with {payload.get('confidence', 'recorded')} confidence."
    if kind == "run_end":
        return f"Finalized {payload.get('n_findings', 0)} findings and {payload.get('n_not_pursued', 0)} non-pursued leads."
    return str(kind).replace("_", " ").title()
