# CodeBERT Vulnerability Classification for Decompiled ELF Functions

Bachelor's thesis project for classifying vulnerability candidates in Ghidra-decompiled pseudo-C functions extracted from Linux ELF binaries.

The system combines headless binary decompilation, conservative function filtering, a fine-tuned CodeBERT classifier, confidence-based abstention, structured reports, and a local web interface. It is an academic decision-support prototype: predictions identify functions for further review and do not prove exploitability.

## Classification Task

Each eligible decompiled function is assigned one of four raw classes:

| Label | Class |
|---:|---|
| 0 | Clean |
| 1 | Buffer Overflow |
| 2 | Format String |
| 3 | Integer Overflow |

Predictions below the `0.70` acceptance threshold are displayed as **Uncertain — Human review recommended**. The raw predicted class and all four softmax scores remain available in the saved output.

## Final System

```text
Uploaded Linux ELF
        |
        v
ELF validation
        |
        v
Ghidra headless / PyGhidra decompilation
        |
        v
Pseudo-C function extraction
        |
        v
Conservative eligibility filtering
        |
        v
Fine-tuned CodeBERT classification
        |
        v
0.70 confidence threshold
        |
        +--> Accepted class decision
        |
        +--> Uncertain — Human review recommended
        |
        v
CSV, JSON, Markdown, and web reporting
```

The inference filter excludes only failed or empty decompilations and confirmed runtime, startup, import, PLT, or thunk functions. Short functions, ambiguous wrappers, and `FUN_*` functions remain eligible because they may represent real application code in stripped binaries.

## Dataset and Training

The controlled dataset was derived from NIST Juliet C/C++ Test Suite cases for CWE-121, CWE-122, CWE-134, and CWE-190. Source cases were compiled into x86-64 Linux ELF binaries with GCC/G++, decompiled with Ghidra, cleaned, weak-labeled, sanity-checked, and balanced.

| Dataset stage | Functions |
|---|---:|
| Raw Ghidra function rows | 106,110 |
| Rows retained after cleaning | 6,073 |
| Candidates retained after labeling and sanity checks | 2,945 |
| Final balanced dataset | 1,040 |
| Functions per class | 260 |

The final group-aware split keeps each derived Juliet family and each binary in exactly one partition:

| Split | Rows | Derived families | Binaries |
|---|---:|---:|---:|
| Train | 728 | 43 | 585 |
| Validation | 155 | 11 | 129 |
| Test | 157 | 14 | 134 |

There is no binary or derived-family overlap across these partitions. See the [group-aware split summary](data/experiments/group_aware/split_summary.md) and [leakage audit](results/experiment_group_aware/grouped_split_audit/leakage_audit.md).

The final CodeBERT configuration uses `microsoft/codebert-base`, a maximum sequence length of 512 tokens, 3 epochs, learning rate `2e-5`, batch size 8, weight decay `0.01`, and seed 42.

## Verified Results

### Internal group-aware evaluation

Both models below use the same group-aware partitions.

| Model | Validation accuracy | Validation macro-F1 | Test accuracy | Test macro-F1 | Test weighted-F1 |
|---|---:|---:|---:|---:|---:|
| TF-IDF + Logistic Regression | 83.87% | 82.60% | 77.07% | 75.31% | 75.44% |
| Fine-tuned CodeBERT | 98.71% | 98.70% | 100.00% | 100.00% | 100.00% |

CodeBERT classified all `157/157` internal test functions correctly. This is a controlled Juliet-derived result, not an estimate of performance on arbitrary real-world binaries. The full comparison is available in the [model comparison report](results/experiment_group_aware/model_comparison.md).

### External seven-ELF evaluation

Seven separately written, unstripped demo programs were used as a small end-to-end generalization check:

| Measure | Result |
|---|---:|
| ELF files completed | 7/7 |
| Functions extracted | 184 |
| Eligible application functions | 34 |
| Raw exact-class accuracy | 22/34 (64.71%) |
| Accepted decisions at threshold 0.70 | 9/34 (26.47% coverage) |
| Correct accepted decisions | 8/9 (88.89%) |
| Human review recommended | 25/34 (73.53%) |

These results show a training-to-demo domain gap, particularly for Buffer Overflow and Integer Overflow. See the [external evaluation report](results/experiment_group_aware/demo_evaluation/evaluation_report.md).

### Stripped binaries

All 34 intended application functions remained eligible after stripping, but application accuracy fell to `14/34` (`41.18%`). A runtime-name filter correction removed confirmed startup-code false positives without changing application predictions. This demonstrates both symbol sensitivity and the importance of separating filtering quality from model accuracy. See the [stripped comparison](results/experiment_group_aware/stripped_comparison/comparison_report.md) and [runtime-filter correction](results/experiment_group_aware/stripped_comparison/runtime_filter_fix_report.md).

### Curated web showcase

Five pattern-aligned showcase ELF files are included under `data/web_demo_showcase/`. Across these controlled examples, all `25/25` expected eligible functions received the expected class and passed the confidence threshold. These files demonstrate the interface in a best-case setting; they are not an independent accuracy benchmark. See the [showcase guide](data/web_demo_showcase/README.md) and [verification report](results/experiment_group_aware/web_demo_showcase_final/showcase_report.md).

## Repository Layout

```text
data/
  experiments/group_aware/       Final train, validation, and test splits
  demo_src/                       Source for the seven external demo programs
  demo_stripped/                  Stripped comparison binaries
  web_demo_showcase/              Curated ELF files for the live demo
  web_demo_showcase_src/          Source for the curated showcase
docs/                              Dataset and pipeline documentation
ghidra_scripts/                    Ghidra pseudo-C extraction script
models/                            Local model directories; weights are not committed
results/experiment_group_aware/   Saved metrics and verified evaluation reports
scripts/                           Dataset, training, evaluation, and inference tools
tests/                             Inference-filtering regression tests
web-demo/backend/                  NestJS API
web-demo/frontend/                 React/Vite interface
```

Large model weights, raw datasets, uploaded binaries, and generated web runs are intentionally excluded from Git.

## Requirements

- Linux (the final pipeline was verified on Linux)
- Python 3.10 or newer
- Java required by Ghidra
- Ghidra with headless analysis support; the final pipeline was verified with Ghidra 12.1.2
- Node.js 18 or newer for the web demo
- NVIDIA CUDA GPU recommended for training; inference can run on CPU

## Python Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/verify_environment.py
```

Install Ghidra separately and make sure its headless launcher is available. The commands below assume:

```text
/opt/ghidra/support/analyzeHeadless
```

See [environment setup](docs/phase1_environment_setup.md) and [Ghidra extraction](docs/phase2_ghidra_extraction.md) for additional details.

## Final Model Files

The trained weights are intentionally not stored in Git. Before running inference, place the final model in:

```text
models/codebert-group-aware/
```

The local export used by this project contains:

```text
config.json
model.safetensors
tokenizer.json
tokenizer_config.json
training_args.bin
```

`config.json`, the model weights, and tokenizer assets are required for inference. `training_args.bin` is retained for training reproducibility but is not loaded by the inference pipeline.

## Run One ELF from the Terminal

The mixed showcase binary contains accepted examples from all four classes:

```bash
source .venv/bin/activate

python scripts/predict_elf.py \
  --binary data/web_demo_showcase/showcase_mixed \
  --ghidra-home /opt/ghidra \
  --model-dir models/codebert-group-aware \
  --output-dir /tmp/codebert-showcase-run \
  --max-length 512 \
  --batch-size 8 \
  --confidence-threshold 0.70
```

The output directory contains:

```text
extracted_functions.csv
elf_predictions.csv
elf_predictions.json
summary.md
```

The CSV and JSON preserve both classified and excluded functions, including exclusion reasons. The temporary Ghidra project is deleted unless `--keep-temp` is supplied.

## Run the Web Demo

Start the backend from the repository root in one terminal:

```bash
cd web-demo/backend
npm install
npm run start:dev
```

Start the frontend in a second terminal:

```bash
cd web-demo/frontend
npm install
npm run dev
```

Open `http://localhost:5173` and upload an ELF such as:

```text
data/web_demo_showcase/showcase_mixed
```

The backend defaults to `models/codebert-group-aware/`. It creates one UUID-named result directory per analysis under `results/web_demo/`. See the [web demo documentation](web-demo/README.md) for configuration options.

## Optional: Reproduce Group-Aware Training

Training is not required to run the supplied pipeline when the final model files are already present. To reproduce training, use separate output directories so an existing model is not overwritten:

```bash
source .venv/bin/activate

python scripts/train_baseline.py \
  --train data/experiments/group_aware/train.csv \
  --val data/experiments/group_aware/val.csv \
  --test data/experiments/group_aware/test.csv \
  --output-dir results/reproduction_group_aware \
  --model-output results/reproduction_group_aware/baseline_tfidf_logreg.joblib

python scripts/train_codebert.py \
  --train data/experiments/group_aware/train.csv \
  --val data/experiments/group_aware/val.csv \
  --test data/experiments/group_aware/test.csv \
  --output-dir results/reproduction_group_aware \
  --model-output-dir models/codebert-group-aware-reproduction \
  --max-length 512 \
  --epochs 3 \
  --train-batch-size 8 \
  --eval-batch-size 8 \
  --learning-rate 2e-5 \
  --weight-decay 0.01 \
  --seed 42
```

## Tests

Run the conservative-filter regression tests from the repository root:

```bash
.venv/bin/python tests/test_inference_filtering.py
```

Build the frontend:

```bash
cd web-demo/frontend
npm install
npm run build
```

## Limitations

- The training data is synthetic, controlled, and Juliet-derived.
- Labels are weak/sanity-checked rather than expert-verified ground truth for every function.
- Juliet identifiers and recurring structures may enable shortcut learning despite group-aware splitting.
- Decompiled pseudo-C changes with compiler settings, optimization, symbols, and Ghidra analysis.
- The model classifies individual functions and does not perform complete interprocedural data-flow analysis.
- The external evaluation is small and is not statistically representative of production software.
- A high softmax score does not guarantee a correct or exploitable finding.

The system is intended for academic research, triage, and human review—not autonomous security decisions.

## Thesis Scope

This repository demonstrates a reproducible bachelor-level research pipeline spanning dataset preparation, ELF compilation, decompilation, function filtering, baseline comparison, CodeBERT fine-tuning, uncertainty handling, external evaluation, stripped-binary analysis, and web-based reporting.
