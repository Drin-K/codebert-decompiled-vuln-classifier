# Group-Aware Split Summary

- Input: `/home/drin/codebert-decompiled-vuln-classifier/data/processed/final_labeled_dataset.csv`
- Random seed for deterministic tie-breaking and row ordering: 42
- Grouping rule: terminal Juliet control-flow variant `_01` through `_18` is removed from `binary_name`
- Assignment method: mixed-integer optimization minimizing class-count deviation

## Distribution

| Split | Rows | Families | Binaries | Clean | Buffer Overflow | Format String | Integer Overflow |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 728 | 43 | 585 | 182 | 182 | 182 | 182 |
| val | 155 | 11 | 129 | 39 | 39 | 38 | 39 |
| test | 157 | 14 | 134 | 39 | 39 | 40 | 39 |

## Verification

- Family overlap across all split pairs: 0
- Binary overlap across all split pairs: 0
- Total rows preserved: 1040/1040
- Every input row occurs in exactly one output split

## Limitation

Class counts are nearly balanced but validation and test contain 155 and 157 rows because complete Juliet families cannot be divided between partitions. This independence constraint is more important than reproducing the exact Experiment 0 sizes.
