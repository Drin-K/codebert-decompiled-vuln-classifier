# Dataset Leakage Audit

This audit reads the supplied splits without modifying them or retraining a model.

## Split rows

- train: 728
- val: 155
- test: 157

## Cross-split overlap

| Comparison | Shared binaries | Rows in second split from seen binaries | Shared families | Rows in second split from seen families |
|---|---:|---:|---:|---:|
| train → val | 0 | 0 | 0 | 0 |
| train → test | 0 | 0 | 0 | 0 |
| val → test | 0 | 0 | 0 | 0 |

- Exact normalized-hash groups crossing splits: 0
- Structural near-duplicate candidate pairs (threshold 0.90): 390

## Label-revealing identifiers

- contains_good: 284/1040 rows (27.31%)
- contains_bad: 787/1040 rows (75.67%)
- good_to_bad_variant: 103/1040 rows (9.90%)
- bad_to_good_variant: 146/1040 rows (14.04%)
- sink_or_source_role: 201/1040 rows (19.33%)
- cwe_identifier: 844/1040 rows (81.15%)
- explicit_vulnerability_name: 844/1040 rows (81.15%)

## Interpretation

No binary or derived-family overlap was found; the supplied splits satisfy the group-independence checks. Identifier signals may still permit shortcut learning from Juliet names rather than vulnerability semantics.

Exact hash overlap and structural similarity use documented deterministic definitions; structural matches are candidates for review, not proof of semantic duplication.

## Recommendation

Use these group-independent splits for the additional evaluation. Evaluate identifier normalization as a separate ablation and preserve Experiment 0 unchanged.
