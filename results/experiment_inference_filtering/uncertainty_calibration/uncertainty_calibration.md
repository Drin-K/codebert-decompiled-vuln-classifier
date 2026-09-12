# Uncertainty Calibration

- Source: `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_inference_filtering/uncertainty_calibration/validation_raw/codebert_test_predictions.csv`
- Calibration split: validation only
- Validation rows: 156
- Raw validation accuracy: 1.0000
- Minimum winning confidence: 0.6576
- Selected threshold: 0.70
- Selected coverage: 0.9936 (155/156)
- Accepted-decision accuracy: 1.0000

| Threshold | Accepted | Uncertain | Coverage | Accepted accuracy |
|---:|---:|---:|---:|---:|
| 0.40 | 156 | 0 | 1.0000 | 1.0000 |
| 0.50 | 156 | 0 | 1.0000 | 1.0000 |
| 0.60 | 156 | 0 | 1.0000 | 1.0000 |
| 0.70 | 155 | 1 | 0.9936 | 1.0000 |
| 0.75 | 154 | 2 | 0.9872 | 1.0000 |
| 0.80 | 151 | 5 | 0.9679 | 1.0000 |
| 0.85 | 149 | 7 | 0.9551 | 1.0000 |
| 0.90 | 135 | 21 | 0.8654 | 1.0000 |
| 0.95 | 102 | 54 | 0.6538 | 1.0000 |

## Interpretation

A 0.70 threshold is used as a high-coverage operating point: it retains 155 of 156 validation decisions while abstaining on the single validation prediction below 0.70.
Raw model outputs remain stored even when the displayed decision is Uncertain.

## Limitations

The original validation split achieved perfect accuracy and may contain Juliet-family similarity with training. This threshold is provisional and must be recalibrated using the future group-aware validation split.
