# Fine-Tuning CodeBERT for Automated Vulnerability Classification in Decompiled Binary Functions

This repository supports a bachelor's thesis on using machine learning to classify security vulnerability types in Ghidra-decompiled pseudo-C functions from Linux ELF binaries.

The project studies whether CodeBERT can retain useful code semantics when source-level identifiers have been lost during compilation and decompilation.

## Classification Task

The model performs function-level multiclass classification over four labels:

| Label | Class |
| --- | --- |
| 0 | Clean |
| 1 | Buffer Overflow |
| 2 | Format String |
| 3 | Integer Overflow |

## High-Level Pipeline

```text
ELF binary
-> Ghidra headless decompilation
-> pseudo-C function extraction
-> CSV dataset
-> cleaning and labeling
-> TF-IDF baseline
-> CodeBERT fine-tuning
-> evaluation and error analysis
```

## Scope

This project is limited to:

- Linux ELF binaries
- x86 and x86-64 architecture
- C and C++ compiled binaries
- Static analysis only
- Function-level classification only
- Ghidra 11.x headless decompilation
- TF-IDF + Logistic Regression baseline
- CodeBERT fine-tuning using `microsoft/codebert-base`

This project does not implement exploit generation, dynamic analysis, a chatbot, RAG, assembly-level machine learning, Windows PE/macOS Mach-O support, or a production vulnerability scanner.

## Repository Structure

```text
data/
  binaries/       # Local ELF binaries, not committed
  raw/            # Raw extracted function data, not committed
  processed/      # Cleaned datasets, not committed
ghidra_scripts/   # Future Ghidra headless extraction scripts
scripts/          # Utility scripts
notebooks/        # Future exploration and training notebooks
outputs/
  reports/        # Generated evaluation reports and figures, not committed
  models/         # Trained checkpoints, not committed
docs/             # Project documentation
tests/            # Minimal test scaffolding
```

## Setup

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify the local Python environment:

```bash
python scripts/verify_environment.py
```

Ghidra must be installed separately. See [docs/phase1_environment_setup.md](docs/phase1_environment_setup.md) for Ubuntu/Linux setup instructions, including Java, Ghidra GUI, Ghidra headless mode, and Google Colab GPU checks.
