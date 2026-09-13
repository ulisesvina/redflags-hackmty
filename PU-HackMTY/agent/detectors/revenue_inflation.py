"""detect_revenue_inflation: sales booked as revenue that were never collected.

The judges' ``revenue_inflation`` type: fictitious sales. In the books it is
revenue in the ledger (account 4000) with no cash ever arriving, and invoices
cancelled at SAT after the fact while the revenue entry stays. The tell is in
the books, not the bank: the ledger credits 4000 Ventas, no payment ever
arrives for the invoice, and one or two invoices are cancelled without any
reversing debit.

Every returned dict is a *lead*, not an accusation. It names the customer whose
revenue was booked but never collected, the invoices, and the counts. A single
uncollected invoice is not a violation — a *customer with no collection history*
(or with cancellations never reversed) is, and that is exactly what separates
``customer_history == 0`` (fresh customer, nothing ever paid) from a regular
customer whose last invoice is still open at year end.

Pure function of the Dataset: no I/O, no LLM, never reads ``hidden/``. The
output is deterministic, sorted by ``entity_id``.

Two independent triggers, both requiring the revenue to be booked (a 4000
credit in the ledger):
* **not collected and recent**: no inbound bank row for the invoice, and either
  ``grace_days`` have passed since ``fecha`` (within the data's last date) or it
  was issued within ``period_end_days`` of the last invoice date;
* **cancelled without reversal**: ``status == "cancelado"`` (judge estates) and
  no 4000 debit reversing it.

A customer with at least one flagged invoice is only *reported* when it is a
fresh customer (``customer_history == 0``) or it has a cancellation never
reversed (``n_cancelled_not_reversed > 0``) — that is the distinction that keeps
``STRONG`` from accusing a regular customer of fraud over a still-open invoice.
"""
from __future__ import annotations

import pandas as pd


def _iso(ts) -> str:
    """ISO date for a timestamp; the detector never assumes a pandas dtype."""
    if pd.isna(ts):
        return ""
    return ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)


def _collected_bank_in(ds) -> pd.DataFrame:
    """The company's inbound bank rows, typed, or an empty typed frame."""
    if len(ds.bank_transactions) == 0:
        return pd.DataFrame(columns=["txn_id", "fecha", "counterparty_clabe", "amount", "invoice_uuid"])
    bank = ds.bank_transactions[ds.bank_transactions["direction"].astype(str) == "in"].copy()
    if len(bank) == 0:
        return pd.DataFrame(columns=["txn_id", "fecha", "counterparty_clabe", "amount", "invoice_uuid"])
    bank["_fecha"] = pd.to_datetime(bank["fecha"], errors="coerce")
    bank["_amount"] = pd.to_numeric(bank.get("amount"), errors="coerce")
    return bank


def _collected_uuids(ds, invoices: pd.DataFrame) -> set[str]:
    """The set of sales-invoice uuids an inbound bank row pays for.

    Primary link: a bank row whose ``invoice_uuid`` is populated (on judge
    estates the loader links it from the payment reference, or by CLABE +
    exact amount + date). Fallback, for a judge estate where the reference
    names nothing: an inbound row with an empty ``invoice_uuid`` that is the
    *unique* candidate for an unpaid sales invoice of the same customer, for the
    same amount, dated at/after the invoice. Ambiguous matches are left alone so
    a collection is never mis-attributed to a different invoice.
    """
    bank = _collected_bank_in(ds)
    if len(bank) == 0:
        return set()

    collected: set[str] = set()
    invoiced = bank[bank["invoice_uuid"].astype(str).str.strip() != ""]
    if len(invoiced):
        collected |= set(invoiced["invoice_uuid"].astype(str))

    # CLABE -> counterparty_id for the sales side (customers).
    clabe_to_customer: dict[str, str] = {}
    if len(ds.customers):
        cus = ds.customers[ds.customers["clabe"].astype(str).str.strip() != ""]
        clabe_to_customer = {
            str(clabe): str(cid) for cid, clabe in zip(cus["customer_id"], cus["clabe"])
        }

    # A per-customer record of invoices for the fallback matching.
    sales = invoices  # already filtered to emitida by the caller
    if len(sales) == 0 or not len(clabe_to_customer):
        return collected

    unpaid = invoices[~invoices["uuid"].isin(collected)].copy()
    if len(unpaid) == 0:
        return collected
    unpaid["_fecha"] = pd.to_datetime(unpaid["fecha"], errors="coerce")
    unpaid["_total"] = pd.to_numeric(unpaid["total"], errors="coerce")

    unmatched = bank[bank["invoice_uuid"].astype(str).str.strip() == ""]
    for _, row in unmatched.iterrows():
        clabe = row.get("counterparty_clabe", "")
        cid = clabe_to_customer.get(str(clabe))
        if not cid:
            continue
        amount = row["_amount"]
        bdate = row["_fecha"]
        if pd.isna(amount) or pd.isna(bdate):
            continue
        cand = unpaid[
            (unpaid["counterparty_id"].astype(str) == cid)
            & (unpaid["_total"] == amount)
            & (unpaid["_fecha"] <= bdate)
            & (~unpaid["uuid"].isin(collected))
        ]
        if len(cand) == 1:
            collected.add(str(cand.iloc[0]["uuid"]))
    return collected


def detect_revenue_inflation(ds, *, grace_days: int = 60, period_end_days: int = 45) -> list[dict]:
    """Sales booked as revenue that were never collected, per customer.

    Per customer (``counterparty_id``) of the company's ``emitida`` invoices:
    flag an invoice when its revenue is booked (ledger 4000 credit) and either
    no inbound payment has arrived (within ``grace_days`` or ``period_end_days``)
    or it was cancelled without a reversing 4000 debit. Report the customer only
    when it is fresh (``customer_history == 0``) or has a cancellation never
    reversed. One dict per customer, sorted by ``entity_id``.
    """
    if len(ds.invoices) == 0:
        return []
    all_invoices = ds.invoices
    has_tipo = "tipo" in all_invoices.columns
    if has_tipo:
        sales = all_invoices[all_invoices["tipo"].astype(str) == "emitida"].copy()
    else:
        sales = all_invoices.copy()
    if len(sales) == 0:
        return []
    sales["_fecha"] = pd.to_datetime(sales["fecha"], errors="coerce")
    sales["_total"] = pd.to_numeric(sales["total"], errors="coerce")
    sales = sales.sort_values(["_fecha", "uuid"]).reset_index(drop=True)

    collected = _collected_uuids(ds, sales)
    has_status = "status" in all_invoices.columns
    if has_status:
        cancelled_uuids = set(sales[sales["status"].astype(str) == "cancelado"]["uuid"].astype(str))
    else:
        cancelled_uuids = set()

    # Revenue booked -> a 4000 credit; reversed -> a 4000 debit for the same uuid.
    booked_uuids: set[str] = set()
    reversed_uuids: set[str] = set()
    if len(ds.ledger):
        ledger = ds.ledger
        has_code = "account_code" in ledger.columns
        has_uuid = "invoice_uuid" in ledger.columns
        if has_code and has_uuid:
            acct = ledger[ledger["account_code"].astype(str) == "4000"]
            if len(acct):
                if "credit" in acct.columns:
                    booked_uuids = set(acct[acct["credit"].astype(float) > 0]["invoice_uuid"].astype(str))
                if "debit" in acct.columns:
                    reversed_uuids = set(acct[acct["debit"].astype(float) > 0]["invoice_uuid"].astype(str))

    if len(collected) == 0 and len(booked_uuids) == 0 and len(sales) == 0:
        return []

    data_last = sales["_fecha"].max()
    last_invoice_date = sales["_fecha"].max()

    rows: list[dict] = []
    for cid, grp in sales.groupby("counterparty_id", sort=False):
        grp = grp.sort_values("_fecha")
        n = len(grp)
        # customer_history: number of *collected* invoices for this customer.
        customer_history = int((grp["uuid"].isin(collected)).sum())

        flagged: list[str] = []
        flagged_total = 0.0
        for _, row in grp.iterrows():
            uuid = str(row["uuid"])
            if uuid not in booked_uuids:
                continue
            is_collected = uuid in collected
            is_cancelled = uuid in cancelled_uuids
            is_reversed = uuid in reversed_uuids

            not_collected_recent = False
            if not is_collected and not pd.isna(row["_fecha"]):
                if not pd.isna(data_last) and (data_last - row["_fecha"]).days >= grace_days:
                    not_collected_recent = True
                if not pd.isna(last_invoice_date) and (last_invoice_date - row["_fecha"]).days <= period_end_days:
                    not_collected_recent = True

            if not_collected_recent or (is_cancelled and not is_reversed):
                flagged.append(uuid)
                flagged_total += float(row["_total"])

        if not flagged:
            continue

        n_cancelled_not_reversed = int(
            sum(1 for u in flagged if u in cancelled_uuids and u not in reversed_uuids)
        )
        # The strong signal: a fresh customer or one with a cancellation never
        # reversed. A regular customer with one still-open invoice is a weak
        # signal and is *not* reported here (the loop treats it as unverified).
        if customer_history > 0 and n_cancelled_not_reversed == 0:
            continue

        rows.append(
            {
                "entity_id": str(cid),
                "n_invoices": n,
                "n_uncollected": int(n - customer_history),
                "n_cancelled_not_reversed": n_cancelled_not_reversed,
                "first_date": _iso(grp["_fecha"].min()),
                "last_date": _iso(grp["_fecha"].max()),
                "total_mxn": round(flagged_total, 2),
                "customer_history": customer_history,
                "invoice_uuids": [str(u) for u in grp["uuid"]],
                "evidence": list(dict.fromkeys(flagged)),
            }
        )

    rows.sort(key=lambda r: r["entity_id"])
    return rows
