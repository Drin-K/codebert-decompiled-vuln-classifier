# Confirmed Runtime-Name Filter Correction

## Change

The conservative inference filter was extended with four runtime/startup names confirmed in the stripped demo ELF outputs:

- `entry`
- `_DT_INIT`
- `_FINI_0`
- `_DT_FINI`

The presentation-layer runtime-name check was updated consistently. Ambiguous `FUN_*` functions, short functions, and wrapper-like functions remain eligible because their names alone do not prove that they are compiler/runtime code.

## Verification

- All seven stripped ELF pipelines completed successfully with the Experiment 1 model.
- Corrected outputs were saved separately under `after_runtime_filter_fix/`; the first stripped comparison was not overwritten.
- All 34 ground-truth application functions remain eligible.
- All 28 occurrences of the four newly confirmed runtime names are now excluded.
- No corrected runtime name remains classified.
- Regression tests confirm both the new exclusions and continued eligibility of ambiguous names.

## Before and After

| Measure | Before correction | After correction | Change |
|---|---:|---:|---:|
| Extracted functions | 184 | 184 | 0 |
| Eligible functions | 82 | 54 | -28 |
| Ground-truth application functions eligible | 34/34 | 34/34 | 0 |
| Extra runtime/startup functions eligible | 48 | 20 | -28 |
| Extra runtime functions predicted non-Clean | 7 | 0 | -7 |
| Confirmed `entry` false positives | 7 | 0 | -7 |
| Functions excluded | 102 | 130 | +28 |

The correction removed 58.33% of the extra runtime functions that passed the initial stripped filter. The 20 remaining extra functions have ambiguous `FUN_*` names and were all predicted Clean. Excluding them solely by name would violate the conservative-filtering rule and could create blind spots in real stripped binaries.

## Per-Binary Result After Correction

| Demo ELF | Extracted | Eligible | Application functions | Remaining ambiguous runtime functions | Remaining runtime functions predicted non-Clean |
|---|---:|---:|---:|---:|---:|
| `demo_buffer_overflow` | 23 | 3 | 1 | 2 | 0 |
| `demo_buffer_overflow_only` | 23 | 7 | 4 | 3 | 0 |
| `demo_format_string_only` | 19 | 7 | 4 | 3 | 0 |
| `demo_integer_overflow_only` | 19 | 7 | 4 | 3 | 0 |
| `demo_mixed_01` | 32 | 10 | 7 | 3 | 0 |
| `demo_mixed_02` | 34 | 10 | 7 | 3 | 0 |
| `demo_mixed_03` | 34 | 10 | 7 | 3 | 0 |

## Effect on Model Evaluation

The 34 application-function predicted classes and decisions are unchanged. Therefore, stripped application accuracy remains 14/34 (41.18%), and the filter correction must not be presented as a model-accuracy improvement.

This correction improves pipeline precision by removing confirmed startup noise without hiding ambiguous stripped functions. The remaining low application accuracy is a model/domain-generalization issue rather than a filtering issue.
