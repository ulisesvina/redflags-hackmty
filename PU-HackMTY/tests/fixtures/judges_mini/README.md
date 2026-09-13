# `judges_mini` — a hand-written estate in the judges' schema (#79)

Eight CSVs in `estate_schema.sql` shape, small enough to reason about by hand and large
enough to exercise every branch of the adapter in `agent/data.py`:

* **company identity is derived, never declared** — `EMP920101AB1` is simply the RFC every
  vendor invoices, and `000000000000000099` the account those invoices are paid from;
* **both payment links** — `BNK-0001` names `INV-0001` in its reference, `BNK-0002` names
  nothing and is matched to `INV-0002` by vendor CLABE, exact amount and date;
* **a third-party leg** — `BNK-0005` moves money from vendor A's account to employee
  `EMP:0001`'s personal account, with the company nowhere in it: a `counterparty_bank` row;
* **a PO standing in for a goods receipt** — `PO-0001` settles `INV-0002`; `INV-0001` has no
  PO and no contract, which is what makes vendor A worth a second look;
* **an approver trail** — vendor B's PO is signed by Ana Ruiz Medina (`EMP:0001`), and the
  ledger names her on `INV-0001` too, so the invoice's `approved_by` falls back to the ledger;
* **a 69-B listing** — vendor A is on `efos_list` as `definitivo`.

The estate is a fixture, not a dataset with an answer key: there is no `hidden/` here, and the
shape (a listed vendor paid with no PO, money moving on to the approver's own account) is the
phantom-vendor/kickback signature the detectors are built to notice.

`tests/test_load_judges.py` also builds `mini.db` from these CSVs to prove the SQLite and CSV
paths produce identical frames.
