# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo/demo_mixed_03`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 34
- Total functions classified: 7
- Total functions excluded: 27
- Accepted decisions: 1
- Uncertain decisions: 6
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 1
- Buffer Overflow: 0
- Format String: 0
- Integer Overflow: 0
- Uncertain — Human review recommended: 6

## Excluded From Classification

- confirmed_import_stub: 10
- compiler_runtime_boilerplate: 8
- ghidra_thunk_function: 8
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| No non-Clean user-code candidates | — | — |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_03/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_03/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/demo_evaluation/demo_mixed_03/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
