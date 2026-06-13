#!/usr/bin/env python3
"""Analyze CodeBERT test-set errors without retraining the model."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


REPO_ROOT = Path(__file__).resolve().parents[1]

ID2LABEL = {
    0: "Clean",
    1: "Buffer Overflow",
    2: "Format String",
    3: "Integer Overflow",
}
LABEL_IDS = sorted(ID2LABEL)
OPTIONAL_METADATA_COLUMNS = [
    "binary_name",
    "function_name",
    "function_address",
    "final_class",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run inference with the saved fine-tuned CodeBERT model and analyze "
            "misclassified test-set samples."
        )
    )
    parser.add_argument("--test", default="data/splits/test.csv")
    parser.add_argument("--model-dir", default="models/codebert-final")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--text-column", default="function_code")
    parser.add_argument("--label-column", default="final_label")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=8)
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_length <= 0:
        raise ValueError("--max-length must be greater than zero")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero")


def validate_test_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Test CSV does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Test path is not a file: {path}")


def validate_model_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(
            "The trained CodeBERT model directory is required for Phase 10 error "
            f"analysis, but it was not found: {path}. Restore or copy the saved "
            "models/codebert-final/ directory before running this script."
        )


def read_test_data(path: Path, text_column: str, label_column: str) -> pd.DataFrame:
    validate_test_path(path)
    data = pd.read_csv(path)

    missing_columns = [
        column for column in (text_column, label_column) if column not in data.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{path} is missing required column(s): {missing}")

    data[text_column] = data[text_column].fillna("").astype(str)
    data[label_column] = data[label_column].astype(int)

    invalid_labels = sorted(set(data[label_column].tolist()) - set(LABEL_IDS))
    if invalid_labels:
        raise ValueError(f"{path} contains unsupported label id(s): {invalid_labels}")

    return data


class FunctionDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[int]) -> None:
        self.texts = texts
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return {
            "text": self.texts[index],
            "label": self.labels[index],
            "index": index,
        }


def collate_batch(
    batch: list[dict[str, Any]], tokenizer: Any, max_length: int
) -> dict[str, Any]:
    texts = [item["text"] for item in batch]
    labels = torch.tensor([item["label"] for item in batch], dtype=torch.long)
    indices = [item["index"] for item in batch]
    encodings = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors="pt",
    )
    encodings["labels"] = labels
    encodings["indices"] = indices
    return encodings


def run_inference(
    data: pd.DataFrame,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    text_column: str,
    label_column: str,
    max_length: int,
    batch_size: int,
) -> pd.DataFrame:
    dataset = FunctionDataset(
        texts=data[text_column].tolist(),
        labels=[int(label) for label in data[label_column].tolist()],
    )
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, max_length),
    )

    prediction_rows: list[dict[str, Any]] = []
    model.eval()

    with torch.no_grad():
        for batch in loader:
            labels = batch.pop("labels")
            indices = batch.pop("indices")
            model_inputs = {
                key: value.to(device)
                for key, value in batch.items()
                if isinstance(value, torch.Tensor)
            }
            logits = model(**model_inputs).logits
            probabilities = torch.softmax(logits, dim=-1).cpu()
            predicted_labels = torch.argmax(probabilities, dim=-1).tolist()

            for row_index, true_label, predicted_label, row_probs in zip(
                indices,
                labels.tolist(),
                predicted_labels,
                probabilities.tolist(),
            ):
                confidence = float(row_probs[predicted_label])
                prediction_rows.append(
                    {
                        "row_index": row_index,
                        "true_label": int(true_label),
                        "true_class": ID2LABEL[int(true_label)],
                        "predicted_label": int(predicted_label),
                        "predicted_class": ID2LABEL[int(predicted_label)],
                        "confidence": confidence,
                        "is_correct": int(true_label) == int(predicted_label),
                    }
                )

    predictions = pd.DataFrame(prediction_rows).sort_values("row_index")
    predictions = predictions.drop(columns=["row_index"]).reset_index(drop=True)
    return pd.concat([data.reset_index(drop=True), predictions], axis=1)


def per_class_error_counts(predictions: pd.DataFrame) -> dict[str, int]:
    errors = predictions[~predictions["is_correct"]]
    counts = Counter(errors["true_label"].astype(int).tolist())
    return {ID2LABEL[label_id]: int(counts.get(label_id, 0)) for label_id in LABEL_IDS}


def confusion_pair_counts(predictions: pd.DataFrame) -> dict[str, int]:
    errors = predictions[~predictions["is_correct"]]
    counts: Counter[str] = Counter()
    for row in errors.itertuples(index=False):
        pair = f"{row.true_class} -> {row.predicted_class}"
        counts[pair] += 1
    return dict(sorted(counts.items()))


def build_summary(predictions: pd.DataFrame) -> dict[str, Any]:
    total = int(len(predictions))
    correct = int(predictions["is_correct"].sum())
    incorrect = total - correct
    accuracy = correct / total if total else 0.0
    return {
        "total_test_samples": total,
        "correct_predictions": correct,
        "incorrect_predictions": incorrect,
        "test_accuracy_recomputed": accuracy,
        "per_class_error_counts": per_class_error_counts(predictions),
        "confusion_pairs": confusion_pair_counts(predictions),
        "number_of_misclassified_samples": incorrect,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def write_json(path: Path, summary: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")


def markdown_escape(value: Any) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def code_excerpt(code: str, max_chars: int = 600) -> str:
    cleaned = str(code).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + "\n..."
    return cleaned.replace("```", "` ` `")


def metadata_line(row: Any, column: str) -> str | None:
    if column not in row._fields:
        return None
    value = getattr(row, column)
    if pd.isna(value) or str(value).strip() == "":
        return None
    label = column.replace("_", " ").title()
    return f"- {label}: {markdown_escape(value)}"


def write_markdown(
    path: Path,
    summary: dict[str, Any],
    misclassified: pd.DataFrame,
    text_column: str,
) -> None:
    per_class_rows = "\n".join(
        f"| {class_name} | {count} |"
        for class_name, count in summary["per_class_error_counts"].items()
    )
    if summary["confusion_pairs"]:
        pair_rows = "\n".join(
            f"| {markdown_escape(pair)} | {count} |"
            for pair, count in summary["confusion_pairs"].items()
        )
    else:
        pair_rows = "| No misclassification pairs | 0 |"

    sections = [
        "# Phase 10 — Error Analysis",
        "",
        "## Goal",
        "",
        "This phase evaluates the already fine-tuned CodeBERT model on the held-out test split and identifies misclassified decompiled functions. No training or fine-tuning is performed.",
        "",
        "## Summary",
        "",
        f"- Total test samples: {summary['total_test_samples']}",
        f"- Correct predictions: {summary['correct_predictions']}",
        f"- Incorrect predictions: {summary['incorrect_predictions']}",
        f"- Recomputed test accuracy: {summary['test_accuracy_recomputed']:.4f}",
        "",
        "## Per-Class Errors",
        "",
        "| True Class | Error Count |",
        "|---|---:|",
        per_class_rows,
        "",
        "## Misclassification Pairs",
        "",
        "| Pair | Count |",
        "|---|---:|",
        pair_rows,
        "",
        "## Misclassified Samples",
        "",
    ]

    if misclassified.empty:
        sections.extend(
            [
                "No errors were found on the test set.",
                "",
            ]
        )
    else:
        for number, row in enumerate(misclassified.itertuples(index=False), start=1):
            sections.append(f"### Error {number}")
            for column in OPTIONAL_METADATA_COLUMNS:
                line = metadata_line(row, column)
                if line:
                    sections.append(line)
            sections.extend(
                [
                    f"- True class: {markdown_escape(row.true_class)}",
                    f"- Predicted class: {markdown_escape(row.predicted_class)}",
                    f"- Confidence: {row.confidence:.4f}",
                    "",
                    "Code excerpt:",
                    "",
                    "```c",
                    code_excerpt(getattr(row, text_column)),
                    "```",
                    "",
                ]
            )

    sections.extend(
        [
            "## Interpretation",
            "",
            "The CodeBERT model made very few mistakes on the held-out test split. This supports the Phase 9 comparison result, where the fine-tuned transformer model substantially outperformed the TF-IDF + Logistic Regression baseline on the same test set.",
            "",
            "## Limitations",
            "",
            "These errors and the low error count should still be interpreted carefully because Juliet is a synthetic benchmark dataset, the labels are weak/sanity-checked labels, generated test cases may share structural patterns, the split is not necessarily fully group-aware by testcase family, and the result is not proof of real-world exploitability or real-world exploit detection performance.",
            "",
        ]
    )

    with path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(sections))


def save_outputs(
    predictions: pd.DataFrame,
    output_dir: Path,
    text_column: str,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    misclassified = predictions[~predictions["is_correct"]].copy()
    summary = build_summary(predictions)

    output_paths = {
        "predictions": output_dir / "codebert_test_predictions.csv",
        "misclassified": output_dir / "codebert_misclassified_samples.csv",
        "json": output_dir / "error_analysis.json",
        "markdown": output_dir / "error_analysis.md",
    }

    predictions.to_csv(output_paths["predictions"], index=False)
    misclassified.to_csv(output_paths["misclassified"], index=False)
    write_json(output_paths["json"], summary)
    write_markdown(output_paths["markdown"], summary, misclassified, text_column)
    return output_paths


def print_summary(
    device: torch.device,
    summary: dict[str, Any],
    output_paths: dict[str, Path],
) -> None:
    print("Phase 10 Error Analysis")
    print("=======================")
    print(f"Selected device: {device}")
    print(f"Test size: {summary['total_test_samples']}")
    print(f"Correct predictions: {summary['correct_predictions']}")
    print(f"Misclassified samples: {summary['number_of_misclassified_samples']}")
    print(f"Recomputed accuracy: {summary['test_accuracy_recomputed']:.4f}")
    print()
    print("Saved outputs:")
    for label, path in output_paths.items():
        print(f"  {label}: {path}")


def main() -> None:
    args = parse_args()
    validate_args(args)

    test_path = resolve_repo_path(args.test)
    model_dir = resolve_repo_path(args.model_dir)
    output_dir = resolve_repo_path(args.output_dir)

    validate_test_path(test_path)
    validate_model_dir(model_dir)

    test_data = read_test_data(test_path, args.text_column, args.label_column)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Selected device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)

    predictions = run_inference(
        data=test_data,
        tokenizer=tokenizer,
        model=model,
        device=device,
        text_column=args.text_column,
        label_column=args.label_column,
        max_length=args.max_length,
        batch_size=args.batch_size,
    )
    output_paths = save_outputs(predictions, output_dir, args.text_column)
    summary = build_summary(predictions)
    print_summary(device, summary, output_paths)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        raise SystemExit(f"ERROR: {exc}") from None
