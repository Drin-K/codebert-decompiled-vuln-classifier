# Thesis Agent Context

Persistent project context for future Codex sessions. Read this file before working on the thesis repository. The numeric audit below is supplied by the project owner as verified Experiment 0 context; creating this file did not independently rerun or re-audit the experiments. Clearly distinguish this recorded state from later findings and assumptions. This context file does not itself authorize running the remaining experiments.

## 1. Thesis title

Title:
“Fine-Tuning CodeBERT for Automated Vulnerability Classification in Decompiled Binary Functions”

Simple explanation:
“Teaching AI to Find Security Vulnerabilities in Compiled Programs Without Source Code.”

## 2. Project goal

This bachelor thesis builds an academic prototype for vulnerability classification in decompiled binary functions.

The pipeline starts from NIST Juliet C/C++ source files, compiles them into Linux ELF binaries, decompiles them using Ghidra/PyGhidra, extracts pseudo-C functions, cleans and weak-labels the data, trains a baseline model and a fine-tuned CodeBERT model, compares them, performs error analysis, and provides an ELF inference pipeline with a React/NestJS web demo.

Important:
The model input is not original source code. The model input is Ghidra-decompiled pseudo-C function bodies.

The system classifies vulnerability candidates. It does not prove exploitability and is not a production-ready vulnerability scanner.

## 3. Target classes

The target labels are:

| Label | Class |
| --- | --- |
| 0 | Clean |
| 1 | Buffer Overflow |
| 2 | Format String |
| 3 | Integer Overflow |

## 4. CWE mapping

* CWE-121 + CWE-122 → Buffer Overflow
* CWE-134 → Format String
* CWE-190 → Integer Overflow

CWE-121 and CWE-122 are grouped because both represent Buffer Overflow, one stack-based and one heap-based.

## 5. Dataset source

The dataset is based on the NIST Juliet Test Suite for C/C++ v1.3, part of NIST SARD.

Dataset context:

* NIST stands for National Institute of Standards and Technology.
* Juliet is a synthetic benchmark dataset organized by CWE categories.
* Juliet is used because it provides controlled vulnerability examples, good/bad variants, and CWE metadata.

Important wording:
Do not say the original Juliet C/C++ test cases were created from scratch by me. Say that the experimental dataset was constructed from selected Juliet source files through compilation, decompilation, cleaning, weak labeling, and balancing.

## 6. Verified numeric audit

The following figures are the recorded verified numeric audit supplied for Experiment 0. Preserve their scope and caveats when reporting results.

Source selection:

* 1,300 selected Juliet C/C++ source files
* 1,086 C files
* 214 C++ files
* CWE-121: 250
* CWE-122: 250
* CWE-134: 400
* CWE-190: 400

Compilation:

* 1,300 successful ELF binaries
* 0 recorded compilation failures
* gcc for C files
* g++ for C++ files
* flags include `-O0` and `-g`

Ghidra extraction:

* 1,269 retained raw Ghidra CSV outputs
* 31 compiled CWE-190 binaries without retained raw CSV outputs
* 106,110 raw decompiled function rows
* all retained raw rows had `decompile_status=success`
* 0 blank/whitespace `function_code` rows

Raw rows by CWE:

* CWE-121: 19,967
* CWE-122: 21,008
* CWE-134: 35,946
* CWE-190: 29,189

Cleaning:

* 106,110 raw rows → 6,073 cleaned rows
* 100,037 rows removed

Cleaning removals:

* Duplicate normalized body: 46,829
* halt_baddata: 22,140
* import/thunk functions: 15,795
* runtime/compiler boilerplate: 11,421
* too short functions: 3,852

Weak labeling:

* Clean: 2,068
* Buffer Overflow: 500
* Format String: 406
* Integer Overflow: 377
* Exclude: 2,722
* Uncertain: 0
* Suggested non-excluded candidates: 3,351

Sanity check / eligibility:

* Included before balancing: 2,945
* Excluded total: 3,128
* Failed visible-pattern checks: 406

Pre-balance distribution:

* Clean: 2,068
* Buffer Overflow: 352
* Integer Overflow: 265
* Format String: 260
* Total: 2,945

Final balanced dataset:

* Total: 1,040 rows
* Clean: 260
* Buffer Overflow: 260
* Format String: 260
* Integer Overflow: 260

Train/validation/test split:

* Train: 728 rows, 182 per class
* Validation: 156 rows, 39 per class
* Test: 156 rows, 39 per class

Baseline:

* TF-IDF + Logistic Regression
* Accuracy: 0.8397
* Macro-F1: 0.8279
* Weighted-F1: 0.8279

CodeBERT:

* `microsoft/codebert-base`
* Accuracy: 0.9936
* Macro-F1: 0.9936
* Weighted-F1: 0.9936

Model comparison:

* Absolute accuracy improvement: +0.1538
* Absolute macro-F1 improvement: +0.1656
* Relative accuracy improvement: +18.32%
* Relative macro-F1 improvement: +20.01%

Error analysis:

* Test size: 156
* Correct predictions: 155
* Misclassified samples: 1
* Sole error: Format String → Clean
* Misclassified function: `badVaSinkB`
* Confidence approximately 0.709721

Phase 11 demo:

* Demo binary: `data/demo/demo_buffer_overflow`
* 23 functions extracted
* 23 predictions made
* CPU inference on Linux
* Important issue: saved demo did not predict Buffer Overflow; it produced 20 Clean and 3 Integer Overflow predictions. Do not present this as successful buffer-overflow detection. Present it only as evidence that the end-to-end pipeline executes.

## 7. Completed phases

The following phases are completed:

* Phase 1 — Environment setup
* Phase 2 — Ghidra extraction pipeline
* Phase 3 — Merge and cleaning
* Phase 4 — Suggested label preparation
* Phase 5 — Final labeled dataset creation
* Phase 6 — Train/validation/test split
* Phase 7 — Baseline TF-IDF + Logistic Regression
* Phase 8 — CodeBERT fine-tuning
* Phase 9 — Model comparison
* Phase 10 — Error analysis
* Phase 11 — ELF inference/demo pipeline
* Web demo — React + NestJS interface

## 8. Current Experiment 0

Experiment 0 is the current verified baseline state.

Experiment 0 includes:

* original balanced dataset
* original stratified train/validation/test split
* baseline metrics
* CodeBERT metrics
* model comparison
* error analysis
* existing CodeBERT checkpoint
* existing Phase 11 demo artifacts

Important:
Experiment 0 must be preserved. Do not overwrite its datasets, splits, metrics, model checkpoint, or result files.

Do not overwrite:

* `data/processed/final_labeled_dataset.csv`
* `data/splits/train.csv`
* `data/splits/val.csv`
* `data/splits/test.csv`
* `results/baseline_metrics.json`
* `results/codebert_metrics.json`
* `results/model_comparison.json`
* `results/error_analysis.json`
* `results/codebert_test_predictions.csv`
* `results/codebert_misclassified_samples.csv`
* `models/codebert-final/`
* `results/phase11_demo/`

## 9. Remaining work

The following steps are not yet completed and should be done next. They are future work, not tasks to execute merely upon reading this file:

1. Fix precise inference filtering.
2. Add uncertainty handling.
3. Run leakage audit.
4. Create one group-aware split.
5. Retrain baseline + CodeBERT on the group-aware split.
6. Evaluate seven demo ELFs.
7. Compare stripped vs unstripped binaries.
8. Document limitations.

All new results must be saved separately, for example:

* `data/experiments/group_aware/`
* `results/experiment_group_aware/`
* `results/experiment_inference_filtering/`
* `results/demo_external_eval/`
* `results/stripped_vs_unstripped/`
* `models/codebert-group-aware/`

## 10. Immediate next priority

The immediate next priority is precise inference filtering.

Goal:
When a user uploads an ELF file, the system should distinguish actual application/demo functions from runtime/startup/import/PLT/thunk/compiler-generated functions.

Confirmed exclusions:

* runtime/startup functions
* imports
* PLT wrappers
* thunks
* failed decompilations
* empty decompilations

Handle carefully:

* short functions
* `FUN_*`
* ambiguous user code

Important:
Do not blindly exclude all `FUN_*` functions because stripped binaries may use `FUN_00101234` names for real user-written code.

Expected behavior:

* preserve all extracted functions
* add eligibility metadata
* mark excluded functions as “Not classified”
* do not include excluded functions in vulnerability class totals
* do not include excluded functions in top suspicious candidates
* keep excluded functions visible in full outputs for transparency

Suggested fields:

* `eligible`
* `classification_status`
* `exclusion_reason`
* `is_runtime_or_import`
* `is_application_function`
* `decompile_status`
* `predicted_label`
* `confidence`

## 11. Correct role separation

Ghidra/pipeline:

* validates ELF
* decompiles binary
* extracts pseudo-C functions
* filters eligibility
* preserves outputs

CodeBERT:

* performs final vulnerability class prediction

Rules/heuristics:

* may be used for eligibility filtering
* may be used as supporting signals/explanations
* must not override CodeBERT predictions
* must not fake detection results

Do not implement:

```text
if strcpy exists: prediction = Buffer Overflow
```

That would turn the project into a rule-based scanner and would be academically dishonest.

## 12. Uncertainty handling

Uncertainty handling is not yet completed.

Desired output:
Low-confidence or near-tied predictions should be shown as:

“Uncertain — manual review recommended”

Thresholds should be selected using validation data, not randomly.

Possible criteria:

* max probability threshold
* margin between top-1 and top-2 probabilities

Report:

* coverage
* accuracy on covered predictions
* number of uncertain predictions

Important:
Uncertainty should be an interpretation layer. It should not modify CodeBERT’s raw probabilities.

## 13. Leakage audit and group-aware split

The original split is stratified by class but not group-aware.

Leakage audit should check:

* binary overlap across splits
* Juliet testcase family overlap
* duplicate normalized function bodies
* near-duplicates
* `good`/`bad` identifiers
* CWE identifiers in names/paths
* class-specific naming artifacts

Group-aware split should:

* keep related Juliet testcase families in one partition
* be saved separately
* not overwrite original splits

Expected:
Group-aware metrics may be lower. This is acceptable and scientifically honest.

## 14. Seven demo ELFs

There are seven demo ELF files:

* three mixed demos
* three single-category demos
* `demo_buffer_overflow`

They should be evaluated as a small external/demo evaluation, not a large benchmark.

Report for each:

* extracted functions
* eligible functions
* excluded runtime/import functions
* predicted class distribution
* top suspicious candidates
* uncertain results
* expected class detected or not
* incorrect classifications

Do not cherry-pick only successful demos. Report failures honestly.

## 15. Stripped vs unstripped comparison

The stripped vs unstripped comparison is not yet completed and is important for assessing dependence on symbols and naming information.

Unstripped binaries:

* retain symbols and, when compiled with debug information, debug metadata
* may include informative function names
* easier for Ghidra/model

Stripped binaries:

* remove symbol/debug information according to the stripping options used
* often use `FUN_00101234` names
* are more realistic and harder

Compare the same examples in both forms.

## 16. Limitations to document

Document the following limitations:

* Juliet is synthetic and controlled.
* Labels are weak and sanity-checked, not perfect manual ground truth.
* Original split is stratified but not group-aware.
* Related Juliet testcase families may inflate original metrics.
* Model supports only four classes.
* Results do not prove exploitability.
* System is not production-ready.
* External demo performance may be weaker than original Juliet test results.
* 31 CWE-190 binaries have no retained raw extraction CSV outputs.
* Function filtering is imperfect, especially for stripped binaries and `FUN_*` functions.
* Performance on optimized, obfuscated, packed, or real-world binaries is not established.
* Some artifacts are local/untracked, so reproducibility from a fresh clone requires documenting data/model availability.
* Environment versions should be recorded.

## 17. Technical concepts

Buffer Overflow:
Occurs when a program writes more data into a buffer than it can hold.
Common patterns (supporting signals, not proof of a vulnerability):

* fixed-size local buffer
* `strcpy`
* `strcat`
* `sprintf`
* `gets`
* unchecked `memcpy`
* missing bounds check

Format String:
Occurs when user-controlled input is used as the format string in printf-like functions.
Bad:
`printf(param_1);`
Good:
`printf("%s", param_1);`

Integer Overflow:
Occurs when arithmetic exceeds the range of an integer type.
Dangerous when used for:

* malloc size
* buffer length
* memcpy length
* array indexing
* loop bounds

## 18. Thesis-safe wording

Use the following thesis-safe wording:

Dataset:
“The experimental dataset was constructed from a controlled subset of the NIST Juliet C/C++ Test Suite. The selected source files were compiled into ELF binaries, decompiled with Ghidra, processed into function-level pseudo-C representations, weak-labeled, sanity-checked, and balanced.”

Model:
“The fine-tuned CodeBERT model classifies Ghidra-decompiled pseudo-C functions into four classes: Clean, Buffer Overflow, Format String, and Integer Overflow.”

Results:
“On the saved class-stratified Juliet-derived test split, CodeBERT achieved 99.36% accuracy, outperforming the TF-IDF Logistic Regression baseline. Because the split was not group-aware by testcase family, this result should be interpreted within the controlled benchmark setting.”

Demo:
“The ELF demo demonstrates the end-to-end workflow from uploaded binary to Ghidra decompilation, function extraction, CodeBERT classification, and result visualization. It should not be interpreted as proof of exploitability.”

Limitations:
“The system classifies vulnerability candidates and is not a production-ready vulnerability scanner.”

## 19. Wording to avoid

Avoid:

* “The model detects all vulnerabilities.”
* “The model proves exploitability.”
* “This is production-ready.”
* “The labels are perfect ground truth.”
* “99.36% means it works perfectly on all binaries.”
* “The demo proves real-world vulnerability detection.”
* “The dataset was created fully from scratch.”
* “CodeBERT was developed from scratch.”
* “31 binaries failed in Ghidra” unless logs prove it.

## 20. Agent behavior rules

Future agents must follow these rules:

* Always preserve Experiment 0.
* Ask before destructive actions.
* Prefer read-only audits before code changes.
* Save new experiments in separate folders.
* Never overwrite current results unless explicitly instructed.
* Never fake predictions.
* Never use rules to override CodeBERT classification.
* Keep thesis wording academically safe.
* Help write Codex prompts when code changes are needed.
* Help prepare thesis chapters and defense explanations.
* Clearly separate verified facts from assumptions.
* Mark unverifiable claims as not verified.
* Keep the project bachelor-level in scope.

For future Codex prompts, explicitly reference this file:

> Before doing anything, read `docs/agents/thesis_agent.md` and follow its rules. Preserve Experiment 0 and save all new work in separate experiment folders.
