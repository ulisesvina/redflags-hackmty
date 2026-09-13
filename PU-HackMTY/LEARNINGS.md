# LEARNINGS.md — what we tried, what happened, what we changed

The judges said they are as interested in failures as in successes. Every entry: timestamp, tried, happened,
changed. Five minutes every four hours. One person owns it.

## 2026-09-11 23:40 · Repo structured for three agents at once
Tried: run Claude Code, Codex, and an unattended Hermes agent against one repo from hour zero, coordinated only
by GitHub issues and AGENTS.md.
Happened: the planning docs assumed a `main` branch; the repo's default is `master`. Nobody on the team has
admin on the repo, so branch protection has to come from the owner.
Changed: docs say `master`; dataset unpacked to `data_estate/`, CI to `.github/workflows/`; `company_42` frozen
behind a checksum test; the issue queue filed as GitHub issues #1–#18 with `hermes-ok` / `cc` / `needs-human` labels.
Also learned: the generator is deterministic. `--seed 42` reproduces `company_42` byte-for-byte on Python 3.14, so the
checksum test guards against edits and schema drift, not against honest regeneration.

## 2026-09-11 23:40 · All inference on the HPC cluster
Tried: the original plan had Ollama locally with the Gemini free tier as fallback.
Happened: a teammate has open-weight models on an HPC cluster approved for sensitive data, reachable through an
OpenAI-compatible endpoint.
Changed: that endpoint is the only place dataset contents may go (AGENTS.md rule 8). Endpoint and key live in
`.env`; `scripts/check_llm.py` checks reachability so an outage is found before the demo, not during it.

## 2026-09-12 00:40 · Two of eight detector specs were impossible as written
Tried: file the detector issues for the unattended agent straight from the one-line queue in the plan.
Happened: checked every threshold against company_42 in pandas first. "Goods invoices with no receipt" returns
zero rows (every goods invoice has a receipt by construction). The round-trip rule "inbound ≥ 90% of the forward
within 10 days" finds none of the three planted chains: the return leg is a sales invoice issued net of IVA, so the
money that comes back is 0.98 / 1.16 ≈ 0.86 of what was forwarded. "Round thousands" only works on `subtotal`;
on `total` (with 16% IVA) the kickback shell scores 0.0. The 7-day fast-pay window is exact on this seed but
business-day rolling can push it to 9 on others.
Changed: no-receipt detector broadened (every purchase without a receipt, with a `receipt_required` flag), round-trip
return threshold 0.80, round-amount test on `subtotal`, fast-pay window 10 days. Every issue now states the exact
expected hits on company_42 and the test that proves them. Rule for the rest of the hackathon: a spec for an
unattended agent must name the number it should find, or it is not a spec.

## 2026-09-12 19:00 · LLM mode lost findings the deterministic path kept
Tried: the same investigation loop with the cluster model (GLM-5.3-Flash) on company_42, seven runs, against the
`--no-llm` path on the same data.
Happened: `--no-llm` scored 4/4 every time; LLM mode scored 1/4, 1/4, 3/4, 3/4, 3/4, 4/4, 4/4. Two causes, both visible
in `runs/*.jsonl`: (1) `record_finding` arguments arrived truncated (`scheme_type` and `rule` missing) because the
completion budget was too small for a reasoning model that spends tokens before the tool call; (2) the model cites
ledger entry IDs (`GL*`) it saw through `query_ledger` as evidence, the contract only accepts invoice/TX/CP/GR IDs,
and a rejected finding ended the lead instead of retrying. Precision was perfect in every run: no decoy accused.
Changed: `max_tokens` raised to 8192 (PR #64). Filed #65 (the guard sets ledger IDs aside instead of rejecting) and
#66 (guard reasons go back to the model for a retry; when it still fails, the deterministic finding stands in and the
trace says where it came from). Rule for the loop: the guard's job is to reject, the loop's job is to recover. A
rejection must never end a lead that the deterministic path can prove.

## 2026-09-12 19:00 · The step log could not be tailed
Tried: point a live UI at the JSONL step log while the agent ran.
Happened: the file is written in one go after `run_end`, so a viewer sees nothing until the run is over. The UI is
now being built outside this repo, which made the missing contract obvious: the only spec was a docstring.
Changed: #67 streams and flushes each line as it is emitted and writes the contract down (`docs/STEP_LOG.md`) with a
validator that fails the build when the writer drifts; #68 exposes the same lines over HTTP as server-sent events.
`demo/sample_trace.jsonl` is a real 4/4 LLM run to build against in the meantime. Also learned: the Hermes brief said
the agent may not touch `agent/`, yet it delivered the tool layer, the guard, the loop and the report without incident.
The brief now says it may work anywhere except the frozen dataset and three protected tests, and merges its own PRs
once CI is green.

## 2026-09-13 09:40 · Canned "why we cleared them" reasons were not evidence
Tried: #69 — replace each fixed `_DET_CLAUSES` sentence in `agent/investigate.py` with a check over the `Dataset`
that returns an innocent explanation *with record IDs*, and an honest `"unverified: ..."` when the records cannot
confirm it.
Happened: every weak-lead detector got a pure pandas `clear_reason` check (new vendor/round amounts, name twin on
69-B, shared address, no receipt / fast pay, cash payments); strong scheme-defining detectors are never cleared.
On company_42 all 14 decoys now carry a reason naming a GR id, invoice UUID, RFC or the co-located supplier — no
`unverified:` anywhere — and the `decision` step-log payload gained `"verified"`.
Changed: `_drop_reason` returns `(reason, verified)`; `_DET_CLAUSES` is gone; `agent/clear.py` is the single place
that answers "how do you know?". The check is only as good as the date-filtered records it reads, so a hand-edited
judge estate that breaks one of the innocent assumptions now surfaces `unverified:` (and #70 escalates it) instead of
a false "cleared".

## 2026-09-12 16:45 · Our own evaluation was averaging two incompatible things
Tried: a first "records it has never seen" table, ten reporting seeds (901–910) the agent had never run,
random scheme subsets, deterministic path.
Happened: recall 1.0 and zero penalties on every seed, but mean evidence validity read 0.70 and looked like
a quality drop. It was not. Three of the ten seeds drew an empty scheme list, and on honest books
`score.py` reports `evidence_validity = 0.0` because nothing was cited, and `results_recall = 1.0` because
the denominator is zero. The batch summary averaged those in, understating evidence validity and flattering
recall at the same time.
Changed: `scripts/eval_batch.py` now reports the headline over the seeds that actually had fraud planted
(`mean_recall_scheme_seeds`, `mean_evidence_validity_scheme_seeds`), lists the clean seeds separately as the
"nothing to find" control, and keeps the all-seed figures for comparability. The pass/fail gate no longer
applies a recall threshold to a batch with no schemes in it. Honest numbers: 1.000 recall and 1.000 evidence
validity on the seven scheme seeds, zero findings on all eight honest estates.
Lesson for the pitch: we nearly put 0.70 on a slide and would have been describing our own scorer's
convention, not our agent. Any aggregate that mixes "nothing to find" with "something to find" is two
different measurements wearing one number.

## 2026-09-12 16:45 · The LLM-mode number exists only on a seed we tuned on
Tried: to run the same ten unseen seeds through the LLM path, which is the headline claim of the project.
Happened: `.env` on this machine still contains the placeholders from `.env.example`
(`https://cluster.example`, empty key and model), so `scripts/check_llm.py` exits 1 and every batch fell back
to the deterministic path. The LLM path *has* been measured (seven runs, GLM-5.3-Flash, entry above), but
only on company_42 — a tuning seed whose answers are committed in this repo, and whose responses the disk
cache may be replaying. Under the judges' rule that is not a reportable number. Two documentation errors
surfaced with it: `docs/PLAN.md` quotes those seven runs as results without saying they are on a tuning seed,
and `demo/sample_trace.jsonl`, described as "a real LLM run", has `"mode": "no-llm"` in its `run_start` line,
so the frontend is being built against a trace with no `tool_call` events in it.
Changed: `docs/eval/README.md` states plainly which path was measured and which was not, and carries the
exact three commands that produce the LLM tables once the cluster credentials are in `.env`. The
`llm_calls` / `mxn_cost` / `wall_s` columns are wired and read `run_metadata` from the case file, so the
cost numbers appear the moment a real call happens.
Lesson: an unmeasured claim in a plan document becomes a false claim on stage. Better to carry a blank with
the command that fills it than a number nobody can reproduce.

## 2026-09-13 02:05 · An `other` finding is parked, never accused
Tried: #70 — escalate unverified weak leads to the model (up to `--max-escalations`, default 4) so a scheme we did
not plan for can still be found, and turn an accepted `other` finding into a "suspicious, unproven" `not_pursued`
entry instead of a finding.
Happened: the R5 (`other`) rule has no amount recomputation (the guard skips the 25% check for it), so there is no
defensible peso figure to put in a finding — and a decoy accused as `other` would still cost the double decoy penalty
on top. So an entity the model flags as `other` is parked as suspicious, with the model's narrative and evidence ids,
and `closed_by: investigator` so #88/#94 export it into `leads_not_pursued` exactly.
Changed: `_llm_loop` escalates the first N unverified weak leads in rank order (SondreTH's note: the escalation prompt
names the real rules from `RULES`, so R6/R7 auto-join); `park_lead` is a new `decision` action in `docs/STEP_LOG.md`
and `agent/steplog.py`; `_drop_reason` now returns the unverified detectors too. Note: the issue's literal
`test_escalation_cap` expected S00009 to be *un*-escalated, but rank order puts S00009 before S00026 — the test was
written to the actual "first N in rank order" behaviour.

## 2026-09-12 17:30 · Exporting to the judges' schema deleted one scheme's only tell
Tried: #80 — project our estate down to the judges' `estate_schema.sql` so held-out numbers are measured on
the shape they actually score.
Happened: their schema has no employee address column and no goods-receipts table. The kickback scheme's
naive tell (supplier registered at the purchasing manager's home) simply does not exist in their world, and
`detect_employee_address_match` returns nothing on an exported estate. The scheme survives only because #84
had already made the kickback signature fire on `detect_kickback_outflow` alone — the shell's own bank
statement paying the buyer's personal account. Two other things vanished: proof of delivery became the
purchase order, and customers stopped existing as master rows.
Changed: the export gives planted phantom/kickback/round-trip invoices **no** purchase order, so the missing
requisition trail is their tell in the judges' world; `payroll` transfers got a named clearing-account CLABE,
because their schema gives a bank row two CLABEs and our own statement left the counterparty blank — a test
we wrote caught that before the judges' validator would have.
Lesson: a schema is an argument about what counts as evidence. Porting to someone else's schema is not a
format conversion, it deletes the evidence their schema has no room for, and you find out which of your
detectors were load-bearing. Ours survived on one leg, and only because a defensive change landed first.

## 2026-09-12 17:30 · The whole judges' pipeline runs end to end
Tried: export seed 42 to `estate.db`, load it with the #79 adapter, investigate with `--no-llm`, write a
submission, and run the judges' own `validate_format.py --estate` against their database.
Happened: all four planted schemes found (recall 1.0), zero decoys accused, and their validator passed with
`--estate`, which is the strict mode: every cited `record_id` resolves in their SQLite file and every
`peso_amount` reconciles to its exhibits within 2%. The 2% guard from #87 is what makes that pass; under the
old 25% tolerance the submission writer was silently rewriting amounts to fit.
Changed: nothing — this is the first run where our output is checked by the judges' own code on the judges'
own data shape rather than by our tests on ours.

## 2026-09-12 18:10 · Two new schemes, and a frozen dataset that fought back
Tried: #81 — plant `threshold_splitting` and `revenue_inflation` plus the two decoys that target them, so all
five of the judges' scheme types exist in our data.
Happened: both additions collided with the frozen estates in ways that were not obvious. Adding a `status`
field to the `Invoice` dataclass would have added a column to `invoices.csv`, because the CSV writer takes its
header from the dataclass — every byte of `company_42` would have moved. And adding the two new decoys
unconditionally would have created two more suppliers, which changes the length of the list that `renumber()`
shuffles, which reassigns **every** supplier id in the estate.
Changed: cancellations live on `Estate.cancelled` (a set of uuids) instead of on the invoice row, and only the
judges' export, whose schema has a `status` column, reads them. The two new decoys are opt-in, appended after
the existing five so they consume RNG only after them, and they appear on any estate carrying a newer scheme.
That is a deliberate deviation from "always present" in the issue: the frozen pair predates them, and a frozen
artifact that quietly changes is worse than a decoy that appears in six estates out of seven.
Lesson: a frozen dataset is not just a file, it is a constraint on the shape of every future change. Twice now
the cheap-looking edit was the one that would have silently invalidated the demo dataset.

## 2026-09-12 18:10 · The agent misses the new schemes, and that is the correct result
Tried: an estate with all six schemes through the deterministic path, before the detectors for the two new
ones exist.
Happened: recall 4/6 — it found everything it has a detector for and missed `threshold_splitting` and
`revenue_inflation`. Judgment penalty was **0**: the two new decoys (a supplier banking at the same
institution as the purchasing manager, and twelve identical monthly invoices just under the approval limit)
produced no false accusation, which is the property that actually matters.
Changed: nothing. #82 and #83 build the two detectors. Recording it because it is the honest baseline the
detector PRs will be measured against, and because "it found nothing and accused nobody" is the right failure
mode for a system whose worst outcome is naming an innocent supplier.
