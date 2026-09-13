"""detect_name_twin_69b: suppliers whose *name* matches a 69-B listing but whose RFC differs.

This is the mirror image of ``detect_efos`` (#4). 69-B is matched on RFC, never on name — so
a real business that happens to share a name with a blacklisted one walks free. This detector
finds exactly that class: a supplier whose ``name`` is identical to a live 69-B entry's
``nombre`` but whose ``rfc`` is different. It is a deliberately **weak signal**: sharing a name
with a listed company is a coincidence, not proof of fraud. The lead carries the exonerating
facts (the differing RFC, the listing's situation, whether the invoices were actually received)
so the investigation loop can show, on record, that it looked and why it walked away. The
detector never decides.

Rules, deliberately strict so it stays honest:

- **Exact name match only** (``name.strip() == nombre.strip()``), case-sensitive. No fuzzy or
  suffix-normalised matching: normalising ``SA de CV`` / ``SAPI de CV`` / ``S de RL de CV``
  collides because the generator draws names from a small vocabulary.
- **Live situation only** (``Presunto``/``Definitivo``). ``Desvirtuado`` / ``Sentencia
  favorable`` were cleared by SAT and are not leads.
- **RFC must differ.** Equal RFC is ``detect_efos``'s job and must not be duplicated here.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``. Output is deterministic:
one dict per supplier, sorted by ``entity_id``.
"""
from __future__ import annotations

ACTIVE_SITUACIONES = ("Presunto", "Definitivo")


def detect_name_twin_69b(ds, **params) -> list[dict]:
    """Return one lead per supplier whose name matches a live 69-B entry but whose RFC differs.

    Steps:
    1. Inner-join ``ds.suppliers`` to ``ds.efos_69b`` on ``name.strip() == nombre.strip()``
       (exact, case-sensitive).
    2. Keep rows whose ``situacion`` is ``Presunto``/``Definitivo`` and whose ``rfc`` differs
       from the listing's ``rfc``.
    3. A supplier may match several list rows: take the row with the latest
       ``fecha_publicacion``.

    One dict per supplier, sorted by ``entity_id``:

        entity_id · name · rfc · listed_rfc · listed_nombre · situacion ·
        fecha_publicacion (ISO) · rfc_listed (False) · n_invoices · total_mxn ·
        n_with_receipt · evidence
    """
    sup = ds.suppliers[["supplier_id", "name", "rfc"]].copy()
    sup["_name"] = sup["name"].str.strip()

    listed = ds.efos_69b.copy()
    listed["_nombre"] = listed["nombre"].str.strip()
    listed = listed[listed["situacion"].isin(ACTIVE_SITUACIONES)]

    matches = sup.merge(listed, how="inner", left_on="_name", right_on="_nombre")
    matches = matches[matches["rfc_x"] != matches["rfc_y"]]  # rfc_x = supplier, rfc_y = listing

    # receipt_set: invoice uuids that were actually received.
    receipt_set = set(ds.goods_receipts["invoice_uuid"]) if len(ds.goods_receipts) else set()
    recibida = ds.invoices[ds.invoices["tipo"] == "recibida"] if len(ds.invoices) else ds.invoices

    rows: list[dict] = []
    # Group by supplier; prefer the latest fecha_publicacion if several list rows matched.
    for supplier_id, grp in matches.groupby("supplier_id"):
        pick = grp.sort_values("fecha_publicacion").iloc[-1]

        sub = recibida[recibida["counterparty_id"] == supplier_id]
        invoice_uuids = sorted(str(u) for u in sub["uuid"])
        n_with_receipt = sum(1 for u in invoice_uuids if u in receipt_set)

        rows.append(
            {
                "entity_id": str(supplier_id),
                "name": str(pick["name"]),
                "rfc": str(pick["rfc_x"]),
                "listed_rfc": str(pick["rfc_y"]),
                "listed_nombre": str(pick["nombre"]),
                "situacion": str(pick["situacion"]),
                "fecha_publicacion": pick["fecha_publicacion"].date().isoformat(),
                "rfc_listed": False,
                "n_invoices": int(len(sub)),
                "total_mxn": float(sub["total"].sum()) if len(sub) else 0.0,
                "n_with_receipt": int(n_with_receipt),
                "evidence": invoice_uuids,
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
