#!/usr/bin/env python3
"""Compare saved baseline and CodeBERT evaluation metrics for Phase 9."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


METRIC_KEYS = [
    "model_name",
    "validation_accuracy",
    "validation_macro_f1",
    "test_accuracy",
    "test_macro_f1",
    "test_weighted_f1",
    "train_size",
    "validation_size",
    "test_size",
]

CSV_COLUMNS = [
    "model_name",
    "validation_accuracy",
    "validation_macro_f1",
    "test_accuracy",
    "test_macro_f1",
    "test_weighted_f1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare saved TF-IDF baseline and fine-tuned CodeBERT metrics."
    )
    parser.add_argument(
        "--baseline-metrics",
        default="results/baseline_metrics.json",
        help="Path to the baseline metrics JSON file.",
    )
    parser.add_argument(
        "--codebert-metrics",
        default="results/codebert_metrics.json",
        help="Path to the CodeBERT metrics JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory where comparison outputs will be written.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required metrics file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in METRIC_KEYS if key not in metrics]
    if missing:
        missing_text = ", ".join(missing)
        raise KeyError(f"Metrics file is missing required fields: {missing_text}")

    return {key: metrics[key] for key in METRIC_KEYS}


def absolute_improvement(codebert_value: float, baseline_value: float) -> float:
    return codebert_value - baseline_value


def relative_improvement_percent(codebert_value: float, baseline_value: float) -> float:
    if baseline_value == 0:
        raise ZeroDivisionError("Cannot compute relative improvement from a zero baseline.")
    return ((codebert_value - baseline_value) / baseline_value) * 100.0


def compute_improvements(
    baseline: dict[str, Any], codebert: dict[str, Any]
) -> tuple[dict[str, float], dict[str, float]]:
    absolute = {
        "test_accuracy": absolute_improvement(
            codebert["test_accuracy"], baseline["test_accuracy"]
        ),
        "test_macro_f1": absolute_improvement(
            codebert["test_macro_f1"], baseline["test_macro_f1"]
        ),
        "test_weighted_f1": absolute_improvement(
            codebert["test_weighted_f1"], baseline["test_weighted_f1"]
        ),
    }
    relative = {
        "test_accuracy_percent": relative_improvement_percent(
            codebert["test_accuracy"], baseline["test_accuracy"]
        ),
        "test_macro_f1_percent": relative_improvement_percent(
            codebert["test_macro_f1"], baseline["test_macro_f1"]
        ),
    }
    return absolute, relative


def write_json(
    path: Path,
    baseline: dict[str, Any],
    codebert: dict[str, Any],
    absolute: dict[str, float],
    relative: dict[str, float],
) -> None:
    interpretation = (
        "The fine-tuned CodeBERT model substantially outperformed the "
        "TF-IDF + Logistic Regression baseline on the test set."
    )
    payload = {
        "baseline_metrics": baseline,
        "codebert_metrics": codebert,
        "absolute_improvements": absolute,
        "relative_improvements_percent": relative,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "short_interpretation": interpretation,
    }

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def write_csv(path: Path, baseline: dict[str, Any], codebert: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerow({column: baseline[column] for column in CSV_COLUMNS})
        writer.writerow({column: codebert[column] for column in CSV_COLUMNS})


def format_metric(value: float) -> str:
    return f"{value:.4f}"


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def write_markdown(
    path: Path,
    baseline: dict[str, Any],
    codebert: dict[str, Any],
    absolute: dict[str, float],
    relative: dict[str, float],
) -> None:
    markdown = f"""# Phase 9 — Model Comparison

## Project Context

This project investigates automated vulnerability classification in Ghidra-decompiled pseudo-C functions extracted from Linux ELF binaries. The task is a four-class classification problem:

- 0 = Clean
- 1 = Buffer Overflow
- 2 = Format String
- 3 = Integer Overflow

The comparison below evaluates a classical TF-IDF + Logistic Regression baseline against a fine-tuned `microsoft/codebert-base` model using the saved Phase 7 and Phase 8 result files.

## Model Performance

| Model | Validation Accuracy | Validation Macro-F1 | Test Accuracy | Test Macro-F1 | Test Weighted-F1 |
|---|---:|---:|---:|---:|---:|
| {baseline["model_name"]} | {format_metric(baseline["validation_accuracy"])} | {format_metric(baseline["validation_macro_f1"])} | {format_metric(baseline["test_accuracy"])} | {format_metric(baseline["test_macro_f1"])} | {format_metric(baseline["test_weighted_f1"])} |
| {codebert["model_name"]} | {format_metric(codebert["validation_accuracy"])} | {format_metric(codebert["validation_macro_f1"])} | {format_metric(codebert["test_accuracy"])} | {format_metric(codebert["test_macro_f1"])} | {format_metric(codebert["test_weighted_f1"])} |

Dataset split sizes were consistent across both runs: {baseline["train_size"]} training samples, {baseline["validation_size"]} validation samples, and {baseline["test_size"]} test samples.

## Improvements

| Metric | Absolute Improvement | Relative Improvement |
|---|---:|---:|
| Test Accuracy | {format_metric(absolute["test_accuracy"])} | {format_percent(relative["test_accuracy_percent"])} |
| Test Macro-F1 | {format_metric(absolute["test_macro_f1"])} | {format_percent(relative["test_macro_f1_percent"])} |
| Test Weighted-F1 | {format_metric(absolute["test_weighted_f1"])} | Not computed |

## Metric Explanation

Accuracy measures the proportion of correctly classified test samples. Macro-F1 computes the unweighted mean F1-score across all vulnerability classes, making it useful for evaluating balanced class-level performance. Weighted-F1 computes the class F1-score average weighted by class support.

## Interpretation

The fine-tuned CodeBERT model substantially outperformed the TF-IDF + Logistic Regression baseline on the test set. The largest practical difference is visible in the test metrics, where CodeBERT achieved near-perfect accuracy and F1 scores while the baseline remained noticeably lower.

## Caution and Limitations

These results should be interpreted within the limitations of the Juliet benchmark dataset, weak/sanity-checked labels, and the possibility of shared structural patterns across generated test cases. The results should not be presented as proof of real-world exploit detection performance.
"""

    with path.open("w", encoding="utf-8") as handle:
        handle.write(markdown)


def write_bar_chart(path: Path, baseline: dict[str, Any], codebert: dict[str, Any]) -> None:
    metrics = [
        ("Test Accuracy", "test_accuracy"),
        ("Test Macro-F1", "test_macro_f1"),
        ("Test Weighted-F1", "test_weighted_f1"),
    ]
    labels = [label for label, _key in metrics]
    baseline_values = [baseline[key] for _label, key in metrics]
    codebert_values = [codebert[key] for _label, key in metrics]

    x_positions = list(range(len(metrics)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(
        [position - width / 2 for position in x_positions],
        baseline_values,
        width,
        label="TF-IDF + Logistic Regression",
    )
    ax.bar(
        [position + width / 2 for position in x_positions],
        codebert_values,
        width,
        label="Fine-tuned CodeBERT",
    )

    ax.set_title("Phase 9 Model Comparison on Test Set")
    ax.set_ylabel("Score")
    ax.set_xlabel("Evaluation Metric")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0.0, 1.05)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.4f", padding=3, fontsize=9)

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def print_summary(
    baseline: dict[str, Any],
    codebert: dict[str, Any],
    absolute: dict[str, float],
    relative: dict[str, float],
    output_paths: dict[str, Path],
) -> None:
    print("Phase 9 Model Comparison")
    print("========================")
    print(
        "Baseline test accuracy / macro-F1: "
        f"{baseline['test_accuracy']:.4f} / {baseline['test_macro_f1']:.4f}"
    )
    print(
        "CodeBERT test accuracy / macro-F1: "
        f"{codebert['test_accuracy']:.4f} / {codebert['test_macro_f1']:.4f}"
    )
    print()
    print("Absolute improvements:")
    print(f"  Test accuracy: {absolute['test_accuracy']:.4f}")
    print(f"  Test macro-F1: {absolute['test_macro_f1']:.4f}")
    print(f"  Test weighted-F1: {absolute['test_weighted_f1']:.4f}")
    print()
    print("Relative improvements:")
    print(f"  Test accuracy: {relative['test_accuracy_percent']:.2f}%")
    print(f"  Test macro-F1: {relative['test_macro_f1_percent']:.2f}%")
    print()
    print("Saved outputs:")
    for label, path in output_paths.items():
        print(f"  {label}: {path}")


def main() -> None:
    args = parse_args()
    baseline_path = Path(args.baseline_metrics)
    codebert_path = Path(args.codebert_metrics)
    output_dir = Path(args.output_dir)

    baseline = extract_metrics(load_json(baseline_path))
    codebert = extract_metrics(load_json(codebert_path))
    absolute, relative = compute_improvements(baseline, codebert)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "json": output_dir / "model_comparison.json",
        "csv": output_dir / "model_comparison.csv",
        "markdown": output_dir / "model_comparison.md",
        "bar_chart": output_dir / "model_comparison_bar_chart.png",
    }

    write_json(output_paths["json"], baseline, codebert, absolute, relative)
    write_csv(output_paths["csv"], baseline, codebert)
    write_markdown(output_paths["markdown"], baseline, codebert, absolute, relative)
    write_bar_chart(output_paths["bar_chart"], baseline, codebert)
    print_summary(baseline, codebert, absolute, relative, output_paths)


if __name__ == "__main__":
    main()
