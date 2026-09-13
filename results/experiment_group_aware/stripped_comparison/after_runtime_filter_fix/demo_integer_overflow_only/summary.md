# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_integer_overflow_only`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 19
- Total functions classified: 7
- Total functions excluded: 12
- Accepted decisions: 5
- Uncertain decisions: 2
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 4
- Buffer Overflow: 1
- Format String: 0
- Integer Overflow: 0
- Uncertain — Human review recommended: 2

## Excluded From Classification

- compiler_runtime_boilerplate: 4
- confirmed_import_stub: 4
- ghidra_thunk_function: 3
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| FUN_0040117c | Buffer Overflow | 0.7375 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_integer_overflow_only/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_integer_overflow_only/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_integer_overflow_only/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
