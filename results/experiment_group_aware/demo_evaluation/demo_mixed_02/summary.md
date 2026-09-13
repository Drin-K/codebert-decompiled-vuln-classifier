# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo/demo_mixed_02`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 34
- Total functions classified: 7
- Total functions excluded: 27
- Accepted decisions: 3
- Uncertain decisions: 4
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 1
- Buffer Overflow: 0
- Format String: 1
- Integer Overflow: 1
- Uncertain — Human review recommended: 4

## Excluded From Classification

- confirmed_import_stub: 10
- compiler_runtime_boilerplate: 8
- ghidra_thunk_function: 8
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| safe_integer_check_example | Integer Overflow | 0.7817 |
| format_string_candidate_2 | Format String | 0.7010 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_02/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_02/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_02/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
