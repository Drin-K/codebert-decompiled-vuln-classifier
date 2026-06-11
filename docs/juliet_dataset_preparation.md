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

Example command using the same limit for every selected CWE:

```bash
python3 scripts/compile_juliet_subset.py \
  --juliet-root data/source_datasets/elfFILES \
  --output-dir data/binaries/juliet \
  --manifest data/binaries_manifest.csv \
  --limit-per-cwe 10 \
  --optimization -O0 \
  --debug-symbols
```

For targeted dataset extension, use per-CWE limits:

```bash
python3 scripts/compile_juliet_subset.py \
  --juliet-root data/source_datasets/elfFILES \
  --output-dir data/binaries/juliet \
  --manifest data/binaries_manifest.csv \
  --cwe-limits CWE121=250,CWE122=250,CWE134=400,CWE190=400 \
  --optimization -O0 \
  --debug-symbols
```

When `--cwe-limits` is provided, all supported keys must be present:

```text
CWE121
CWE122
CWE134
CWE190
```

Preview selected files and compile commands without compiling:

```bash
python3 scripts/compile_juliet_subset.py --dry-run
```

## Verify ELF Files

```bash
find data/binaries/juliet -type f | head -n 10
file $(find data/binaries/juliet -type f | head -n 5)
```

## Run Ghidra Extraction After Compilation

After ELF binaries exist, run bulk extraction:

```bash
python3 scripts/run_bulk_extraction.py \
  --input-dir data/binaries/juliet \
  --output-dir data/raw \
  --ghidra-home /opt/ghidra
```

This produces raw pseudo-C CSV files. Function cleaning, final labeling, TF-IDF training, CodeBERT fine-tuning, and evaluation happen in later phases.
