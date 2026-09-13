# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_integer_overflow_only`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 19
- Total functions classified: 11
- Total functions excluded: 8
- Accepted decisions: 9
- Uncertain decisions: 2
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 7
- Buffer Overflow: 1
- Format String: 0
- Integer Overflow: 1
- Uncertain — Human review recommended: 2

## Excluded From Classification

- confirmed_import_stub: 4
- ghidra_thunk_function: 3
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| entry | Integer Overflow | 0.9684 |
| FUN_0040117c | Buffer Overflow | 0.7375 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_integer_overflow_only/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_integer_overflow_only/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_integer_overflow_only/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
