# Phase 10 — Error Analysis

## Goal

This phase evaluates the already fine-tuned CodeBERT model on the held-out test split and identifies misclassified decompiled functions. No training or fine-tuning is performed.

## Summary

- Total test samples: 156
- Correct predictions: 155
- Incorrect predictions: 1
- Recomputed test accuracy: 0.9936

## Per-Class Errors

| True Class | Error Count |
|---|---:|
| Clean | 0 |
| Buffer Overflow | 0 |
| Format String | 1 |
| Integer Overflow | 0 |

## Misclassification Pairs

| Pair | Count |
|---|---:|
| Format String -> Clean | 1 |

## Misclassified Samples

### Error 1
- Binary Name: juliet_CWE134_CWE134_Uncontrolled_Format_String__char_connect_socket_vprintf_02
- Function Name: badVaSinkB
- Function Address: 00101389
- Final Class: Format String
- True class: Format String
- Predicted class: Clean
- Confidence: 0.7097

Code excerpt:

```c
void badVaSinkB(char *data,...)

{
  long lVar1;
  char in_AL;
  undefined8 in_RCX;
  undefined8 in_RDX;
  undefined8 in_RSI;
  undefined8 in_R8;
  undefined8 in_R9;
  long in_FS_OFFSET;
  undefined8 in_XMM0_Qa;
  undefined8 in_XMM1_Qa;
  undefined8 in_XMM2_Qa;
  undefined8 in_XMM3_Qa;
  undefined8 in_XMM4_Qa;
  undefined8 in_XMM5_Qa;
  undefined8 in_XMM6_Qa;
  undefined8 in_XMM7_Qa;
  char *data_local;
  va_list args;
  undefined1 local_b8 [8];
  undefined8 local_b0;
  undefined8 local_a8;
  undefined8 local_a0;
  undefined8 local_98;
  undefined8 local_90;
  undefi
...
```

## Interpretation

The CodeBERT model made very few mistakes on the held-out test split. This supports the Phase 9 comparison result, where the fine-tuned transformer model substantially outperformed the TF-IDF + Logistic Regression baseline on the same test set.

## Limitations

These errors and the low error count should still be interpreted carefully because Juliet is a synthetic benchmark dataset, the labels are weak/sanity-checked labels, generated test cases may share structural patterns, the split is not necessarily fully group-aware by testcase family, and the result is not proof of real-world exploitability or real-world exploit detection performance.
