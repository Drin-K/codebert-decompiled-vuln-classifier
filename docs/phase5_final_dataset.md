# Phase 5: Final Dataset Creation

Phase 5 creates the final training CSV from the Phase 4 suggested labels. It does not train a model, run Ghidra, compile binaries, or modify Phase 3 cleaning.

The input file is:

```text
data/processed/suggested_labels.csv
```

The outputs are:

```text
data/processed/final_labeled_dataset.csv
data/processed/final_dataset_summary.md
```

## Why Sanity Checks Were Added

Juliet metadata and `bad` function names are useful weak labels, but the model only sees Ghidra-decompiled pseudo-C. Some vulnerable source variants can lose the visible vulnerability signal during decompilation because of truncation, optimization, unreachable block removal, or constant folding.

Training on a vulnerable label when the pseudo-C body does not show the vulnerable operation would teach CodeBERT the wrong association. Phase 5 therefore keeps vulnerable samples only when the class-specific operation is visible in `function_code`.

## Sanity Check Rules

Buffer Overflow samples must show a buffer-overflow-relevant operation, such as an unsafe copy/write call, array write with a non-constant index, pointer/index access, or a weak bounds pattern.

Format String samples must show a format-string sink such as `printf`, `fprintf`, `sprintf`, `snprintf`, `vfprintf`, `vprintf`, or `vsnprintf`, with a non-literal format argument such as `data`.

Integer Overflow samples must show arithmetic involving relevant variables such as `data`, `result`, or decompiler temporary variables. If the decompiler constant-folded the issue into a literal value with no visible arithmetic, the row is excluded.

Clean samples do not require vulnerable-pattern sanity checks. Juliet good functions may contain APIs such as `memcpy`, `memmove`, `malloc`, input functions, arithmetic, or array indexing while still being safe because of good source or good sink logic.

## Final Decisions

Phase 5 writes validation fields:

```text
sanity_check_status = passed / failed / not_required
final_decision = include / exclude / review
```

Rows are included only when `final_decision = include` and the final class is one of:

```text
Clean
Buffer Overflow
Format String
Integer Overflow
```

Rows marked `Exclude`, `Uncertain`, review, or failed sanity check are not used for training. Exclude rows are intentionally omitted because wrappers, dispatchers, helpers, stubs, and weak/ambiguous samples can cause the model to learn benchmark structure instead of vulnerability logic.

## Balanced Dataset

The script samples a balanced final dataset with deterministic sampling:

```text
seed = 42
minimum target per class = 250
```

`--target-per-class` is treated as a minimum requirement, not an exact final size. After sanity checks, the script finds the smallest available final class count and downsamples all classes to that count.

If the smallest class has at least the requested minimum, the minimum target is achieved and the final dataset uses the smallest available class count. If the smallest class has fewer than the requested minimum, the script still creates the largest possible balanced dataset, reports the limiting class, and records the actual class counts in the summary.

## Limitations

The final dataset is still weak-labeled and benchmark-derived. It is appropriate for bachelor thesis prototype training and controlled experiments, but it is not production-grade exploitation detection data.

## Commands

Create the final dataset:

```bash
python3 scripts/create_final_dataset.py \
  --input data/processed/suggested_labels.csv \
  --output data/processed/final_labeled_dataset.csv \
  --summary data/processed/final_dataset_summary.md \
  --target-per-class 250 \
  --seed 42
```

Inspect the summary:

```bash
cat data/processed/final_dataset_summary.md
```

Check final distribution:

```bash
python3 - <<'PY'
import csv
from collections import Counter

with open("data/processed/final_labeled_dataset.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("Total:", len(rows))
print(Counter(r["final_class"] for r in rows))
print(Counter(r["final_label"] for r in rows))
PY
```

Sample final classes:

```bash
python3 scripts/sample_final_dataset.py \
  --input data/processed/final_labeled_dataset.csv \
  --class-name "Clean" \
  --n 5

python3 scripts/sample_final_dataset.py \
  --input data/processed/final_labeled_dataset.csv \
  --class-name "Buffer Overflow" \
  --n 5

python3 scripts/sample_final_dataset.py \
  --input data/processed/final_labeled_dataset.csv \
  --class-name "Format String" \
  --n 5

python3 scripts/sample_final_dataset.py \
  --input data/processed/final_labeled_dataset.csv \
  --class-name "Integer Overflow" \
  --n 5
```
