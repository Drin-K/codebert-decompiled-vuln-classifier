# Dataset Leakage Audit

This audit reads Experiment 0 splits without modifying them or retraining a model.

## Split rows

- train: 728
- val: 156
- test: 156

## Cross-split overlap

| Comparison | Shared binaries | Rows in second split from seen binaries | Shared families | Rows in second split from seen families |
|---|---:|---:|---:|---:|
| train → val | 41 | 42 | 56 | 156 |
| train → test | 41 | 41 | 60 | 155 |
| val → test | 6 | 7 | 51 | 140 |

- Exact normalized-hash groups crossing splits: 0
- Structural near-duplicate candidate pairs (threshold 0.90): 1266

## Label-revealing identifiers

- contains_good: 284/1040 rows (27.31%)
- contains_bad: 787/1040 rows (75.67%)
- good_to_bad_variant: 103/1040 rows (9.90%)
- bad_to_good_variant: 146/1040 rows (14.04%)
- sink_or_source_role: 201/1040 rows (19.33%)
- cwe_identifier: 844/1040 rows (81.15%)
- explicit_vulnerability_name: 844/1040 rows (81.15%)

## Interpretation

Binary and family overlap can make the original random stratified evaluation optimistic because related functions occur across partitions. Identifier signals may also permit shortcut learning from Juliet names rather than vulnerability semantics.

Exact hash overlap and structural similarity use documented deterministic definitions; structural matches are candidates for review, not proof of semantic duplication.

## Recommendation

Create a group-aware split that keeps every derived Juliet family, and preferably every binary, in exactly one partition. Evaluate identifier normalization as a separate ablation and preserve Experiment 0 unchanged.
