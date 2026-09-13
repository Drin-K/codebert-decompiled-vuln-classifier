# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/web_demo_showcase/showcase_mixed`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 46
- Total functions classified: 8
- Total functions excluded: 38
- Accepted decisions: 8
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 2
- Buffer Overflow: 2
- Format String: 2
- Integer Overflow: 2
- Uncertain — Human review recommended: 0

## Excluded From Classification

- confirmed_import_stub: 17
- ghidra_thunk_function: 11
- compiler_runtime_boilerplate: 9
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| CWE134_Uncontrolled_Format_String__char_console_snprintf_01_bad | Format String | 0.9828 |
| CWE134_Uncontrolled_Format_String__char_console_printf_01_bad | Format String | 0.9806 |
| CWE190_Integer_Overflow__char_rand_square_08_bad | Integer Overflow | 0.9797 |
| CWE190_Integer_Overflow__char_rand_add_08_bad | Integer Overflow | 0.9791 |
| CWE121_Stack_Based_Buffer_Overflow__CWE131_memmove_16_bad | Buffer Overflow | 0.7824 |
| CWE121_Stack_Based_Buffer_Overflow__CWE131_memcpy_16_bad | Buffer Overflow | 0.7606 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_mixed/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_mixed/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_mixed/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
