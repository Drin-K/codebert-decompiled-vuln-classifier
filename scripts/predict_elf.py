#!/usr/bin/env python3
"""Phase 11: classify Ghidra-decompiled functions from one Linux ELF binary.

The script only performs inference with the already fine-tuned CodeBERT model.
It does not train or alter any of the project datasets.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


REPO_ROOT = Path(__file__).resolve().parents[1]
GHIDRA_SCRIPT_DIR = REPO_ROOT / "ghidra_scripts"
GHIDRA_SCRIPT_NAME = "extract_functions.py"
GHIDRA_EXTRACTION_RUNNER = REPO_ROOT / "scripts" / "run_ghidra_extraction.py"
ID2LABEL = {
    0: "Clean",
    1: "Buffer Overflow",
    2: "Format String",
    3: "Integer Overflow",
}
RUNTIME_OR_LIBRARY_FUNCTIONS = {
    "_start", "_init", "_fini", "_dl_relocate_static_pie", "deregister_tm_clones",
    "register_tm_clones", "__do_global_dtors_aux", "frame_dummy", "__libc_start_main",
    "__cxa_finalize", "__stack_chk_fail", "__gmon_start__", "_global_offset_table_",
}


class Phase11Error(RuntimeError):
    """A clear, user-facing Phase 11 failure."""


def is_runtime_or_library_function(function_name: str) -> bool:
    """Exclude known non-user functions only from presentation-layer highlights."""
    name = function_name.strip().lower()
    return (
        name in RUNTIME_OR_LIBRARY_FUNCTIONS
        or name.startswith("__")
        or name.startswith("fun_")
        or name.startswith("thunk_")
        or name.startswith("plt_")
        or name.startswith("imp_")
        or name.endswith("@plt")
    )


def is_highlight_candidate(row: dict[str, Any]) -> bool:
    return row["predicted_label"] != 0 and not is_runtime_or_library_function(row["function_name"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decompile one Linux ELF binary with Ghidra and classify functions with CodeBERT."
    )
    parser.add_argument("--binary", required=True, help="Path to a compiled Linux ELF binary.")
    parser.add_argument("--ghidra-home", required=True, help="Path to the Ghidra installation.")
    parser.add_argument("--model-dir", required=True, help="Path to the saved CodeBERT model.")
    parser.add_argument("--output-dir", required=True, help="Directory for Phase 11 outputs.")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temporary Ghidra project directory.")
    parser.add_argument("--project-name", default="phase11_elf_demo", help="Temporary Ghidra project name.")
    parser.add_argument("--timeout", type=int, default=900, help="Ghidra timeout in seconds (default: 900).")
    parser.add_argument("--show-functions", action="store_true", help="Print every function prediction in a compact table.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top non-Clean candidates to display (default: 10).")
    parser.add_argument("--verbose", action="store_true", help="Show Ghidra/PyGhidra command output.")
    return parser.parse_args()


def resolve_repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def find_analyze_headless(ghidra_home: Path) -> Path:
    names = ("analyzeHeadless.bat", "analyzeHeadless") if sys.platform == "win32" else ("analyzeHeadless", "analyzeHeadless.sh")
    for name in names:
        candidate = ghidra_home / "support" / name
        if candidate.is_file():
            return candidate
    expected = ghidra_home / "support" / names[0]
    raise Phase11Error(f"Ghidra analyzeHeadless was not found: {expected}")


def validate_inputs(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    if args.max_length <= 0:
        raise Phase11Error("--max-length must be greater than zero.")
    if args.batch_size <= 0:
        raise Phase11Error("--batch-size must be greater than zero.")
    if args.timeout <= 0:
        raise Phase11Error("--timeout must be greater than zero.")
    if args.top_k <= 0:
        raise Phase11Error("--top-k must be greater than zero.")

    binary = resolve_repo_path(args.binary)
    ghidra_home = resolve_repo_path(args.ghidra_home)
    model_dir = resolve_repo_path(args.model_dir)
    output_dir = resolve_repo_path(args.output_dir)

    if not binary.is_file():
        raise Phase11Error(f"ELF binary was not found: {binary}")
    with binary.open("rb") as handle:
        elf_magic = handle.read(4)
    if elf_magic != b"\x7fELF":
        raise Phase11Error(f"Input is not a Linux ELF binary: {binary}")
    if not ghidra_home.is_dir():
        raise Phase11Error(f"Ghidra home directory was not found: {ghidra_home}")
    find_analyze_headless(ghidra_home)
    if not model_dir.is_dir():
        raise Phase11Error(f"Saved model directory was not found: {model_dir}")
    if not (model_dir / "config.json").is_file():
        raise Phase11Error(f"Model config.json was not found in: {model_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return binary, model_dir, output_dir, ghidra_home


def run_ghidra(
    ghidra_home: Path,
    binary: Path,
    output_dir: Path,
    project_name: str,
    timeout: int,
    verbose: bool,
) -> Path:
    script_path = GHIDRA_SCRIPT_DIR / GHIDRA_SCRIPT_NAME
    if not script_path.is_file():
        raise Phase11Error(f"Ghidra exporter script was not found: {script_path}")
    if not GHIDRA_EXTRACTION_RUNNER.is_file():
        raise Phase11Error(
            f"Ghidra extraction runner was not found: {GHIDRA_EXTRACTION_RUNNER}"
        )

    extracted_csv = output_dir / "extracted_functions.csv"
    project_dir = output_dir / "ghidra_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(GHIDRA_EXTRACTION_RUNNER),
        "--binary",
        str(binary),
        "--output",
        str(extracted_csv),
        "--ghidra-home",
        str(ghidra_home),
        "--project-dir",
        str(project_dir),
        "--project-name",
        project_name,
    ]
    if verbose:
        print("Ghidra/PyGhidra command:", file=sys.stderr)
        print(" ".join(command), file=sys.stderr)
    try:
        completed = subprocess.run(
            command,
            check=False,
            timeout=timeout,
            text=True,
            capture_output=not verbose,
        )
    except subprocess.TimeoutExpired as error:
        raise Phase11Error(f"Ghidra timed out after {timeout} seconds.") from error
    if completed.returncode != 0:
        details = ""
        if not verbose:
            output = "\n".join(
                part for part in (completed.stdout, completed.stderr) if part
            ).strip()
            if output:
                details = f"\nGhidra/PyGhidra output (last 20 lines):\n" + "\n".join(output.splitlines()[-20:])
        raise Phase11Error(
            f"Ghidra extraction failed with exit code {completed.returncode}. "
            "CodeBERT inference did not start. Check Ghidra's application log or rerun with --verbose."
            f"{details}"
        )
    if not extracted_csv.is_file() or extracted_csv.stat().st_size == 0:
        raise Phase11Error(
            "Ghidra completed, but decompilation/export did not create a non-empty "
            f"extracted_functions.csv at: {extracted_csv}. CodeBERT inference did not start. "
            "Check Ghidra's application log or rerun with --verbose."
        )
    return extracted_csv


def load_extracted_functions(extracted_csv: Path, binary: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with extracted_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"binary_name", "function_name", "function_address", "function_code", "decompile_status"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise Phase11Error("Ghidra output is missing required function-export columns.")
        records = []
        for row in reader:
            row["binary_path"] = str(binary)
            records.append(row)

    # Persist an enriched extraction file so it is useful independently of prediction output.
    fieldnames = ["binary_name", "binary_path", "function_name", "function_address", "function_code", "decompile_status"]
    with extracted_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    usable = [
        row for row in records
        if row.get("decompile_status") == "success" and row.get("function_code", "").strip()
    ]
    if not usable:
        raise Phase11Error("No successfully decompiled functions with pseudo-C code were extracted.")
    return records, usable


class FunctionDataset(Dataset[dict[str, str]]):
    def __init__(self, records: list[dict[str, str]]) -> None:
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, str]:
        return self.records[index]


def load_model(model_dir: Path, device: torch.device) -> tuple[Any, Any]:
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
    except Exception as error:
        raise Phase11Error(f"Could not load the CodeBERT model from: {model_dir}. {error}") from error
    model.to(device)
    model.eval()
    return tokenizer, model


def predict(
    records: list[dict[str, str]], tokenizer: Any, model: Any, device: torch.device,
    max_length: int, batch_size: int,
) -> list[dict[str, Any]]:

    def collate(batch: list[dict[str, str]]) -> dict[str, Any]:
        encodings = tokenizer(
            [row["function_code"] for row in batch],
            truncation=True, padding="max_length", max_length=max_length, return_tensors="pt",
        )
        encodings["rows"] = batch
        return encodings

    predictions: list[dict[str, Any]] = []
    loader = DataLoader(FunctionDataset(records), batch_size=batch_size, shuffle=False, collate_fn=collate)
    with torch.no_grad():
        for batch in loader:
            rows = batch.pop("rows")
            inputs = {key: value.to(device) for key, value in batch.items() if isinstance(value, torch.Tensor)}
            probabilities = torch.softmax(model(**inputs).logits, dim=-1).cpu().tolist()
            for row, scores in zip(rows, probabilities):
                label = int(max(range(len(scores)), key=scores.__getitem__))
                predictions.append({
                    "binary_name": row["binary_name"], "binary_path": row["binary_path"],
                    "function_name": row["function_name"], "function_address": row["function_address"],
                    "function_code": row["function_code"], "decompile_status": row["decompile_status"],
                    "predicted_label": label, "predicted_label_name": ID2LABEL[label],
                    "confidence": float(scores[label]),
                    "probabilities": {ID2LABEL[index]: float(score) for index, score in enumerate(scores)},
                })
    return predictions


def save_outputs(
    predictions: list[dict[str, Any]], extracted_count: int, binary: Path,
    model_dir: Path, output_dir: Path, device: torch.device,
) -> tuple[Path, Path, Path, Counter[str]]:
    csv_path = output_dir / "elf_predictions.csv"
    json_path = output_dir / "elf_predictions.json"
    markdown_path = output_dir / "summary.md"
    distribution: Counter[str] = Counter(row["predicted_label_name"] for row in predictions)

    csv_fields = ["binary_name", "binary_path", "function_name", "function_address", "predicted_label", "predicted_label_name", "confidence", "function_code", "decompile_status"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for row in predictions:
            writer.writerow({key: row[key] for key in csv_fields})

    metadata = {
        "phase": "Phase 11 ELF Prediction Demo", "binary": str(binary), "model_dir": str(model_dir),
        "device": str(device), "total_functions_extracted": extracted_count,
        "total_functions_predicted": len(predictions), "class_distribution": dict(distribution),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump({"metadata": metadata, "predictions": predictions}, handle, indent=2)
        handle.write("\n")

    suspicious = sorted((row for row in predictions if is_highlight_candidate(row)), key=lambda row: row["confidence"], reverse=True)[:10]
    lines = [
        "# Phase 11 ELF Prediction Demo", "", f"- Binary analyzed: `{binary}`", f"- Model path: `{model_dir}`",
        f"- Device used: `{device}`", f"- Total functions extracted: {extracted_count}",
        f"- Total functions predicted: {len(predictions)}", "", "## Class Distribution", "",
    ]
    lines.extend(f"- {label}: {distribution.get(label, 0)}" for label in ID2LABEL.values())
    lines.extend(["", "## Top Suspicious Functions", "", "| Function | Predicted class | Confidence |", "|---|---|---:|"])
    if suspicious:
        lines.extend(f"| {row['function_name']} | {row['predicted_label_name']} | {row['confidence']:.4f} |" for row in suspicious)
    else:
        lines.append("| No non-Clean user-code candidates | — | — |")
    lines.extend([
        "", "## Output Files", "", f"- `{csv_path}`", f"- `{json_path}`", f"- `{markdown_path}`",
        "", "## Limitation", "", "This model classifies vulnerability candidates in Ghidra-decompiled pseudo-C functions and does not prove real-world exploitability.", "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, json_path, markdown_path, distribution


def print_banner(args: argparse.Namespace, device: torch.device) -> None:
    print("=" * 60)
    print("Phase 11 — ELF Vulnerability Classification Demo")
    print("Fine-Tuned CodeBERT on Ghidra-Decompiled Functions")
    print("=" * 60)
    print(f"Binary: {args.binary}")
    print(f"Model: {args.model_dir}")
    print(f"Ghidra home: {args.ghidra_home}")
    print(f"Output directory: {args.output_dir}")
    print(f"Max length: {args.max_length} | Batch size: {args.batch_size} | Device: {device}")


def print_summary(
    predictions: list[dict[str, Any]], distribution: Counter[str], extracted_csv: Path,
    paths: tuple[Path, Path, Path], top_k: int, show_functions: bool,
) -> None:
    print("\nClassification summary:")
    for label in ID2LABEL.values():
        print(f"{label}: {distribution.get(label, 0)}")
    print("\nTop vulnerability candidates:")
    suspicious = sorted(
        (row for row in predictions if is_highlight_candidate(row)),
        key=lambda row: row["confidence"],
        reverse=True,
    )[:top_k]
    if suspicious:
        for index, row in enumerate(suspicious, start=1):
            print(
                f"{index}. {row['function_name']} | {row['predicted_label_name']} | "
                f"confidence: {row['confidence']:.2%} | address: {row['function_address']}"
            )
    else:
        print("No non-clean user-code vulnerability candidates were predicted.")
    if show_functions:
        print("\nAll function predictions:")
        print(f"{'Function name':<32} {'Address':<18} {'Prediction':<20} Confidence")
        print("-" * 90)
        for row in predictions:
            print(
                f"{row['function_name']:<32.32} {row['function_address']:<18.18} "
                f"{row['predicted_label_name']:<20.20} {row['confidence']:.2%}"
            )
    print("\nNote:")
    print("These predictions classify vulnerability candidates in Ghidra-decompiled pseudo-C functions.")
    print("They do not prove real-world exploitability.")
    print("\nSaved outputs:")
    print(f"Extracted functions: {extracted_csv}")
    print(f"Predictions CSV: {paths[0]}")
    print(f"Predictions JSON: {paths[1]}")
    print(f"Summary: {paths[2]}")


def main() -> int:
    args = parse_args()
    temporary_project: Path | None = None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print_banner(args, device)
    try:
        print("\n[1/6] Validating inputs...")
        binary, model_dir, output_dir, ghidra_home = validate_inputs(args)
        print("[OK] ELF binary found")
        print("[OK] Ghidra Headless / PyGhidra configuration found")
        print("[OK] CodeBERT model directory found")
        temporary_project = output_dir / "ghidra_project"
        print("\n[2/6] Running Ghidra decompilation...")
        print("[WORKING] Importing and analyzing ELF with Ghidra...")
        extracted_csv = run_ghidra(
            ghidra_home, binary, output_dir, args.project_name, args.timeout, args.verbose
        )
        print("[OK] Ghidra extraction completed")
        print("\n[3/6] Loading extracted pseudo-C functions...")
        extracted, usable = load_extracted_functions(extracted_csv, binary)
        print(f"[OK] Extracted {len(extracted)} functions; {len(usable)} have usable pseudo-C")
        print("\n[4/6] Loading fine-tuned CodeBERT model...")
        tokenizer, model = load_model(model_dir, device)
        print("[OK] Model loaded successfully")
        print(f"[INFO] Running on {device}")
        print("\n[5/6] Classifying functions...")
        print("[WORKING] Predicting vulnerability class per function...")
        predictions = predict(usable, tokenizer, model, device, args.max_length, args.batch_size)
        print(f"[OK] {len(predictions)} functions classified")
        print("\n[6/6] Writing reports...")
        csv_path, json_path, markdown_path, distribution = save_outputs(predictions, len(extracted), binary, model_dir, output_dir, device)
        print("[OK] CSV saved")
        print("[OK] JSON saved")
        print("[OK] Markdown summary saved")
        print_summary(
            predictions, distribution, extracted_csv, (csv_path, json_path, markdown_path),
            args.top_k, args.show_functions,
        )
        return 0
    except (Phase11Error, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary_project is not None and temporary_project.exists() and not args.keep_temp:
            shutil.rmtree(temporary_project, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
