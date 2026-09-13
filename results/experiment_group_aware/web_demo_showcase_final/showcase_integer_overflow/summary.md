# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/web_demo_showcase/showcase_integer_overflow`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 30
- Total functions classified: 4
- Total functions excluded: 26
- Accepted decisions: 4
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 2
- Buffer Overflow: 0
- Format String: 0
- Integer Overflow: 2
- Uncertain — Human review recommended: 0

## Excluded From Classification

- confirmed_import_stub: 11
- compiler_runtime_boilerplate: 9
- ghidra_thunk_function: 5
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| CWE190_Integer_Overflow__char_rand_square_08_bad | Integer Overflow | 0.9797 |
| CWE190_Integer_Overflow__char_rand_add_08_bad | Integer Overflow | 0.9791 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_integer_overflow/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_integer_overflow/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_integer_overflow/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
