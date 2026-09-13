# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_mixed_02`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 34
- Total functions classified: 10
- Total functions excluded: 24
- Accepted decisions: 7
- Uncertain decisions: 3
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 4
- Buffer Overflow: 0
- Format String: 1
- Integer Overflow: 2
- Uncertain — Human review recommended: 3

## Excluded From Classification

- confirmed_import_stub: 10
- ghidra_thunk_function: 9
- compiler_runtime_boilerplate: 4
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| FUN_00401216 | Integer Overflow | 0.8993 |
| FUN_00401319 | Format String | 0.8821 |
| FUN_004012a0 | Integer Overflow | 0.8777 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_mixed_02/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_mixed_02/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_mixed_02/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
