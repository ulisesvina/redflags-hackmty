# The brief — HackMTY 2026 · Infosys track 2 · "The Forensic Auditor"

Sources: the Infosys tracks PDF (`HackMTY_2026_Infosys_Challenge_Tracks.pdf`, page 3 of 5) and the briefing by
Richard and Koss of Infosys STG (`briefing_transcript.md`, 2026-09-11). Team strategy: `STRATEGY.md`. Execution: `PLAN.md`.

## The ask (verbatim from the PDF)
> Given a company's books and only the hint that something is wrong, can an AI agent find the fraud, follow the
> money, and prove it, without accusing anyone it cannot back up?

Deliverable: working code plus a 3-minute live demo. Judges hide a fresh scheme in the data, the agent traces the
money on screen, then answers one surprise question about its reasoning.

## Judging criteria
| Criterion | Question |
|---|---|
| Results | On records it has never seen, how much hidden fraud does the agent find and correctly prove? |
| Judgment | Does it refuse to accuse suppliers it cannot back up, and can it defend a finding when a judge asks? |
| Feasibility | Could a real finance or audit team trust and use this? |
| Clarity | Is the case file easy to follow, with a clear money trail? |

## What the judges said in the briefing
- This is not anomaly detection. Trace the flow of transactions; never accuse anyone over a one-off.
- Explainability is critical: what path did it take, why was this flagged and that not.
- They will inject synthetic fraudulent data live and watch how the system reacts and explains itself.
- They are as interested in failures as in successes. Keep `LEARNINGS.md` from hour zero and present it.
- Most of the time goes into the data. Use what governments publish (SAT Art. 69-B "EFOS" list).
- Think like an entrepreneur pitching for money: what is the MVP, and what can it not do.

## Domain in one paragraph
Mexico's tax authority SAT publishes a blacklist of fake-invoice issuers under Article 69-B of the Código Fiscal
(EFOS). By the time a supplier appears there, the company has already deducted the invoices and is on the hook as
a participant, not a victim. Today's tools flag odd rows one at a time; nobody follows the money or builds the
proof, and honest suppliers that merely look odd get accused.

## Our answer in one line
Deterministic detectors produce leads; the LLM (open-weight, on the HPC cluster, see `.env.example`) forms a
hypothesis per lead and calls tools that return record IDs; an evidence guard rejects anything it cannot verify;
the case file lists both accusations and the leads it chose not to pursue, with reasons.
