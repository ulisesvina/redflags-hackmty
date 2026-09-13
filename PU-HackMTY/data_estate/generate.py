"""
Synthetic company data estate for the Forensic Auditor track.

Produces, for one fiscal year of a small Monterrey manufacturing company:
  suppliers.csv               supplier master (RFC, CLABE, address, onboarding date)
  customers.csv               customer master
  employees.csv               employees (needed for related-party detection)
  invoices.csv                CFDI 4.0-shaped invoices, both received (egreso for us) and issued
  goods_receipts.csv          proof of delivery for purchase invoices
  bank_transactions.csv       the company's own bank statement
  counterparty_bank.csv       obtained statements for a handful of counterparties (subpoena / AMLSim style)
  ledger.csv                  general ledger entries linked to invoices and bank txns
  efos_69b.csv                mock SAT Article 69-B list
  ground_truth.json           HIDDEN: what was planted, where, and how much. Never ship to the agent.

Usage:
  python -m data_estate.generate --seed 42 --out out/company_42
  python -m data_estate.generate --seed 7 --schemes efos,kickback --out out/demo
  python -m data_estate.generate --seed 100 --n 5 --out out/batch_100   # batch: out/company_100..company_104
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import string
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

FY_START = date(2025, 1, 1)
FY_END = date(2025, 12, 31)
IVA = 0.16

# Internal purchasing policy: what each role may approve, on the invoice SUBTOTAL.
# A judge will ask where this number lives; it lives here, in code, and agent/rules.py
# mirrors it for the detector. Splitting a purchase to stay under a limit is the
# threshold_splitting scheme.
APPROVAL_LIMIT_SUBTOTAL = {
    "Gerente de Compras": 250_000.0,
    "Director General": float("inf"),
}

COMPANY = {
    "name": "Talleres Industriales del Norte SA de CV",
    "rfc": "TIN091214KL3",
    "clabe": "012580001234567890",
    "city": "Monterrey, NL",
}

FIRST = ["Rodrigo", "Ana", "Luis", "María", "Jorge", "Carla", "Diego", "Sofía", "Héctor", "Paola",
         "Raúl", "Elena", "Mauricio", "Fernanda", "Iván", "Daniela", "Emilio", "Regina", "Óscar", "Lucía"]
LAST = ["García", "Martínez", "López", "Hernández", "Treviño", "Garza", "Elizondo", "Cantú", "Villarreal",
        "Salinas", "Zambrano", "Montemayor", "Rodríguez", "Sada", "Lozano", "Guerra", "Chapa", "Quintanilla"]

SUPPLIER_WORDS = ["Aceros", "Metálica", "Suministros", "Herramientas", "Logística", "Transportes",
                  "Electrónica", "Servicios", "Industrias", "Maquinados", "Refacciones", "Soldadura",
                  "Neumática", "Hidráulica", "Empaques", "Pinturas", "Ferretera", "Grupo", "Distribuidora"]
SUPPLIER_TAIL = ["del Norte", "Regiomontana", "Monterrey", "Nuevo León", "Industrial", "de México",
                 "San Nicolás", "Apodaca", "Santa Catarina", "Guadalupe", "Escobedo"]
LEGAL = ["SA de CV", "S de RL de CV", "SAPI de CV"]

STREETS = ["Av. Ruiz Cortines", "Av. Universidad", "Blvd. Díaz Ordaz", "Av. Lincoln", "Av. Garza Sada",
           "Calle Zaragoza", "Av. Constitución", "Av. Lázaro Cárdenas", "Av. Miguel Alemán", "Av. Sendero"]
CITIES = ["Monterrey, NL", "San Nicolás de los Garza, NL", "Apodaca, NL", "Guadalupe, NL",
          "Santa Catarina, NL", "General Escobedo, NL", "San Pedro Garza García, NL"]

# (category, clave_prod_serv, description pool, needs goods receipt?)
CATEGORIES = [
    ("materia_prima", "30102000", ["Lámina de acero cal. 14", "Placa de acero A36", "Tubo estructural",
                                   "Perfil PTR 2x2", "Barra redonda 1018"], True),
    ("refacciones", "40141600", ["Rodamientos SKF", "Bandas industriales", "Sellos hidráulicos",
                                 "Motor eléctrico 5HP", "Válvulas neumáticas"], True),
    ("consumibles", "31161500", ["Discos de corte", "Electrodos 6013", "Brocas HSS", "Guantes de carnaza",
                                 "Solvente industrial"], True),
    ("servicios", "80101500", ["Servicio de mantenimiento", "Consultoría de procesos", "Capacitación",
                               "Servicios de limpieza", "Asesoría fiscal"], False),
    ("logistica", "78101800", ["Flete local", "Flete foráneo", "Maniobras de carga"], False),
    ("renta_util", "80131500", ["Renta de nave industrial", "Servicio de energía", "Renta de montacargas"], False),
]

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def rfc_moral(rng: random.Random) -> str:
    letters = "".join(rng.choices(string.ascii_uppercase, k=3))
    yy = rng.choice(list(range(85, 100)) + list(range(0, 25)))
    mm = rng.randint(1, 12)
    dd = rng.randint(1, 28)
    homo = "".join(rng.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{letters}{yy:02d}{mm:02d}{dd:02d}{homo}"


def rfc_fisica(rng: random.Random, first: str, last: str) -> str:
    letters = (last[:2] + first[:1] + "X").upper()
    letters = "".join(ch if ch.isalpha() else "X" for ch in letters)[:4]
    yy = rng.randint(60, 99)
    mm = rng.randint(1, 12)
    dd = rng.randint(1, 28)
    homo = "".join(rng.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{letters}{yy:02d}{mm:02d}{dd:02d}{homo}"


def clabe(rng: random.Random) -> str:
    bank = rng.choice(["002", "012", "014", "021", "072", "127", "058"])
    return bank + "".join(rng.choices(string.digits, k=15))


def cfdi_uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128))).upper()


def rand_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def business_day(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def person_name(rng: random.Random) -> tuple[str, str]:
    return rng.choice(FIRST), rng.choice(LAST)


def address(rng: random.Random) -> tuple[str, str]:
    return f"{rng.choice(STREETS)} {rng.randint(100, 4999)}", rng.choice(CITIES)


# ----------------------------------------------------------------------------
# Records
# ----------------------------------------------------------------------------


@dataclass
class Supplier:
    supplier_id: str
    name: str
    rfc: str
    street: str
    city: str
    clabe: str
    account_holder: str
    category: str
    onboarded: str
    approved_by: str  # employee_id
    status: str = "activo"


@dataclass
class Customer:
    customer_id: str
    name: str
    rfc: str
    street: str
    city: str
    clabe: str


@dataclass
class Employee:
    employee_id: str
    name: str
    rfc: str
    role: str
    home_street: str
    home_city: str
    personal_clabe: str


@dataclass
class Invoice:
    uuid: str
    tipo: str            # "recibida" (we are receptor) or "emitida" (we are emisor)
    serie: str
    folio: str
    fecha: str
    fecha_timbrado: str
    rfc_emisor: str
    nombre_emisor: str
    rfc_receptor: str
    nombre_receptor: str
    uso_cfdi: str
    forma_pago: str      # 03 transferencia, 01 efectivo, 04 tarjeta
    metodo_pago: str     # PUE / PPD
    clave_prod_serv: str
    descripcion: str
    cantidad: float
    valor_unitario: float
    subtotal: float
    iva: float
    total: float
    moneda: str
    po_number: str
    counterparty_id: str
    approved_by: str


@dataclass
class GoodsReceipt:
    receipt_id: str
    po_number: str
    supplier_id: str
    invoice_uuid: str
    fecha: str
    descripcion: str
    cantidad: float
    received_by: str
    warehouse: str


@dataclass
class BankTxn:
    txn_id: str
    fecha: str
    account_clabe: str      # our account
    direction: str          # "out" / "in"
    amount: float
    counterparty_name: str
    counterparty_clabe: str
    reference: str
    invoice_uuid: str       # may be empty


@dataclass
class CounterpartyTxn:
    """Obtained statement of some other entity (shell, employee, customer)."""
    record_id: str
    entity_name: str
    entity_clabe: str
    fecha: str
    direction: str
    amount: float
    counterparty_name: str
    counterparty_clabe: str
    reference: str


@dataclass
class LedgerEntry:
    entry_id: str
    fecha: str
    account_code: str
    account_name: str
    debit: float
    credit: float
    descripcion: str
    invoice_uuid: str
    txn_id: str


@dataclass
class Estate:
    suppliers: list[Supplier] = field(default_factory=list)
    customers: list[Customer] = field(default_factory=list)
    employees: list[Employee] = field(default_factory=list)
    invoices: list[Invoice] = field(default_factory=list)
    receipts: list[GoodsReceipt] = field(default_factory=list)
    bank: list[BankTxn] = field(default_factory=list)
    counterparty_bank: list[CounterpartyTxn] = field(default_factory=list)
    ledger: list[LedgerEntry] = field(default_factory=list)
    efos: list[dict] = field(default_factory=list)
    # Uuids of sales invoices cancelled after the fact. The judges' schema has an
    # invoices.status column for this; our legacy CSV layout does not, and adding one
    # would change every byte of the frozen company_42, so it is tracked here and read
    # only by data_estate/export_judges.py.
    cancelled: set[str] = field(default_factory=set)
    truth: dict = field(default_factory=lambda: {"schemes": [], "decoys": []})


# ----------------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------------


class Generator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.seed = seed
        self.e = Estate()
        self._ids = {"S": 0, "C": 0, "E": 0, "GR": 0, "TX": 0, "CP": 0, "GL": 0, "PO": 0}
        self._folio = 1000
        self._entry_counter = 0

    def nid(self, prefix: str) -> str:
        self._ids[prefix] += 1
        return f"{prefix}{self._ids[prefix]:05d}"

    # ---- masters ---------------------------------------------------------

    def make_employees(self):
        roles = [("Director General", 1), ("Gerente de Compras", 1), ("Contador", 1),
                 ("Jefe de Almacén", 1), ("Supervisor de Producción", 2), ("Ventas", 2),
                 ("Operador", 6), ("Administrativo", 2)]
        for role, n in roles:
            for _ in range(n):
                first, last = person_name(self.rng)
                st, ct = address(self.rng)
                self.e.employees.append(Employee(
                    employee_id=self.nid("E"), name=f"{first} {last}",
                    rfc=rfc_fisica(self.rng, first, last), role=role,
                    home_street=st, home_city=ct, personal_clabe=clabe(self.rng)))

    def emp(self, role: str) -> Employee:
        return next(x for x in self.e.employees if x.role == role)

    def make_supplier(self, category: str, *, name: str | None = None, onboarded: date | None = None,
                      street: str | None = None, city: str | None = None, clabe_: str | None = None,
                      holder: str | None = None, approved_by: str | None = None) -> Supplier:
        rng = self.rng
        if name is None:
            name = f"{rng.choice(SUPPLIER_WORDS)} {rng.choice(SUPPLIER_TAIL)} {rng.choice(LEGAL)}"
        st, ct = address(rng)
        s = Supplier(
            supplier_id=self.nid("S"), name=name, rfc=rfc_moral(rng),
            street=street or st, city=city or ct, clabe=clabe_ or clabe(rng),
            account_holder=holder or name, category=category,
            onboarded=(onboarded or rand_date(rng, date(2019, 1, 1), date(2024, 10, 1))).isoformat(),
            approved_by=approved_by or self.emp("Gerente de Compras").employee_id)
        self.e.suppliers.append(s)
        return s

    def make_suppliers(self, n: int = 34):
        cats = [c[0] for c in CATEGORIES]
        weights = [5, 4, 4, 3, 2, 2]
        for _ in range(n):
            self.make_supplier(self.rng.choices(cats, weights)[0])

    def make_customers(self, n: int = 18):
        for _ in range(n):
            st, ct = address(self.rng)
            nm = f"{self.rng.choice(['Manufacturas', 'Autopartes', 'Construcciones', 'Grupo', 'Envases'])} " \
                 f"{self.rng.choice(LAST)} {self.rng.choice(LEGAL)}"
            self.e.customers.append(Customer(self.nid("C"), nm, rfc_moral(self.rng), st, ct, clabe(self.rng)))

    # ---- primitives that write consistent invoice+receipt+bank+ledger ----

    def cat_info(self, category: str):
        return next(c for c in CATEGORIES if c[0] == category)

    def purchase_invoice(self, s: Supplier, d: date, subtotal: float, *, descripcion: str | None = None,
                         with_receipt: bool | None = None, forma_pago: str = "03",
                         approved_by: str | None = None, pay_delay: tuple[int, int] = (15, 45),
                         pay: bool = True, pay_count: int = 1) -> Invoice:
        """A purchase invoice, optional goods receipt, payment(s) and ledger entries."""
        rng = self.rng
        cat = self.cat_info(s.category)
        desc = descripcion or rng.choice(cat[2])
        if with_receipt is None:
            with_receipt = cat[3]
        qty = float(rng.randint(1, 200)) if cat[3] else 1.0
        subtotal = round(subtotal, 2)
        iva = round(subtotal * IVA, 2)
        total = round(subtotal + iva, 2)
        po = self.nid("PO")
        self._folio += 1
        inv = Invoice(
            uuid=cfdi_uuid(rng), tipo="recibida", serie="A", folio=str(rng.randint(100, 99999)),
            fecha=d.isoformat(), fecha_timbrado=(d + timedelta(days=rng.randint(0, 2))).isoformat(),
            rfc_emisor=s.rfc, nombre_emisor=s.name, rfc_receptor=COMPANY["rfc"], nombre_receptor=COMPANY["name"],
            uso_cfdi="G03", forma_pago=forma_pago, metodo_pago=rng.choice(["PUE", "PPD"]),
            clave_prod_serv=cat[1], descripcion=desc, cantidad=qty, valor_unitario=round(subtotal / qty, 2),
            subtotal=subtotal, iva=iva, total=total, moneda="MXN", po_number=po, counterparty_id=s.supplier_id,
            approved_by=approved_by or s.approved_by)
        self.e.invoices.append(inv)

        if with_receipt:
            self.e.receipts.append(GoodsReceipt(
                receipt_id=self.nid("GR"), po_number=po, supplier_id=s.supplier_id, invoice_uuid=inv.uuid,
                fecha=business_day(d - timedelta(days=rng.randint(0, 5))).isoformat(), descripcion=desc,
                cantidad=qty, received_by=self.emp("Jefe de Almacén").employee_id,
                warehouse=rng.choice(["ALM-01", "ALM-02"])))

        # ledger: expense / IVA acreditable / AP
        self.gl(d, "6000", f"Gastos {s.category}", subtotal, 0, f"Factura {inv.folio} {s.name}", inv.uuid, "")
        self.gl(d, "1180", "IVA acreditable", iva, 0, f"IVA factura {inv.folio}", inv.uuid, "")
        self.gl(d, "2100", "Proveedores", 0, total, f"Factura {inv.folio} {s.name}", inv.uuid, "")

        if pay:
            for _ in range(pay_count):
                pd = business_day(d + timedelta(days=rng.randint(*pay_delay)))
                if pd > FY_END:
                    pd = FY_END
                self.pay_out(s, pd, total, inv.uuid, reference=f"PAGO FACT {inv.folio}")
        return inv

    def pay_out(self, s: Supplier, d: date, amount: float, invoice_uuid: str, reference: str) -> BankTxn:
        tx = BankTxn(self.nid("TX"), d.isoformat(), COMPANY["clabe"], "out", round(amount, 2),
                     s.account_holder, s.clabe, reference, invoice_uuid)
        self.e.bank.append(tx)
        self.gl(d, "2100", "Proveedores", amount, 0, f"Pago {s.name}", invoice_uuid, tx.txn_id)
        self.gl(d, "1020", "Bancos", 0, amount, f"Pago {s.name}", invoice_uuid, tx.txn_id)
        return tx

    def sales_invoice(self, c: Customer, d: date, subtotal: float, *, pay: bool = True,
                      pay_delay: tuple[int, int] = (20, 60), descripcion: str | None = None) -> Invoice:
        rng = self.rng
        subtotal = round(subtotal, 2)
        iva = round(subtotal * IVA, 2)
        total = round(subtotal + iva, 2)
        self._folio += 1
        inv = Invoice(
            uuid=cfdi_uuid(rng), tipo="emitida", serie="F", folio=str(self._folio), fecha=d.isoformat(),
            fecha_timbrado=d.isoformat(), rfc_emisor=COMPANY["rfc"], nombre_emisor=COMPANY["name"],
            rfc_receptor=c.rfc, nombre_receptor=c.name, uso_cfdi="G01", forma_pago="03", metodo_pago="PPD",
            clave_prod_serv="23271800", descripcion=descripcion or rng.choice(
                ["Maquinado de piezas", "Fabricación de estructura", "Soldadura industrial", "Corte y doblez"]),
            cantidad=1.0, valor_unitario=subtotal, subtotal=subtotal, iva=iva, total=total, moneda="MXN",
            po_number="", counterparty_id=c.customer_id, approved_by=self.emp("Ventas").employee_id)
        self.e.invoices.append(inv)
        self.gl(d, "1200", "Clientes", total, 0, f"Venta {inv.folio} {c.name}", inv.uuid, "")
        self.gl(d, "4000", "Ventas", 0, subtotal, f"Venta {inv.folio} {c.name}", inv.uuid, "")
        self.gl(d, "2180", "IVA trasladado", 0, iva, f"IVA venta {inv.folio}", inv.uuid, "")
        if pay:
            pd = business_day(d + timedelta(days=rng.randint(*pay_delay)))
            if pd > FY_END:
                pd = FY_END
            self.pay_in(c, pd, total, inv.uuid, f"COBRO F{inv.folio}")
        return inv

    def pay_in(self, c: Customer, d: date, amount: float, invoice_uuid: str, reference: str) -> BankTxn:
        tx = BankTxn(self.nid("TX"), d.isoformat(), COMPANY["clabe"], "in", round(amount, 2),
                     c.name, c.clabe, reference, invoice_uuid)
        self.e.bank.append(tx)
        self.gl(d, "1020", "Bancos", amount, 0, f"Cobro {c.name}", invoice_uuid, tx.txn_id)
        self.gl(d, "1200", "Clientes", 0, amount, f"Cobro {c.name}", invoice_uuid, tx.txn_id)
        return tx

    def gl(self, d: date, code: str, name: str, debit: float, credit: float, desc: str,
           inv_uuid: str, txn_id: str):
        self.e.ledger.append(LedgerEntry(self.nid("GL"), d.isoformat(), code, name, round(debit, 2),
                                         round(credit, 2), desc, inv_uuid, txn_id))

    def cp_txn(self, entity_name: str, entity_clabe: str, d: date, direction: str, amount: float,
               cp_name: str, cp_clabe: str, reference: str):
        self.e.counterparty_bank.append(CounterpartyTxn(
            self.nid("CP"), entity_name, entity_clabe, d.isoformat(), direction, round(amount, 2),
            cp_name, cp_clabe, reference))

    # ---- baseline (honest) activity ---------------------------------------

    def baseline(self):
        rng = self.rng
        # purchases: each supplier has a rhythm
        for s in self.e.suppliers:
            n = rng.randint(4, 24)
            base = rng.choice([8_000, 15_000, 30_000, 60_000, 120_000])
            for _ in range(n):
                d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
                amt = base * rng.uniform(0.4, 1.8)
                amt = round(amt / 10) * 10 + rng.choice([0, 0.5, 12.4, 37.8, 99.9])
                self.purchase_invoice(s, d, amt)
        # sales
        for c in self.e.customers:
            for _ in range(rng.randint(3, 14)):
                d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
                self.sales_invoice(c, d, rng.uniform(40_000, 400_000))
        # payroll + rent noise in bank/ledger
        for m in range(1, 13):
            d = business_day(date(2025, m, 28) if m != 2 else date(2025, 2, 27))
            amt = round(rng.uniform(410_000, 440_000), 2)
            tx = BankTxn(self.nid("TX"), d.isoformat(), COMPANY["clabe"], "out", amt, "NOMINA", "", "NOMINA QUINCENAL", "")
            self.e.bank.append(tx)
            self.gl(d, "6100", "Sueldos y salarios", amt, 0, "Nómina", "", tx.txn_id)
            self.gl(d, "1020", "Bancos", 0, amt, "Nómina", "", tx.txn_id)
        # also an unrelated set of real EFOS entries we never dealt with (noise on the 69-B list)
        for _ in range(60):
            self.e.efos.append({
                "rfc": rfc_moral(rng),
                "nombre": f"{rng.choice(SUPPLIER_WORDS)} {rng.choice(SUPPLIER_TAIL)} {rng.choice(LEGAL)}",
                "situacion": rng.choice(["Presunto", "Definitivo", "Desvirtuado", "Sentencia favorable"]),
                "fecha_publicacion": rand_date(rng, date(2021, 1, 1), FY_END).isoformat()})

    # ---- schemes -----------------------------------------------------------

    def scheme_efos(self):
        """Two fake service suppliers: invoices for 'consultoría', no deliverables, both on 69-B."""
        rng = self.rng
        buyer = self.emp("Gerente de Compras")
        found = []
        total = 0.0
        for k in range(2):
            s = self.make_supplier("servicios", onboarded=rand_date(rng, date(2024, 9, 1), date(2025, 2, 1)),
                                   approved_by=buyer.employee_id)
            invs, txs = [], []
            for _ in range(rng.randint(4, 7)):
                d = business_day(rand_date(rng, date(2025, 2, 1), date(2025, 10, 31)))
                amt = rng.choice([85_000, 120_000, 150_000, 200_000, 250_000])
                inv = self.purchase_invoice(s, d, amt, descripcion=rng.choice(
                    ["Consultoría estratégica", "Servicios de asesoría integral", "Estudio de mercado"]),
                    with_receipt=False, pay_delay=(2, 7))
                invs.append(inv.uuid)
                txs.extend(t.txn_id for t in self.e.bank if t.invoice_uuid == inv.uuid)
                total += inv.total
            # 69-B: one listed before we paid (definitivo), one presunto mid-year
            pub = date(2025, 11, 15) if k == 0 else date(2025, 7, 10)
            self.e.efos.append({"rfc": s.rfc, "nombre": s.name,
                                "situacion": "Definitivo" if k == 0 else "Presunto",
                                "fecha_publicacion": pub.isoformat()})
            found.append({"supplier_id": s.supplier_id, "rfc": s.rfc, "name": s.name,
                          "invoice_uuids": invs, "bank_txn_ids": txs,
                          "efos_status": "Definitivo" if k == 0 else "Presunto"})
        self.e.truth["schemes"].append({
            "type": "efos_fake_supplier",
            "description": "Suppliers invoicing consulting services with no deliverables; both appear on SAT 69-B.",
            "rule": "CFF Art. 69-B (operaciones inexistentes); CFF Art. 29-A; LISR Art. 27 (deducción improcedente)",
            "entities": found,
            "amount_mxn": round(total, 2),
            "how_to_prove": "RFC match on 69-B + invoices with no goods receipt/PO deliverable + paid within days."})

    def scheme_kickback(self):
        """Purchasing manager approves a shell 'gestoría' that pays part back to his personal account."""
        rng = self.rng
        buyer = self.emp("Gerente de Compras")
        shell = self.make_supplier("servicios", name=f"Gestoría y Enlace {rng.choice(SUPPLIER_TAIL)} S de RL de CV",
                                   onboarded=date(2025, 3, 3), street=buyer.home_street, city=buyer.home_city,
                                   approved_by=buyer.employee_id)
        invs, txs, cps = [], [], []
        total = kick = 0.0
        for _ in range(rng.randint(5, 8)):
            d = business_day(rand_date(rng, date(2025, 3, 15), date(2025, 11, 20)))
            amt = rng.choice([48_000, 64_000, 96_000, 128_000])
            inv = self.purchase_invoice(shell, d, amt, descripcion="Servicios de gestión y enlace comercial",
                                        with_receipt=False, pay_delay=(1, 4))
            invs.append(inv.uuid)
            tx = next(t for t in self.e.bank if t.invoice_uuid == inv.uuid)
            txs.append(tx.txn_id)
            total += inv.total
            # shell's own statement: receives from us, sends ~40% to buyer's personal CLABE within days
            self.cp_txn(shell.name, shell.clabe, d + timedelta(days=rng.randint(1, 4)), "in", inv.total,
                        COMPANY["name"], COMPANY["clabe"], tx.reference)
            k = round(inv.total * 0.4, 2)
            kick += k
            kd = business_day(d + timedelta(days=rng.randint(3, 9)))
            self.cp_txn(shell.name, shell.clabe, kd, "out", k, buyer.name, buyer.personal_clabe, "TRANSFERENCIA")
            cps.append(self.e.counterparty_bank[-1].record_id)
        self.e.truth["schemes"].append({
            "type": "kickback_shell",
            "description": "Shell supplier registered at the purchasing manager's home address, approved by him, "
                           "pays ~40% of every invoice to his personal account.",
            "rule": "CFF Art. 69-B; LISR Art. 27-I (no estrictamente indispensable); conflict of interest / "
                    "Ley General de Responsabilidades (private-sector bribery analog, Art. 7 fracc. IX of LFPIORPI where applicable)",
            "entities": [{"supplier_id": shell.supplier_id, "rfc": shell.rfc, "name": shell.name,
                          "employee_id": buyer.employee_id, "employee_name": buyer.name,
                          "invoice_uuids": invs, "bank_txn_ids": txs, "counterparty_record_ids": cps}],
            "amount_mxn": round(total, 2),
            "kickback_mxn": round(kick, 2),
            "how_to_prove": "Supplier address == employee home address; approver == same employee; "
                            "counterparty statement shows outflows to employee's personal CLABE."})

    def scheme_round_trip(self):
        """Fake sales inflate revenue: we pay a 'supplier', it forwards the cash to a 'customer', who pays us."""
        rng = self.rng
        pipe = self.make_supplier("servicios", name=f"Promotora Comercial {rng.choice(LAST)} SA de CV",
                                  onboarded=date(2025, 4, 1))
        st, ct = address(rng)
        cust = Customer(self.nid("C"), f"Comercializadora {rng.choice(LAST)} SAPI de CV", rfc_moral(rng),
                        st, ct, clabe(rng))
        self.e.customers.append(cust)
        legs = []
        total = 0.0
        for _ in range(rng.randint(3, 5)):
            d = business_day(rand_date(rng, date(2025, 5, 1), date(2025, 11, 10)))
            amt = rng.choice([300_000, 450_000, 600_000])
            # leg 1: we "buy" marketing services
            out_inv = self.purchase_invoice(pipe, d, amt, descripcion="Promoción y desarrollo de mercado",
                                            with_receipt=False, pay_delay=(1, 3))
            out_tx = next(t for t in self.e.bank if t.invoice_uuid == out_inv.uuid)
            # leg 2: pipe forwards to customer (counterparty statement)
            d2 = business_day(date.fromisoformat(out_tx.fecha) + timedelta(days=rng.randint(1, 3)))
            self.cp_txn(pipe.name, pipe.clabe, date.fromisoformat(out_tx.fecha), "in", out_inv.total,
                        COMPANY["name"], COMPANY["clabe"], out_tx.reference)
            self.cp_txn(pipe.name, pipe.clabe, d2, "out", out_inv.total * 0.98, cust.name, cust.clabe, "PAGO")
            fwd_id = self.e.counterparty_bank[-1].record_id
            # leg 3: customer "buys" from us for roughly the same amount, pays promptly
            d3 = business_day(d2 + timedelta(days=rng.randint(1, 5)))
            in_inv = self.sales_invoice(cust, d3, amt * 0.98 / (1 + IVA), pay_delay=(1, 4),
                                        descripcion="Fabricación de estructura (lote especial)")
            in_tx = next(t for t in self.e.bank if t.invoice_uuid == in_inv.uuid)
            total += in_inv.total
            legs.append({"purchase_invoice": out_inv.uuid, "out_txn": out_tx.txn_id,
                         "forward_record": fwd_id, "sales_invoice": in_inv.uuid, "in_txn": in_tx.txn_id})
        self.e.truth["schemes"].append({
            "type": "round_trip_sales",
            "description": "Cash leaves as 'marketing services', returns days later as a 'sale' to a customer "
                           "that only ever pays with money it received from the supplier.",
            "rule": "Simulación de operaciones (CFF Art. 69-B / 113 Bis); revenue recognition — fictitious sales",
            "entities": [{"supplier_id": pipe.supplier_id, "supplier_rfc": pipe.rfc,
                          "customer_id": cust.customer_id, "customer_rfc": cust.rfc, "legs": legs}],
            "amount_mxn": round(total, 2),
            "how_to_prove": "Match amounts ±2% across out→forward→in within ~10 days; customer has no other "
                            "trading history; supplier has no deliverables."})

    def scheme_duplicate_payment(self):
        """Legit supplier, real invoices, but three of them were paid twice (once to a different CLABE)."""
        rng = self.rng
        cands = [s for s in self.e.suppliers if s.category in ("materia_prima", "refacciones")
                 and not any(s.supplier_id in json.dumps(x) for x in self.e.truth["schemes"])]
        if not cands:
            scheme_sids = {ent.get("supplier_id") for sc in self.e.truth["schemes"]
                           for ent in sc.get("entities", [])}
            cands = [s for s in self.e.suppliers
                     if sum(1 for i in self.e.invoices if i.counterparty_id == s.supplier_id) >= 3
                     and s.supplier_id not in scheme_sids]
            if not cands:
                raise ValueError(f"seed {self.seed}: no candidate supplier for duplicate payment")
        s = rng.choice(cands)
        invs = [i for i in self.e.invoices if i.counterparty_id == s.supplier_id]
        picks = rng.sample(invs, min(3, len(invs)))
        dup_txs = []
        total = 0.0
        alt_clabe = clabe(rng)
        for inv in picks:
            orig = next(t for t in self.e.bank if t.invoice_uuid == inv.uuid)
            d = business_day(date.fromisoformat(orig.fecha) + timedelta(days=rng.randint(10, 40)))
            if d > FY_END:
                d = FY_END
            tx = BankTxn(self.nid("TX"), d.isoformat(), COMPANY["clabe"], "out", inv.total,
                         s.account_holder, alt_clabe, f"PAGO FACT {inv.folio}", inv.uuid)
            self.e.bank.append(tx)
            self.gl(d, "6000", f"Gastos {s.category}", inv.total, 0, f"Pago factura {inv.folio}", inv.uuid, tx.txn_id)
            self.gl(d, "1020", "Bancos", 0, inv.total, f"Pago factura {inv.folio}", inv.uuid, tx.txn_id)
            dup_txs.append({"invoice_uuid": inv.uuid, "original_txn": orig.txn_id, "duplicate_txn": tx.txn_id})
            total += inv.total
        self.e.truth["schemes"].append({
            "type": "duplicate_invoice_payment",
            "description": "Genuine invoices paid twice; second payment went to a CLABE not on the supplier master "
                           "and was booked straight to expense instead of AP.",
            "rule": "Control failure / possible embezzlement; LISR Art. 27 (deducción duplicada)",
            "entities": [{"supplier_id": s.supplier_id, "rfc": s.rfc, "name": s.name,
                          "alternate_clabe": alt_clabe, "payments": dup_txs}],
            "amount_mxn": round(total, 2),
            "how_to_prove": "Two bank txns referencing the same UUID; second CLABE ≠ master; GL bypasses 2100.",
            "note": "Supplier itself is honest — the accusation should target the payment, not the supplier."})

    def scheme_threshold_splitting(self):
        """One purchase, split into invoices that each sit just under an approval limit.

        The goods are real and the receipts are genuine. The fraud is against the
        company's own control: the purchasing manager may approve up to MXN 250,000, so
        a 900,000 order arrives as four invoices of ~230,000 two days apart and nobody
        above him ever sees it. No single row is odd; only the cluster is.
        """
        rng = self.rng
        buyer = self.emp("Gerente de Compras")
        limit = APPROVAL_LIMIT_SUBTOTAL["Gerente de Compras"]
        vendor = self.make_supplier(
            "refacciones",
            onboarded=rand_date(rng, date(2025, 1, 10), date(2025, 3, 1)),
            approved_by=buyer.employee_id,
        )
        part = rng.choice(["Rodamientos SKF", "Motor eléctrico 5HP", "Válvulas neumáticas"])
        invs, txs, clusters = [], [], []
        total = 0.0
        # Three clusters, each at least 30 days after the previous one.
        start = date(2025, 3, 10)
        for k in range(3):
            base = business_day(start + timedelta(days=k * rng.randint(30, 55)))
            cluster_uuids = []
            for j in range(rng.randint(3, 4)):
                d = business_day(base + timedelta(days=min(j, 2)))
                subtotal = round(rng.uniform(0.80, 0.98) * limit, 2)
                inv = self.purchase_invoice(vendor, d, subtotal, descripcion=part,
                                            with_receipt=True, approved_by=buyer.employee_id)
                cluster_uuids.append(inv.uuid)
                invs.append(inv.uuid)
                txs.extend(t.txn_id for t in self.e.bank if t.invoice_uuid == inv.uuid)
                total += inv.total
            clusters.append(cluster_uuids)
        self.e.truth["schemes"].append({
            "type": "threshold_splitting",
            "description": "Purchases split across same-week invoices that each sit just under the "
                           "purchasing manager's approval limit, so no higher approval was ever sought.",
            "rule": "Fraccionamiento de operaciones para evadir niveles de autorización; "
                    "LGRA / política interna de compras; CFF Art. 83 (comprobantes) — "
                    "approval-limit circumvention",
            "entities": [{"supplier_id": vendor.supplier_id, "rfc": vendor.rfc, "name": vendor.name,
                          "employee_id": buyer.employee_id, "employee_name": buyer.name,
                          "approval_limit": limit, "clusters": clusters,
                          "invoice_uuids": invs, "bank_txn_ids": txs}],
            "amount_mxn": round(total, 2),
            "how_to_prove": "Three or more invoices from one vendor within two business days, each "
                            "between 80% and 100% of the approver's limit, summing well above it."})

    def scheme_revenue_inflation(self):
        """Revenue booked for sales that were never collected, some later cancelled.

        Money never moves, so no bank rule can see it. The tell is in the books: the
        ledger credits 4000 Ventas, no payment ever arrives, and one or two of the
        invoices are cancelled at SAT without anyone reversing the revenue entry.
        """
        rng = self.rng
        st, ct = address(rng)
        cust = Customer(self.nid("C"), f"Comercial {rng.choice(LAST)} SA de CV",
                        rfc_moral(rng), st, ct, clabe(rng))
        self.e.customers.append(cust)
        invs = []
        total = 0.0
        for _ in range(rng.randint(3, 5)):
            d = business_day(rand_date(rng, FY_END - timedelta(days=45), FY_END - timedelta(days=2)))
            # pay=False: the revenue is booked, the cash never arrives.
            inv = self.sales_invoice(cust, d, rng.uniform(150_000, 400_000), pay=False,
                                     descripcion="Fabricación de estructura (pedido especial)")
            invs.append(inv.uuid)
            total += inv.total
        # One or two are cancelled at SAT; the ledger keeps the revenue either way.
        for uuid_ in rng.sample(invs, min(len(invs), rng.randint(1, 2))):
            self.e.cancelled.add(uuid_)
        self.e.truth["schemes"].append({
            "type": "revenue_inflation",
            "description": "Sales invoices to a brand-new customer, booked as revenue, never collected; "
                           "some cancelled at SAT with no reversing ledger entry.",
            "rule": "Ingresos simulados / reconocimiento indebido de ingresos; CFF Art. 69-B / 113 Bis; "
                    "NIF D-1 (ingresos)",
            "entities": [{"customer_id": cust.customer_id, "rfc": cust.rfc, "name": cust.name,
                          "invoice_uuids": invs, "bank_txn_ids": [],
                          "cancelled_uuids": sorted(self.e.cancelled & set(invs))}],
            "amount_mxn": round(total, 2),
            "how_to_prove": "Revenue credited to 4000 with no inbound payment for the invoice, a customer "
                            "with no collection history, and cancellations with no reversing entry."})

    # ---- decoys: honest suppliers that look suspicious ---------------------

    def decoys(self, extra: bool = False):
        """Honest suppliers that trip a detector and check out on inspection.

        ``extra`` adds D6 and D7, which target the newer schemes. They are opt-in
        because they create suppliers, and :func:`renumber` shuffles supplier ids, so
        adding them to every estate would change every id in the frozen company_42.
        """
        rng = self.rng

        # D1: brand-new supplier, round-number invoices, but full delivery trail
        s1 = self.make_supplier("refacciones", onboarded=date(2025, 6, 2))
        for _ in range(5):
            d = business_day(rand_date(rng, date(2025, 6, 16), date(2025, 12, 1)))
            self.purchase_invoice(s1, d, rng.choice([50_000, 100_000, 75_000]), with_receipt=True)
        self.e.truth["decoys"].append({
            "supplier_id": s1.supplier_id, "rfc": s1.rfc, "name": s1.name,
            "looks_like": "New vendor + round amounts (EFOS smell)",
            "why_honest": "Goods receipts exist for every invoice, warehouse-signed; not on 69-B; active RFC."})

        # D2: name nearly identical to a 69-B company, different RFC
        efos_twin = rng.choice([e for e in self.e.efos if e["situacion"] == "Definitivo"])
        s2 = self.make_supplier("consumibles", name=efos_twin["nombre"].replace("SA de CV", "S de RL de CV"))
        for _ in range(8):
            d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
            self.purchase_invoice(s2, d, rng.uniform(6_000, 22_000))
        self.e.truth["decoys"].append({
            "supplier_id": s2.supplier_id, "rfc": s2.rfc, "name": s2.name,
            "looks_like": f"Name almost matches 69-B entry '{efos_twin['nombre']}' ({efos_twin['rfc']})",
            "why_honest": "69-B is matched on RFC, not name. RFC differs; deliveries documented."})

        # D3: supplier at same address as another supplier (shared office park) — not the buyer's home
        pool = ([s for s in self.e.suppliers if s.category == "logistica"]
                or [s for s in self.e.suppliers if s.category in ("renta_util", "servicios")]
                or self.e.suppliers)
        anchor = rng.choice(pool)
        s3 = self.make_supplier("logistica", street=anchor.street, city=anchor.city)
        for _ in range(6):
            d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
            self.purchase_invoice(s3, d, rng.uniform(4_000, 18_000), with_receipt=True,
                                  descripcion="Flete local — carta porte anexa")
        self.e.truth["decoys"].append({
            "supplier_id": s3.supplier_id, "rfc": s3.rfc, "name": s3.name,
            "looks_like": f"Shares address with {anchor.name} ({anchor.supplier_id})",
            "why_honest": "Shared address is a commercial building, not an employee's home; both are real freight "
                          "companies with carta porte on every invoice."})

        # D4: one large one-off legal fee, paid fast, approved by the director — legit
        s4 = self.make_supplier("servicios", name=f"{rng.choice(LAST)} y Asociados SC",
                                approved_by=self.emp("Director General").employee_id)
        d = business_day(date(2025, 8, 14))
        inv = self.purchase_invoice(s4, d, 380_000, descripcion="Honorarios — litigio mercantil exp. 412/2025",
                                    with_receipt=False, pay_delay=(1, 3))
        self.e.truth["decoys"].append({
            "supplier_id": s4.supplier_id, "rfc": s4.rfc, "name": s4.name, "invoice_uuid": inv.uuid,
            "looks_like": "Large one-off service invoice, no goods receipt, paid in days",
            "why_honest": "Law firm; invoice cites a court case number; approved by the director, not purchasing; "
                          "no 69-B match; no related-party links."})

        # D5: legit supplier paid partly in cash (forma_pago 01) — unusual but under the deductibility cap
        scheme_sids = {ent.get("supplier_id") for sc in self.e.truth["schemes"]
                       for ent in sc.get("entities", [])}
        s5 = rng.choice(
            [s for s in self.e.suppliers if s.category == "consumibles" and s.supplier_id != s2.supplier_id]
            or [s for s in self.e.suppliers if s.category == "refacciones" and s.supplier_id != s2.supplier_id]
            or [s for s in self.e.suppliers if s.supplier_id not in (s2.supplier_id,)
                and s.supplier_id not in scheme_sids])
        for _ in range(3):
            d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
            self.purchase_invoice(s5, d, rng.uniform(800, 1_900), forma_pago="01", with_receipt=True)
        self.e.truth["decoys"].append({
            "supplier_id": s5.supplier_id, "rfc": s5.rfc, "name": s5.name,
            "looks_like": "Cash payments (forma_pago 01)",
            "why_honest": "Each cash invoice is under the MXN 2,000 deductibility threshold (LISR Art. 27-III); "
                          "goods received."})

        if not extra:
            return

        buyer = self.emp("Gerente de Compras")
        buyer_bank = buyer.personal_clabe[:3]

        # D6: shares a bank with the purchasing manager. Same three-digit institution
        # code, different account, and no transfer ever passes between the two. A
        # kickback check that matched on bank code instead of account would accuse them.
        s6 = self.make_supplier("materia_prima", onboarded=rand_date(rng, date(2021, 1, 1), date(2024, 6, 1)),
                                clabe_=buyer_bank + "".join(rng.choices(string.digits, k=15)))
        for _ in range(rng.randint(4, 7)):
            d = business_day(rand_date(rng, FY_START, FY_END - timedelta(days=10)))
            self.purchase_invoice(s6, d, rng.uniform(20_000, 90_000), with_receipt=True)
        self.e.truth["decoys"].append({
            "supplier_id": s6.supplier_id, "rfc": s6.rfc, "name": s6.name,
            "looks_like": f"Banks at the same institution as {buyer.name} (bank code {buyer_bank})",
            "why_honest": f"Same bank code {buyer_bank}, different account; no transfer between the two "
                          f"accounts in any statement; every invoice has a goods receipt."})

        # D7: twelve identical monthly invoices just under the approval limit. It looks
        # like threshold splitting until you notice they are one per month, not
        # clustered, and a framework contract fixes the fee.
        limit = APPROVAL_LIMIT_SUBTOTAL["Gerente de Compras"]
        s7 = self.make_supplier("servicios", onboarded=date(2023, 11, 15))
        monthly = round(0.9 * limit, 2)
        for month in range(1, 13):
            d = business_day(date(2025, month, min(5 + rng.randint(0, 3), 28)))
            self.purchase_invoice(s7, d, monthly, descripcion="Mantenimiento preventivo mensual",
                                  with_receipt=False)
        self.e.truth["decoys"].append({
            "supplier_id": s7.supplier_id, "rfc": s7.rfc, "name": s7.name,
            "looks_like": f"Twelve invoices of MXN {monthly:,.2f}, just under the "
                          f"MXN {limit:,.0f} approval limit",
            "why_honest": "One invoice per month under a framework contract that fixes the monthly fee; "
                          "never clustered within days, and the contract is on file."})

    # ---- assembly ----------------------------------------------------------

    def build(self, schemes: list[str]):
        self.make_employees()
        self.make_suppliers()
        self.make_customers()
        self.baseline()
        table = {"efos": self.scheme_efos, "kickback": self.scheme_kickback,
                 "roundtrip": self.scheme_round_trip, "duplicate": self.scheme_duplicate_payment,
                 "threshold": self.scheme_threshold_splitting,
                 "revenue": self.scheme_revenue_inflation}
        for name in schemes:
            table[name]()
        # The two newer decoys (D6, D7) only appear on estates that carry a newer
        # scheme. They add suppliers, and renumber() shuffles supplier ids, so adding
        # them unconditionally would change every id in the frozen company_42 and
        # estate_42. See the PR for #81: the frozen pair predates them.
        self.decoys(extra=any(name in schemes for name in ("threshold", "revenue")))
        self.e.invoices.sort(key=lambda i: i.fecha)
        self.e.bank.sort(key=lambda t: t.fecha)
        self.e.ledger.sort(key=lambda g: g.fecha)
        self.e.counterparty_bank.sort(key=lambda g: g.fecha)
        renumber(self.e, self.rng)
        self.e.truth["meta"] = {"seed": self.seed, "schemes": schemes, "company": COMPANY,
                                "fiscal_year": [FY_START.isoformat(), FY_END.isoformat()],
                                "total_planted_mxn": round(sum(s["amount_mxn"] for s in self.e.truth["schemes"]), 2)}
        return self.e

_ID_RE = re.compile(r"\b(S|C|E|GR|TX|CP|GL|PO)(\d{5})\b")


def renumber(e: Estate, rng: random.Random) -> Estate:
    """Reassign IDs so generation order (baseline first, planted last) is not recoverable.
    Masters get shuffled IDs; dated records get IDs in date order."""
    m: dict[str, str] = {}

    def shuffled(prefix, items, key):
        ids = [getattr(x, key) for x in items]
        new = ids[:]
        rng.shuffle(new)
        m.update(zip(ids, new))

    def by_date(prefix, items, key):
        srt = sorted(items, key=lambda x: (x.fecha, getattr(x, key)))
        for i, x in enumerate(srt, 1):
            m[getattr(x, key)] = f"{prefix}{i:05d}"

    shuffled("S", e.suppliers, "supplier_id")
    shuffled("C", e.customers, "customer_id")
    pos = sorted({i.po_number for i in e.invoices if i.po_number})
    newpos = pos[:]
    rng.shuffle(newpos)
    m.update(zip(pos, newpos))
    by_date("TX", e.bank, "txn_id")
    by_date("GR", e.receipts, "receipt_id")
    by_date("CP", e.counterparty_bank, "record_id")
    by_date("GL", e.ledger, "entry_id")

    def fix(v):
        return _ID_RE.sub(lambda mo: m.get(mo.group(0), mo.group(0)), v) if isinstance(v, str) else v

    for table in (e.suppliers, e.customers, e.employees, e.invoices, e.receipts, e.bank,
                  e.counterparty_bank, e.ledger):
        for r in table:
            for k, v in r.__dict__.items():
                r.__dict__[k] = fix(v)
    e.truth = json.loads(fix(json.dumps(e.truth, ensure_ascii=False)))
    e.suppliers.sort(key=lambda x: x.supplier_id)
    e.customers.sort(key=lambda x: x.customer_id)
    e.bank.sort(key=lambda x: x.txn_id)
    e.receipts.sort(key=lambda x: x.receipt_id)
    e.counterparty_bank.sort(key=lambda x: x.record_id)
    e.ledger.sort(key=lambda x: x.entry_id)
    return e


def write_csv(path: Path, rows, cls=None):
    dicts = [asdict(r) if not isinstance(r, dict) else r for r in rows]
    if cls is not None:
        fields = list(cls.__dataclass_fields__)
    elif dicts:
        fields = list(dicts[0].keys())
    else:
        fields = []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(dicts)


def write_estate(e: Estate, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "suppliers.csv", e.suppliers, Supplier)
    write_csv(out / "customers.csv", e.customers, Customer)
    write_csv(out / "employees.csv", e.employees, Employee)
    write_csv(out / "invoices.csv", e.invoices, Invoice)
    write_csv(out / "goods_receipts.csv", e.receipts, GoodsReceipt)
    write_csv(out / "bank_transactions.csv", e.bank, BankTxn)
    write_csv(out / "counterparty_bank.csv", e.counterparty_bank, CounterpartyTxn)
    write_csv(out / "ledger.csv", e.ledger, LedgerEntry)
    write_csv(out / "efos_69b.csv", e.efos)
    (out / "company.json").write_text(json.dumps(COMPANY, indent=2, ensure_ascii=False))
    hidden = out / "hidden"
    hidden.mkdir(exist_ok=True)
    (hidden / "ground_truth.json").write_text(json.dumps(e.truth, indent=2, ensure_ascii=False))
    (hidden / "README").write_text("Do NOT mount this directory into the agent's workspace.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=1,
                    help="number of consecutive seeds to generate (batch); --n 1 writes to --out directly")
    ap.add_argument("--out", type=Path, default=Path("out/company"))
    ap.add_argument("--schemes", default="efos,kickback,roundtrip,duplicate",
                    help="comma list from: efos,kickback,roundtrip,duplicate (empty string = clean books)")
    ap.add_argument("--format", choices=("legacy", "judges"), default="legacy",
                    help="legacy = our CSV layout (default); judges = estate_schema.sql "
                         "(estate.db + csv/), see data_estate/export_judges.py")
    args = ap.parse_args()
    if args.n < 1:
        ap.error(f"--n must be >= 1 (got {args.n})")
    schemes = [s for s in args.schemes.split(",") if s]
    for s in range(args.seed, args.seed + args.n):
        stem = "estate" if args.format == "judges" else "company"
        out = args.out if args.n == 1 else args.out / f"{stem}_{s}"
        e = Generator(s).build(schemes)
        if args.format == "judges":
            from .export_judges import write_judges_estate
            tables = write_judges_estate(e, out, seed=s, company=COMPANY)
            print(f"wrote {out} (judges' schema): "
                  + ", ".join(f"{len(rows)} {name}" for name, rows in tables.items()))
        else:
            write_estate(e, out)
            print(f"wrote {out}: {len(e.suppliers)} suppliers, {len(e.invoices)} invoices, "
                  f"{len(e.bank)} bank txns, {len(e.ledger)} ledger lines, "
                  f"{len(e.counterparty_bank)} counterparty records")
        print(f"planted: {[t['type'] for t in e.truth['schemes']]}  total {e.truth['meta']['total_planted_mxn']:,.2f} MXN")
        print(f"decoys: {len(e.truth['decoys'])}")


if __name__ == "__main__":
    main()
