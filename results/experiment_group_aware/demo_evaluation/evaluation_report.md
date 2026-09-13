# Experiment 1 — Seven Demo ELF External Evaluation

## Scope

- Model: `models/codebert-group-aware/`
- Confidence threshold: `0.70`, selected on the Experiment 1 validation split
- Inputs: seven hand-written, unstripped demo ELF binaries
- Evaluation unit: eligible decompiled function
- This is a small external demonstration check, not a statistically representative benchmark.

Ground-truth labels were assigned from the corresponding source files in `data/demo_src/`. Unsafe fixed-buffer copies/concatenations are Buffer Overflow, non-constant format arguments are Format String, unchecked arithmetic used for allocation sizes is Integer Overflow, and explicitly bounded helpers plus dispatcher `main` functions are Clean. The standalone `demo_buffer_overflow` has a vulnerable `main`.

## Aggregate Results

| Measure | Result |
|---|---:|
| ELF binaries completed | 7/7 |
| Functions extracted | 184 |
| Eligible application functions | 34 |
| Runtime/import/PLT/thunk functions excluded | 150 |
| Raw exact-class accuracy | 22/34 (64.71%) |
| Vulnerable functions assigned the exact class | 6/16 (37.50%) |
| Vulnerable functions assigned any non-Clean class | 11/16 (68.75%) |
| Clean functions assigned Clean | 16/18 (88.89%) |
| Accepted decisions at threshold 0.70 | 9/34 (26.47% coverage) |
| Correct accepted decisions | 8/9 (88.89%) |
| Human review recommended | 25/34 (73.53%) |

The validation-derived threshold prevented every low-confidence raw error from becoming an automatic decision. It did not prevent one high-confidence false positive: `safe_integer_check_example` in `demo_mixed_02` was accepted as Integer Overflow with confidence `0.782` although its source checks for overflow.

## Per-Binary Results

| Demo ELF | Extracted | Eligible | Excluded | Raw correct | Accepted correct / accepted | Uncertain | Vulnerable functions with exact class |
|---|---:|---:|---:|---:|---:|---:|---:|
| `demo_buffer_overflow` | 23 | 1 | 22 | 1/1 | 0/0 | 1 | 1/1 |
| `demo_buffer_overflow_only` | 23 | 4 | 19 | 1/4 | 1/1 | 3 | 0/2 |
| `demo_format_string_only` | 19 | 4 | 15 | 4/4 | 1/1 | 3 | 2/2 |
| `demo_integer_overflow_only` | 19 | 4 | 15 | 2/4 | 1/1 | 3 | 0/2 |
| `demo_mixed_01` | 32 | 7 | 25 | 5/7 | 2/2 | 5 | 1/3 |
| `demo_mixed_02` | 34 | 7 | 27 | 4/7 | 2/3 | 4 | 1/3 |
| `demo_mixed_03` | 34 | 7 | 27 | 5/7 | 1/1 | 6 | 1/3 |

Excluded-function breakdown below is ordered as compiler runtime / PLT / thunk / confirmed import:

| Demo ELF | Exclusion breakdown |
|---|---:|
| `demo_buffer_overflow` | 9 / 1 / 3 / 9 |
| `demo_buffer_overflow_only` | 8 / 1 / 4 / 6 |
| `demo_format_string_only` | 8 / 1 / 2 / 4 |
| `demo_integer_overflow_only` | 8 / 1 / 2 / 4 |
| `demo_mixed_01` | 8 / 1 / 7 / 9 |
| `demo_mixed_02` | 8 / 1 / 8 / 10 |
| `demo_mixed_03` | 8 / 1 / 8 / 10 |

## Raw Predicted Class Distributions

| Demo ELF | Clean | Buffer Overflow | Format String | Integer Overflow |
|---|---:|---:|---:|---:|
| `demo_buffer_overflow` | 0 | 1 | 0 | 0 |
| `demo_buffer_overflow_only` | 3 | 0 | 0 | 1 |
| `demo_format_string_only` | 2 | 0 | 2 | 0 |
| `demo_integer_overflow_only` | 3 | 1 | 0 | 0 |
| `demo_mixed_01` | 4 | 1 | 1 | 1 |
| `demo_mixed_02` | 4 | 1 | 1 | 1 |
| `demo_mixed_03` | 5 | 0 | 1 | 1 |

## Top Suspicious Candidates

| Demo ELF | Highest-confidence non-Clean raw candidates |
|---|---|
| `demo_buffer_overflow` | `main`: Buffer Overflow, 0.502 (uncertain) |
| `demo_buffer_overflow_only` | `clean_length_helper`: Integer Overflow, 0.595 (uncertain, incorrect) |
| `demo_format_string_only` | `format_string_candidate_fprintf`: Format String, 0.696; `format_string_candidate_printf`: Format String, 0.582 (both uncertain, correct raw classes) |
| `demo_integer_overflow_only` | `integer_overflow_candidate_add`: Buffer Overflow, 0.509 (uncertain, wrong class) |
| `demo_mixed_01` | `format_string_candidate_1`: Format String, 0.677 (correct); `buffer_overflow_candidate_1`: Integer Overflow, 0.596 (wrong); `integer_overflow_candidate_1`: Buffer Overflow, 0.492 (wrong); all uncertain |
| `demo_mixed_02` | `safe_integer_check_example`: Integer Overflow, 0.782 (accepted, incorrect); `format_string_candidate_2`: Format String, 0.701 (accepted, correct); `integer_overflow_candidate_2`: Buffer Overflow, 0.593 (uncertain, wrong) |
| `demo_mixed_03` | `format_string_candidate_3`: Format String, 0.664 (correct); `buffer_overflow_candidate_3`: Integer Overflow, 0.497 (wrong); both uncertain |

## Incorrect Raw Classifications

- `demo_buffer_overflow_only`: the clean length helper was called Integer Overflow; both Buffer Overflow candidates were called Clean.
- `demo_integer_overflow_only`: the multiply candidate was called Clean; the add candidate was called Buffer Overflow.
- `demo_mixed_01`: the Buffer Overflow and Integer Overflow candidates were swapped.
- `demo_mixed_02`: the safe checked-add helper was called Integer Overflow; the Buffer Overflow candidate was called Clean; the Integer Overflow candidate was called Buffer Overflow.
- `demo_mixed_03`: the Buffer Overflow candidate was called Integer Overflow; the Integer Overflow candidate was called Clean.
- `demo_buffer_overflow` and `demo_format_string_only` had no raw exact-class errors, but their vulnerability decisions remained below the automatic-accept threshold.

## Interpretation

The end-to-end Linux pipeline, conservative function filter, Experiment 1 model, and uncertainty output all operate correctly on all seven ELF files. The filtering result is strong: all 34 intended application functions were retained, while 150 runtime/import/PLT/thunk functions were excluded.

The model result is not yet strong enough to claim reliable performance on unseen demo binaries. Its 100% group-aware test accuracy does not transfer to this small external set: raw exact-class accuracy is 64.71%, exact vulnerable-class recall is 37.50%, and 73.53% of functions require human review. Format String transfers best; Buffer Overflow and Integer Overflow are frequently missed or confused. This is evidence of a training-to-demo domain gap, not a pipeline activation or filtering failure.

Per-function CSV, JSON, and Markdown outputs are stored in each demo's subdirectory under this directory.
