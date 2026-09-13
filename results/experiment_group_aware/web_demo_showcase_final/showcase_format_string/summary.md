# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/web_demo_showcase/showcase_format_string`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-group-aware`
- Device used: `cpu`
- Total functions extracted: 32
- Total functions classified: 4
- Total functions excluded: 28
- Accepted decisions: 4
- Uncertain decisions: 0
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 2
- Buffer Overflow: 0
- Format String: 2
- Integer Overflow: 0
- Uncertain — Human review recommended: 0

## Excluded From Classification

- confirmed_import_stub: 12
- compiler_runtime_boilerplate: 9
- ghidra_thunk_function: 6
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| CWE134_Uncontrolled_Format_String__char_console_snprintf_01_bad | Format String | 0.9828 |
| CWE134_Uncontrolled_Format_String__char_console_printf_01_bad | Format String | 0.9806 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_format_string/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_format_string/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/web_demo_showcase_final/showcase_format_string/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
