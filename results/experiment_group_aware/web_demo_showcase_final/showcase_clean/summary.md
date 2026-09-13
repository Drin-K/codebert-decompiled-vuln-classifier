# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/web_demo_showcase/showcase_clean`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 25
- Total functions classified: 5
- Total functions excluded: 20
- Accepted decisions: 5
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 5
- Buffer Overflow: 0
- Format String: 0
- Integer Overflow: 0
- Uncertain — Human review recommended: 0

## Excluded From Classification

- compiler_runtime_boilerplate: 9
- confirmed_import_stub: 8
- ghidra_thunk_function: 2
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| No non-Clean user-code candidates | — | — |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_clean/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_clean/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_clean/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
