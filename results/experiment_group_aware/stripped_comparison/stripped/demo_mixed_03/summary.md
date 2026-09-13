# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo_stripped/demo_mixed_03`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 34
- Total functions classified: 14
- Total functions excluded: 20
- Accepted decisions: 10
- Uncertain decisions: 4
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 7
- Buffer Overflow: 0
- Format String: 1
- Integer Overflow: 2
- Uncertain — Human review recommended: 4

## Excluded From Classification

- confirmed_import_stub: 10
- ghidra_thunk_function: 9
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| entry | Integer Overflow | 0.9688 |
| FUN_0040131f | Format String | 0.8851 |
| FUN_00401216 | Integer Overflow | 0.8572 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_mixed_03/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_mixed_03/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/stripped_comparison/stripped/demo_mixed_03/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
