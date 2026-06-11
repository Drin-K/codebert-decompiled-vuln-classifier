# Phase 3 Merge and Cleaning

Phase 3 merges raw Ghidra extraction CSV files and removes obvious non-useful functions. It does not assign vulnerability labels, train models, or evaluate classifiers.

## Why Cleaning Is Needed

Raw Ghidra output contains more than user-written testcase functions. ELF binaries also include compiler, linker, runtime, import, thunk, and startup functions such as `_start`, `_init`, `_fini`, PLT-style wrappers, and clone-table helpers. These functions add noise for a function-level vulnerability classification dataset.

## Why Merge First

Each ELF binary produces one raw CSV. Merging them first creates one consistent table before applying shared cleaning rules across all binaries. The merge step also records `source_csv`, so each function can still be traced back to the original raw extraction file.

## Cleaning Rules

Rows are removed when:

- `decompile_status` is not `success`
- `function_code` is empty
- the code contains `halt_baddata()`
- the function name is known compiler/runtime boilerplate
- the function appears to be an external import wrapper or thunk
- the decompiled code is too short
- the normalized decompiled function body is duplicated

Functions named `FUN_...` are not automatically removed. In stripped binaries, real user functions may only have synthetic Ghidra names, so those functions are kept unless another cleaning rule clearly applies.

## Outputs

```text
data/processed/merged_raw_functions.csv
data/processed/clean_functions.csv
data/processed/cleaning_summary.md
```

The cleaned CSV includes:

```text
normalized_code_hash
code_line_count
code_char_count
cleaning_removed_reason
```

For kept rows, `cleaning_removed_reason` is empty.

## Commands

Merge raw CSV files:

```bash
python scripts/merge_raw_csvs.py \
  --input-dir data/raw \
  --output data/processed/merged_raw_functions.csv
```

Clean merged functions:

```bash
python scripts/clean_functions.py \
  --input data/processed/merged_raw_functions.csv \
  --output data/processed/clean_functions.csv \
  --summary data/processed/cleaning_summary.md
```

Inspect cleaned dataset statistics:

```bash
python scripts/dataset_stats.py \
  --input data/processed/clean_functions.csv
```

## Phase Boundary

Vulnerability labels are not assigned in Phase 3. Cleaning prepares the function table for the next phase, where candidate functions will be reviewed and labeled according to the thesis class schema.
