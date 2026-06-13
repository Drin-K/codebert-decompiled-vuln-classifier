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
| TF-IDF + Logistic Regression | 0.8654 | 0.8522 | 0.8397 | 0.8279 | 0.8279 |
| microsoft/codebert-base | 1.0000 | 1.0000 | 0.9936 | 0.9936 | 0.9936 |

Dataset split sizes were consistent across both runs: 728 training samples, 156 validation samples, and 156 test samples.

## Improvements

| Metric | Absolute Improvement | Relative Improvement |
|---|---:|---:|
| Test Accuracy | 0.1538 | 18.32% |
| Test Macro-F1 | 0.1656 | 20.01% |
| Test Weighted-F1 | 0.1656 | Not computed |

## Metric Explanation

Accuracy measures the proportion of correctly classified test samples. Macro-F1 computes the unweighted mean F1-score across all vulnerability classes, making it useful for evaluating balanced class-level performance. Weighted-F1 computes the class F1-score average weighted by class support.

## Interpretation

The fine-tuned CodeBERT model substantially outperformed the TF-IDF + Logistic Regression baseline on the test set. The largest practical difference is visible in the test metrics, where CodeBERT achieved near-perfect accuracy and F1 scores while the baseline remained noticeably lower.

## Caution and Limitations

These results should be interpreted within the limitations of the Juliet benchmark dataset, weak/sanity-checked labels, and the possibility of shared structural patterns across generated test cases. The results should not be presented as proof of real-world exploit detection performance.
