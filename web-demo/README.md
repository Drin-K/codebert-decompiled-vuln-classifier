# Phase 11 Web Demo

This local academic demo is a UI around the existing Phase 11 pipeline. The backend never reimplements Ghidra extraction or CodeBERT inference: it invokes `scripts/predict_elf.py` with safe argument arrays.

## Run locally

In one terminal:

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

Open `http://localhost:5173`, then upload `data/demo/demo_buffer_overflow`.

## Backend configuration

All paths are resolved from the repository root unless absolute. Defaults are suitable for this repository:

| Variable | Default |
| --- | --- |
| `PYTHON_BIN` | `.venv/bin/python` |
| `GHIDRA_HOME` | `/opt/ghidra` |
| `MODEL_DIR` | `models/codebert-final` |
| `OUTPUT_ROOT` | `results/web_demo` |
| `SCRIPT_PATH` | `scripts/predict_elf.py` |
| `MAX_LENGTH` | `512` |
| `BATCH_SIZE` | `8` |
| `ANALYSIS_TIMEOUT_MS` | `900000` |

Uploads and generated web-demo runs remain local and are ignored by Git. The trained model is also intentionally local.
