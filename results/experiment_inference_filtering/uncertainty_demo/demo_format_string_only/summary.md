# Phase 11 ELF Prediction Demo

- Binary analyzed: `/home/drin/codebert-decompiled-vuln-classifier/data/demo/demo_format_string_only`
- Model path: `/home/drin/codebert-decompiled-vuln-classifier/models/codebert-final`
- Device used: `cpu`
- Total functions extracted: 19
- Total functions classified: 4
- Total functions excluded: 15
- Accepted decisions: 3
- Uncertain decisions: 1
- Confidence threshold: 0.70

## Class Distribution (Accepted Decisions Only)

- Clean: 1
- Buffer Overflow: 0
- Format String: 2
- Integer Overflow: 0
- Uncertain: 1

## Excluded From Classification

- compiler_runtime_boilerplate: 8
- confirmed_import_stub: 4
- ghidra_thunk_function: 2
- ghidra_plt_function: 1

## Top Suspicious Functions

| Function | Predicted class | Confidence |
|---|---|---:|
| format_string_candidate_printf | Format String | 0.9258 |
| format_string_candidate_fprintf | Format String | 0.9227 |

## Output Files

- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_inference_filtering/uncertainty_demo/demo_format_string_only/elf_predictions.csv`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_inference_filtering/uncertainty_demo/demo_format_string_only/elf_predictions.json`
- `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_inference_filtering/uncertainty_demo/demo_format_string_only/summary.md`

## Limitation

This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.
