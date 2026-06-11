# Phase 4: Label Preparation

Phase 4 creates suggested labels for manual verification. It does not assign final labels, train models, run Ghidra, compile binaries, or change the Phase 3 cleaning rules.

The input file is:

```text
data/processed/clean_functions.csv
```

The outputs are:

```text
data/processed/suggested_labels.csv
data/processed/labeling_summary.md
```

## Class Mapping

The thesis target classes are:

```text
0 = Clean
1 = Buffer Overflow
2 = Format String
3 = Integer Overflow
```

Rows that should not be used for model training are marked:

```text
-2 = Exclude
```

Juliet CWE metadata maps to the vulnerable classes as follows:

```text
CWE121 + CWE122 -> Buffer Overflow
CWE134 -> Format String
CWE190 -> Integer Overflow
```

Buffer Overflow combines CWE121 and CWE122 because both represent memory overwrite vulnerabilities, with CWE121 covering stack-based cases and CWE122 covering heap-based cases.

## Suggested Label Logic

The script uses deterministic rules based on Juliet metadata, Juliet function names, and pseudo-C code patterns.

Juliet `good`, `good1`, `good2`, `goodB2G`, `goodG2B`, `goodB2G1`, `goodB2G2`, `goodG2B1`, and `goodG2B2` patterns are treated as Clean candidates. Juliet good variants may still contain APIs such as `memcpy`, `memmove`, `recv`, `scanf`, `malloc`, arithmetic operations, or array indexing. These operations do not automatically make a Juliet good function vulnerable because Juliet good variants are designed to be safe through good source or good sink logic.

Juliet `bad` patterns are mapped to the vulnerable class associated with the inferred CWE. When the CWE and Juliet bad naming agree, the suggested label is high confidence. When bad naming exists but the vulnerability pattern is less obvious in decompiled pseudo-C, the suggested label is medium confidence.

Main functions, dispatcher wrappers, empty return-only stubs, and Juliet support/helper functions are marked:

```text
suggested_label = -2
suggested_class = Exclude
review_status = exclude
```

Exclude rows are not used for model training. This prevents the model from learning dispatcher or support-library logic instead of vulnerability logic.

Ambiguous functions that cannot be suggested confidently are marked:

```text
suggested_label = -1
suggested_class = Uncertain
review_status = needs_manual_review
```

`FUN_...` names are not treated as suspicious by themselves because stripped/decompiled binaries commonly use generated function names.

## Manual Review

Final labels require manual verification. The `final_label` and `final_class` columns are intentionally left blank. The final training dataset should be created only after reviewing suggested labels and filling final label fields.

A final balanced dataset will be created later from verified labels. This phase only prepares suggested labels and review categories.

Use these commands:

```bash
python3 scripts/prepare_labels.py \
  --input data/processed/clean_functions.csv \
  --output data/processed/suggested_labels.csv \
  --summary data/processed/labeling_summary.md
```

```bash
python3 scripts/sample_label_review.py \
  --input data/processed/suggested_labels.csv \
  --n 10
```

```bash
python3 scripts/sample_label_review.py \
  --input data/processed/suggested_labels.csv \
  --class-name "Buffer Overflow" \
  --n 10
```

```bash
python3 scripts/sample_label_review.py \
  --input data/processed/suggested_labels.csv \
  --class-name "Exclude" \
  --n 10
```

```bash
python3 scripts/sample_label_review.py \
  --input data/processed/suggested_labels.csv \
  --class-name "Uncertain" \
  --n 10
```
