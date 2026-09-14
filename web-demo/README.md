# Local ELF Vulnerability Classification Demo

This React/Vite and NestJS application is a local interface around the repository's ELF inference pipeline. The backend invokes `scripts/predict_elf.py`; it does not reimplement Ghidra extraction or CodeBERT inference.

## Prerequisites

- Python environment available at `.venv/`
- Ghidra installed, by default under `/opt/ghidra`
- Final model files under `models/codebert-group-aware/`
- Node.js 18 or newer

Inference requires `config.json`, `model.safetensors`, and the tokenizer assets. The local training export also retains `training_args.bin` for reproducibility, although the inference pipeline does not load it.

## Run Locally

In one terminal, from the repository root:

```bash
cd web-demo/backend
npm install
npm run start:dev
```

In another terminal:

```bash
cd web-demo/frontend
npm install
npm run dev
```

Open `http://localhost:5173`, then upload `data/web_demo_showcase/showcase_mixed` or another Linux ELF file.

## What the Demo Runs

```text
ELF upload
-> ELF magic validation
-> Ghidra/PyGhidra decompilation
-> conservative function filtering
-> CodeBERT classification
-> 0.70 confidence threshold
-> accepted or human-review decision
-> downloadable CSV, JSON, and Markdown reports
```

The frontend shows accepted class counts, uncertain-decision counts, top accepted non-Clean candidates, classified-function details, and decompiled pseudo-C. The full CSV and JSON also preserve excluded functions and their exclusion reasons.

## Backend Configuration

Relative paths are resolved from the repository root.

| Variable | Default |
|---|---|
| `PYTHON_BIN` | `.venv/bin/python` |
| `GHIDRA_HOME` | `/opt/ghidra` |
| `MODEL_DIR` | `models/codebert-group-aware` |
| `OUTPUT_ROOT` | `results/web_demo` |
| `SCRIPT_PATH` | `scripts/predict_elf.py` |
| `MAX_LENGTH` | `512` |
| `BATCH_SIZE` | `8` |
| `CONFIDENCE_THRESHOLD` | `0.70` |
| `ANALYSIS_TIMEOUT_MS` | `900000` |
| `HOST` | `127.0.0.1` |
| `PORT` | `3000` |
| `FRONTEND_ORIGIN` | `http://localhost:5173` |

Example override:

```bash
cd web-demo/backend
MODEL_DIR=models/codebert-group-aware GHIDRA_HOME=/opt/ghidra npm run start:dev
```

## Local Outputs

Each successful request receives a UUID and writes reports under:

```text
results/web_demo/<run-id>/
```

Uploaded files remain local under `web-demo/backend/uploads/`. Uploads and generated web runs are ignored by Git. Trained model weights are also intentionally local and must not be committed.

## Interpretation

The interface reports vulnerability candidates, not confirmed vulnerabilities. Scores below the configured threshold are marked **Uncertain — Human review recommended**. Supporting code signals are heuristic presentation aids; they do not alter CodeBERT predictions and are not explanations of the model's internal reasoning.
