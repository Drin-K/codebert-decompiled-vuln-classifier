# Phase 9 — Model Comparison

## Project Context

This project investigates automated vulnerability classification in Ghidra-decompiled pseudo-C functions extracted from Linux ELF binaries. The task is a four-class classification problem:

- 0 = Clean
- 1 = Buffer Overflow
- 2 = Format String
- 3 = Integer Overflow

The comparison below evaluates a classical TF-IDF + Logistic Regression baseline against a fine-tuned `microsoft/codebert-base` model using the saved Phase 7 and Phase 8 result files.

## Model Performance

| Model | Validation Accuracy | Validation Macro-F1 | Test Accuracy | Test Macro-F1 | Test Weighted-F1 |
|---|---:|---:|---:|---:|---:|
| TF-IDF + Logistic Regression | 0.8387 | 0.8260 | 0.7707 | 0.7531 | 0.7544 |
| microsoft/codebert-base | 0.9871 | 0.9870 | 1.0000 | 1.0000 | 1.0000 |

Dataset split sizes were consistent across both runs: 728 training samples, 155 validation samples, and 157 test samples.

## Improvements

| Metric | Absolute Improvement | Relative Improvement |
|---|---:|---:|
| Test Accuracy | 0.2293 | 29.75% |
| Test Macro-F1 | 0.2469 | 32.79% |
| Test Weighted-F1 | 0.2456 | Not computed |

## Metric Explanation

Accuracy measures the proportion of correctly classified test samples. Macro-F1 computes the unweighted mean F1-score across all vulnerability classes, making it useful for evaluating balanced class-level performance. Weighted-F1 computes the class F1-score average weighted by class support.

## Interpretation

The fine-tuned CodeBERT model substantially outperformed the TF-IDF + Logistic Regression baseline on the test set. The largest practical difference is visible in the test metrics, where CodeBERT achieved near-perfect accuracy and F1 scores while the baseline remained noticeably lower.

## Caution and Limitations

These results should be interpreted within the limitations of the Juliet benchmark dataset, weak/sanity-checked labels, and the possibility of shared structural patterns across generated test cases. The results should not be presented as proof of real-world exploit detection performance.
