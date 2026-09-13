| seed | schemes | recall | found | missed | penalty | false_acc | decoys_acc | evidence_validity | not_pursued | contract_errors | llm_calls | mxn_cost | wall_s | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 901 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 0.936 | 19 | 0 | 0 | 0.0000 | 1.28 |  |
| 902 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 15 | 0 | 0 | 0.0000 | 1.44 |  |
| 903 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 16 | 0 | 0 | 0.0000 | 1.40 |  |
| 904 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 13 | 0 | 0 | 0.0000 | 1.31 |  |
| 905 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 21 | 0 | 0 | 0.0000 | 1.46 |  |
| 906 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 14 | 0 | 0 | 0.0000 | 1.26 |  |
| 907 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 19 | 0 | 0 | 0.0000 | 1.28 |  |
| 908 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 19 | 0 | 0 | 0.0000 | 1.42 |  |
| 909 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 20 | 0 | 0 | 0.0000 | 1.46 |  |
| 910 | efos,kickback,roundtrip,duplicate | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 19 | 0 | 0 | 0.0000 | 1.37 |  |

## Summary
- seeds: [901, 902, 903, 904, 905, 906, 907, 908, 909, 910]
- mode: no-llm
- seeds_with_schemes: [901, 902, 903, 904, 905, 906, 907, 908, 909, 910]
- clean_seeds (nothing to find): []
- **mean_recall (scheme seeds): 1.000**
- min_recall (scheme seeds): 1.000
- **mean_evidence_validity (scheme seeds): 0.994**
- mean_recall (all seeds, clean counted as 1.0): 1.000
- min_recall (all seeds): 1.000
- seeds_with_penalty: []
- clean_seeds_with_findings: []
- mean_evidence_validity (all seeds, clean scored 0.0 because there is nothing to validate): 0.994
- wall_p50_s: 1.38
- wall_p95_s: 1.46
- total_llm_calls: 0
- total_mxn_cost: 0.0000
- mxn_per_seed: 0.0000
- command: scripts/eval_batch.py --seeds 901-910 --schemes all --no-llm --workdir /tmp/claude-1000/-home-sondre-Programming-Hackathons-PU-HackMTY/0b784a6f-e3ee-446b-9fea-fdd69796270c/scratchpad/eval72/repall --out docs/eval/2026-09-12-nollm-reporting-all.md
