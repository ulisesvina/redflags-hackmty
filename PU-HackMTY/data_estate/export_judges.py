"""Export an estate to the judges' schema (#80).

The judges score on estates built to ``student-materials/forensic-auditor/estate_schema.sql``
and hand us one at a path at run time. Our generator produces a richer estate than that
schema can hold, so this module projects it down: eight tables, their exact column names
and order, as a SQLite file and as CSVs, plus ground truth in the judges' answer-key
shape. Measuring ourselves on that shape is the point — a number measured on our own
layout says nothing about how we do on theirs.

    python -m data_estate.generate --seed 42 --format judges --out data_estate/out/estate_42

Writes::

    estate.db                     the eight tables
    csv/<table>.csv               the same rows, for a judge who would rather open a CSV
    hidden/ground_truth.json      judges' shape (ground_truth_schema.json)
    hidden/ground_truth_internal.json   our own shape, for the legacy scorer
    hidden/README

What the projection loses, deliberately, because the judges' schema has no column for it:

* **Employee home addresses.** The kickback scheme's naive tell disappears, and the
  scheme becomes provable only through the third-party bank leg (shell CLABE to the
  buyer's personal CLABE) and the approver on the purchase order and ledger. That is
  harder, and it is the judges' world.
* **Goods receipts.** A purchase order stands in as the proof-of-delivery trail. The
  planted phantom, kickback and round-trip invoices get **no** purchase order, which is
  their tell here.
* **Customers as master rows.** The schema has a vendor master and no customer master,
  so a customer exists only as an RFC on the sales invoices it received.

Stdlib only, deterministic: the same seed produces the same bytes.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sqlite3
import unicodedata
from datetime import date, timedelta
from pathlib import Path

# The judges' DDL, column-for-column. Copied from estate_schema.sql; the order matters
# because a judge reads these column names directly and our tests compare them.
SCHEMA: dict[str, list[str]] = {
    "vendors": ["rfc", "legal_name", "registered_date", "address", "bank_clabe", "category", "contact_email"],
    "invoices": ["uuid", "issuer_rfc", "receiver_rfc", "issue_date", "subtotal", "iva", "total",
                 "concepto_text", "uso_cfdi", "forma_pago", "metodo_pago", "status"],
    "ledger": ["entry_id", "date", "account_code", "account_name", "debit", "credit",
               "description", "invoice_uuid", "cost_center", "approver"],
    "bank_txns": ["txn_id", "date", "from_clabe", "to_clabe", "amount", "reference", "channel"],
    "purchase_orders": ["po_id", "vendor_rfc", "date", "amount", "requester", "approver", "description"],
    "contracts": ["contract_id", "vendor_rfc", "start_date", "value", "scope_text"],
    "employees": ["emp_id", "name", "role", "bank_clabe", "hire_date"],
    "efos_list": ["rfc", "legal_name", "status", "publication_date"],
}

DDL = """
CREATE TABLE vendors (
    rfc             TEXT PRIMARY KEY,
    legal_name      TEXT,
    registered_date TEXT,
    address         TEXT,
    bank_clabe      TEXT,
    category        TEXT,
    contact_email   TEXT
);
CREATE TABLE invoices (
    uuid          TEXT PRIMARY KEY,
    issuer_rfc    TEXT,
    receiver_rfc  TEXT,
    issue_date    TEXT,
    subtotal      REAL,
    iva           REAL,
    total         REAL,
    concepto_text TEXT,
    uso_cfdi      TEXT,
    forma_pago    TEXT,
    metodo_pago   TEXT,
    status        TEXT
);
CREATE TABLE ledger (
    entry_id     INTEGER PRIMARY KEY,
    date         TEXT,
    account_code TEXT,
    account_name TEXT,
    debit        REAL,
    credit       REAL,
    description  TEXT,
    invoice_uuid TEXT,
    cost_center  TEXT,
    approver     TEXT
);
CREATE TABLE bank_txns (
    txn_id     TEXT PRIMARY KEY,
    date       TEXT,
    from_clabe TEXT,
    to_clabe   TEXT,
    amount     REAL,
    reference  TEXT,
    channel    TEXT
);
CREATE TABLE purchase_orders (
    po_id       TEXT PRIMARY KEY,
    vendor_rfc  TEXT,
    date        TEXT,
    amount      REAL,
    requester   TEXT,
    approver    TEXT,
    description TEXT
);
CREATE TABLE contracts (
    contract_id TEXT PRIMARY KEY,
    vendor_rfc  TEXT,
    start_date  TEXT,
    value       REAL,
    scope_text  TEXT
);
CREATE TABLE employees (
    emp_id     TEXT PRIMARY KEY,
    name       TEXT,
    role       TEXT,
    bank_clabe TEXT,
    hire_date  TEXT
);
CREATE TABLE efos_list (
    rfc              TEXT PRIMARY KEY,
    legal_name       TEXT,
    status           TEXT,
    publication_date TEXT
);
"""

# Our internal scheme names -> the judges' fixed enum, with the difficulty we claim.
# duplicate_invoice_payment has no judges' type: it is a control failure, not one of
# their five schemes, so it is exported as a control observation instead of a scheme.
SCHEME_MAP = {
    "efos_fake_supplier": ("phantom_vendor", "easy"),
    "kickback_shell": ("kickback", "medium"),
    "round_trip_sales": ("round_tripping", "hard"),
    "threshold_splitting": ("threshold_splitting", "medium"),
    "revenue_inflation": ("revenue_inflation", "medium"),
}

GOODS_CATEGORIES = {"materia_prima", "refacciones", "consumibles"}


def _payroll_clabe(company: dict) -> str:
    """The account payroll is settled into.

    Our legacy statement leaves the counterparty blank on the monthly payroll transfer,
    but the judges' schema gives a bank row two CLABEs and a real statement always names
    both sides. So payroll settles to the company's own bank, into a clearing account
    that belongs to no vendor and no employee: it must never look like a payout to a
    person, or it would read as a kickback.
    """
    return (company["clabe"][:3] + "9" * 15)[:18]


def _slug(name: str) -> str:
    """A deterministic e-mail-safe slug from a company name."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = [w for w in re.split(r"[^A-Za-z0-9]+", plain) if w]
    return ("".join(words[:2]) or "vendor").lower()


def _entry_int(entry_id: str) -> int:
    """``GL00042`` -> ``42``; the judges' ledger key is an integer."""
    digits = re.sub(r"\D", "", entry_id)
    return int(digits) if digits else 0


def _emp_id(employee_id: str) -> str:
    """``E00002`` -> ``EMP:00002``, the id the judges match findings on."""
    return "EMP:" + employee_id[1:]


def _rfc_of_entity(estate, entity_id: str) -> str:
    for s in estate.suppliers:
        if s.supplier_id == entity_id:
            return s.rfc
    for c in estate.customers:
        if c.customer_id == entity_id:
            return c.rfc
    return ""


def _prefixed(estate, entity_id: str) -> str:
    """An internal id as the judges spell it: ``RFC:<rfc>`` or ``EMP:<digits>``."""
    if entity_id.startswith("E"):
        return _emp_id(entity_id)
    rfc = _rfc_of_entity(estate, entity_id)
    return f"RFC:{rfc}" if rfc else entity_id


# --------------------------------------------------------------------------- tables
def _vendors(estate) -> list[dict]:
    seen: set[str] = set()
    rows = []
    for s in estate.suppliers:
        if s.rfc in seen:
            continue
        seen.add(s.rfc)
        rows.append({
            "rfc": s.rfc,
            "legal_name": s.name,
            "registered_date": s.onboarded,
            "address": f"{s.street}, {s.city}",
            "bank_clabe": s.clabe,
            "category": s.category,
            "contact_email": f"contacto@{_slug(s.name)}.mx",
        })
    return rows


def _invoices(estate) -> list[dict]:
    return [{
        "uuid": i.uuid,
        "issuer_rfc": i.rfc_emisor,
        "receiver_rfc": i.rfc_receptor,
        "issue_date": i.fecha,
        "subtotal": i.subtotal,
        "iva": i.iva,
        "total": i.total,
        "concepto_text": i.descripcion,
        "uso_cfdi": i.uso_cfdi,
        "forma_pago": i.forma_pago,
        "metodo_pago": i.metodo_pago,
        # The judges' schema has a status column; our legacy CSV layout does not, so
        # cancellations are tracked on the Estate (#81) and surface only here.
        "status": "cancelado" if i.uuid in getattr(estate, "cancelled", ()) else "vigente",
    } for i in estate.invoices]


def _ledger(estate, emp_name: dict[str, str], inv_by_uuid: dict, sup_by_id: dict) -> list[dict]:
    rows = []
    for g in estate.ledger:
        inv = inv_by_uuid.get(g.invoice_uuid)
        category = ""
        approver = ""
        if inv is not None:
            supplier = sup_by_id.get(inv.counterparty_id)
            category = supplier.category if supplier is not None else ""
            # The approver is on the invoice rows; a payment row records no signature,
            # which is itself evidence when nobody signed.
            if not g.txn_id:
                approver = emp_name.get(inv.approved_by, "")
        rows.append({
            "entry_id": _entry_int(g.entry_id),
            "date": g.fecha,
            "account_code": g.account_code,
            "account_name": g.account_name,
            "debit": g.debit,
            "credit": g.credit,
            "description": g.descripcion,
            "invoice_uuid": g.invoice_uuid,
            "cost_center": "CC-100 Produccion" if category in GOODS_CATEGORIES else "CC-200 Administracion",
            "approver": approver,
        })
    return rows


def _bank_txns(estate, company: dict, inv_by_uuid: dict) -> list[dict]:
    rows = []
    for t in estate.bank:
        inv = inv_by_uuid.get(t.invoice_uuid)
        if t.invoice_uuid:
            verb = "Pago" if t.direction == "out" else "Cobro"
            # The judges' schema has no invoice_uuid column on a bank row, so the link
            # lives in the reference text, which is where a real statement carries it.
            reference = f"{verb} factura {t.invoice_uuid}"
        else:
            reference = t.reference or "NOMINA QUINCENAL"
        channel = "efectivo" if (inv is not None and inv.forma_pago == "01") else "SPEI"
        out = t.direction == "out"
        counterparty = t.counterparty_clabe or _payroll_clabe(company)
        rows.append({
            "txn_id": t.txn_id,
            "date": t.fecha,
            "from_clabe": company["clabe"] if out else counterparty,
            "to_clabe": counterparty if out else company["clabe"],
            "amount": t.amount,
            "reference": reference,
            "channel": channel,
        })
    # Third-party legs: only the outgoing side. A counterparty's incoming row mirrors a
    # payment we already export from our own statement, and exporting both would show
    # the same peso twice.
    for c in estate.counterparty_bank:
        if c.direction != "out":
            continue
        rows.append({
            "txn_id": c.record_id,
            "date": c.fecha,
            "from_clabe": c.entity_clabe,
            "to_clabe": c.counterparty_clabe,
            "amount": c.amount,
            "reference": c.reference,
            "channel": "SPEI",
        })
    rows.sort(key=lambda r: (r["date"], r["txn_id"]))
    return rows


def _purchase_orders(estate, rng: random.Random, emp_name: dict[str, str],
                     sup_by_id: dict, planted_supplier_ids: set[str]) -> list[dict]:
    """A PO for every purchase that has a real delivery trail.

    An invoice earns a PO when a goods receipt exists for it, or when its supplier is
    honest and sells a service (services never carry receipts, but an honest service
    purchase is still requisitioned). The planted phantom, kickback and round-trip
    invoices get nothing: no requisition, no approval trail, which is exactly how they
    look in a real book.
    """
    receipted = {r.invoice_uuid for r in estate.receipts}
    non_buyers = [e for e in estate.employees if e.role not in ("Gerente de Compras",)]
    rows = []
    for inv in estate.invoices:
        if inv.tipo != "recibida" or not inv.po_number:
            continue
        supplier = sup_by_id.get(inv.counterparty_id)
        if supplier is None:
            continue
        has_receipt = inv.uuid in receipted
        honest_service = (supplier.supplier_id not in planted_supplier_ids
                          and supplier.category not in GOODS_CATEGORIES)
        if not (has_receipt or honest_service):
            continue
        issued = date.fromisoformat(inv.fecha) - timedelta(days=rng.randint(1, 10))
        rows.append({
            "po_id": inv.po_number,
            "vendor_rfc": supplier.rfc,
            "date": issued.isoformat(),
            "amount": inv.total,
            "requester": rng.choice(non_buyers).name if non_buyers else "",
            "approver": emp_name.get(inv.approved_by, ""),
            "description": inv.descripcion,
        })
    rows.sort(key=lambda r: r["po_id"])
    return rows


def _contracts(estate, sup_by_id: dict) -> list[dict]:
    """Standing agreements that explain a repeated amount: rent, and the freight decoy."""
    totals: dict[str, list[float]] = {}
    for inv in estate.invoices:
        if inv.tipo == "recibida":
            totals.setdefault(inv.counterparty_id, []).append(inv.total)

    wanted: dict[str, str] = {}
    for s in estate.suppliers:
        if s.category == "renta_util":
            wanted[s.supplier_id] = "Contrato marco, cuota mensual fija"
    for decoy in estate.truth.get("decoys", []):
        if str(decoy.get("looks_like", "")).startswith("Shares address"):
            wanted[decoy["supplier_id"]] = "Contrato de fletes, carta porte por viaje"

    rows = []
    for supplier_id, scope in sorted(wanted.items()):
        supplier = sup_by_id.get(supplier_id)
        amounts = totals.get(supplier_id, [])
        if supplier is None or not amounts:
            continue
        rows.append({
            "contract_id": "CTR-" + supplier_id,
            "vendor_rfc": supplier.rfc,
            "start_date": supplier.onboarded,
            "value": round(12 * (sum(amounts) / len(amounts)), 2),
            "scope_text": scope,
        })
    return rows


def _employees(estate, rng: random.Random) -> list[dict]:
    return [{
        "emp_id": _emp_id(e.employee_id),
        "name": e.name,
        "role": e.role,
        "bank_clabe": e.personal_clabe,
        "hire_date": date(rng.randint(2015, 2024), rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
    } for e in estate.employees]


def _efos_list(estate) -> list[dict]:
    """Only live listings. The judges' schema has two statuses, not our four."""
    rows, seen = [], set()
    for row in estate.efos:
        if row["situacion"] not in ("Presunto", "Definitivo") or row["rfc"] in seen:
            continue
        seen.add(row["rfc"])
        rows.append({
            "rfc": row["rfc"],
            "legal_name": row["nombre"],
            "status": row["situacion"].lower(),
            "publication_date": row["fecha_publicacion"],
        })
    return rows


# --------------------------------------------------------------------- ground truth
def _planted_supplier_ids(estate) -> set[str]:
    """Supplier ids named by a planted scheme, whatever field they sit in."""
    ids: set[str] = set()
    for scheme in estate.truth.get("schemes", []):
        for ent in scheme.get("entities", []):
            for key in ("supplier_id", "customer_id"):
                if ent.get(key):
                    ids.add(ent[key])
    return ids


def _collect(entity: dict, keys: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for key in keys:
        value = entity.get(key)
        if isinstance(value, list):
            out.extend(str(v) for v in value)
    return out


def _judges_truth(estate, seed: int, company: dict) -> dict:
    schemes, observations = [], []
    counters: dict[str, int] = {}
    for scheme in estate.truth.get("schemes", []):
        internal = scheme["type"]
        mapped = SCHEME_MAP.get(internal)
        entities, invoices, txns = [], [], []
        for ent in scheme.get("entities", []):
            for key in ("supplier_id", "customer_id", "employee_id"):
                if ent.get(key):
                    entities.append(_prefixed(estate, ent[key]))
            invoices.extend(_collect(ent, ("invoice_uuids",)))
            txns.extend(_collect(ent, ("bank_txn_ids", "counterparty_record_ids")))
            for leg in ent.get("legs", []) or []:
                invoices.extend(x for x in (leg.get("purchase_invoice"), leg.get("sales_invoice")) if x)
                txns.extend(x for x in (leg.get("out_txn"), leg.get("in_txn"), leg.get("forward_record")) if x)
            for pay in ent.get("payments", []) or []:
                if pay.get("invoice_uuid"):
                    invoices.append(pay["invoice_uuid"])
                txns.extend(x for x in (pay.get("original_txn"), pay.get("duplicate_txn")) if x)

        record = {
            "entities": sorted(set(entities)),
            "supporting_invoices": sorted(set(invoices)),
            "supporting_txns": sorted(set(txns)),
            "peso_amount": scheme["amount_mxn"],
        }
        if mapped is None:
            # Not one of the judges' five. A double payment is a control failure, and
            # accusing the honest supplier of it would be a false accusation, so it is
            # recorded outside `schemes` where a scorer can credit or ignore it.
            observations.append({**record, "type": internal, "description": scheme.get("description", "")})
            continue
        judges_type, difficulty = mapped
        counters[judges_type] = counters.get(judges_type, 0) + 1
        schemes.append({
            "scheme_id": f"S{len(schemes) + 1}_{judges_type}_{counters[judges_type]}",
            "type": judges_type,
            "difficulty": difficulty,
            **record,
        })

    decoys = [{
        "entity": _prefixed(estate, d["supplier_id"]),
        "signal": d.get("looks_like", ""),
        "why_innocent": d.get("why_honest", ""),
        "invoices": [d["invoice_uuid"]] if d.get("invoice_uuid") else [],
    } for d in estate.truth.get("decoys", [])]

    return {
        "seed": seed,
        "company_rfc": company["rfc"],
        "schemes": schemes,
        "decoys": decoys,
        "control_observations": observations,
    }


# --------------------------------------------------------------------------- writing
def build_tables(estate, seed: int, company: dict) -> dict[str, list[dict]]:
    """Every judges' table as a list of row dicts, in ``SCHEMA`` column order."""
    # Derived from the seed so an export is reproducible, and offset so it never
    # consumes the generator's own stream (seed 42 must stay byte-identical in legacy).
    rng = random.Random(seed * 7919 + 13)
    emp_name = {e.employee_id: e.name for e in estate.employees}
    sup_by_id = {s.supplier_id: s for s in estate.suppliers}
    inv_by_uuid = {i.uuid: i for i in estate.invoices}
    planted = _planted_supplier_ids(estate)
    return {
        "vendors": _vendors(estate),
        "invoices": _invoices(estate),
        "ledger": _ledger(estate, emp_name, inv_by_uuid, sup_by_id),
        "bank_txns": _bank_txns(estate, company, inv_by_uuid),
        "purchase_orders": _purchase_orders(estate, rng, emp_name, sup_by_id, planted),
        "contracts": _contracts(estate, sup_by_id),
        "employees": _employees(estate, rng),
        "efos_list": _efos_list(estate),
    }


def write_judges_estate(estate, out: Path, *, seed: int, company: dict) -> dict[str, list[dict]]:
    """Write ``estate.db``, ``csv/`` and ``hidden/`` under ``out``. Returns the tables."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tables = build_tables(estate, seed, company)

    db_path = out / "estate.db"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(DDL)
        for table, columns in SCHEMA.items():
            placeholders = ", ".join("?" for _ in columns)
            conn.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                [tuple(row[c] for c in columns) for row in tables[table]],
            )
        conn.commit()
    finally:
        conn.close()

    csv_dir = out / "csv"
    csv_dir.mkdir(exist_ok=True)
    for table, columns in SCHEMA.items():
        with (csv_dir / f"{table}.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            writer.writerows(tables[table])

    hidden = out / "hidden"
    hidden.mkdir(exist_ok=True)
    (hidden / "ground_truth.json").write_text(
        json.dumps(_judges_truth(estate, seed, company), indent=2, ensure_ascii=False), encoding="utf-8")
    (hidden / "ground_truth_internal.json").write_text(
        json.dumps(estate.truth, indent=2, ensure_ascii=False), encoding="utf-8")
    (hidden / "README").write_text(
        "Do NOT mount this directory into the agent's workspace.\n", encoding="utf-8")
    return tables
