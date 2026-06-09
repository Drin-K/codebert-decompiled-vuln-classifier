# Phase 1 Environment Setup

This document prepares the local environment for the thesis pipeline. Phase 1 does not train CodeBERT and does not implement the full Ghidra extraction pipeline yet. The goal is to make sure the repository, Python environment, Ghidra installation, and future Colab training environment are ready.

## A. System Requirements

- Ubuntu/Linux recommended
- Python 3.10 or newer
- Java JDK for running Ghidra
- Ghidra 11.x
- Google Colab for GPU training in later phases

## B. Java/JDK Installation

Install a Java Development Kit:

```bash
sudo apt update
sudo apt install default-jdk
```

Verify the installation:

```bash
java -version
javac -version
```

Both commands should print version information. If either command is missing, Ghidra may not start correctly.

## C. Ghidra Installation

Download Ghidra from the official NSA GitHub release page:

```text
https://github.com/NationalSecurityAgency/ghidra/releases
```

Download the release ZIP for Ghidra 11.x. Do not download the source-code ZIP, because it does not contain the ready-to-run Ghidra distribution.

Extract the release ZIP. A common installation location is:

```text
/opt/ghidra
```

Depending on where you extract Ghidra, the exact path may include the version number first. You can either keep that versioned directory or rename it to `/opt/ghidra` for simpler commands.

## D. Ghidra GUI Test

Start the Ghidra graphical interface:

```bash
/opt/ghidra/ghidraRun
```

If the GUI opens, Java and the Ghidra installation are working.

## E. Ghidra Headless Test

Check that Ghidra headless mode is available:

```bash
/opt/ghidra/support/analyzeHeadless
```

Seeing usage/help output means the headless analyzer is accessible. This is the command that will later be used for scripted decompilation and pseudo-C function extraction.

## F. Python Virtual Environment Setup

From the repository root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## G. Verify Python Dependencies

Run the repository verification script:

```bash
python scripts/verify_environment.py
```

The script checks imports for:

- `pandas`
- `sklearn`
- `torch`
- `transformers`
- `datasets`

It also prints the Python version and reports whether CUDA is available through PyTorch. CUDA is not required on the local machine for Phase 1.

## H. Google Colab GPU Verification

Training will later be done in Google Colab with GPU support. In a Colab notebook, enable a GPU runtime and run:

```python
import torch

print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU")
```

If this prints `True` and a GPU name, Colab is ready for later CodeBERT fine-tuning.

## I. Phase 1 Success Criteria

At the end of Phase 1, you should be able to:

- Clone the repository
- Create and activate the Python virtual environment
- Install dependencies from `requirements.txt`
- Start the Ghidra GUI
- Run the `analyzeHeadless` help command
- Verify Python dependencies with `scripts/verify_environment.py`
- Verify GPU availability in Google Colab
