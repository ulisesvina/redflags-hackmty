| seed | schemes | recall | found | missed | penalty | false_acc | decoys_acc | evidence_validity | not_pursued | contract_errors | llm_calls | mxn_cost | wall_s | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | kickback,roundtrip,duplicate,efos | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 23 | 0 | 0 | 0.0000 | 1.34 |  |
| 102 | roundtrip | 1.000 | round_trip_sales |  | 0 |  |  | 1.000 | 21 | 0 | 0 | 0.0000 | 1.13 |  |
| 103 | kickback,roundtrip,efos | 1.000 | efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 23 | 0 | 0 | 0.0000 | 1.30 |  |
| 104 |  | 1.000 |  |  | 0 |  |  | 0.000 | 16 | 0 | 0 | 0.0000 | 1.06 |  |
| 105 | roundtrip,duplicate,efos,kickback | 1.000 | duplicate_invoice_payment,efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 17 | 0 | 0 | 0.0000 | 1.32 |  |
| 106 | efos,roundtrip,kickback | 1.000 | efos_fake_supplier,kickback_shell,round_trip_sales |  | 0 |  |  | 1.000 | 14 | 0 | 0 | 0.0000 | 1.35 |  |
| 107 | duplicate | 1.000 | duplicate_invoice_payment |  | 0 |  |  | 1.000 | 18 | 0 | 0 | 0.0000 | 0.97 |  |
| 108 | efos | 1.000 | efos_fake_supplier |  | 0 |  |  | 1.000 | 14 | 0 | 0 | 0.0000 | 1.06 |  |
| 109 | kickback,duplicate | 1.000 | duplicate_invoice_payment,kickback_shell |  | 0 |  |  | 1.000 | 16 | 0 | 0 | 0.0000 | 1.18 |  |
| 110 | kickback,duplicate,roundtrip | 1.000 | duplicate_invoice_payment,kickback_shell,round_trip_sales |  | 0 |  |  | 0.960 | 16 | 0 | 0 | 0.0000 | 1.33 |  |

## Summary
- seeds: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
- mode: no-llm
- seeds_with_schemes: [101, 102, 103, 105, 106, 107, 108, 109, 110]
- clean_seeds (nothing to find): [104]
- **mean_recall (scheme seeds): 1.000**
- min_recall (scheme seeds): 1.000
- **mean_evidence_validity (scheme seeds): 0.996**
- mean_recall (all seeds, clean counted as 1.0): 1.000
- min_recall (all seeds): 1.000
- seeds_with_penalty: []
- clean_seeds_with_findings: []
- mean_evidence_validity (all seeds, clean scored 0.0 because there is nothing to validate): 0.896
- wall_p50_s: 1.24
- wall_p95_s: 1.35
- total_llm_calls: 0
- total_mxn_cost: 0.0000
- mxn_per_seed: 0.0000
- command: scripts/eval_batch.py --seeds 101-110 --schemes random --no-llm --workdir /tmp/claude-1000/-home-sondre-Programming-Hackathons-PU-HackMTY/0b784a6f-e3ee-446b-9fea-fdd69796270c/scratchpad/eval72/tun --out docs/eval/2026-09-12-nollm-tuning.md
