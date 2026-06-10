# Juliet Dataset Preparation

This step compiles a small, deterministic subset of NIST SARD Juliet C/C++ source files into Linux ELF binaries for later Ghidra decompilation.

Juliet is useful for this thesis because it contains many known CWE-focused C/C++ test cases. This project only selects CWEs that match the thesis classification scope:

| Juliet CWE | Thesis Class |
| --- | --- |
| CWE-121 Stack Based Buffer Overflow | Buffer Overflow |
| CWE-122 Heap Based Buffer Overflow | Buffer Overflow |
| CWE-134 Uncontrolled Format String | Format String |
| CWE-190 Integer Overflow | Integer Overflow |

The source dataset is expected at:

```text
data/source_datasets/elfFILES/
```

Juliet support files are required at:

```text
data/source_datasets/elfFILES/testcasesupport/
```

Verify the required support files:

```bash
find data/source_datasets/elfFILES/testcasesupport -name "std_testcase.h"
find data/source_datasets/elfFILES/testcasesupport -name "io.c"
```

Generated ELF binaries are written to:

```text
data/binaries/juliet/
```

The metadata manifest is written to:

```text
data/binaries_manifest.csv
```

## Compile Juliet Subset

Example command:

```bash
python scripts/compile_juliet_subset.py \
  --juliet-root data/source_datasets/elfFILES \
  --output-dir data/binaries/juliet \
  --manifest data/binaries_manifest.csv \
  --limit-per-cwe 10 \
  --optimization -O0 \
  --debug-symbols
```

Preview selected files and compile commands without compiling:

```bash
python scripts/compile_juliet_subset.py --dry-run
```

## Verify ELF Files

```bash
find data/binaries/juliet -type f | head -n 10
file $(find data/binaries/juliet -type f | head -n 5)
```

## Run Ghidra Extraction After Compilation

After ELF binaries exist, run bulk extraction:

```bash
python scripts/run_bulk_extraction.py \
  --input-dir data/binaries/juliet \
  --output-dir data/raw \
  --ghidra-home /opt/ghidra
```

This produces raw pseudo-C CSV files. Function cleaning, final labeling, TF-IDF training, CodeBERT fine-tuning, and evaluation happen in later phases.
