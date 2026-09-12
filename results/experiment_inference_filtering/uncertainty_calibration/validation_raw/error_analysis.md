# Phase 10 — Error Analysis

## Goal

This phase evaluates the already fine-tuned CodeBERT model on the held-out test split and identifies misclassified decompiled functions. No training or fine-tuning is performed.

## Summary

- Total test samples: 156
- Correct predictions: 156
- Incorrect predictions: 0
- Recomputed test accuracy: 1.0000

## Per-Class Errors

| True Class | Error Count |
|---|---:|
| Clean | 0 |
| Buffer Overflow | 0 |
| Format String | 0 |
| Integer Overflow | 0 |

## Misclassification Pairs

| Pair | Count |
|---|---:|
| No misclassification pairs | 0 |

## Misclassified Samples

No errors were found on the test set.

## Interpretation

The CodeBERT model made very few mistakes on the held-out test split. This supports the Phase 9 comparison result, where the fine-tuned transformer model substantially outperformed the TF-IDF + Logistic Regression baseline on the same test set.

## Limitations

These errors and the low error count should still be interpreted carefully because Juliet is a synthetic benchmark dataset, the labels are weak/sanity-checked labels, generated test cases may share structural patterns, the split is not necessarily fully group-aware by testcase family, and the result is not proof of real-world exploitability or real-world exploit detection performance.
