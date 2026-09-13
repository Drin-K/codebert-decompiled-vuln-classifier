# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/web_demo_showcase/showcase_buffer_overflow`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 28
- Total functions classified: 4
- Total functions excluded: 24
- Accepted decisions: 4
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 2
- Buffer Overflow: 2
- Format String: 0
- Integer Overflow: 0
- Uncertain — Human review recommended: 0

## Excluded From Classification

- confirmed_import_stub: 10
- compiler_runtime_boilerplate: 9
- ghidra_thunk_function: 4
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| CWE121_Stack_Based_Buffer_Overflow__CWE131_memmove_16_bad | Buffer Overflow | 0.7877 |
| CWE121_Stack_Based_Buffer_Overflow__CWE131_memcpy_16_bad | Buffer Overflow | 0.7658 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_buffer_overflow/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_buffer_overflow/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_buffer_overflow/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
