# HackMTY 2026 · Infosys track 2 · The Forensic Auditor

Team strategy doc. Sources: the Infosys tracks PDF and the transcript of the briefing by Richard (finance AI architect, Infosys STG) and Koss (healthcare R&D, Infosys STG). Both will be around during the hackathon for questions.

---

## TL;DR

- We build a **forensic agent** that takes a company's books plus the hint "something is wrong", follows the money, and hands in a **case file**: scheme, suppliers involved, evidence trail, peso amount, and a list of leads it chose not to chase and why.
- The judges score **precision as much as recall**. Accusing an honest supplier costs more than missing a scheme. Every accusation must cite a rule broken, the evidence rows, and a peso amount, or it gets downgraded to "suspicious, unproven".
- The LLM **proposes**, deterministic tools **prove**. The LLM never produces evidence, it only calls tools that return row IDs. A verifier re-runs every citation before anything is called "proven".
- The demo is live: **judges inject a fresh scheme**, the agent traces it on screen, then answers one surprise question. Design for that from hour zero: a simple documented schema, a scheme injector, a fast investigation loop, and an inspectable trace.
- Both speakers explicitly want to hear about **failures and learnings**. Keep the lab notebook (bottom of this doc) from the first hour.

---

## 1. What the track actually asks

From the PDF (page "3 of 5"):

> Given a company's books and only the hint that something is wrong, can an AI agent find the fraud, follow the money, and prove it, without accusing anyone it cannot back up?

Deliverable: working code and a 3-minute live demo where judges hide a fresh scheme in the data, the agent traces the money on screen, then answers one surprise question about its reasoning.

Judging criteria, verbatim:

| Criterion | Question |
|---|---|
| Results | On records it has never seen, how much hidden fraud does the agent find and correctly prove? |
| Judgment | Does it refuse to accuse suppliers it cannot back up, and can it defend a finding when a judge asks? |
| Feasibility | Could a real finance or audit team trust and use this? |
| Clarity | Is the case file easy to follow, with a clear money trail? |

Suggested approaches in the PDF: (1) investigate step by step, form a theory, follow leads, change course at dead ends; (2) simple detectors point the agent at what is worth digging into; (3) evidence trail for every accusation, refuse to name a supplier without a clear rule broken and a peso amount.

Domain context they gave us: Mexico's tax authority SAT publishes a blacklist of fake-invoice issuers under Article 69-B of the Código Fiscal (the "EFOS" list). By the time a supplier shows up there, the company has already deducted the invoices and is on the hook. Today's tools flag odd rows one at a time; nobody follows the money or builds the proof; honest suppliers who merely look odd get accused.

## 2. What the judges told us in the briefing, and what it implies

| They said | So we |
|---|---|
| "We want to see how you think about the problem. We're as interested in your failures as in the successes. Note down your learnings throughout the 36 hours and present them." | Keep `LEARNINGS.md` from hour zero. Every dead end, every model swap, every dataset redesign goes in with a timestamp. It becomes a slide. |
| "This is not just anomaly detection. Trace the flow of the transactions. You don't want to accuse anyone over a one-off." | Multi-hop money tracing is the core. Single-row anomalies are leads, never accusations. At least one scheme in our data must be invisible to simple detectors. |
| "Explainability is critical. It can't just say 'I found the answer'. What path did it take? Why was this flagged and that not?" | The investigation trace is a first-class artifact, shown live and kept for the surprise question. Cleared suspects get reasons too. |
| "If we inject synthetic fraudulent data, how does the system react?" | Build a scheme injector and a one-page schema doc so judges can inject without our help. Rehearse with a blind injection by a teammate. |
| "The vast majority of your time goes into the data: understanding it, making sure it's correct." | Data estate is the first workstream, time-boxed. Version the generator. |
| "Use what governments publish: they track these transactions and publish the patterns you should look for." | Use the real SAT 69-B list. Cite SAT/UIF/FATF typologies as the rule catalog. |
| "Think like an entrepreneur asking for money. What can you offer, what is the MVP, what can you *not* do." | Pitch has an explicit "what this cannot do" section. Say it before they ask. |
| "Local model with caching is safer than the Gemini free tier." (PDF) | vLLM on the H100 cluster, with an API fallback. |

Richard is a forward-deployed AI architect at a global financial firm in New York. This track is his home turf. Expect specific questions. Depth on the domain gets rewarded; a generic "LLM reads CSV" gets found out.

## 3. How we win

1. **Precision first, tiered output.** Findings come in three tiers: **Proven** (rule + evidence rows + amount, passed the verifier), **Suspicious but unproven** (what would be needed to prove it), **Cleared** (why the odd-looking supplier is fine). Recall shows up in tier 2 without costing us on Judgment.
2. **Decoys in our own data.** Honest suppliers that look odd. If our agent clears them with a reason, we have a story no detector-only team has.
3. **Propose / verify split.** The LLM never writes a number it did not get from a tool. A deterministic verifier re-executes every citation. Reproducible conclusions even if the wording varies between runs.
4. **The money trail on screen.** A graph that animates hop by hop *as the agent takes the hop*, with dead ends visibly abandoned. This is the Clarity criterion and the demo in one.
5. **Tax exposure in pesos.** Beyond "fraud amount", compute what a CFO cares about: income tax deduction at risk and VAT credit at risk for every invoice from a proven fake supplier. Nobody else will do this.
6. **Blind test results.** A teammate who did not build the agent injects schemes; we report precision and recall on those. That is our answer to "records it has never seen".

## 4. System design

```
                 +------------------+
  CSV data  ---> |  DuckDB / pandas | <--- SAT 69-B list (real)
  estate         |  + networkx graph|
                 +--------+---------+
                          |
              deterministic tool layer (every result carries row IDs)
                          |
   detectors ---> leads ---> LLM agent loop ---> findings (structured)
   (cheap,        (ranked)   hypothesis, tool        |
   rule-based)               calls, dead ends        v
                                               verifier (re-runs citations,
                                                 downgrades unproven claims)
                                                     |
                             +-----------------------+---------------------+
                             |                                             |
                     case file (md/pdf)                     live UI (graph + trace stream)
                                                                  + chat over the trace
```

### 4.1 Data estate (synthetic Monterrey company, ~12 months of books)

Keep it to flat CSVs. Judges need to be able to open and edit them. Suggested files and key columns:

| File | Key columns |
|---|---|
| `suppliers.csv` | supplier_id, rfc, name, address, clabe, bank, onboarded_date, category |
| `employees.csv` | employee_id, name, role, department, address, clabe, hire_date |
| `purchase_orders.csv` | po_id, supplier_id, date, amount, description, requested_by, approved_by |
| `goods_receipts.csv` | receipt_id, po_id, date, received_by, amount |
| `invoices.csv` (purchase, CFDI-like) | invoice_id, uuid, folio, issue_date, supplier_rfc, receiver_rfc, concept, subtotal, iva, total, metodo_pago (PUE/PPD), forma_pago, uso_cfdi, po_id |
| `sales_invoices.csv` | invoice_id, uuid, issue_date, customer_rfc, concept, subtotal, iva, total |
| `customers.csv` | customer_id, rfc, name, address, clabe |
| `bank_transactions.csv` (our accounts) | txn_id, date, account_id, counterparty_clabe, counterparty_name, amount (signed), reference |
| `ledger.csv` (journal lines) | entry_id, date, account_code, account_name, debit, credit, description, source_doc_id |
| `external_flows.csv` (AMLSim-style network beyond our books) | txn_id, date, from_entity, from_clabe, to_entity, to_clabe, amount |
| `sat_69b.csv` (real download) | rfc, nombre, situacion (Presunto / Desvirtuado / Definitivo / Sentencia favorable), publication dates |

Stated assumption for the pitch: `external_flows.csv` represents counterparty bank data a forensic auditor obtains through bank cooperation, SAT, or the UIF. A company alone only sees its own side. Say this out loud; it is a "what we cannot do" item.

Generator requirements: seedable, parameterized, base honest activity first, then schemes and decoys layered on by name. `python gen.py --seed 7 --schemes S1,S2 --decoys D1,D3`.

### 4.2 Schemes to plant

| ID | Scheme | Footprint in the data | Needs multi-hop? |
|---|---|---|---|
| S1 | Fake supplier (EFOS) | Supplier RFC on 69-B (Definitivo, or listed *after* our invoices), vague concepts ("asesoría", "servicios de consultoría"), round totals, no PO or receipt, onboarded weeks before first invoice, amounts just under an approval threshold, paid same day | No, but the proof needs invoice + payment + ledger + 69-B joined |
| S2 | Kickback through a shell | Real supplier B, prices inflated vs. last year; one procurement manager approves everything; in `external_flows` B pays shell C ~10% within days of each payment; C's CLABE or address matches the manager; C has no other activity | Yes |
| S3 | Round-tripping / fake sales | We sell to customer K, K pays; we pay "supplier" D for marketing; D pays K in `external_flows`; amounts and dates line up; revenue inflated | Yes, cycle detection |
| S4 | Payment diversion | A real invoice paid twice, second time to a CLABE that is not in the supplier master | No |
| S5 | Invoice splitting | Several invoices from one supplier on one day, each just under the approval limit | No, and it is a lead not an accusation on its own |

Make S2 and S3 undetectable by any single-row rule. That is what forces the agent to follow the money.

### 4.3 Decoys (honest but odd)

| ID | Decoy | Why a naive system flags it | Why it is fine |
|---|---|---|---|
| D1 | Rent or retainer supplier | Round monthly amounts, vague concept "renta" | Multi-year contract, PO on file, stable |
| D2 | Name near-matches a 69-B entity | Fuzzy name match | Different RFC, RFC valid, not on the list |
| D3 | Supplier listed as Presunto, later Desvirtuado | Appears on 69-B | Status is Desvirtuado; SAT cleared them |
| D4 | Payment mismatch from a credit note or PPD partial payments | Invoice total ≠ payment | Credit note / payment complement reconciles it |
| D5 | New high-volume supplier | Recent onboarding + big spend | Full PO, receipt, approval chain, market prices |
| D6 | Payments to an employee's CLABE | Looks like a shell payout | HR-approved expense reimbursements, small, documented |

### 4.4 Detectors (cheap, deterministic, lead generation only)

69-B exact RFC match with status · RFC format and check digit · invoice/payment mismatch (missing, duplicate, wrong CLABE) · invoice without PO or receipt above threshold · threshold clustering and same-day splitting · round-number ratio and Benford per supplier · onboarding recency vs. spend · supplier–employee shared CLABE/address/phone · unit price vs. history · cycles in the flow graph (depth-capped) · vague concept text · weekend and off-hours postings.

Each detector emits leads with a score and the rows that triggered it.

### 4.5 Agent tools (every result carries row IDs)

`run_detectors()` · `get_supplier(id|rfc)` (master + 69-B status + stats) · `list_invoices(supplier, window)` · `match_payments(invoice_ids)` · `get_po_chain(invoice_id)` · `trace_flows(clabe|entity, direction, depth, window)` · `find_cycles(entity, max_len)` · `compare_prices(supplier, category)` · `check_employee_links(supplier_id)` · `sql(read_only_query, row_limit)` as the escape hatch for schemes we did not anticipate · `record_finding(...)`, `clear_lead(...)`, `park_lead(...)` as structured outputs.

### 4.6 Agent loop

1. Run detectors, rank leads.
2. For each lead (parallel, capped): form a hypothesis naming the scheme type, call tools, follow the money up to N hops, stop at dead ends and say why.
3. Emit one of: finding (rule_id, entities, money trail as an ordered list of row IDs, amount), cleared (reason, rows), parked (reason, what evidence would be needed).
4. Verifier re-runs every cited tool call from the row IDs, checks the amount equals the sum of cited rows within tolerance, checks the rule's preconditions. Anything that fails drops to "suspicious, unproven".
5. Case file renders from the structured findings. Trace is stored for the chat.

Rule catalog (the "clear rule broken"): keep a short `rules.yaml`, e.g. R1 deductions claimed on invoices from a 69-B Definitivo issuer; R2 payment without a matching invoice or to an unregistered account; R3 circular flow returning funds to the company or its people; R4 undisclosed related party between supplier and approver; R5 price inflation combined with an outbound flow to a related party. Each rule names its required evidence types and how the peso amount is computed. Cite the legal basis where we can (CFF 69-B, LISR deductibility requirements).

### 4.7 UI

- Entity graph: company, suppliers, customers, shells, employees, bank accounts. Edges are flows, weighted by amount.
- Animate each hop when the agent takes it. Fade abandoned leads. Highlight the proven trail at the end.
- Side panel: live trace stream (hypothesis, tool call, result summary, decision).
- Case file view: Proven / Suspicious / Cleared / Not chased, each expandable to the rows.
- Chat box over the trace for the surprise question.
- Injector panel for judges: pick a scheme, set parameters, or upload edited CSVs. Then "Investigate".

## 5. Model and infra

- **Serving:** vLLM on the H100 cluster, OpenAI-compatible endpoint, prefix caching on, a tool-call parser that matches the model. Fix `temperature=0` and a seed for demo consistency. Note for the pitch: batching means it is not bit-for-bit deterministic, and it does not need to be, because evidence is tool-computed and the verifier makes conclusions reproducible.
- **Model:** a strong open-weight tool-calling model. Check what is current on the day; Qwen3 large variants and gpt-oss-120b are known to work with vLLM tool parsers. Test multi-hop tool use on S2 before committing.
- **Fallback:** the same client with `base_url` swapped to a hosted API (Anthropic or Gemini). Test the switch. If the cluster is unreachable from the venue we must not discover it during the demo.
- **Caching:** tool results memoized on (tool, args, dataset hash). Prefix caching for the system prompt and schema.
- **Privacy pitch:** RFCs, CLABEs, and bank data never leave the premises. This is a real requirement for Mexican finance clients, and it maps to the Feasibility criterion.
- **Speed budget:** the whole investigation must land inside about 90 seconds on stage. Parallel leads, depth caps, and cached detectors get us there.

## 6. Demo script (3 minutes)

| Time | Beat |
|---|---|
| 0:00 | One sentence: fake invoices get deducted long before SAT lists the issuer, and today's tools flag rows, not schemes. |
| 0:20 | Judge injects a scheme (injector panel or edited CSV). Press Investigate. |
| 0:40 | Leads appear. Graph animates hops. One lead visibly dead-ends and is parked with a reason. |
| 2:00 | Case file: proven findings with rule, trail, pesos, and tax exposure. Cleared suspects with reasons. Leads not chased. |
| 2:40 | Surprise question. Ask the chat, or answer from the trace ourselves. Either way the trace is on screen. |

Likely surprise questions: "Why did you not flag supplier X?" · "What if that supplier was just new?" · "How do you know the money came back?" · "What would you need to prove the unproven one?" · "What happens if the 69-B list is stale?" Prepare answers for each and make sure the trace supports them.

## 7. Timeline (36 h)

| Hours | Goal | Done when |
|---|---|---|
| 0–2 | Repo, schema agreed, vLLM up and reachable, 69-B downloaded, owners assigned | `gen.py` writes empty-but-valid CSVs; a tool call round-trips through the model |
| 2–8 | Generator v0 (honest company + S1 + S2 + D1–D3), tool layer v0, detectors v0 | Detectors find S1 leads; `trace_flows` follows S2 by hand |
| 8–14 | Agent loop v0 end-to-end in the terminal on S1, case file as markdown, static graph in UI | Agent proves S1 with rows and pesos, clears D1 |
| 14–20 | S3, S4, remaining decoys, verifier, trace streaming to the UI. Sleep in shifts. | Agent handles S1–S3 unaided, verifier downgrades a planted bad citation |
| 20–28 | Injector, blind test by the non-agent teammate, latency work, case file polish, tax exposure | Blind scheme investigated inside 90 s, precision/recall table exists |
| 28–33 | Three full demo rehearsals, pitch deck, `LEARNINGS.md` compiled, "cannot do" slide | A rehearsal with a scheme none of us designed |
| 33–36 | Code freeze, final rehearsal, buffer | Nothing new after freeze |

## 8. Risks

| Risk | Mitigation |
|---|---|
| Cluster unreachable from the venue | Test tonight. SSH tunnel ready. API fallback tested. |
| Generator eats the whole hackathon | Time-box to hour 8. Ugly data that works beats a beautiful generator with no agent. |
| Agent is detectors plus a narrative | S2 and S3 are undetectable by single rows. If the agent cannot find them, the design is wrong, not the data. |
| Hallucinated evidence | Verifier. LLM never emits a number it did not get from a tool. |
| Judge injects something we did not foresee | Generic tools plus the read-only `sql` escape hatch. Rehearse with blind injections. |
| Too slow on stage | Parallel leads, depth cap, cached detectors. Streaming trace makes waiting tolerable, but it still has to finish. |
| Graph UI rabbit hole | Static graph by hour 14, animation only after the agent works end-to-end. |
| No learnings recorded | One person owns `LEARNINGS.md`. Five minutes every four hours. |

## 9. Pitch outline

1. The problem in one slide: the deduction is claimed long before the 69-B listing, and flagging rows does not build a case.
2. Our thesis: investigate, then prove. LLM proposes, tools prove, verifier gates.
3. Live demo (section 6).
4. Results on blind tests: table of schemes planted vs. proven vs. suspicious vs. missed, and decoys cleared vs. wrongly accused.
5. Failures and learnings (from `LEARNINGS.md`).
6. What it cannot do: only sees what is in the books plus whatever counterparty data an auditor can obtain; cannot prove a service was really delivered without contracts and receiving records; the 69-B list lags reality; synthetic data is not a real company.
7. What a real deployment needs: on-prem inference, integration with the accounting system and CFDI downloads from SAT, a human reviewer in the loop, an audit log.

## 10. Resources

- SAT Article 69-B listing (search "listado completo 69-B" on sat.gob.mx; downloadable CSV/XLS with Presunto / Desvirtuado / Definitivo / Sentencia favorable statuses).
- CFDI 4.0 schema (SAT Anexo 20) for realistic invoice fields.
- IBM AMLSim, github.com/IBM/AMLSim, for money-flow rings and shell patterns.
- IEEE-CIS fraud dataset on Kaggle, only as a baseline for anomaly checks.
- FATF and UIF typologies for trade-based money laundering and fake-invoice schemes, as sources for the rule catalog.
- Domain terms to use correctly: EFOS (issuer of fake invoices) and EDOS (deductor of them), "materialidad" (proof the service actually happened), CFF art. 69-B, LISR deductibility requirements.

---

## LEARNINGS.md template

Copy this into `LEARNINGS.md` and keep it updated. Every entry: timestamp, what we tried, what happened, what we changed.

```
## 2026-09-12 01:30 · Dataset v0 was too easy
Tried: S1 and S2 with default parameters.
Happened: detectors alone found everything, the agent had nothing to do.
Changed: S2 shell no longer shares a CLABE with the employee; only the address matches, and only via external flows.

## 2026-09-12 04:10 · Model invented a supplier name
Tried: letting the model write the finding summary freely.
Happened: it named a supplier that does not exist in suppliers.csv.
Changed: findings are structured; entity fields must be IDs that the verifier resolves.
```
