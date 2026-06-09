# Phase 2 Ghidra Extraction

Phase 2 sets up automated static extraction of Ghidra-decompiled pseudo-C from Linux ELF binaries. It does not label functions, clean datasets, train models, evaluate models, or prove exploitability.

The output of this phase is one raw CSV file per ELF binary. Each row represents one function discovered by Ghidra and contains metadata plus the decompiled pseudo-C text when decompilation succeeds.

## Why Ghidra Is Used

Ghidra provides a headless analysis mode that can import compiled binaries, analyze functions, and run custom scripts without using the GUI. This makes it suitable for repeatable extraction of pseudo-C functions from ELF binaries.

## Key Terms

- ELF binary: A compiled Linux executable or shared object file.
- Assembly: Low-level processor instructions recovered from the binary.
- Decompiled pseudo-C: Ghidra's C-like reconstruction of binary functions. It is not original source code.
- Raw CSV: The direct extraction output from Ghidra. It contains function metadata and pseudo-C text, but no labels.

## Folder Roles

Place local ELF binaries in:

```text
data/binaries/
```

Generated raw extraction CSV files are written to:

```text
data/raw/
```

Both folders contain `.gitkeep` placeholders so the directory structure remains in git. Real binaries and generated CSV files are ignored by `.gitignore`.

## Compile the Example Test Binary

The repository includes a harmless C example in `examples/simple_test.c`. Compile it with:

```bash
gcc -O0 -g -o data/binaries/simple_test examples/simple_test.c
```

This produces a local ELF binary for testing Ghidra decompilation. The compiled binary should not be committed.

## Run Extraction for One Binary

```bash
python scripts/run_ghidra_extraction.py \
  --binary data/binaries/simple_test \
  --output data/raw/simple_test_functions.csv \
  --ghidra-home /opt/ghidra \
  --project-dir /tmp/ghidra_projects \
  --project-name simple_test_project
```

The wrapper runs Ghidra headless with this pattern:

```text
<ghidra-home>/support/analyzeHeadless <project-dir> <project-name> -import <binary> -scriptPath ghidra_scripts -postScript extract_functions.py <output> -deleteProject
```

## Run Bulk Extraction

To process every ELF binary in `data/binaries/`:

```bash
python scripts/run_bulk_extraction.py \
  --input-dir data/binaries \
  --output-dir data/raw \
  --ghidra-home /opt/ghidra
```

This creates one CSV per binary:

```text
data/raw/<binary_name>_functions.csv
```

## Inspect the Resulting CSV

Use Python or command-line tools to inspect the raw output:

```bash
python -c "import pandas as pd; df = pd.read_csv('data/raw/simple_test_functions.csv'); print(df.head()); print(df.columns.tolist())"
```

Expected columns:

```text
binary_name,function_name,function_address,function_code,decompile_status
```

`function_code` may be empty when Ghidra cannot decompile a function. In that case, `decompile_status` records the failure reason.

## Troubleshooting

If plain `analyzeHeadless` prints an error like:

```text
Ghidra was not started with PyGhidra. Python is not available
```

then the installed Ghidra version/runtime is not loading Python scripts through plain `analyzeHeadless`. Newer Ghidra versions may require PyGhidra for headless Python scripts.

The wrapper `scripts/run_ghidra_extraction.py` automatically uses Ghidra's local PyGhidra environment when it is available. If PyGhidra is not installed yet, install it from the wheel bundled with Ghidra:

```bash
~/.config/ghidra/ghidra_12.1.2_PUBLIC/venv/bin/python3 -m pip install --no-index -f /opt/ghidra/Ghidra/Features/PyGhidra/pypkg/dist pyghidra
```

The exact `ghidra_12.1.2_PUBLIC` directory may differ if your local Ghidra version is different.

## Phase 2 Boundaries

- Labeling is not done in Ghidra.
- Labeling is not done in Phase 2.
- Phase 2 only creates raw pseudo-C extraction CSVs.
- Cleaning and labeling come in later phases.
- TF-IDF, CodeBERT fine-tuning, evaluation, and error analysis are not implemented in this phase.
