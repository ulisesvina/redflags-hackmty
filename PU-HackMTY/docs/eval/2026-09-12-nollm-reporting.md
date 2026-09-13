| seed | schemes | recall | found | missed | penalty | false_acc | decoys_acc | evidence_validity | not_pursued | contract_errors | llm_calls | mxn_cost | wall_s | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 901 | roundtrip,efos,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,round_trip_sales |  | 0 |  |  | 1.000 | 22 | 0 | 0 | 0.0000 | 1.32 |  |
| 902 | duplicate,kickback | 1.000 | duplicate_invoice_payment,kickback_shell |  | 0 |  |  | 1.000 | 14 | 0 | 0 | 0.0000 | 1.20 |  |
| 903 |  | 1.000 |  |  | 0 |  |  | 0.000 | 16 | 0 | 0 | 0.0000 | 1.08 |  |
| 904 | roundtrip,duplicate,kickback,efos | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 14 | 0 | 0 | 0.0000 | 1.30 |  |
| 905 | roundtrip,duplicate | 1.000 | duplicate_invoice_payment,round_trip_sales |  | 0 |  |  | 1.000 | 21 | 0 | 0 | 0.0000 | 1.25 |  |
| 906 |  | 1.000 |  |  | 0 |  |  | 0.000 | 16 | 0 | 0 | 0.0000 | 0.95 |  |
| 907 | efos,duplicate,kickback | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell |  | 0 |  |  | 1.000 | 18 | 0 | 0 | 0.0000 | 1.19 |  |
| 908 |  | 1.000 |  |  | 0 |  |  | 0.000 | 19 | 0 | 0 | 0.0000 | 1.14 |  |
| 909 | duplicate | 1.000 | duplicate_invoice_payment |  | 0 |  |  | 1.000 | 20 | 0 | 0 | 0.0000 | 1.17 |  |
| 910 | duplicate,roundtrip,efos,kickback | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 19 | 0 | 0 | 0.0000 | 1.40 |  |

## Summary
- seeds: [901, 902, 903, 904, 905, 906, 907, 908, 909, 910]
- mode: no-llm
- seeds_with_schemes: [901, 902, 904, 905, 907, 909, 910]
- clean_seeds (nothing to find): [903, 906, 908]
- **mean_recall (scheme seeds): 1.000**
- min_recall (scheme seeds): 1.000
- **mean_evidence_validity (scheme seeds): 1.000**
- mean_recall (all seeds, clean counted as 1.0): 1.000
- min_recall (all seeds): 1.000
- seeds_with_penalty: []
- clean_seeds_with_findings: []
- mean_evidence_validity (all seeds, clean scored 0.0 because there is nothing to validate): 0.700
- wall_p50_s: 1.19
- wall_p95_s: 1.40
- total_llm_calls: 0
- total_mxn_cost: 0.0000
- mxn_per_seed: 0.0000
- command: scripts/eval_batch.py --seeds 901-910 --schemes random --no-llm --workdir /tmp/claude-1000/-home-sondre-Programming-Hackathons-PU-HackMTY/0b784a6f-e3ee-446b-9fea-fdd69796270c/scratchpad/eval72/rep --out docs/eval/2026-09-12-nollm-reporting.md
