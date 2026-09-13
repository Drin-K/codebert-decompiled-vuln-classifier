# Experiment 1 — Stripped vs Unstripped Demo ELF Comparison

## Scope and Method

- Model: `models/codebert-group-aware/`
- Confidence threshold: `0.70`
- Inputs: the same seven demo programs used in the external demo evaluation
- Unstripped outputs: `results/experiment_group_aware/demo_evaluation/`
- Stripped outputs: `results/experiment_group_aware/stripped_comparison/stripped/`

The stripped binaries were created with `objcopy --strip-all` as separate files under `data/demo_stripped/`. The original binaries were not modified. `file` verified that every original contains debug information and is not stripped, while every comparison copy is stripped. Matching Build IDs confirm that each pair represents the same build.

Ground truth was transferred from each unstripped application function to the stripped function at the identical virtual address. All 34 application functions matched by address; none were missing. This avoids using stripped `FUN_*` names to assign labels.

## Main Comparison

| Measure | Unstripped | Stripped | Change |
|---|---:|---:|---:|
| Extracted functions | 184 | 184 | 0 |
| Ground-truth application functions found | 34/34 | 34/34 | 0 |
| Functions considered eligible by the filter | 34 | 82 | +48 |
| Raw exact-class accuracy on application functions | 22/34 (64.71%) | 14/34 (41.18%) | -23.53 percentage points |
| Exact class on vulnerable functions | 6/16 (37.50%) | 6/16 (37.50%) | 0 |
| Any non-Clean prediction on vulnerable functions | 11/16 (68.75%) | 14/16 (87.50%) | +18.75 points |
| Clean functions predicted Clean | 16/18 (88.89%) | 8/18 (44.44%) | -44.45 points |
| Accepted application decisions | 9/34 (26.47%) | 18/34 (52.94%) | +26.47 points |
| Correct accepted application decisions | 8/9 (88.89%) | 11/18 (61.11%) | -27.78 points |
| Application functions marked uncertain | 25/34 (73.53%) | 16/34 (47.06%) | -26.47 points |

The increase in “any non-Clean” detection and accepted-decision coverage is not evidence of improvement. It comes with a major increase in false positives: stripping caused many Clean functions to be predicted confidently as Integer Overflow.

## Per-Binary Application-Function Accuracy

| Demo ELF | Unstripped raw correct | Stripped raw correct | Unstripped accepted correct / accepted | Stripped accepted correct / accepted | Extra eligible runtime functions after stripping |
|---|---:|---:|---:|---:|---:|
| `demo_buffer_overflow` | 1/1 | 1/1 | 0/0 | 0/0 | 6 |
| `demo_buffer_overflow_only` | 1/4 | 1/4 | 1/1 | 1/2 | 7 |
| `demo_format_string_only` | 4/4 | 3/4 | 1/1 | 3/4 | 7 |
| `demo_integer_overflow_only` | 2/4 | 1/4 | 1/1 | 1/2 | 7 |
| `demo_mixed_01` | 5/7 | 3/7 | 2/2 | 2/3 | 7 |
| `demo_mixed_02` | 4/7 | 2/7 | 2/3 | 2/4 | 7 |
| `demo_mixed_03` | 5/7 | 3/7 | 1/1 | 2/3 | 7 |

## Effect on Filtering

For the unstripped binaries, the filter selected exactly the 34 intended application functions and excluded 150 recognized runtime/import/PLT/thunk functions.

For the stripped binaries, the filter still retained all 34 application functions, so it did not create false exclusions. However, it also classified 48 additional runtime/startup functions whose informative symbols had disappeared or changed. These consisted of six extra functions in `demo_buffer_overflow` and seven in each other binary.

The recurring extra functions included `_DT_INIT`, `entry`, `_FINI_0`, `_DT_FINI`, and several ambiguous `FUN_*` functions. Every stripped `entry` function was accepted as Integer Overflow with confidence between approximately `0.968` and `0.971`. These seven findings are false positives from startup code, not real vulnerabilities.

This reveals a real limitation of symbol-based filtering. Some explicitly recognizable stripped-runtime names can be added safely to the known-runtime list, but ambiguous `FUN_*` functions cannot be excluded merely because of their names without risking removal of genuine user code.

## Effect on Model Predictions

Stripping changed the raw predicted class for 15 of the 34 matched application functions (44.12%). Important changes included:

- Several safe copy and safe format helpers changed from Clean to Integer Overflow.
- Both Buffer Overflow candidates in `demo_buffer_overflow_only` changed from Clean to Integer Overflow; they remained incorrect.
- The clean output helper in `demo_format_string_only` changed from Clean to an accepted Integer Overflow false positive.
- The two known format-string candidates remained Format String in every relevant demo.
- The model still assigned the exact vulnerability class to only 6 of 16 vulnerable functions: the standalone buffer-overflow `main` and the five format-string functions.
- None of the five integer-overflow functions received the correct Integer Overflow class.

Because the machine-code build is the same and all application functions were matched at the same addresses, the prediction changes are attributable to changes in Ghidra's decompiled representation, especially removed or replaced symbol names and renamed local calls. This is evidence that the model is sensitive to identifier information and does not yet generalize reliably from code structure alone.

## Conclusion

The stripped test exposes two independent weaknesses:

1. **Inference filtering weakness:** loss of symbols causes known compiler/startup code to pass the conservative filter, creating extra findings.
2. **Model generalization weakness:** application-function accuracy falls from 64.71% to 41.18%, while accepted-decision accuracy falls from 88.89% to 61.11%.

The result supports the earlier leakage-audit warning that label-revealing identifiers in the Juliet-derived dataset may inflate internal performance. The system remains suitable as a bachelor-level research prototype if these limitations and the contrast between internal and external results are reported honestly. It should not be described as production-ready or as achieving 95% accuracy on arbitrary ELF binaries.
