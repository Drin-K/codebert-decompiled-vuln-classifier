# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_buffer_overflow`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 23
- Total functions classified: 7
- Total functions excluded: 16
- Accepted decisions: 6
- Uncertain decisions: 1
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 5
- Buffer Overflow: 0
- Format String: 0
- Integer Overflow: 1
- Uncertain — Human review recommended: 1

## Excluded From Classification

- confirmed_import_stub: 9
- ghidra_thunk_function: 4
- compiler_runtime_boilerplate: 2
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| entry | Integer Overflow | 0.9694 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_buffer_overflow/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_buffer_overflow/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_buffer_overflow/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
