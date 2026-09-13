# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_format_string_only`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 19
- Total functions classified: 7
- Total functions excluded: 12
- Accepted decisions: 7
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 4
- Buffer Overflow: 0
- Format String: 2
- Integer Overflow: 1
- Uncertain — Human review recommended: 0

## Excluded From Classification

- compiler_runtime_boilerplate: 4
- confirmed_import_stub: 4
- ghidra_thunk_function: 3
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| FUN_0040122a | Format String | 0.8857 |
| FUN_00401184 | Format String | 0.8823 |
| FUN_00401156 | Integer Overflow | 0.7255 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_format_string_only/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_format_string_only/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/after_runtime_filter_fix/demo_format_string_only/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
