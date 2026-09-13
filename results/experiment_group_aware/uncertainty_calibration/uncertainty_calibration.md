# Uncertainty Calibration

- Source: `/home/drin/codebert-decompiled-vuln-classifier/results/experiment_group_aware/uncertainty_calibration/validation_raw/codebert_test_predictions.csv`
- Calibration split: validation only
- Validation rows: 155
- Raw validation accuracy: 0.9871
- Minimum winning confidence: 0.6666
- Selected threshold: 0.70
- Selected coverage: 0.9806 (152/155)
- Accepted-decision accuracy: 1.0000

| Threshold | Accepted | Uncertain | Coverage | Accepted accuracy |
|---:|---:|---:|---:|---:|
| 0.40 | 155 | 0 | 1.0000 | 0.9871 |
| 0.50 | 155 | 0 | 1.0000 | 0.9871 |
| 0.60 | 155 | 0 | 1.0000 | 0.9871 |
| 0.70 | 152 | 3 | 0.9806 | 1.0000 |
| 0.75 | 148 | 7 | 0.9548 | 1.0000 |
| 0.80 | 144 | 11 | 0.9290 | 1.0000 |
| 0.85 | 136 | 19 | 0.8774 | 1.0000 |
| 0.90 | 124 | 31 | 0.8000 | 1.0000 |
| 0.95 | 73 | 82 | 0.4710 | 1.0000 |

## Interpretation

A 0.70 threshold is used as a high-coverage operating point: it retains 155 of 156 validation decisions while abstaining on the single validation prediction below 0.70.
Raw model outputs remain stored when the displayed decision is Uncertain — Human review recommended.

## Limitations

The original validation split achieved perfect accuracy and may contain Juliet-family similarity with training. This threshold is provisional and must be recalibrated using the future group-aware validation split.
