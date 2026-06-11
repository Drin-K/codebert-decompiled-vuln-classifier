# Split Summary

Input dataset: `/home/drin/codebert-decompiled-vuln-classifier/data/processed/final_labeled_dataset.csv`

## Output Paths

- train: `/home/drin/codebert-decompiled-vuln-classifier/data/splits/train.csv`
- validation: `/home/drin/codebert-decompiled-vuln-classifier/data/splits/val.csv`
- test: `/home/drin/codebert-decompiled-vuln-classifier/data/splits/test.csv`

## Configuration

- Train size: 0.70
- Validation size: 0.15
- Test size: 0.15
- Random seed: 42
- Stratify column: `final_label`

Total rows: 1040

## Split Distributions

### Train

- Rows: 728 (70.00% of dataset)
- Class distribution:
- 0: 182 (25.00%)
- 1: 182 (25.00%)
- 2: 182 (25.00%)
- 3: 182 (25.00%)

### Validation

- Rows: 156 (15.00% of dataset)
- Class distribution:
- 0: 39 (25.00%)
- 1: 39 (25.00%)
- 2: 39 (25.00%)
- 3: 39 (25.00%)

### Test

- Rows: 156 (15.00% of dataset)
- Class distribution:
- 0: 39 (25.00%)
- 1: 39 (25.00%)
- 2: 39 (25.00%)
- 3: 39 (25.00%)

## Notes

- This is a stratified split, so class proportions are preserved across train, validation, and test files.
- Limitation: this split is stratified by class, but not fully group-aware by binary or testcase family unless implemented later.
