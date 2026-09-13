"""Tool layer (#12). The ONLY way the LLM touches data.

Every tool returns JSON-serialisable dicts/list-of-dicts whose rows carry the
record IDs those facts came from, so anything the model cites can be re-checked
by the evidence guard (#14). No tool ever produces a number the model could not
point back to a row. All tools are pure functions of the ``Dataset``: no I/O, no
LLM, never touch ``hidden/``.

Conventions
-----------
- Dates are ISO strings (``YYYY-MM-DD``), money is plain float, quantities int.
- Every list is capped at ``limit`` and sorted deterministically.
- Unknown IDs return ``{"error": "... not found"}`` rather than raising. A
  filter that matches nothing returns ``[]`` (a legitimately empty answer is not
  a lookup failure).
- Output rows carry the record IDs (invoice ``uuid``, ``txn_id``, ``CP*``
  ``record_id``, ``GR*`` ``receipt_id``, ledger ``entry_id``) they were built
  from, so the model always cites IDs that exist in the dataset.
"""
from __future__ import annotations

import statistics
from datetime import timedelta

# Legal-entity suffixes that are stripped for name matching. The 69-B name twin
# trap is "SA de CV" vs "S de RL de CV" vs "SAPI de CV": same trading name, only
# the legal wrapper differs. Match on the stripped stem, never on the raw name.
_NAME_SUFFIXES = (
    "S de RL de CV",
    "S de RL de C.V.",
    "SAPI de CV",
    "SA de CV",
    "S de CV",
    "SC",
)


def _strip_suffix(name: str) -> str:
    n = name.strip()
    for suf in _NAME_SUFFIXES:
        if n.endswith(suf):
            return n[: -len(suf)].strip()
    return n


def _iso(value) -> str:
    """A pandas Timestamp/date/NaT to an ISO date string ('' when empty)."""
    try:
        if value is None:
            return ""
        import pandas as pd
        if pd.isna(value):
            return ""
        return value.date().isoformat()
    except (AttributeError, TypeError, ValueError):
        return ""


def _num(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _strip_entity_prefix(value) -> str:
    """Strip a judges' id prefix so ``RFC:BBBB020202BB2`` and ``BBBB020202BB2``
    compare equal, and an ``EMP:`` id matches its bare form. Legacy ids (``S*``,
    ``C*``, ``E*``) pass through unchanged."""
    v = str(value)
    for prefix in ("RFC:", "EMP:"):
        if v.startswith(prefix):
            return v[len(prefix):]
    return v


def _id_match(stored, query) -> bool:
    """A stored entity id equals the query, allowing for an RFC:/EMP: prefix on
    either side (a judge passes ``RFC:...``, a legacy dataset ``S*``/``E*``)."""
    return str(stored) == str(query) or _strip_entity_prefix(stored) == _strip_entity_prefix(query)


def _bank_code(clabe) -> str:
    """The first three digits of a CLABE — the bank/branch institution code used
    for the same-bank-institution decoy (same bank, different account)."""
    c = str(clabe)
    return c[:3] if len(c) >= 3 else c


def _record_source(ds, record_id: str, fallback: str) -> str:
    """The judges' table a record id lives in, from ``ds.record_table`` (#79)."""
    return ds.record_table.get(record_id, fallback)



class Tools:
    """Deterministic predicates over the dataset. The LLM proposes, these prove."""

    def __init__(self, ds):
        self.ds = ds
        self._inv_by_uuid = ds.invoices.set_index("uuid")
        # Outgoing bank transactions keyed by invoice uuid (first payment timing).
        self._out_by_invoice: dict[str, list] = {}
        if len(ds.bank_transactions):
            out = ds.bank_transactions[
                (ds.bank_transactions["direction"] == "out")
                & (ds.bank_transactions["invoice_uuid"] != "")
            ]
            for t in out.itertuples(index=False):
                self._out_by_invoice.setdefault(t.invoice_uuid, []).append(t)
        # Receipt set: invoice uuids that have at least one goods receipt.
        self._receipt_set = (
            set(ds.goods_receipts["invoice_uuid"]) if len(ds.goods_receipts) else set()
        )
        self._receipts_by_uuid: dict[str, list] = {}
        if len(ds.goods_receipts):
            for r in ds.goods_receipts.itertuples(index=False):
                self._receipts_by_uuid.setdefault(r.invoice_uuid, []).append(r)
        # Vendor RFC -> contract id (#85): a contract covering a vendor means an
        # invoice is not a phantom purchase.
        self._contract_by_rfc: dict[str, str] = {}
        if len(ds.contracts):
            for c in ds.contracts.itertuples(index=False):
                rfc = str(c.vendor_rfc)
                if rfc:
                    self._contract_by_rfc.setdefault(rfc, str(c.contract_id))
        # Inbound payments keyed by invoice uuid (collected / days_to_collect).
        self._in_by_invoice: dict[str, list] = {}
        if len(ds.bank_transactions):
            inn = ds.bank_transactions[
                (ds.bank_transactions["direction"] == "in")
                & (ds.bank_transactions["invoice_uuid"] != "")
            ]
            for t in inn.itertuples(index=False):
                self._in_by_invoice.setdefault(t.invoice_uuid, []).append(t)

    # ---- lookups ---------------------------------------------------------

    def get_supplier(self, supplier_id: str) -> dict:
        """The master supplier row plus EFOS status, invoice stats and employee links."""
        if not len(self.ds.suppliers):
            return {"error": f"{supplier_id} not found"}
        sup = self.ds.suppliers[
            self.ds.suppliers["supplier_id"].map(lambda x: _id_match(x, supplier_id))
        ]
        if not len(sup):
            sup = self.ds.suppliers[self.ds.suppliers["rfc"].astype(str) == str(supplier_id)]
        if not len(sup):
            return {"error": f"{supplier_id} not found"}
        s = next(iter(sup.itertuples(index=False)))

        # EFOS 69-B status on exact RFC.
        efos = {"listed": False, "situacion": "", "fecha_publicacion": ""}
        if len(self.ds.efos_69b):
            efos_rows = self.ds.efos_69b[self.ds.efos_69b["rfc"] == s.rfc]
            if len(efos_rows):
                pick = efos_rows.sort_values("fecha_publicacion").iloc[-1]
                efos = {
                    "listed": True,
                    "situacion": str(pick.situacion),
                    "fecha_publicacion": _iso(pick.fecha_publicacion),
                }

        # Invoice stats over this supplier's received (purchase) invoices.
        sub = self.ds.invoices[
            (self.ds.invoices["counterparty_id"] == supplier_id)
            & (self.ds.invoices["tipo"] == "recibida")
        ] if len(self.ds.invoices) else self.ds.invoices

        n_invoices = int(len(sub))
        total_mxn = float(sub["total"].sum()) if n_invoices else 0.0
        first_invoice = _iso(sub["fecha"].min()) if n_invoices else ""
        last_invoice = _iso(sub["fecha"].max()) if n_invoices else ""
        n_with_receipt = sum(1 for u in sub["uuid"] if u in self._receipt_set)
        days: list[int] = []
        for u in sub["uuid"]:
            txns = self._out_by_invoice.get(u, [])
            if txns:
                first = min(t.fecha for t in txns)
                inv_row = self._inv_by_uuid.loc[u]
                days.append(max(0, (first - inv_row.fecha).days))
        median_days_to_pay = statistics.median(days) if days else None

        # Deliverable trail (#85): does the vendor actually deliver? POs and a
        # contract are the judges' version of "goods on the books".
        n_with_po = int((sub["po_number"].astype(str) != "").sum()) if n_invoices else 0
        supplier_rfc = str(s.rfc)
        n_contracts = int(supplier_rfc in self._contract_by_rfc)

        # Approvers: who signed off each invoice (the judge asks who approved).
        approvers: list[dict] = []
        if n_invoices:
            grouped: dict[str, int] = {}
            for emp in sub["approved_by"]:
                key = str(emp)
                if key:
                    grouped[key] = grouped.get(key, 0) + 1
            role_by_id: dict[str, str] = {}
            if len(self.ds.employees):
                for e in self.ds.employees.itertuples(index=False):
                    role_by_id[str(e.employee_id)] = str(e.role)
            approvers = [
                {"employee_id": emp_id, "role": role_by_id.get(emp_id, ""), "n_invoices": cnt}
                for emp_id, cnt in sorted(grouped.items())
            ]

        # Employee links: same home address, same CLABE, or the approver.
        links: list[dict] = []
        if len(self.ds.employees):
            for e in self.ds.employees.itertuples(index=False):
                emp_id = str(e.employee_id)
                if str(e.home_street) == str(s.street) and str(e.home_city) == str(s.city):
                    links.append({"employee_id": emp_id, "kind": "address",
                                  "detail": f"home {e.home_street}, {e.home_city}"})
                if str(e.personal_clabe) == str(s.clabe):
                    links.append({"employee_id": emp_id, "kind": "clabe",
                                  "detail": "personal CLABE == supplier account"})
                if (_bank_code(e.personal_clabe) == _bank_code(s.clabe)
                        and str(e.personal_clabe) != str(s.clabe)):
                    links.append({"employee_id": emp_id, "kind": "same_bank",
                                  "detail": "same bank institution, different account"})
                if str(e.employee_id) == str(s.approved_by):
                    links.append({"employee_id": emp_id, "kind": "approver",
                                  "detail": f"approved onboarding ({e.role})"})

        return {
            "supplier_id": str(s.supplier_id),
            "name": str(s.name),
            "rfc": str(s.rfc),
            "street": str(s.street),
            "city": str(s.city),
            "clabe": str(s.clabe),
            "account_holder": str(s.account_holder),
            "category": str(s.category),
            "onboarded": _iso(s.onboarded) if str(s.onboarded) else "",
            "approved_by": str(s.approved_by),
            "status": str(s.status),
            "efos": efos,
            "stats": {
                "n_invoices": n_invoices,
                "total_mxn": round(total_mxn, 2),
                "first_invoice": first_invoice,
                "last_invoice": last_invoice,
                "n_with_receipt": n_with_receipt,
                "median_days_to_pay": median_days_to_pay,
            },
            "deliverable_trail": {
                "n_invoices": n_invoices,
                "n_with_po": n_with_po,
                "n_with_receipt": n_with_receipt,
                "n_contracts": n_contracts,
            },
            "approvers": approvers,
            "employee_links": links,
        }

    def get_customer(self, customer_id: str) -> dict:
        """The master customer row plus sales-invoice stats."""
        if not len(self.ds.customers):
            return {"error": f"{customer_id} not found"}
        cus = self.ds.customers[
            self.ds.customers["customer_id"].map(lambda x: _id_match(x, customer_id))
        ]
        if not len(cus):
            return {"error": f"{customer_id} not found"}
        c = next(iter(cus.itertuples(index=False)))
        sub = self.ds.invoices[
            (self.ds.invoices["counterparty_id"] == customer_id)
            & (self.ds.invoices["tipo"] == "emitida")
        ] if len(self.ds.invoices) else self.ds.invoices
        n = int(len(sub))
        return {
            "customer_id": str(c.customer_id),
            "name": str(c.name),
            "rfc": str(c.rfc),
            "street": str(c.street),
            "city": str(c.city),
            "clabe": str(c.clabe),
            "stats": {
                "n_invoices": n,
                "total_mxn": round(float(sub["total"].sum()), 2) if n else 0.0,
                "first_invoice": _iso(sub["fecha"].min()) if n else "",
                "last_invoice": _iso(sub["fecha"].max()) if n else "",
            },
        }

    def get_employee(self, employee_id: str) -> dict:
        """The master employee row plus any suppliers they are linked to."""
        if not len(self.ds.employees):
            return {"error": f"{employee_id} not found"}
        rows = self.ds.employees[
            self.ds.employees["employee_id"].map(lambda x: _id_match(x, employee_id))
        ]
        if not len(rows):
            return {"error": f"{employee_id} not found"}
        e = next(iter(rows.itertuples(index=False)))
        # Money from vendors landing on this employee's account (the kickback
        # tell); and the bank institution code, so the model can see same-bank.
        n_from_vendors = 0
        if len(self.ds.counterparty_bank):
            n_from_vendors = int(
                (self.ds.counterparty_bank["counterparty_clabe"].astype(str)
                 == str(e.personal_clabe)).sum()
            )
        supplier_links: list[str] = []
        if len(self.ds.suppliers):
            sup = self.ds.suppliers
            m = sup[
                (sup["approved_by"] == employee_id)
                | ((sup["street"].astype(str) == str(e.home_street))
                   & (sup["city"].astype(str) == str(e.home_city)))
                | (sup["clabe"].astype(str) == str(e.personal_clabe))
            ]
            supplier_links = sorted(str(x) for x in m["supplier_id"])
        return {
            "employee_id": str(e.employee_id),
            "name": str(e.name),
            "rfc": str(e.rfc),
            "role": str(e.role),
            "home_street": str(e.home_street),
            "home_city": str(e.home_city),
            "personal_clabe": str(e.personal_clabe),
            "bank_code": _bank_code(e.personal_clabe),
            "n_transfers_received_from_vendors": n_from_vendors,
            "linked_suppliers": supplier_links,
        }

    # ---- invoices / receipts --------------------------------------------

    def get_invoices(self, counterparty_id: str, limit: int = 50) -> list[dict]:
        """Invoices for a counterparty, with receipt/payment facts attached."""
        if not len(self.ds.invoices):
            return []
        sub = self.ds.invoices[self.ds.invoices["counterparty_id"].map(
            lambda x: _id_match(x, counterparty_id)
        )]
        sub = sub.sort_values(["fecha", "uuid"]).head(limit)
        drop = {"nombre_emisor", "nombre_receptor", "moneda", "serie"}
        rows: list[dict] = []
        for r in sub.itertuples(index=False):
            uuid = str(r.uuid)
            receipt_ids = sorted(
                str(x.receipt_id) for x in self._receipts_by_uuid.get(uuid, [])
            )
            payer = self._out_by_invoice.get(uuid, [])
            paid_by = sorted(str(t.txn_id) for t in payer)
            days_to_pay = None
            if payer:
                first_pay = min(t.fecha for t in payer)
                days_to_pay = max(0, (first_pay - r.fecha).days)
            row = {k: getattr(r, k) for k in r._fields if k not in drop}
            for k in ("uuid", "po_number", "counterparty_id", "approved_by",
                      "rfc_emisor", "rfc_receptor", "uso_cfdi", "forma_pago",
                      "metodo_pago", "clave_prod_serv", "descripcion"):
                row[k] = str(row[k])
            row["fecha"] = _iso(r.fecha)
            row["fecha_timbrado"] = _iso(r.fecha_timbrado)
            for k in ("cantidad", "valor_unitario", "subtotal", "iva", "total"):
                row[k] = float(row[k])
            row["has_receipt"] = uuid in self._receipt_set
            row["receipt_ids"] = receipt_ids
            row["paid_by"] = paid_by
            row["days_to_pay"] = days_to_pay
            # Judge-estate extras (#85): status, the PO it settles, the contract
            # covering the vendor, and whether a sale was ever collected.
            row["status"] = str(getattr(r, "status", ""))
            row["po_id"] = str(getattr(r, "po_number", ""))
            row["contract_id"] = (
                self._contract_by_rfc.get(str(getattr(r, "rfc_emisor", "")), "")
                if str(getattr(r, "tipo", "")) == "recibida"
                else ""
            )
            inn = self._in_by_invoice.get(uuid, [])
            row["collected"] = bool(inn)
            row["days_to_collect"] = (
                max(0, (min(t.fecha for t in inn) - r.fecha).days) if inn else None
            )
            rows.append(row)
        return rows

    def get_receipts(self, invoice_uuid: str) -> list[dict]:
        """Goods receipts for an invoice (the deliverable proof)."""
        recs = self._receipts_by_uuid.get(invoice_uuid, [])
        recs = sorted(recs, key=lambda r: str(r.receipt_id))
        out: list[dict] = []
        for r in recs:
            out.append({
                "receipt_id": str(r.receipt_id),
                "po_number": str(r.po_number),
                "supplier_id": str(r.supplier_id),
                "invoice_uuid": str(r.invoice_uuid),
                "fecha": _iso(r.fecha),
                "descripcion": str(r.descripcion),
                "cantidad": float(r.cantidad),
                "received_by": str(r.received_by),
                "warehouse": str(r.warehouse),
            })
        return out

    # ---- bank / ledger ----------------------------------------------------

    def get_bank_txns(self, *, counterparty_clabe: str = "", invoice_uuid: str = "",
                      direction: str = "", limit: int = 100) -> list[dict]:
        """Bank transactions filtered by any combination of the keyword args."""
        if not len(self.ds.bank_transactions):
            return []
        bank = self.ds.bank_transactions
        if counterparty_clabe:
            bank = bank[bank["counterparty_clabe"].astype(str) == str(counterparty_clabe)]
        if invoice_uuid:
            bank = bank[bank["invoice_uuid"].astype(str) == str(invoice_uuid)]
        if direction:
            bank = bank[bank["direction"].astype(str) == str(direction)]
        bank = bank.sort_values(["fecha", "txn_id"]).head(limit)
        out: list[dict] = []
        for r in bank.itertuples(index=False):
            out.append({
                "txn_id": str(r.txn_id),
                "fecha": _iso(r.fecha),
                "account_clabe": str(r.account_clabe),
                "direction": str(r.direction),
                "amount": float(r.amount),
                "counterparty_name": str(r.counterparty_name),
                "counterparty_clabe": str(r.counterparty_clabe),
                "reference": str(r.reference),
                "invoice_uuid": str(r.invoice_uuid),
            })
        return out

    def query_ledger(self, *, invoice_uuid: str = "", txn_id: str = "",
                     account_code: str = "", limit: int = 100) -> list[dict]:
        """Ledger rows filtered by any combination of the keyword args."""
        if not len(self.ds.ledger):
            return []
        ledger = self.ds.ledger
        if invoice_uuid:
            ledger = ledger[ledger["invoice_uuid"].astype(str) == str(invoice_uuid)]
        if txn_id:
            ledger = ledger[ledger["txn_id"].astype(str) == str(txn_id)]
        if account_code:
            ledger = ledger[ledger["account_code"].astype(str) == str(account_code)]
        ledger = ledger.sort_values(["fecha", "entry_id"]).head(limit)
        out: list[dict] = []
        for r in ledger.itertuples(index=False):
            out.append({
                "entry_id": str(r.entry_id),
                "fecha": _iso(r.fecha),
                "account_code": str(r.account_code),
                "account_name": str(r.account_name),
                "debit": float(r.debit),
                "credit": float(r.credit),
                "descripcion": str(r.descripcion),
                "invoice_uuid": str(r.invoice_uuid),
                "txn_id": str(r.txn_id),
            })
        return out

    # ---- 69-B -------------------------------------------------------------

    def check_69b(self, rfc: str) -> dict:
        """Is this RFC on the 69-B list, and what entries share its name (ignoring suffix)?

        The exact RFC decides ``listed``. ``name_matches`` exists so the model can
        SEE the name-twin decoy and explain why it is not a match.
        """
        # Resolve the supplier carrying this RFC so we can compare names.
        supplier_name = ""
        if len(self.ds.suppliers):
            sup = self.ds.suppliers[self.ds.suppliers["rfc"].astype(str) == str(rfc)]
            if len(sup):
                supplier_name = str(sup.itertuples(index=False).__next__().name)

        listed = False
        situacion = ""
        fecha = ""
        nombre = ""
        matches: list[dict] = []
        if len(self.ds.efos_69b):
            rows = self.ds.efos_69b[self.ds.efos_69b["rfc"].astype(str) == str(rfc)]
            if len(rows):
                pick = rows.sort_values("fecha_publicacion").iloc[-1]
                listed = True
                situacion = str(pick.situacion)
                fecha = _iso(pick.fecha_publicacion)
                nombre = str(pick.nombre)

            # name_matches: entries whose stripped nombre equals the supplier's
            # stripped name (only meaningful when we know the supplier's name).
            if supplier_name:
                stem = _strip_suffix(supplier_name)
                for e in self.ds.efos_69b.itertuples(index=False):
                    if _strip_suffix(str(e.nombre)) == stem:
                        matches.append({
                            "rfc": str(e.rfc),
                            "nombre": str(e.nombre),
                            "situacion": str(e.situacion),
                        })
            matches.sort(key=lambda m: (m["rfc"], m["nombre"]))

        return {
            "rfc": str(rfc),
            "listed": listed,
            "situacion": situacion,
            "fecha_publicacion": fecha,
            "nombre": nombre,
            "name_matches": matches,
        }

    # ---- money flow -------------------------------------------------------

    def trace_flow(self, clabe: str, *, days: int = 10, min_ratio: float = 0.8,
                   depth: int = 2) -> list[dict]:
        """Follow money leaving a CLABE through its counterparty's statement.

        Hops start at ``counterparty_bank`` rows with ``entity_clabe == clabe``
        and ``direction == 'out'`` (money leaving that entity) **and** at the
        company's own ``bank_transactions`` ``out`` rows whose ``account_clabe``
        is this CLABE, then follow the destination ``counterparty_clabe`` up to
        ``depth``. Each hop reports whether the money returns to the company
        (true when a later ``bank_transactions`` ``in`` row from that destination
        CLABE exists within ``days`` at >= ``min_ratio`` of the forwarded amount)
        and, on a judges' estate, the ``source_table`` the record id lives in.
        """
        cb = self.ds.counterparty_bank
        bank = self.ds.bank_transactions
        if not len(cb) and not len(bank):
            return []

        def _out_rows(from_clabe):
            rows: list[dict] = []
            if len(cb):
                sel = cb[
                    (cb["entity_clabe"].astype(str) == str(from_clabe))
                    & (cb["direction"].astype(str) == "out")
                ].sort_values(["fecha", "record_id"])
                for r in sel.itertuples(index=False):
                    rid = str(r.record_id)
                    rows.append({
                        "record_id": rid,
                        "source_table": _record_source(self.ds, rid, "counterparty_bank"),
                        "fecha": r.fecha,
                        "to_clabe": str(r.counterparty_clabe),
                        "amount": float(r.amount),
                        "counterparty_name": str(r.counterparty_name),
                    })
            if len(bank):
                sel = bank[
                    (bank["account_clabe"].astype(str) == str(from_clabe))
                    & (bank["direction"].astype(str) == "out")
                ].sort_values(["fecha", "txn_id"])
                for r in sel.itertuples(index=False):
                    rid = str(r.txn_id)
                    rows.append({
                        "record_id": rid,
                        "source_table": _record_source(self.ds, rid, "bank_txns"),
                        "fecha": r.fecha,
                        "to_clabe": str(r.counterparty_clabe),
                        "amount": float(r.amount),
                        "counterparty_name": str(r.counterparty_name),
                    })
            # A leg never appears in both tables; keep the first, sort by date.
            uniq: dict[str, dict] = {}
            for row in rows:
                uniq.setdefault(row["record_id"], row)
            return [uniq[k] for k in sorted(uniq, key=lambda k: (uniq[k]["fecha"], k))]

        hops: list[dict] = []
        seen_records: set[str] = set()

        def _walk(from_clabe, hop_num):
            for r in _out_rows(from_clabe):
                rec_id = r["record_id"]
                if rec_id in seen_records:
                    continue
                seen_records.add(rec_id)
                to_clabe = r["to_clabe"]
                amt = r["amount"]
                fecha = r["fecha"]

                # returns_to_company: later company bank deposit from to_clabe.
                returns = False
                if len(bank) and to_clabe:
                    later = bank[
                        (bank["direction"].astype(str) == "in")
                        & (bank["counterparty_clabe"].astype(str) == to_clabe)
                        & (bank["fecha"] >= fecha)
                        & (bank["fecha"] <= fecha + timedelta(days=days))
                    ]
                    returns = bool(
                        len(later) and max(float(t.amount) for t in later.itertuples(index=False))
                        >= min_ratio * amt
                    )

                hops.append({
                    "hop": hop_num,
                    "record_id": rec_id,
                    "source_table": r["source_table"],
                    "fecha": _iso(fecha),
                    "from_clabe": str(from_clabe),
                    "to_clabe": to_clabe,
                    "amount": round(amt, 2),
                    "counterparty_name": r["counterparty_name"],
                    "returns_to_company": returns,
                })
                if hop_num < depth and to_clabe:
                    _walk(to_clabe, hop_num + 1)

        _walk(clabe, 1)
        hops.sort(key=lambda h: (h["hop"], h["fecha"], h["record_id"]))
        return hops

    def get_purchase_orders(self, *, vendor_id: str = "", invoice_uuid: str = "",
                            limit: int = 50) -> list[dict]:
        """Purchase orders for a vendor or for the PO an invoice settles.

        On a judges' estate the ``purchase_orders`` table is the deliverable trail
        (a PO is the only proof the goods were ordered). On a legacy dataset the
        table does not exist, so this returns a single ``note`` row.
        """
        pos = self.ds.purchase_orders
        if not len(pos):
            if self.ds.source_format == "legacy":
                return [{"note": "no purchase_orders table in this estate"}]
            return []
        out = pos
        if vendor_id:
            q = str(vendor_id)
            out = out[out["vendor_rfc"].astype(str).map(
                lambda r: _id_match(r, q) or r == _strip_entity_prefix(q)
            )]
        if invoice_uuid:
            po_ids: set[str] = set()
            inv = self.ds.invoices[self.ds.invoices["uuid"].astype(str) == str(invoice_uuid)]
            if len(inv):
                pn = str(inv.iloc[0].get("po_number", ""))
                if pn:
                    po_ids.add(pn)
            out = out[out["po_id"].astype(str).isin(po_ids)]
        out = out.sort_values("po_id").head(limit)
        rows: list[dict] = []
        for r in out.itertuples(index=False):
            rfc = str(r.vendor_rfc)
            rows.append({
                "po_id": str(r.po_id),
                "vendor_id": ("RFC:" + rfc) if rfc else "",
                "vendor_rfc": rfc,
                "date": _iso(r.date),
                "amount": float(r.amount),
                "requester": str(r.requester),
                "approver": str(r.approver),
                "description": str(r.description),
            })
        return rows

    def get_contracts(self, vendor_id: str) -> list[dict]:
        """Contracts covering a vendor.

        A contract is the judges' proof that a supplier relationship was long-
        term and legitimate, so the model can see (and dismiss) the same-bank
        decoy. On a legacy dataset the table does not exist.
        """
        cnts = self.ds.contracts
        if not len(cnts):
            if self.ds.source_format == "legacy":
                return [{"note": "no contracts table in this estate"}]
            return []
        q = str(vendor_id)
        out = cnts[cnts["vendor_rfc"].astype(str).map(
            lambda r: _id_match(r, q) or r == _strip_entity_prefix(q)
        )]
        out = out.sort_values("contract_id")
        rows: list[dict] = []
        for r in out.itertuples(index=False):
            rfc = str(r.vendor_rfc)
            rows.append({
                "contract_id": str(r.contract_id),
                "vendor_id": ("RFC:" + rfc) if rfc else "",
                "vendor_rfc": rfc,
                "start_date": _iso(r.start_date),
                "value": float(r.value),
                "scope_text": str(r.scope_text),
            })
        return rows


# ---- OpenAI function-calling schemas ------------------------------------

def _schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


_TOOLS = [
    _schema(
        "get_supplier",
        "Get one supplier's master row, its SAT 69-B status, invoice stats "
        "(count, total MXN, first/last invoice, median days-to-pay, "
        "deliverable_trail: invoices with a PO/receipt/contract), the approvers "
        "who signed off its invoices, and any links to employees (same home "
        "address, same CLABE, same bank institution, or who approved onboarding). "
        "Every figure is traceable to record IDs. Accepts supplier_id (e.g. "
        "'S00004'), a judges' id (e.g. 'RFC:BBBB020202BB2'), or a bare RFC.",
        {"supplier_id": {"type": "string", "description": "The supplier_id or RFC to look up."}},
        ["supplier_id"],
    ),
    _schema(
        "get_customer",
        "Get one customer's master row and sales-invoice stats.",
        {"customer_id": {"type": "string", "description": "The customer_id to look up."}},
        ["customer_id"],
    ),
    _schema(
        "get_employee",
        "Get one employee's master row (including bank_code and how many "
        "transfers from vendors land on their account) and any suppliers they "
        "are linked to (via approval, matching home address, matching CLABE, or "
        "same bank). Accepts employee_id (e.g. 'E00002') or a judges' id "
        "(e.g. 'EMP:0001').",
        {"employee_id": {"type": "string", "description": "The employee_id to look up."}},
        ["employee_id"],
    ),
    _schema(
        "get_invoices",
        "List the invoices for a counterparty (supplier or customer), each with "
        "status, the PO it settles (po_id), the contract covering the vendor "
        "(contract_id), whether it has a goods receipt, the receipt IDs, the bank "
        "txns that paid it, days-to-pay, and for sales whether it was collected "
        "(collected) and days-to-collect. Capped and sorted. Accepts supplier_id / "
        "customer_id (e.g. 'S00004') or a judges' id (e.g. 'RFC:BBBB020202BB2').",
        {
            "counterparty_id": {"type": "string", "description": "supplier_id, customer_id or RFC id."},
            "limit": {"type": "integer", "description": "Max rows (default 50)."},
        },
        ["counterparty_id"],
    ),
    _schema(
        "get_bank_txns",
        "List bank transactions on the company account, filtered by any "
        "combination of counterparty CLABE, invoice UUID and direction. Returns "
        "txn_id, fecha, amount, direction, counterparty and reference.",
        {
            "counterparty_clabe": {"type": "string", "description": "The counterparty CLABE."},
            "invoice_uuid": {"type": "string", "description": "The invoice UUID."},
            "direction": {"type": "string", "description": "'in' or 'out'."},
            "limit": {"type": "integer", "description": "Max rows (default 100)."},
        },
        [],
    ),
    _schema(
        "get_receipts",
        "Goods receipts (deliverables) for an invoice.",
        {"invoice_uuid": {"type": "string", "description": "The invoice UUID."}},
        ["invoice_uuid"],
    ),
    _schema(
        "check_69b",
        "Check an RFC against SAT's 69-B list. 'listed' is on the exact RFC; "
        "'name_matches' lists 69-B entries whose name equals this RFC's holder "
        "ignoring the legal suffix (SA de CV vs S de RL de CV vs SAPI de CV). "
        "Use 'name_matches' to see a name-twin and explain why it is not a match.",
        {"rfc": {"type": "string", "description": "The RFC to check."}},
        ["rfc"],
    ),
    _schema(
        "trace_flow",
        "Follow money leaving a CLABE through its counterparty bank statement, "
        "hop by hop. Each hop has record_id, source_table, fecha, from/to CLABE, "
        "amount and 'returns_to_company' (true when the company later receives "
        ">= min_ratio of the amount back from that CLABE within days).",
        {
            "clabe": {"type": "string", "description": "The starting CLABE."},
            "days": {"type": "integer", "description": "Lookback window (default 10)."},
            "min_ratio": {"type": "number", "description": "Return ratio (default 0.8)."},
            "depth": {"type": "integer", "description": "Max hops (default 2)."},
        },
        ["clabe"],
    ),
    _schema(
        "query_ledger",
        "Query the general ledger, filtered by invoice UUID, txn ID and/or "
        "account code. Shows whether a payment was booked to AP (2100) or "
        "straight to expense (6000).",
        {
            "invoice_uuid": {"type": "string", "description": "The invoice UUID."},
            "txn_id": {"type": "string", "description": "The bank txn ID."},
            "account_code": {"type": "string", "description": "The account code, e.g. '2100'."},
            "limit": {"type": "integer", "description": "Max rows (default 100)."},
        },
        [],
    ),
    _schema(
        "get_purchase_orders",
        "Purchase orders for a vendor, or for the PO an invoice settles. A PO is "
        "the deliverable trail on a judges' estate. Takes vendor_id (supplier_id, "
        "'RFC:...' or a bare RFC) and/or invoice_uuid. On a legacy dataset returns "
        "a note that the table does not exist.",
        {
            "vendor_id": {"type": "string", "description": "The vendor id / RFC."},
            "invoice_uuid": {"type": "string", "description": "An invoice UUID to find the PO it settles."},
            "limit": {"type": "integer", "description": "Max rows (default 50)."},
        },
        [],
    ),
    _schema(
        "get_contracts",
        "Contracts covering a vendor. A contract is proof of a long-term, "
        "legitimate supplier relationship. Takes vendor_id (supplier_id, "
        "'RFC:...' or a bare RFC). On a legacy dataset returns a note that the "
        "table does not exist.",
        {"vendor_id": {"type": "string", "description": "The vendor id / RFC."}},
        ["vendor_id"],
    ),
]

TOOL_SCHEMAS: list[dict] = _TOOLS
