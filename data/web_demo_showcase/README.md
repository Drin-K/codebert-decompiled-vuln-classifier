# Curated Web Demo Showcase

These five ELF files are curated, Juliet-style best-case examples for demonstrating the web interface with the Experiment 1 model:

| Upload this ELF | Expected result | Verified model result |
|---|---|---|
| `showcase_buffer_overflow` | 2 Buffer Overflow functions + Clean support/main | Correct, all accepted |
| `showcase_format_string` | 2 Format String functions + Clean support/main | Correct, all accepted |
| `showcase_integer_overflow` | 2 Integer Overflow functions + Clean support/main | Correct, all accepted |
| `showcase_clean` | 5 Clean functions | Correct, all accepted |
| `showcase_mixed` | Clean + all three vulnerability classes | Correct, all accepted |

Verified confidence range by class:

- Buffer Overflow: 76.06% to 78.77%
- Format String: 98.06% to 98.28%
- Integer Overflow: 97.91% to 97.97%
- Clean: 87.76% to 90.93%

Across the five files, all 25 eligible functions received the expected raw class, all 25 decisions were accepted at the 0.70 threshold, and none required human review. The mixed ELF alone contains 8 eligible functions: 2 Buffer Overflow, 2 Format String, 2 Integer Overflow, and 2 Clean.

These are deliberately selected, unstripped, pattern-aligned examples. Their identifiers and structures resemble the Juliet data used in the project. They demonstrate model capability but must not be reported as an independent accuracy benchmark. Use the seven-demo external evaluation and stripped comparison for honest generalization results.

The corresponding source files are in `data/web_demo_showcase_src/`. Verified inference outputs are in `results/experiment_group_aware/web_demo_showcase_final/`.
