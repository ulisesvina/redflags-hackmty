| seed | schemes | recall | found | missed | penalty | false_acc | decoys_acc | evidence_validity | not_pursued | contract_errors | llm_calls | mxn_cost | wall_s | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 201 |  | 1.000 |  |  | 0 |  |  | 0.000 | 17 | 0 | 0 | 0.0000 | 1.07 |  |
| 202 |  | 1.000 |  |  | 0 |  |  | 0.000 | 19 | 0 | 0 | 0.0000 | 0.95 |  |
| 203 |  | 1.000 |  |  | 0 |  |  | 0.000 | 19 | 0 | 0 | 0.0000 | 0.92 |  |
| 204 |  | 1.000 |  |  | 0 |  |  | 0.000 | 15 | 0 | 0 | 0.0000 | 1.05 |  |
| 205 |  | 1.000 |  |  | 0 |  |  | 0.000 | 17 | 0 | 0 | 0.0000 | 1.00 |  |

## Summary
- seeds: [201, 202, 203, 204, 205]
- mode: no-llm
- seeds_with_schemes: []
- clean_seeds (nothing to find): [201, 202, 203, 204, 205]
- **mean_recall (scheme seeds): 0.000**
- min_recall (scheme seeds): 0.000
- **mean_evidence_validity (scheme seeds): 0.000**
- mean_recall (all seeds, clean counted as 1.0): 1.000
- min_recall (all seeds): 1.000
- seeds_with_penalty: []
- clean_seeds_with_findings: []
- mean_evidence_validity (all seeds, clean scored 0.0 because there is nothing to validate): 0.000
- wall_p50_s: 1.00
- wall_p95_s: 1.07
- total_llm_calls: 0
- total_mxn_cost: 0.0000
- mxn_per_seed: 0.0000
- command: scripts/eval_batch.py --seeds 201-205 --schemes clean --no-llm --workdir /tmp/claude-1000/-home-sondre-Programming-Hackathons-PU-HackMTY/0b784a6f-e3ee-446b-9fea-fdd69796270c/scratchpad/eval72/cln --out docs/eval/2026-09-12-nollm-clean.md
